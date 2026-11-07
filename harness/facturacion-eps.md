# Harness · Facturación de cuentas a EPS

> Harness de una persona del área de facturación para el pipeline de datos con IA del repositorio CristianBTA/subagentes-big-data. Sin datos personales ni nombres de personas, clientes o empresas.

## 1. Propósito

Trabaja en el área de facturación. Recibe un paquete de cuentas, genera una factura por cada soporte y verifica los copagos cuando la atención tiene cobro. Si el proceso no se hace bien, el paciente paga un valor distinto al que le corresponde y la institución tiene pérdidas.

**La pregunta de negocio que responde:** ¿Qué porcentaje de las facturas generadas cada día, por convenio (la EPS a la que se le cobra la cuenta), tiene un copago cobrado de más o de menos? Referencia actual: cerca del 5 % de las facturas genera cobros extra o pérdidas para la institución.

## 2. Principios de trabajo

1. La IA propone; una prueba sin IA comprueba.
2. Ninguna cifra se entrega sin compararla contra la fuente.
3. La IA solo resume y redacta; por su uso limitado, no se usa como validador.

## 3. Herramientas

| Herramienta | Uso |
|---|---|
| Excel | Trabajar los datos de facturación y llevar el reporte de facturas pendientes por radicar |
| Aplicativos de validación | Validar la autorización, el tipo de documento, el código cargado y el recaudo del copago |
| Sistema de facturación | Generar la factura |
| IA (Copilot) | Resumir información y redactar informes |

## 4. Procedimiento

Cada paso tiene su control. Si el control no se cumple, no se avanza.

| # | Paso | Control |
|---|---|---|
| 1 | Recibe el paquete de cuentas y lo separa por entidad (el convenio o EPS a la que se cobra la cuenta). | (sin control) |
| 2 | Abre los aplicativos necesarios y valida la autorización, el tipo de documento, que el código cargado coincida con el autorizado y que el copago esté recaudado. | El código cargado coincide con el autorizado y el copago aparece recaudado. |
| 3 | Entra al sistema y genera la factura. | Tipifica y verifica que lo facturado coincida con lo que se cobra. Al cerrar el día genera el listado del total facturado, que hoy no se compara contra otra fuente. |
| 4 | Soporta la factura: da el visto bueno a todos los documentos, incluidas las historias clínicas. | (sin control) |
| 5 | Pasa la factura a radicación, donde se hace el checklist de las facturas a radicar. | Reporte en Excel de las facturas pendientes por radicar, contra el plazo de 22 días hábiles para presentar la cuenta a la EPS. |
| 6 | Deja las facturas en un repositorio y agrupa el listado de las facturas radicadas en orden consecutivo. | Revisa que cada factura entregada esté en el listado del total facturado del día. |

**Si un control falla:** antes de radicar, (por completar). Después de radicar, cuando llega la notificación de glosa total o parcial de la cuenta, vuelve a verificar lo que se está glosando, incluidas las tarifas.

## 5. Criterio de aceptación

Diferencia cero: al ser facturación no se aceptan errores y el resultado debe ser igual a la fuente. Quién acordó esta regla y cuándo: (por completar).

## 6. Errores frecuentes y la prueba que los atrapa

| Error | Cómo se nota | Prueba que lo habría atrapado |
|---|---|---|
| (por completar) | Glosa o devolución de la EPS después de radicar; de ella depende que se haga el pago. | Comparar conjuntos de datos, cantidades y montos esperados de facturación. Hoy no hay un sistema establecido para hacerlo. |

## 7. Datos personales y sensibles

Toca cédulas, historias clínicas, direcciones, diagnósticos, datos de contacto, contratos, información personal y copias de documentos. No se usa IA con esta información, por el tipo de datos que se tratan. Cómo protegerlos además de eso: (por completar).

## Origen

Escrito el 2026-11-07 con el grill-me de `GENERAR-HARNESS.md`, solo con las respuestas de la persona: nada se inventó.
