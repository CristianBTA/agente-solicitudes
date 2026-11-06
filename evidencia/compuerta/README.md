# Compuerta de seguridad: qué se midió y qué salió

La pregunta: si todo el código que escribe la IA pasa por una compuerta sin IA antes de entregarse, ¿qué parte de lo entregado queda seguro? La meta acordada fue **al menos 85 % seguro, con 95 % de confianza**, sobre un catálogo fijo de 11 debilidades (CWE-89, 798, 502, 295, 78, 22, 79, 327, 330, 532 y 1333). Medido el 6 de noviembre de 2026.

Dos medidas, porque miden cosas distintas: lotes sellados (¿la compuerta atrapa el código vulnerable?) y código generado de verdad (¿qué queda en lo entregado?). Se juzga con la cota inferior de una cola, nunca con la cifra observada.

## 1 · Código generado de verdad

55 tareas de datos, escritas por otro modelo que no conoce la compuerta. Sonnet escribe el programa. Califican dos jueces de modelos distintos (Sonnet y Opus), con una segunda llamada a Opus si no coinciden, sin saber de dónde viene cada programa. Sonnet también es el autor. Las tareas no se publican.

| Brazo | Programas | Seguros según el jurado | Cota inferior | Sin entregar |
|---|---|---|---|---|
| Solo el modelo, sin compuerta | 55 | 47 (85,5 %) | 75,3 % | 0 |
| Modelo con compuerta y hasta 2 reparaciones | 45 | 43 (95,6 %) | **86,7 %** | 10 |
| Ficha con la compuerta conectada de verdad (gancho de Claude Code) | 49 | 49 (100 %) | **94,1 %** | 6 |
| Lo mismo, con las falsas alarmas afinadas y programas nuevos | 55 | 55 (100 %) | **94,7 %** | 0 |

Qué se lee:

- **El 40 % no se reprodujo.** Sin compuerta, el jurado encontró 8 vulnerables de 55 (14,5 %). La cifra de 40 % (Pearce y otros, 2021) viene de otro modelo, otro catálogo y otra época: no es comparable.
- **Lo que no pasa la compuerta no se entrega.** Por eso la seguridad sube y la cobertura baja: la parte sin entregar es un costo real, no un acierto gratis.
- **La compuerta es estricta.** Frente al jurado, en el código crudo: bloqueó 7 de los 8 vulnerables, y también 28 de los 47 que el jurado dio por seguros. Se le escapó 1. Muchos de esos 28 son malas prácticas que el jurado no cuenta como debilidad alcanzable; otros son falsas alarmas.
- **La fila conectada no separa la ficha de la compuerta.** La ficha ya pide buenas prácticas: esas filas miden las dos juntas. Sí consta que la compuerta actuó: en la última, 22 de 55 programas fueron rechazados al menos una vez antes de quedar bien. Según el jurado, 3 de esos 55 no cumplen del todo lo pedido (52 de 55, 94,5 %).
- **Una ficha sin herramientas no mide nada.** El primer intento de ese brazo, sin poder escribir archivos, no entregó código en 52 de 55 tareas, porque la ficha prohíbe pegarlo en el chat. Se descartó y se repitió con herramientas y gancho real.

## 2 · Lotes sellados

Cada lote: 66 fragmentos vulnerables y 22 seguros, escritos por otro modelo que no conoce la compuerta, con etiquetas revisadas por un panel independiente y selladas por huella antes de cambiar una regla (`baterias/sellada/MANIFIESTO.json`). Los lotes no se publican mientras sirven de examen. Requisito: cota de al menos 85 % (62 de 66, o 60 de 64) y 0 falsas alarmas. **Ningún lote lo ha cumplido todavía.** El lote A fue el primero y no se selló. Al revelarlos, una etiqueta errada movió un fragmento de seguro a malo en A y otro en B: por eso en las baterías esos lotes tienen 67 y 21. Los lotes miden las reglas de seguridad, sin la lista de librerías que sí aplica `comprobar.py`: ese comando puede rechazar más.

