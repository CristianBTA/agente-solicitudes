# Conectar la compuerta con su asistente

La compuerta es un solo comando, sin IA, sin llaves y sin red. No ejecuta el código: lo lee.

```bash
python herramientas/comprobar.py mi_codigo.py mi_cuaderno.ipynb
```

Sale con 0 si pasa, con 1 si no pasa y con 2 si no se pudo revisar. Lo que no se pudo revisar nunca se da por bueno.

Lo que cambia entre herramientas es **quién obliga a correrla**:

| Dónde trabaja | Cómo se conecta | ¿Obliga? |
|---|---|---|
| Pipeline de este repositorio (`flujo.js`) | `verificar.py` ya la corre sobre cada generador | Sí |
| Claude Code | Gancho sobre el subagente, instalado a nivel de usuario: [`claude-code/`](claude-code/README.md) | Sí, si queda instalado así; allí se explica cómo comprobarlo |
| Git, en un clon de este repositorio (con cualquier editor) | Freno de commit: `git config core.hooksPath .githooks`, una vez por clon | Al hacer commit, salvo que se salte con `--no-verify`: sirve contra el descuido; después queda el filtro de GitHub |
| GitHub | El filtro `validar-aporte` de cada pull request | Sí |
| ChatGPT, Gemini o Claude en el navegador | Celda de Colab (abajo) | **No: depende de que la persona la corra** |

## En Colab

```python
!git clone --depth 1 https://github.com/CristianBTA/subagentes-big-data /content/compuerta
!pip install -q --require-hashes -r /content/compuerta/requirements-compuerta.txt
!python /content/compuerta/herramientas/comprobar.py /content/mi_codigo.py
```

## Dos perfiles

- `--perfil usuario` (por defecto): código que sí usa red y archivos. Bloquea la debilidad en sí.
- `--perfil pura`: el contrato de los generadores del pipeline: sin red, sin escritura y sin comandos.

## Lo que no garantiza

Es análisis estático de 11 debilidades. Sigue el dato dentro de una función, no entre funciones. Lo que queda fuera del catálogo no lo ve. Pasar quiere decir «no se encontró nada de esto», no «es seguro».
