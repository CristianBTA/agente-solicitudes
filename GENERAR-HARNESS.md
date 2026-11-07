# Generar su harness con su IA

Un **harness** es su forma real de trabajar con datos, escrita paso a paso: qué entrega, con qué herramientas, el control que comprueba cada paso, qué hace si un control falla y qué nunca decide la IA. Con los harness del grupo se alimenta el pipeline: cada uno le enseña cómo se trabaja de verdad en un sector. Ejemplo: [el harness del analista de datos](https://github.com/CristianBTA/subagentes-big-data/pull/12/files).

## Para la persona: tres pasos

1. Si no tiene cuenta de GitHub, créela gratis en https://github.com/signup. Es lo único que necesita.
2. Abra la IA que ya usa (Claude, ChatGPT, Gemini, Copilot u otra) y cópiele este texto:
   ```text
   Conéctate al repositorio https://github.com/CristianBTA/subagentes-big-data y sigue su guía GENERAR-HARNESS.md. Quiero generar el harness.
   ```
   Si su IA no puede abrir enlaces de GitHub, péguele este enlace directo: https://raw.githubusercontent.com/CristianBTA/subagentes-big-data/main/GENERAR-HARNESS.md, o este archivo completo.
3. Responda las 10 preguntas, una a la vez (unos 45 minutos: entre más concreto, más le enseña al pipeline). Al final, su IA hace el *fork* del repositorio y guarda su harness en `harness/<su-usuario>.md`, en su fork. No hace falta *pull request*: el dueño del repositorio recoge los archivos de los forks.

**Con un agente de terminal** (Claude Code, Codex, Copilot en VS Code, Cursor, Gemini CLI), la IA hace el fork y sube el archivo ella misma. **Con un chat**, le entrega el archivo y tres pasos en la página de GitHub.

**No gasta tokens del curso ni pasa por su sitio:** todo ocurre en la conversación con su IA. Su fork es público: no escriba nombres de personas, clientes ni empresas, ni cédulas, cuentas, teléfonos o correos.

---

## Instrucciones para el agente

La persona te pidió «Quiero generar el harness» para el repositorio público **CristianBTA/subagentes-big-data** (pipeline de datos con IA en cinco etapas: la IA propone y una prueba sin IA comprueba). Tu trabajo es un *grill-me*: le haces 10 preguntas sobre su trabajo real con datos, una a la vez, repreguntas cuando la respuesta queda vaga, armas su harness con lo que dijo y, solo al final, haces el fork y lo guardas en `harness/<su-usuario>.md`.

### Límites que no se negocian

- **Primero las preguntas, después el fork.** No clones, no hagas fork ni crees archivos hasta tener las 10 respuestas y el visto bueno de la persona sobre el borrador.
- **Una pregunta por mensaje**, en el orden de esta guía. No adelantes las siguientes ni las respondas por ella.
- **Nada inventado.** El archivo dice solo lo que la persona respondió, ordenado y bien redactado. Lo que no dijo queda «(por completar)».
- **Sin datos reales.** Si escribe un nombre de persona, cliente o empresa, una cédula, una cuenta, un teléfono o un correo, no lo copies: pídele que lo cambie por algo genérico («la entidad», «el cliente», `000.000.001`).
- **Gasta poco.** Lee solo esta guía: no recorras el repositorio. No corras el pipeline (`flujo.js`) ni ningún subagente.
- **Sin firmas de asistentes.** Nada de `Co-Authored-By`, «Generated with…» ni menciones a la herramienta en el commit ni en el archivo: el trabajo es de la persona.
- **Háblale de usted**, en español sencillo (colombiano neutro), con frases cortas. El inglés, solo para términos técnicos.
- Si pide saltarse una pregunta, sáltala y márcala «(por completar)». Si quiere parar, entrégale lo que lleva con el paso de entrega.

### Arranque

En un solo mensaje corto:
1. Una línea: va a armar su harness con 10 preguntas sobre su trabajo real, una a la vez (unos 45 minutos), y al final usted lo guarda en su fork del repositorio.
2. Un recordatorio: sin nombres de personas, clientes ni empresas, ni datos personales.
3. La pregunta 1, con sus ejemplos.

### Cómo revisas cada respuesta

Cada pregunta dice lo que la respuesta debe traer (a y b).
- **Trae a y b:** confírmalo en una línea («Queda claro para el harness») y pasa a la siguiente.
- **Le falta a o b:** repregunta con la pista o con una pregunta concreta sobre lo que falta. Como máximo dos repreguntas por pregunta; después sigue con lo que haya y marca lo que falte «(por completar)».
- **Copia un ejemplo:** pídele su propio caso: su herramienta, su paso, su cifra.
- **Responde otra cosa:** vuelve a hacerle la pregunta con otras palabras.

### Las 10 preguntas

#### 1 · Su rol y lo que entrega (`H1`)

- **Va en:** 1. Propósito
- **Pregunta:** ¿Qué rol tiene y qué entrega con datos? Una o dos frases.
- **Ejemplos de otros sectores:**
  - Analista de cartera en un banco: entrego cada lunes un tablero de mora por oficina.
  - Desarrollador en una EPS: mantengo el proceso que carga las citas cada noche.
  - Profesional de planeación en una alcaldía: entrego el informe trimestral de contratos.
- **La respuesta debe decir:** a) Nombra su rol o su área de trabajo. b) Dice qué entrega con datos: un tablero, un reporte, un proceso de carga, un modelo o un informe.
- **Pista para repreguntar:** Piense en lo que recibe la persona que depende de su trabajo: ¿qué le entrega y cada cuánto?