| Lote y momento | Bloqueó | Cota inferior | Falsas alarmas | ¿Cumple? |
|---|---|---|---|---|
| Compuerta anterior, lote A | 36 de 66 (54,5 %) | — | 8 de 22 | No |
| Compuerta nueva, lote A, primera vez a ciegas | 60 de 66 (90,9 %) | 82,8 % | 2 de 22 | No |
| Lote B, sellado, a ciegas | 60 de 66 (90,9 %) | 82,8 % | 1 de 22 | No |
| Lote C, sellado, a ciegas | 58 de 66 (87,9 %) | 79,2 % | 0 de 22 | No |
| Lote D, sellado, a ciegas (64 vulnerables: el panel retiró 2 etiquetas erradas antes de medir) | 59 de 64 (92,2 %) | 84,3 % | 0 de 22 | No, por un fragmento: hacían falta 60 |

Una lección quedó a la vista: después de corregir, los lotes revelados dan 66 de 66, y el siguiente lote sin ver bajó. **La cifra que vale es la del lote que nadie ha visto.** Revelar un lote lo gasta como medida; sus fragmentos pasan a las baterías.

## 3 · Ataque a la compuerta

16 atacantes con acceso a las reglas buscaron código vulnerable que pasa, código correcto que se bloquea, caídas y formas de esquivar la conexión. Cada hallazgo se verificó con enfoques independientes. Se confirmaron 46 escapes, 2 falsas alarmas y 18 fallas de conexión. La verificación se detuvo por tiempo antes de terminar: 121 hallazgos del revisor de lógica y 36 de caídas quedaron sin verificar con esos enfoques. Los escapes y la conexión se corrigieron; los archivos están en `baterias/seguridad/malos_usuario/ataque_*`, junto con variantes que se agregaron al corregir sin pasar por esa verificación completa.

Las fallas más serias eran de conexión, no de reglas: una caída de Bandit contaba como cero hallazgos, un archivo `logging.py` en la carpeta bastaba para apagarlo, y el freno de git revisaba el disco en vez de lo preparado.

## Qué se garantiza y qué no

- **Mecánico:** donde la conexión obliga (gancho de Claude Code a nivel de usuario, freno de git, filtro de GitHub y pipeline), el código no pasa sin revisión, y si la revisión no se puede hacer, no se aprueba. El freno de git se activa una vez por clon de este repositorio y se salta con `--no-verify`: sirve contra el descuido, y después queda el filtro de GitHub. En un chat del navegador no obliga nada.
- **Estadístico:** una cota sobre este catálogo, estas tareas y este modelo. No es seguridad absoluta.
- **Fuera de la cifra:** lo que no está en el catálogo, el código que nunca pasa por la compuerta, y la lógica de negocio.
- **Sigue siendo análisis estático:** se puede esquivar a propósito. Sirve contra el descuido, no contra quien quiere engañarla.
- **Ajuste con las mismas tareas:** las reglas de falsas alarmas se afinaron mirando el primer brazo real, y por eso la fila afinada se midió con programas nuevos. Las tareas son las mismas: esa fila es menos independiente que las anteriores.

## Cómo se repite

```bash
.venv/bin/python herramientas/medir_compuerta.py <lote> --perfil usuario           # lote sellado
# Todas las etapas de medir_real.py, menos informe, gastan la licencia de quien las corre. Una carpeta por brazo.
.venv/bin/python herramientas/medir_real.py generar   <sin-ficha> <tareas.json>
.venv/bin/python herramientas/medir_real.py compuerta <sin-ficha> <tareas.json>
.venv/bin/python herramientas/medir_real.py conectado <conectado> <tareas.json>
.venv/bin/python herramientas/medir_real.py jurado    <carpeta>   <tareas.json>    # en cada una
.venv/bin/python herramientas/medir_real.py informe   <carpeta>   <tareas.json>    # en cada una
```

Costo medido: US$ 7,34 el brazo sin ficha con su jurado; US$ 4,07 y US$ 3,85 cada corrida del brazo conectado con su jurado.
