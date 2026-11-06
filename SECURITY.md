# Seguridad

## Reportar una vulnerabilidad

Usa el reporte privado de GitHub: pestaña **Security** del repositorio → **Report a vulnerability**. Solo lo ve el dueño.

- No abras un *issue* público con el detalle de una vulnerabilidad.
- No incluyas datos de personas, filas de SECOP ni llaves, ni siquiera como ejemplo.
- Si encontraste una forma de saltar una defensa (la compuerta, la caja de arena o el filtro de aportes), basta con el fragmento mínimo que lo reproduce.

## Qué pasa después: según la propiedad que se perdió

Cada reporte se evalúa con la tríada C·I·D del [SGSI](sgsi/README.md) (A.5.25):

| Se perdió | Respuesta |
|---|---|
| **C · confidencialidad** (no tiene reversa) | Contener de inmediato: retirar el archivo, limpiar la historia si hace falta y revocar y cambiar cualquier llave expuesta. Se asume que lo publicado ya se copió. Si hay datos de personas, el dueño evalúa informar a la Superintendencia de Industria y Comercio (Ley 1581 de 2012, art. 17, lit. n). |
| **I · integridad** (se corrige) | Medir el alcance: qué corridas o herramientas cambiaron y desde qué commit. Revertir y verificar de nuevo desde el último sello bueno. |
| **D · disponibilidad** (se restablece) | Restablecer desde GitHub o un clon y reconstruir los datos con el contrato o la semilla ([Restablecer](sgsi/README.md#restablecer)). |

En todos los casos, el hallazgo se vuelve lección y prueba en `baterias/` (A.5.27), y la evidencia queda en el *advisory* privado (A.5.28). Quien reporta aparece en el registro de cambios si lo acepta.