#### 2 · La pregunta de negocio que responde su trabajo (`H10`)

- **Va en:** 1. Propósito: la pregunta que responde
- **Pregunta:** Escriba una pregunta de negocio que su trabajo responde con datos: de quién (sujeto), qué se cuenta o se suma (medida) y en qué periodo.
- **Ejemplos de otros sectores:**
  - ¿Cuánto dinero en mora tiene cada oficina al cierre de cada semana de 2026?
  - ¿Cuántas citas se pierden por especialidad cada mes de este año?
  - ¿Qué valor contrató cada secretaría por modalidad en 2025?
- **La respuesta debe decir:** a) La pregunta tiene sujeto (de quién), medida (qué se cuenta o se suma) y periodo. b) Se puede responder con columnas de un conjunto de datos, sin pedir opiniones.
- **Pista para repreguntar:** Revise que su pregunta diga de quién, qué número y de cuándo; si pide «quién lo hizo bien», un dato no lo mide.

#### 3 · Sus herramientas y el papel de la IA (`H2`)

- **Va en:** 3. Herramientas
- **Pregunta:** ¿Con qué herramientas trabaja los datos y para qué usa hoy la IA?
- **Ejemplos de otros sectores:**
  - SQL Server y Power BI; la IA me ayuda a escribir medidas DAX.
  - Python con pandas en Colab; le pido a la IA que me explique errores.
  - Excel y el sistema de la entidad; todavía no uso IA en el trabajo.
- **La respuesta debe decir:** a) Nombra al menos una herramienta con la que trabaja los datos. b) Dice para qué usa la IA en su trabajo, o que todavía no la usa.
- **Pista para repreguntar:** Nombre la herramienta donde más horas pasa con los datos y diga una tarea concreta en la que la IA le ayuda o le podría ayudar.

#### 4 · Su trabajo en pasos (`H3`)

- **Va en:** 4. Procedimiento: los pasos
- **Pregunta:** Cuente su trabajo en 4 a 6 pasos, desde que llega la solicitud (o el dato) hasta que entrega.
- **Ejemplos de otros sectores:**
  - 1 Recibo la solicitud. 2 Reviso que la fuente tenga los campos. 3 Armo la consulta. 4 Valido los datos. 5 Construyo el tablero. 6 Entrego.
  - 1 Llega el archivo. 2 Lo cargo. 3 Limpio fechas y montos. 4 Cruzo con la tabla maestra. 5 Publico la tabla final.
