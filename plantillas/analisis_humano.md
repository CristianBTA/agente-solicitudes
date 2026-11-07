# Análisis de las personas

> Esta plantilla la llenan las personas del curso, no la IA. La IA solo resume lo desarrollado en el `whitepaper.md` de la corrida; el análisis y la conclusión son de ustedes. Copien este archivo, llénenlo y guárdenlo con su nombre.

**Corrida:** `corridas/<fecha-nombre>/` · **Whitepaper:** `whitepaper.md` de esa carpeta

## 1. Pregunta

Tomen una pregunta de «Preguntas para el análisis de las personas» del whitepaper, o escriban la suya.

- Tipo (costo, calidad o impacto):
- Pregunta:
- Para qué decisión sirve la respuesta:

## 2. Hipótesis, escrita ANTES de mirar

Escríbanla antes de consultar los datos: mover el umbral después de ver el resultado convierte cualquier dato en confirmación.

- Fecha y hora en que la escriben:
- Enunciado (lo que creen que pasa):
- Medida (qué número exacto y sobre qué filas):
- Umbral (desde qué valor la hipótesis se sostiene):
- Línea base (contra qué se compara: reparto uniforme, otro grupo u otro período):
- Qué resultado los haría cambiar de opinión:

## 3. Consulta con la que la prueban

La consulta o el archivo, y sobre qué datos corre (el dato crudo, la capa limpia o el resultado aprobado).

Pueden usar `herramientas/verificar_hipotesis.py`, que deja la hipótesis registrada antes de mirar. Trabajen sobre una copia de la carpeta de la corrida (por ejemplo, `analisis/<su-nombre>/`): así no tocan la corrida sellada. La consulta corre en la caja de arena aislada, sobre una copia de su código y de sus tablas: lee solo lo que recibe en `datos`, nunca la corrida, el `hipotesis.json` sellado ni el caso conocido.

1. Escriban `hipotesis.json` en la copia: una lista con `id`, `enunciado`, `medida`, `umbral` (`operador` y `valor`), `linea_base` y `por_que_importa`.
2. Séllenla antes de cualquier consulta: `python herramientas/verificar_hipotesis.py <copia> --sellar`.
3. Escriban la consulta en `hipotesis.py`, una función `@hipotesis("H1")` por hipótesis que devuelve `valor`, `linea_base` y `detalle`, calculada desde los CSV que recibe en `datos`.
4. Córranla: `python herramientas/verificar_hipotesis.py <copia>`. La herramienta comprueba el sello, pasa la consulta por las mismas compuertas de seguridad que el código de la IA, la corre en la caja de arena aislada y da el veredicto contra el umbral.

## 4. Lo que encontraron

Cada cifra con su fuente: el archivo y el campo, o la consulta que la produjo.

| Cifra | Qué mide | Fuente |
|---|---|---|
| | | |

## 5. Conclusión y por qué

Su conclusión, con las cifras que la sostienen: qué permite decidir (reducir un costo, mejorar una calidad, el impacto en la sociedad) y por qué.

## 6. Límites

Lo que esta conclusión no dice: las preguntas abiertas y los supuestos del whitepaper que la cambiarían, los datos que faltan y lo que no se pudo probar.

## 7. Quiénes y cuándo

- Nombres:
- Fecha:
