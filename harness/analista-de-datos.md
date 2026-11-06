# Harness del analista de datos

## 1. Propósito

Este documento describe el procedimiento de trabajo para atender solicitudes de información, desde la recepción del caso hasta la entrega de un tablero o reporte. Para cada etapa define la actividad, el apoyo permitido de la inteligencia artificial (IA) y el control que verifica el resultado antes de continuar.

Los controles identificados como **(recomendado)** son prácticas sugeridas que aún no forman parte de la rutina establecida.

## 2. Principios de trabajo

1. **Comprender antes de transformar.** Toda solicitud inicia con el entendimiento de la necesidad del negocio y de las fuentes: tablas, campos, relaciones y reglas del proceso.
2. **Validar antes de publicar.** Ninguna cifra se entrega sin haber sido conciliada contra la fuente.
3. **Generar información útil.** El resultado debe facilitar el análisis y la toma de decisiones.
4. **La IA propone; el analista verifica.** Las sugerencias de la IA se tratan como insumo, nunca como resultado final.

## 3. Herramientas

| Herramienta | Uso |
|---|---|
| SQL Server | Fuente principal de datos y ejecución de consultas. |
| Power Query | Extracción, limpieza y transformación de datos. |
| Excel | Verificación detallada de registros frente a la fuente. |
| Plataforma interna de validación | Revisión de la información entregada por la consulta. |
| Power BI y DAX | Modelo de datos, relaciones, medidas, columnas calculadas y visualizaciones. |
| Report Builder | Elaboración de reportes, cuando la solicitud lo requiere. |
| IA | Propuestas de diseño (mockups) y apoyo en la interpretación de archivos de Excel de contexto desconocido. |

## 4. Roles y responsabilidades

| Rol | Responsabilidad |
|---|---|
| Área encargada / DBA | Construye las consultas y realiza los ajustes solicitados. |
| Analista de datos | Valida los datos, construye el modelo, desarrolla las medidas DAX y diseña las visualizaciones. |
| IA | Propone diseños, interpretaciones de datos, relaciones o medidas. No determina cifras. |

## 5. Procedimiento

Cada etapa cuenta con un control. Si el control no se cumple, no se avanza a la siguiente etapa.

| # | Etapa | Actividad | Control | Acción ante desviación |
|---|---|---|---|---|
| 1 | Recepción del caso | Analizar la solicitud y definir el entregable: tablero en Power BI o reporte. | Entregable acordado con el solicitante. | Aclarar el alcance con el solicitante. |
| 2 | Análisis de la fuente | Verificar que los datos requeridos existan en la fuente y sean correctos, e identificar si la consulta requiere ajustes. | Tablas, campos y relaciones necesarias identificados. | Documentar los ajustes requeridos. |
| 3 | Obtención de la consulta | Recibir la consulta del área encargada. | La consulta contiene los campos y el período solicitados. | Solicitar los ajustes al área DBA. |
| 4 | Validación de datos | Revisar los datos en la plataforma interna y verificarlos en Excel. | Conteo de registros igual al de la fuente. Suma de la columna de valor **(recomendado)**. Conteo de llaves distintas **(recomendado)**. | Solicitar al área DBA la corrección de la consulta. |
| 5 | Interpretación de archivos de contexto desconocido | Solicitar a la IA la lectura del archivo y una explicación de su contenido y de cómo integrarlo al modelo. | **(Recomendado)** Verificar número de filas, columnas, vacíos y duplicados antes de usar la interpretación de la IA. | Descartar cualquier interpretación que no corresponda con el contenido real del archivo. |
| 6 | Modelo y relaciones | Conectar las consultas al modelo y crear las relaciones entre tablas. | Las relaciones cruzan correctamente. | Revisar la fuente para identificar el origen del error antes de ajustar el modelo. |
| 7 | Medidas y columnas calculadas | Desarrollar las medidas DAX y columnas calculadas que dan contexto al tablero. | Tarjeta de conteo igual al conteo de la consulta. Tarjeta de suma igual a la suma de la consulta **(recomendado)**. | Si el conteo coincide y la suma no, revisar las relaciones. |
| 8 | Diseño (mockup) | Solicitar a la IA un mockup como referencia visual al iniciar un tablero desde cero. | El mockup se usa únicamente como guía de diseño; ninguna cifra proviene de él. | No aplica. |
| 9 | Visualizaciones | Construir los visuales con las medidas validadas. | Las cifras del tablero coinciden con la consulta validada. | Aplicar el protocolo de conciliación (sección 6). |
| 10 | Entrega | Entregar el tablero o reporte al solicitante. | Revisión final de las cifras clave contra la fuente. | Corregir antes de entregar. |

## 6. Protocolo de conciliación

Se aplica cuando los datos en Excel y los del tablero no coinciden. La revisión sigue este orden:

1. **Consulta frente a Excel.**
   - Si no coinciden, la diferencia se origina en la fuente o en la consulta (filtros, límite de filas o formato). No se modifica el modelo; se escala al área DBA.
   - Si coinciden, se continúa con el paso 2.
2. **Tarjeta de conteo frente a la consulta.**
   - Más registros: probable relación mal definida, con una llave duplicada que multiplica registros.
   - Menos registros: una relación o un filtro está excluyendo registros.
   - Igual cantidad: se continúa con el paso 3.
3. **Cifra del visual frente a la consulta.**
   - Si no coinciden, la diferencia se origina en la medida DAX o en el filtro del visual.

## 7. Criterio de aceptación

- **Umbral de diferencia: cero.** Cualquier diferencia en conteo o en totales entre el tablero y la consulta indica un problema en la relación entre tablas o en el filtro de la consulta, y debe resolverse antes de la entrega.
- **Redondeo:** cuando los datos incluyan decimales, la regla de redondeo se acuerda antes de construir el tablero. No se utiliza después para justificar una diferencia.

## 8. Errores frecuentes

### 8.1 Error principal: relaciones mal definidas

| Aspecto | Descripción |
|---|---|
| Síntoma | La consulta entrega datos aparentemente correctos, pero al cruzarla con otra tabla en Power BI los totales se inflan. |
| Causa | Una relación mal definida (por ejemplo, muchos a muchos donde corresponde muchos a uno) duplica registros. |
| Detección | El conteo de la tarjeta, o los datos del tablero exportados a Excel, no coinciden con la fuente. |
| Corrección | Solicitar al área DBA la depuración de la consulta o la inclusión de un campo clave único que garantice la relación correcta. |

### 8.2 Otros errores observados

- La consulta aparenta estar correcta, pero los datos verificados en Excel no lo están.
- La información se desborda.
- Una relación no cruza o queda mal creada.
- Los datos en Excel y en el tablero no coinciden.

### 8.3 Causas técnicas de referencia

- Excel admite un máximo de 1.048.576 filas por hoja; los registros excedentes se descartan sin aviso.
- Excel conserva 15 dígitos significativos; los códigos extensos pueden perder precisión o ceros a la izquierda.
- Una llave duplicada en el lado «uno» de una relación infla las sumas sin generar error visible.
- Un filtro de fecha aplicado sobre campos con hora puede excluir registros del último día del período.
- Una medida DAX que no respeta el contexto de filtro produce totales distintos a los de la consulta.

## 9. Reglas obligatorias

1. No se publica ninguna cifra que no haya sido conciliada contra la fuente.
2. Ante una relación que no cruza, se revisa la fuente antes de forzar la relación en el modelo.
3. Toda propuesta de la IA (mockup, interpretación de datos o medida) se verifica antes de usarla.