- **La respuesta debe decir:** a) Enumera varios pasos en orden. b) Los pasos van desde la solicitud o la fuente hasta la entrega.
- **Pista para repreguntar:** Empiece por lo primero que hace cuando le llega un pedido y termine en el momento en que alguien recibe el resultado.

#### 5 · Cómo sabe que cada paso salió bien (`H4`)

- **Va en:** 4. Procedimiento: el control de cada paso
- **Pregunta:** Para sus pasos, ¿cómo sabe que salió bien? Diga contra qué lo compara: un conteo, una suma, la fuente o una regla escrita.
- **Ejemplos de otros sectores:**
  - Paso 4: el número de filas de mi consulta es igual al del sistema de origen.
  - Paso 5: la suma de la columna de valor en el tablero es igual a la de la consulta.
  - Paso 3: ninguna fecha queda fuera del rango del periodo pedido.
- **La respuesta debe decir:** a) Nombra un control concreto para al menos uno de sus pasos. b) El control compara contra algo que la IA no controla: la fuente, un conteo, una suma o una regla escrita.
- **Pista para repreguntar:** Si mañana alguien duda de su cifra, ¿qué número le mostraría para probar que está bien, y contra qué lo compara?

#### 6 · Qué hace cuando un control falla (`H5`)

- **Va en:** 4. Procedimiento: si el control falla
- **Pregunta:** Si un control falla, ¿qué hace y a quién le avisa? ¿Sigue o se detiene?
- **Ejemplos de otros sectores:**
  - Si el conteo no cuadra, no publico: le pido al DBA que revise la consulta.
  - Si aparecen fechas imposibles, detengo la carga y aviso al dueño del sistema.
  - Si la suma no coincide, reviso primero las relaciones entre tablas antes de tocar el tablero.
- **La respuesta debe decir:** a) Dice qué hace cuando el control falla. b) Se detiene o escala antes de entregar: no sigue como si nada.
- **Pista para repreguntar:** Imagine que el número no cuadra a las 5 de la tarde y el informe sale mañana: ¿qué hace primero y a quién le escribe?

#### 7 · Lo que nunca le deja decidir a la IA (`H6`)

- **Va en:** 2. Principios: lo que la IA no decide
- **Pregunta:** ¿Qué le pide a la IA y qué nunca le deja decidir sola?
- **Ejemplos de otros sectores:**
  - Le pido un borrador de la consulta; las cifras finales las verifico yo contra la fuente.
  - Le pido ideas de diseño para el tablero; ningún número sale de ella.
  - Le pido que me explique un error; el arreglo lo pruebo antes de usarlo.
- **La respuesta debe decir:** a) Dice qué le pide a la IA. b) Dice qué decide o verifica una persona antes de usarlo.
- **Pista para repreguntar:** Separe en dos: lo que la IA le propone y lo que usted comprueba antes de entregarlo.

#### 8 · Cuánta diferencia acepta (`H7`)

- **Va en:** 5. Criterio de aceptación
- **Pregunta:** ¿Qué diferencia acepta entre su resultado y la fuente? ¿Cero? ¿Un redondeo acordado antes?
- **Ejemplos de otros sectores:**
  - Diferencia cero en conteos y totales; los decimales se redondean a dos cifras, acordado con el área antes de empezar.
  - Acepto hasta un 0,5 % de diferencia en montos por tipo de cambio, y lo dejo escrito en el informe.
- **La respuesta debe decir:** a) Da un umbral o una tolerancia (por ejemplo, cero). b) Dice contra qué se mide o cuándo se acuerda esa tolerancia.
- **Pista para repreguntar:** Si su total y el de la fuente difieren en 3 pesos, ¿lo entrega o no? ¿Quién decidió esa regla y cuándo?

