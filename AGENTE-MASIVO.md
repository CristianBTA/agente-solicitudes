# Agente masivo de datos públicos: cómo usarlo

El agente recorre un catálogo completo de datos abiertos (datos.gov.co tiene 8.470 conjuntos). Con mediciones sin IA, encuentra los conjuntos que son **big data de verdad** y que permiten decir «este contrato está así, aquí, y tiene tal impacto». A los mejores les pide a la IA una **ficha de oportunidad**: preguntas de costo, calidad e impacto para que **las personas** hagan el análisis. Después valida cada ficha sin IA contra la fuente real.

La IA propone y una prueba sin IA comprueba. **Que una ficha pase el validador no la hace publicable:** el validador mide la forma y el juicio de valor lo hacen un juez ciego y las personas.

## Antes de empezar

```bash
git clone https://github.com/CristianBTA/agente-solicitudes && cd agente-solicitudes
python3.13 -m venv .venv && .venv/bin/pip install --require-hashes -r requirements.txt
```

**La primera vez cuenta las filas de todo el catálogo**, y eso tarda horas: unos 8.470 conjuntos, de 1 a 4 segundos cada uno. Queda en `fuentes/catalogo/.cache.json`; las veces siguientes usa esa caché, y `--actualizar` retoma el conteo. Nada de eso entra a Git.

## Tres formas de invocarlo

### 1. Desde la terminal, con agy como la IA que escribe las fichas

```bash
.venv/bin/python herramientas/agente_masivo.py www.datos.gov.co --trabajo fuentes/fichas/mi-corrida --top 8 --motor agy
```

### 2. Con cualquier IA de terminal (Claude Code, Codex, Gemini CLI u otra), que es la que escribe

Pégale este texto:

```text
En la carpeta del repositorio agente-solicitudes corre: .venv/bin/python herramientas/agente_masivo.py www.datos.gov.co --trabajo fuentes/fichas/mi-corrida --top 8 --motor ninguno. Después escribe las fichas siguiendo el ENCARGO.md que genera en esa carpeta, cada una con su bucle de validación, sin tocar los archivos *.dictamen.json. Al final corre el mismo comando con --solo-validar y muéstrame RESULTADO.md.
```

### 3. Paso a paso, sin ninguna IA conectada

1. Corre el comando con `--motor ninguno`. Deja listos los candidatos, su tamaño medido y el `ENCARGO.md`.
2. Escribe o consigue las fichas en `fuentes/fichas/mi-corrida/fichas/<id>.json`.
3. Valida con `--solo-validar`.

**Los chats sin terminal** (ChatGPT o Gemini en el navegador) no sirven para este agente: necesita leer el catálogo local y consultar el portal. Para aportar al repositorio desde un chat está [«Conectar la IA»](README.md#conectar-la-ia).

## Llamarlo con una palabra, en tu propia herramienta

Si tu IA de terminal permite comandos propios, crea uno con el texto de la forma 2 y un nombre como `agente-masivo`. Ese comando va en **tu** configuración personal, **nunca dentro de este repositorio**. Por ejemplo, en Claude Code es un archivo en `~/.claude/commands/`.

## Opciones

| Opción | Qué hace |
|---|---|
| `<dominio>` | El portal Socrata, por ejemplo `www.datos.gov.co` |
| `--trabajo <carpeta>` | Dónde quedan `ENCARGO.md`, `fichas/` y `RESULTADO.md` |
| `--top 8` | Cuántos candidatos, de mayor a menor relevancia |
| `--min-filas 1000000` | Tamaño mínimo para ser candidato |
| `--motor agy` o `--motor ninguno` | agy escribe las fichas, o se imprime el texto para otra IA |
| `--actualizar` | Retoma el conteo del catálogo completo |
| `--solo-validar` | Solo valida las fichas que ya están en la carpeta |

## Qué hace, paso a paso

1. **Catálogo sin IA** (`explorador_catalogo.py`): inventario, filas reales y riesgo de datos personales.
2. **Relevancia sin IA** (`relevancia_catalogo.py`): si cada conjunto permite decir estado, lugar e impacto, y con qué llaves de cruce.
3. **Candidatos:** los mejores con al menos `--min-filas`.
4. **Tamaño medido sin IA** (`dictamen_bigdata.py`): nivel 1, «no es big data»; nivel 2, «frontera»; nivel 3, «big data». La IA no escribe este dato. Si un conjunto no se puede medir, el agente lo avisa y lo deja fuera.
5. **Encargo para la IA,** desde `plantillas/encargo_fichas.md`.
6. **La IA escribe las fichas.**
7. **Validación sin IA,** contra la fuente real y sin caché (`validar_ficha.py`, de V1 a V16): columnas, consultas reales, cruces medidos, grano, sumas creíbles, lugar, k-anonimato, normas verificadas y que no haya conclusiones. El resultado queda en `RESULTADO.md`.

## Reglas que el agente no negocia

- Ninguna fila de datos se guarda en el repositorio: todo vive en `fuentes/`, que está fuera de Git.
- Las columnas personales se excluyen. Que un dato sea público no autoriza a usar cédulas, cuentas ni nombres (Ley 1712 de 2014 y Ley 1581 de 2012).
- **La IA no concluye:** el análisis lo hacen las personas.
