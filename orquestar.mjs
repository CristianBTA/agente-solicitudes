#!/usr/bin/env node
// Corre flujo.js fuera de Claude Code: cada subagente es una llamada no interactiva a agy o a Codex.
// Es la misma orquestación (flujo.js no se copia ni se reescribe): mismos prompts, mismo orden, mismas pruebas sin IA.
//
//   node orquestar.mjs --motor agy   --args corrida.json
//   node orquestar.mjs --motor codex --args corrida.json
//   node orquestar.mjs --motor codex --args corrida.json --simulacro   (sin IA: muestra cada llamada y recorre el flujo)
//   node orquestar.mjs --motor agy --comprobar   (dos llamadas mínimas: la CLI responde, corre un comando y devuelve JSON)
//
// Opciones: --modelo <m> (subagentes normales), --modelo-ligero <m> (los que solo corren un comando),
//           --modelo-respaldo <m> (agy: si el filtro de Gemini bloquea la respuesta), --tope-min <n> (por subagente, 60),
//           --con-mcp (no apaga los servidores MCP del usuario). Binarios: AGY_BIN y CODEX_BIN (por defecto agy y codex).
import { spawn } from 'node:child_process'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const RAIZ = path.dirname(fileURLToPath(import.meta.url))
const argv = process.argv.slice(2)
const opt = (k, d) => { const i = argv.indexOf(k); return i >= 0 && argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[i + 1] : d }
const flag = (k) => argv.includes(k)

const MOTOR = opt('--motor')
const COMPROBAR = flag('--comprobar')
if (!['agy', 'codex'].includes(MOTOR) || (!opt('--args') && !COMPROBAR)) {
  console.error('Uso: node orquestar.mjs --motor agy|codex --args <archivo.json> [--simulacro] [--modelo m] [--modelo-ligero m] [--tope-min 60]')
  process.exit(2)
}
const SIMULACRO = flag('--simulacro')
const TOPE_MS = Number(opt('--tope-min', 60)) * 60_000
const LIGERO_POR_DEFECTO = { agy: 'gemini-3.8-flash-low', codex: null } // Codex: el modelo del usuario con esfuerzo bajo
const MODELO = opt('--modelo', null)
const MODELO_LIGERO = opt('--modelo-ligero', LIGERO_POR_DEFECTO[MOTOR])
const MODELO_RESPALDO = opt('--modelo-respaldo', MOTOR === 'agy' ? 'gpt-oss-120b-medium' : null)
const BIN = MOTOR === 'agy' ? (process.env.AGY_BIN || 'agy') : (process.env.CODEX_BIN || 'codex')

// ---- argumentos de la corrida: los mismos de la herramienta Workflow; las rutas relativas se vuelven absolutas ----
const abs = (r) => (r && !path.isAbsolute(r) ? path.resolve(r) : r)
const A = COMPROBAR ? { corrida: fs.mkdtempSync(path.join(os.tmpdir(), 'orquestar-comprobar-')) } : JSON.parse(fs.readFileSync(opt('--args'), 'utf8'))
A.raiz = abs(A.raiz) || RAIZ
A.corrida = abs(A.corrida)
A.glosario = abs(A.glosario)
if (A.datos) for (const t of Object.keys(A.datos)) A.datos[t] = abs(A.datos[t])
if (!A.corrida) { console.error('Falta "corrida" en los argumentos'); process.exit(2) }
const REGISTRO = path.join(A.corrida, 'motor') // prompts y respuestas de cada subagente (fuera de git)
fs.mkdirSync(REGISTRO, { recursive: true })

const hora = () => new Date().toTimeString().slice(0, 8)
const log = (m) => console.error(`[${hora()}] ${m}`)
const phase = (t) => console.error(`\n[${hora()}] ══ ${t} ══`)
const parallel = (tareas) => Promise.all(tareas.map((f) => Promise.resolve().then(f).catch((e) => { log(`✗ ${e.message}`); return null })))