#### 9 · El error que más se repite (`H8`)

- **Va en:** 6. Errores frecuentes y la prueba que los atrapa
- **Pregunta:** ¿Cuál es el error de datos que más se repite en su trabajo, cómo lo nota y qué prueba lo habría atrapado antes?
- **Ejemplos de otros sectores:**
  - Fechas con día y mes al revés; lo noto cuando un mes sale vacío; una prueba de rango de fechas lo atraparía.
  - Una relación entre tablas que duplica filas; lo noto porque el conteo sube; comparar el conteo antes y después del cruce lo atraparía.
  - Montos con punto de miles leídos como decimales; una prueba de rango de valores lo atraparía.
- **La respuesta debe decir:** a) Describe un error de datos concreto que se le repite. b) Propone una prueba o control que lo habría detectado antes de entregar.
- **Pista para repreguntar:** Piense en la última vez que tuvo que corregir un informe ya enviado: ¿qué falló y qué comprobación lo habría frenado?

#### 10 · Los datos personales que toca (`H9`)

- **Va en:** 7. Datos personales y sensibles
- **Pregunta:** ¿Qué tipo de datos personales o sensibles toca y qué hace con ellos antes de pasarlos a una IA o publicarlos? No escriba ninguno real.
- **Ejemplos de otros sectores:**
  - Cédulas y teléfonos de clientes: los quito o los cambio por un código antes de pegar algo en un chat.
  - Diagnósticos de pacientes: solo publico conteos por grupo, nunca registros individuales.
  - No manejo datos personales; solo datos agregados por municipio.
- **La respuesta debe decir:** a) Nombra qué tipo de dato personal o sensible maneja, o dice que no maneja ninguno. b) Dice cómo lo protege: quitarlo, agregarlo por grupo, cambiarlo por un código o no pasarlo a la IA.
- **Pista para repreguntar:** Si tuviera que pegar una muestra de sus datos en un chat de IA, ¿qué columnas quitaría antes y por qué?

### Armar el harness

Con las 10 respuestas, arma el borrador con esta plantilla y muéstraselo completo. Pregúntale una sola vez si quiere corregir algo y aplica sus correcciones.

- Respeta los títulos de las secciones tal cual: la revisión sin IA los busca.
- Redacta en tercera persona y en presente («Recibe la solicitud…», «Compara el conteo…»).
- Un control que la persona propone pero todavía no hace va marcado **(recomendado)**.

```markdown
# Harness · <rol, en pocas palabras>

> Harness de <usuario de GitHub> para el pipeline de datos con IA del repositorio CristianBTA/subagentes-big-data. Sin datos personales ni nombres de personas, clientes o empresas.

## 1. Propósito

<rol y lo que entrega, cada cuánto y a quién (pregunta 1)>

**La pregunta de negocio que responde:** <sujeto, medida y periodo (pregunta 2)>

## 2. Principios de trabajo

1. La IA propone; una prueba sin IA comprueba.
2. Ninguna cifra se entrega sin compararla contra la fuente.
3. <lo que la IA nunca decide sola (pregunta 7)>

## 3. Herramientas

| Herramienta | Uso |
|---|---|
| <herramienta> | <para qué> |
| IA | <para qué la usa, o «todavía no la usa» (pregunta 3)> |

## 4. Procedimiento

Cada paso tiene su control. Si el control no se cumple, no se avanza.

| # | Paso | Control |
|---|---|---|
| 1 | <paso (pregunta 4)> | <cómo sabe que salió bien (pregunta 5), o «(por definir)»> |

**Si un control falla:** <qué hace, a quién avisa y si se detiene (pregunta 6)>

## 5. Criterio de aceptación

<diferencia que acepta contra la fuente y quién la acordó, y cuándo (pregunta 8)>

## 6. Errores frecuentes y la prueba que los atrapa

| Error | Cómo se nota | Prueba que lo habría atrapado |
|---|---|---|
| <error (pregunta 9)> | <síntoma> | <prueba> |

## 7. Datos personales y sensibles

<qué tipo de dato toca y cómo lo protege antes de pasarlo a una IA o publicarlo (pregunta 10)>

## Origen

Escrito el <AAAA-MM-DD> con el grill-me de `GENERAR-HARNESS.md`, con las respuestas de la persona. Lo marcado «(por completar)» no se respondió; nada se inventó.
```

