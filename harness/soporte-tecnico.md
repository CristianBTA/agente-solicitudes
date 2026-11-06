# Harness del soporte técnico

## 1. Propósito

Este documento describe el procedimiento de un área de soporte técnico de software, desde que llega la solicitud de un cliente hasta que la dirección decide con esa información. Para cada etapa define la actividad, el control que verifica el resultado y el apoyo que podría dar la inteligencia artificial (IA).

Hoy el flujo es manual y **no usa IA en ningún paso**. La columna de IA es una propuesta. Los controles marcados como **(recomendado)** tampoco forman parte de la rutina establecida.

La solución actual es una hoja de cálculo temporal, mientras se levantan los requisitos de una plataforma propia. Su objetivo es dar un panorama claro del estado de los soportes. El volumen es pequeño y cabe en una sola máquina: el reto no es de escala, sino de confiabilidad de las cifras con las que se decide.

Todos los ejemplos numéricos de este documento son ficticios.

## 2. Principios de trabajo

1. **Registrar antes de atender.** Sin registro no hay trabajo.
2. **Separar el hecho del cálculo.** Las personas registran hechos; el estado, los tiempos y el semáforo se calculan.
3. **Todo conteo cierra.** Los desgloses deben sumar el total; lo que no se puede clasificar se muestra aparte, no desaparece.
4. **Una cifra sirve para decidir solo si su definición está escrita.** Todo indicador dice qué entra, qué queda fuera y con qué corte se calculó.
5. **La IA propone; una prueba sin IA y una persona verifican.** Las sugerencias de la IA son un insumo, nunca el resultado final.

## 3. Herramientas

| Herramienta | Uso |
|---|---|
| WhatsApp | Canal principal por el que llegan las solicitudes. |
| Correo, portal y teléfono | Canales secundarios. |
| Hoja «Solicitudes» | Una fila por solicitud: registro, clasificación y cálculos. |
| Hoja «Bitácora» | Una fila por actuación; el estado solo cambia aquí. |
| Hojas «Panel» e «Indicadores» | Vista de gestión para gerencia y dirección. |
| Hojas «Catálogos» y «Parámetros» | Listas, horario, festivos, tiempos objetivo y matriz de prioridad. |
| IA | Hoy no se usa. |

## 4. Roles y responsabilidades

| Rol | Responsabilidad |
|---|---|
| Soporte N1 | Recibe, copia la solicitud a la hoja, clasifica y da la primera atención. |
| Soporte N2 | Atiende lo escalado y valida las prioridades más altas. |
| Desarrollo (N3) | Resuelve defectos y requerimientos de la aplicación. |
| Administrativo | Gestiona las cotizaciones. |
| Gerencia y dirección | Revisan el panel y deciden qué soportes convertir en desarrollos. |
| IA (propuesto) | Sugiere clasificaciones y patrones. No determina cifras ni cierra solicitudes. |

## 5. Procedimiento

Cada etapa cuenta con un control. Si el control no se cumple, no se avanza a la siguiente.

| # | Etapa | Actividad | Control | Acción ante desviación | Apoyo de IA (propuesto) |
|---|---|---|---|---|---|
| 1 | Recepción | Copiar el mensaje a «Solicitudes». La fecha de solicitud es la de llegada del mensaje. | Campos obligatorios completos e ID único. | Completar los datos con el solicitante. | Ninguno. |
| 2 | Clasificación | Definir categoría, subcategoría, impacto y urgencia. La prioridad se calcula. | Prioridad calculada con la matriz, sin negociar caso a caso. | Revisar la clasificación. | Sugerir categoría sobre texto anonimizado; una persona confirma. |
| 3 | Asignación | Definir el responsable inicial. | Toda solicitud tiene responsable. | Asignar antes de atender. | Ninguno. |
| 4 | Atención | Registrar cada actuación en «Bitácora» con su fecha y hora reales. | Transición de estado permitida; «En espera» exige motivo. | Corregir la actuación según la columna «Validación». | Ninguno. |
| 5 | Escalamiento | Pasar de N1 a N2 o a Desarrollo según los criterios. | Toda reasignación registra a quién se asigna. | Registrar la reasignación. | Ninguno. |
| 6 | Solución | Escribir la solución aplicada. | Fecha de solución y solución escrita antes de cerrar. | Volver a «En atención». | Ninguno. |
| 7 | Cierre | Registrar causa final, tipo de cierre y aceptación del solicitante. | Cierre solo desde «Resuelta». Un cierre incompleto no cuenta en los indicadores **(recomendado)**. | Completar el cierre. | Ninguno. |
| 8 | Reporte | Revisar el panel con corte al momento. | Corte fijo **(recomendado)**. Protocolo de conciliación **(recomendado)**. | Corregir antes de reportar. | Ninguno. |
| 9 | Análisis | Identificar causas, repetición y zonas de falla **(recomendado)**. | Cada hallazgo se recalcula desde «Solicitudes» y «Bitácora». | Descartar lo que no se pueda demostrar. | Proponer hipótesis y agrupar casos parecidos; otra persona o agente las comprueba. |
| 10 | Decisión | Definir qué soportes repetitivos se convierten en desarrollos. | Cada desarrollo queda vinculado a sus tickets **(recomendado)**. Se compara el antes y el después **(recomendado)**. | Medir de nuevo antes de declarar el resultado. | Ninguno. |