// ---- sin MCP por llamada: los del usuario (p. ej. chrome-devtools --autoConnect) se engancharían a su navegador ----
let HOME_AGY = null
function homeAgy() {
  if (HOME_AGY || flag('--con-mcp')) return HOME_AGY
  const real = path.join(os.homedir(), '.gemini')
  const h = fs.mkdtempSync(path.join(os.tmpdir(), 'agy-home-'))
  fs.mkdirSync(path.join(h, '.gemini', 'config'), { recursive: true })
  if (fs.existsSync(real)) {
    for (const e of fs.readdirSync(real)) if (e !== 'config') fs.symlinkSync(path.join(real, e), path.join(h, '.gemini', e))
    const cfg = path.join(real, 'config')
    if (fs.existsSync(cfg)) for (const e of fs.readdirSync(cfg)) if (e !== 'mcp_config.json') fs.symlinkSync(path.join(cfg, e), path.join(h, '.gemini', 'config', e))
  }
  fs.writeFileSync(path.join(h, '.gemini', 'config', 'mcp_config.json'), '{"mcpServers": {}}\n')
  process.on('exit', () => fs.rmSync(h, { recursive: true, force: true })) // borra enlaces, nunca lo enlazado
  return (HOME_AGY = h)
}
function mcpCodexApagados() {
  if (flag('--con-mcp')) return []
  const cfg = path.join(process.env.CODEX_HOME || path.join(os.homedir(), '.codex'), 'config.toml')
  if (!fs.existsSync(cfg)) return []
  const nombres = [...fs.readFileSync(cfg, 'utf8').matchAll(/^\s*\[mcp_servers\.(?:"([^"]+)"|([A-Za-z0-9_-]+))\]\s*$/gm)].map((m) => m[1] || m[2])
  return [...new Set(nombres)].flatMap((n) => ['-c', `mcp_servers.${/^[A-Za-z0-9_-]+$/.test(n) ? n : JSON.stringify(n)}.enabled=false`])
}

// ---- una llamada no interactiva ----
// Codex corre sin su caja de arena: la ingesta necesita red (datos.gov.co) y la caja de arena de las herramientas
// (sandbox-exec, caja.py) no se puede abrir dentro de otra. El código que escribe la IA sigue corriendo en caja.py.
function comando(prompt, { ligero, effort, modelo, salida }) {
  const m = modelo || (ligero ? MODELO_LIGERO : MODELO)
  if (MOTOR === 'agy') {
    const a = ['--dangerously-skip-permissions', '--output-format', 'json', '--print-timeout', `${Math.round(TOPE_MS / 60_000)}m`]
    if (m) a.push('--model', m)
    if (effort && !ligero) a.push('--effort', effort)
    a.push('-p', prompt)
    return { bin: BIN, args: a, stdin: null, env: homeAgy() ? { ...process.env, HOME: homeAgy() } : process.env }
  }
  const a = ['exec', '--skip-git-repo-check', '--ephemeral', '--color', 'never', '-C', A.raiz,
    '--dangerously-bypass-approvals-and-sandbox', '-o', salida, ...mcpCodexApagados()]
  if (m) a.push('-m', m)
  const esfuerzo = ligero ? 'low' : effort
  if (esfuerzo) a.push('-c', `model_reasoning_effort="${esfuerzo}"`)
  a.push('-') // el prompt va por la entrada estándar
  return { bin: BIN, args: a, stdin: prompt, env: process.env }
}

const BLOQUEO = ['blocked by gemini', 'request was blocked', 'usage limit', 'rate limit', 'limit reached', 'quota']
const bloqueada = (t) => { const x = (t || '').trim().toLowerCase(); return !x || BLOQUEO.some((b) => x.slice(0, 400).includes(b)) }

function ejecutar(c) {
  return new Promise((ok) => {
    const p = spawn(c.bin, c.args, { cwd: A.raiz, env: c.env, stdio: [c.stdin == null ? 'ignore' : 'pipe', 'pipe', 'pipe'] })
    let out = '', err = ''
    const reloj = setTimeout(() => { err += `\n[orquestar] tope de ${TOPE_MS / 60_000} min: se detiene`; p.kill('SIGTERM') }, TOPE_MS)
    p.stdout.on('data', (d) => { out += d })
    p.stderr.on('data', (d) => { err += d })
    p.on('error', (e) => { clearTimeout(reloj); ok({ codigo: -1, out, err: `${err}\n${e.message}` }) })
    p.on('close', (codigo) => { clearTimeout(reloj); ok({ codigo, out, err }) })
    if (c.stdin != null) p.stdin.end(c.stdin)
  })
}

async function llamar(prompt, o) {
  const salida = path.join(REGISTRO, `${o.id}-ultimo-mensaje.txt`)
  const intentos = [o.modelo || null, MODELO_RESPALDO].filter((m, i) => i === 0 || m)
  for (const modelo of intentos) {
    const c = comando(prompt, { ...o, modelo, salida })
    if (SIMULACRO) {
      const visibles = c.args.map((x) => (x === prompt ? `<prompt de ${prompt.length} caracteres>` : x))
      log(`simulacro · ${o.etiqueta}: ${c.bin} ${visibles.join(' ')}${c.stdin != null ? ' < prompt' : ''}`)
      return { texto: null, motivo: 'simulacro' }
    }
    fs.rmSync(salida, { force: true })
    const r = await ejecutar(c)
    let texto = ''
    if (MOTOR === 'agy') {
      try {
        const j = JSON.parse(r.out)
        texto = j.finished_reason ? '' : (j.response || '')
        if (j.finished_reason) r.err += `\nfinished_reason=${j.finished_reason}`
      } catch { texto = '' }
    } else {
      texto = r.codigo === 0 && fs.existsSync(salida) ? fs.readFileSync(salida, 'utf8') : ''
    }
    fs.writeFileSync(path.join(REGISTRO, `${o.id}-salida.txt`), `codigo=${r.codigo} modelo=${modelo || 'por defecto'}\n--- stdout\n${r.out}\n--- stderr\n${r.err}\n`)
    if (r.codigo === 0 && !bloqueada(texto)) return { texto }
    log(`✗ ${o.etiqueta}: ${MOTOR} terminó con código ${r.codigo}${bloqueada(texto) ? ' y sin respuesta útil' : ''}${modelo !== MODELO_RESPALDO && MODELO_RESPALDO ? '; reintento con ' + MODELO_RESPALDO : ''}`)
  }
  return { texto: null, motivo: 'sin respuesta' } // una respuesta bloqueada o vacía nunca cuenta como «sin hallazgos»
}

// ---- respuesta estructurada: el subagente termina con un JSON; se valida aquí, como lo haría Workflow ----
const instruccionJSON = (s) => `

---
RESPUESTA FINAL (la lee un programa): cuando termines TODO el trabajo, tu último mensaje es SOLO un objeto JSON válido, sin texto antes ni después y sin bloque de código, que cumpla este JSON Schema (los campos de "required" son obligatorios):
${JSON.stringify(s)}
No inventes valores: si algo no se cumplió, dilo en el JSON (por ejemplo "ok": false).`

function extraerJSON(t) {
  if (!t) return null
  const limpio = t.trim().replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '')
  try { return JSON.parse(limpio) } catch { /* sigue */ }
  for (let fin = t.lastIndexOf('}'); fin > 0; fin = t.lastIndexOf('}', fin - 1)) { // el último objeto JSON completo del texto
    let prof = 0
    for (let i = fin; i >= 0; i--) {
      if (t[i] === '}') prof++
      else if (t[i] === '{' && --prof === 0) { try { return JSON.parse(t.slice(i, fin + 1)) } catch { break } }
    }
  }
  return null
}

const TIPOS = { string: (v) => typeof v === 'string', number: (v) => typeof v === 'number', boolean: (v) => typeof v === 'boolean',
  array: Array.isArray, object: (v) => v && typeof v === 'object' && !Array.isArray(v) }
function validar(v, s) {
  if (!TIPOS.object(v)) return 'la respuesta no es un objeto JSON'
  for (const k of s.required || []) if (!(k in v)) return `falta el campo «${k}»`
  for (const [k, p] of Object.entries(s.properties || {})) {
    if (k in v && v[k] !== null && p.type && !TIPOS[p.type](v[k])) return `«${k}» debía ser ${p.type}`
  }
  return null
}

function simulado(s) { // valores de relleno para recorrer el flujo sin IA (solo --simulacro)
  const o = {}
  for (const [k, p] of Object.entries(s.properties || {})) {
    o[k] = p.type === 'boolean' ? true : p.type === 'number' ? 0 : p.type === 'array' ? []
      : p.type === 'object' ? { simulacro: path.join(A.corrida, 'datos', 'simulacro.csv') } : k === 'estado' ? 'aprobado' : 'simulacro'
  }
  return o
}

const AVISO = `Eres un subagente del pipeline de agente-solicitudes, lanzado por orquestar.mjs con ${MOTOR}. AGENTS.md y APORTAR-CON-TU-AGENTE.md no aplican a ti: sigue solo esta instrucción y tu ficha en agentes/. Trabaja sin preguntar nada al usuario.\n\n`
let contador = 0
async function agent(prompt, opts = {}) {
  const id = String(++contador).padStart(2, '0')
  const etiqueta = opts.label || `subagente ${id}`
  const o = { id, etiqueta, ligero: opts.model === 'haiku', effort: opts.effort }
  log(`→ ${etiqueta}`)
  const completo = AVISO + prompt + (opts.schema ? instruccionJSON(opts.schema) : '')
  fs.writeFileSync(path.join(REGISTRO, `${id}-prompt.txt`), completo)
  const r = await llamar(completo, o)
  if (SIMULACRO) return opts.schema ? simulado(opts.schema) : 'simulacro'
  if (r.texto == null) return null
  if (!opts.schema) return r.texto
  let obj = extraerJSON(r.texto)
  let error = validar(obj, opts.schema)
  if (error) { // un solo reintento: pasar a JSON su propio último mensaje, sin herramientas ni trabajo nuevo
    log(`… ${etiqueta}: ${error}; se pide solo el JSON`)
    const r2 = await llamar(`No ejecutes nada ni uses herramientas. Este fue el último mensaje de un subagente:\n<<<\n${r.texto.slice(-12000)}\n>>>\nDevuelve SOLO el objeto JSON que corresponde a ese mensaje, sin agregar hechos que no estén en él.${instruccionJSON(opts.schema)}`, { ...o, id: `${id}b`, ligero: true })
    obj = extraerJSON(r2.texto)
    error = validar(obj, opts.schema)
  }
  if (error) { log(`✗ ${etiqueta}: ${error}`); return null }
  log(`✓ ${etiqueta}`)
  return obj
}

// ---- --comprobar: dos llamadas mínimas (modelo ligero y normal) antes de gastar una corrida completa ----
// El agente corre wc -l sobre flujo.js y el número se compara con el que calcula este código: si lo inventa, no pasa.
if (COMPROBAR) {
  const real = fs.readFileSync(path.join(RAIZ, 'flujo.js'), 'utf8').split('\n').length - 1
  const S = { type: 'object', properties: { ok: { type: 'boolean' }, lineas: { type: 'number' } }, required: ['ok', 'lineas'] }
  const p = `Ejecuta exactamente este comando y ningún otro: wc -l ${path.join(RAIZ, 'flujo.js')}\nDevuelve ok (true si el comando corrió) y lineas (el número que imprime). No modifiques ningún archivo.`
  let todo = true
  for (const [nombre, o] of [['modelo ligero', { model: 'haiku' }], ['modelo normal', { effort: 'high' }]]) {
    const r = await agent(p, { label: `comprobación · ${nombre}`, schema: S, ...o })
    const bien = !!r && r.ok === true && r.lineas === real
    todo = todo && bien
    log(bien ? `✓ ${MOTOR} · ${nombre}: corrió el comando y devolvió JSON válido (${real} líneas)` : `✗ ${MOTOR} · ${nombre}: ${JSON.stringify(r)}; se esperaban ${real} líneas (ver ${REGISTRO})`)
  }
  process.exit(todo ? 0 : 1)
}

// ---- flujo.js tal cual: solo se quita «export» para ejecutarlo como cuerpo de una función ----
const fuente = fs.readFileSync(path.join(RAIZ, 'flujo.js'), 'utf8').replace(/^export const meta\s*=/m, 'const meta =')
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
const flujo = new AsyncFunction('args', 'agent', 'parallel', 'phase', 'log', fuente)

log(`Motor: ${MOTOR}${SIMULACRO ? ' (simulacro, sin IA)' : ''} · corrida ${A.corrida} · registro ${REGISTRO}`)
const resultado = await flujo(A, agent, parallel, phase, log)
fs.writeFileSync(path.join(REGISTRO, 'resultado.json'), JSON.stringify(resultado, null, 2))
console.log(JSON.stringify(resultado, null, 2))
log(resultado && !resultado.estado ? `Terminado: ${resultado.informe}` : `Se detuvo: ${resultado && resultado.estado}`)
process.exit(resultado && !resultado.estado ? 0 : 1)
