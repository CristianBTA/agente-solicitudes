# Conectar la compuerta con un subagente de Claude Code

Esta carpeta se llama así, y no `.claude`, a propósito: el repositorio es público y no lleva configuración de ninguna herramienta. Cada quien la copia en su máquina.

1. Clone este repositorio en `$HOME/agente-solicitudes` e instale el entorno (`python3 -m venv .venv && .venv/bin/pip install --require-hashes -r requirements.txt`). Si lo clona en otra parte, defina `COMPUERTA_HOME` con esa ruta.
2. Copie el subagente a su máquina, fuera de cualquier repositorio:
   ```bash
   cp conexion/claude-code/ingeniero-datos-seguro.md ~/.claude/agents/
   ```
3. Pídale el código a ese subagente.

## Qué pasa

- Cada vez que el subagente guarda un `.py` o un `.ipynb`, el gancho lo revisa. Si no pasa, el motivo le vuelve y tiene que corregir.
- Cuando termina, el gancho revisa todo lo que tocó. Si algo no pasa, sigue trabajando, hasta 2 rondas.
- Si después de 2 rondas sigue sin pasar, el archivo queda en cuarentena (`.bloqueado`) y lo decide una persona.
- Si el gancho no puede correr (falta el entorno, falta Bandit), bloquea: nunca se da por bueno sin revisión.

## Para conectar otro subagente

Copie el bloque `hooks` del encabezado de `ingeniero-datos-seguro.md` en su subagente, y dele `Write` y `Edit`: un subagente que solo responde en el chat no deja nada que revisar.

## Cuidado: se puede quedar sin freno y sin aviso

Se probó el 6 de noviembre de 2026, con Claude Code 2.1.319, pidiéndole a un subagente de verdad un código que la compuerta bloquea:

| Dónde queda el subagente con los ganchos | ¿Corrieron? |
|---|---|
| `~/.claude/agents/` (nivel de usuario) | **Sí** |
| `claude --settings <archivo>`, con los ganchos en ese archivo | **Sí** |
| `.claude/agents/` del proyecto, en una carpeta sin el diálogo de confianza aceptado | **No, y no hubo ningún aviso**: el código inseguro quedó entregado |

Por eso se instala a nivel de usuario. Para comprobar que su instalación sí actúa, defina `COMPUERTA_BITACORA=/ruta/bitacora.jsonl`: cada decisión deja una línea. Sin líneas, el gancho no corrió. Además, cuando un archivo pasa, la compuerta se lo confirma al modelo: sin esa confirmación, la ficha le ordena decir que no quedó revisado.

Otros límites:
- El subagente de esta carpeta no tiene `Bash`. Si le da `Bash`, lo que escriba por ahí solo se revisa al terminar y solo dentro de un repositorio git.
- Si le pide a Claude Code sin subagente, estos ganchos no aplican: están en la ficha del subagente. En un clon de este repositorio, el freno de git sigue funcionando.