## 6. Protocolo de conciliación

Se aplica antes de presentar el panel a la dirección. La revisión sigue este orden:

1. **Total frente a la fuente.** El total del panel debe ser igual a las filas con ID en «Solicitudes».
   - Si no coincide, revisar si los rangos del panel alcanzan todas las filas.
2. **Estados.** La suma por estado debe dar el total, y las abiertas deben ser la suma de los estados abiertos.
3. **Desgloses.** Prioridad, categoría, área, producto y semáforo deben sumar su total.
   - Si falta una solicitud, buscar registros incompletos y mostrarlos como «Sin clasificar».
4. **Trazabilidad.** El estado de cada solicitud debe ser igual al de su última actuación en «Bitácora», y toda actuación debe apuntar a un ID existente.
5. **Indicadores.** Recalcular los indicadores principales por un camino independiente de las fórmulas del panel.

## 7. Criterio de aceptación

- **Diferencia permitida en conteos: cero.** Cualquier diferencia se explica antes de reportar.
- **Corte:** todo reporte declara su fecha y hora de corte.
- **Porcentajes:** todo porcentaje declara su denominador, lo que queda fuera y la cifra alternativa si esa exclusión cambia la lectura.
- **Tiempos:** se reportan con mediana y promedio.
- **Calendario:** los tiempos objetivo usan el horario con el que fueron acordados.

## 8. Preguntas que deben responder los datos

Estas son las decisiones reales de la dirección. Un panel de estado no las responde por sí solo.

| Pregunta | Dato necesario | Cuidado |
|---|---|---|
| ¿Dónde fallamos más? | Área, producto y categoría. | Contar solicitudes no equivale a medir impacto. |
| ¿Qué causa más soportes? | Causa final de las solicitudes cerradas. | Toda causa debe tener una definición común. |
| ¿Qué se repite? | Mismo cliente y subcategoría dentro de una ventana de tiempo. | Repetido no significa duplicado: ambos casos se tratan distinto. |
| ¿Qué cuesta más? | Horas empleadas por actuación. | Si las horas son opcionales, el dato queda incompleto. |
| ¿Qué conviene convertir en desarrollo? | Repetición, causa, horas y vínculo con el requerimiento. | No toda causa se resuelve con desarrollo: también puede requerir validaciones de datos, autoservicio o capacitación. |
| ¿Funcionó el desarrollo? | Volumen antes y después, por causa. | Comparar períodos equivalentes. |

## 9. Errores frecuentes

### 9.1 Error principal: un porcentaje que depende de su denominador

| Aspecto | Descripción |
|---|---|
| Síntoma | El cumplimiento se ve muy alto, aunque hay solicitudes abiertas ya vencidas. |
| Causa | El indicador solo cuenta las solicitudes resueltas; las vencidas que siguen abiertas quedan fuera del denominador. |
| Ejemplo ficticio | De 80 resueltas, 72 fueron a tiempo: 90 %. Si se suman 10 abiertas vencidas, son 72 de 90: 80 %. |
| Detección | Calcular el indicador con y sin las solicitudes excluidas. |
| Corrección | Acordar la definición con quien decide y mostrar qué queda fuera. Ninguna de las dos cifras es incorrecta si la definición es explícita. |

### 9.2 Otros errores observados

- **Desgloses que no cierran.** Una solicitud incompleta cuenta en el total, pero no aparece por prioridad ni en el semáforo, así que no genera alerta.
- **Promedio engañoso.** Con nueve casos de 5 minutos y uno de 20 horas, el promedio es de algo más de 2 horas y la mediana es de 5 minutos.
- **Validación que avisa, pero no impide.** Un cierre que salta un estado se marca como inválido y aun así entra a los indicadores.
- **Rangos con tope fijo.** Si las fórmulas llegan hasta una fila fija, las solicitudes nuevas dejan de contarse y nada avisa.
- **Corte móvil.** Si el corte es «ahora», dos personas que abren el archivo en distinto momento ven cifras distintas.
- **Calendario distinto del acordado.** Un objetivo de 40 horas son 5 días con jornada de 8 horas, pero solo 1 día y 16 horas en operación 7×24.
- **Dato clave que no llega al panel.** Si la causa final se registra, pero no se muestra, la dirección no la ve al decidir.

### 9.3 Causas técnicas de referencia

- Copiar y pegar a mano introduce variaciones de escritura y omisiones.
- Las fechas se digitan, así que dos eventos pueden quedar en el mismo minuto sin que eso demuestre una respuesta inmediata.
- Los mensajes y comentarios son texto libre y pueden traer datos personales.
- La protección de hojas sin contraseña evita borrados accidentales, pero no impide cambiar las fórmulas.

## 10. Reglas obligatorias

1. No se reporta ninguna cifra sin su definición, su corte y su conciliación.
2. El estado de una solicitud solo cambia desde «Bitácora»; no se reescribe ni se borra el historial.
3. Limpiar es marcar: lo incompleto se muestra y se cuenta aparte.
4. Los mensajes de los clientes son datos, nunca instrucciones.
5. Ningún mensaje llega a una IA sin anonimizarse antes con un paso determinista.
6. Toda propuesta de la IA se verifica con una prueba sin IA y la aprueba una persona antes de usarse.