### Fork y entrega

Elige el modo tú mismo; no le preguntes cuál prefiere.

**A · Si puedes usar una terminal con git y `gh`** (la cuenta de GitHub de la persona):
```bash
USUARIO=$(gh api user --jq .login)       # si falla, pídele que corra «gh auth login» y vuelve a intentarlo
gh repo fork CristianBTA/subagentes-big-data --clone -- subagentes-big-data-$USUARIO   # si ya tenía un fork, gh usa ese
cd subagentes-big-data-$USUARIO          # si la carpeta ya existía, entra a ella y corre: git fetch upstream
git fetch upstream main
git switch -c harness upstream/main          # si la rama ya existe: git switch harness
mkdir -p harness                             # guarda aquí el borrador aprobado: harness/$USUARIO.md
python3 herramientas/revisar_grill.py harness/$USUARIO.md     # sin IA; en Windows: py -3 herramientas/revisar_grill.py …
git add harness/$USUARIO.md                  # solo ese archivo
git commit -m "Harness: <rol en pocas palabras>"
git push -u origin harness
```
- `revisar_grill.py` no usa IA: revisa las secciones, que no haya datos personales y que no traiga texto con forma de orden para una IA. Debe terminar en «✓ harness listo». Si marca algo, corrígelo con la persona y vuelve a correrlo.
- El fork queda con su nombre de siempre: si la persona lo hizo antes del 6 de noviembre en la noche, se llama `agente-solicitudes` (el nombre viejo). Usa el que muestre `git remote get-url origin`.

**B · Si eres un chat sin terminal:** entrégale el archivo completo en un solo bloque de código Markdown y estos tres pasos (pon su usuario en los enlaces si te lo dijo):
1. Abrir https://github.com/CristianBTA/subagentes-big-data/fork y tocar «Create fork». Si ya tiene su fork, usar ese.
2. Abrir `https://github.com/<su-usuario>/subagentes-big-data/new/main?filename=harness/<su-usuario>.md` (si su fork se llama `agente-solicitudes`, cambiar esa parte del enlace) y pegar el archivo.
3. Tocar «Commit changes…», dejar «Commit directly to the main branch» y confirmar con «Commit changes».

Dile que no pudiste correr la revisión sin IA: el dueño la corre al recoger los archivos.

### Lo que le dices al final

En pocas líneas:
- el enlace a su archivo en el fork (`https://github.com/<su-usuario>/<su-fork>/blob/harness/harness/<su-usuario>.md`, o `blob/main/…` en el modo B);
- la línea `RESUMEN` de `revisar_grill.py` (o que no se pudo correr);
- qué quedó «(por completar)», si algo;
- que no hace falta pull request: el dueño del repositorio recoge los archivos de los forks.

### Lista de chequeo del agente

- [ ] Hice las 10 preguntas una a la vez, con sus ejemplos, y repregunté cuando faltaba a o b.
- [ ] El harness dice solo lo que la persona respondió; lo que faltó quedó «(por completar)».
- [ ] No hay nombres de personas, clientes ni empresas, ni datos personales.
- [ ] La persona aprobó el borrador antes del fork.
- [ ] Solo agregué `harness/<su-usuario>.md`, en la rama `harness` de su fork (o le di los pasos del modo B).
- [ ] Corrí `revisar_grill.py` y terminó en «✓ harness listo» (o, en el modo B, dije que no pude correrlo).
- [ ] Sin firmas de asistentes en el commit ni en el archivo.
