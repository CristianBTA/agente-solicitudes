# Registro de cambios

Cada aporte aceptado queda aquí, con el usuario de GitHub de quien lo propuso (si aceptó aparecer).

## v1 · 6 de noviembre de 2026 · semilla

- Pipeline de cinco etapas con once subagentes, herramientas sin IA, directrices, baterías (seguridad, privacidad, FAILFAST y lecciones), dos corridas selladas y evidencia de los experimentos.
- Primeras lecciones de la revisión ciega de seguridad (L15–L20): reglas en caja de arena, lectura estricta de CSV, mensajes saneados, URLs bloqueadas, enlaces solo locales y ejecución desde la fuente.

## v1.1 · 6 de noviembre de 2026 · prueba de la guía de aportes

- `APORTAR-CON-TU-AGENTE.md`, probada con tres participantes simulados (cerca de 110.000 tokens por aporte, 11 minutos).
- Lo que encontraron se integró: la familia exec/spawn de `os` y sus alias, el CSV con separador distinto de la coma (FAILFAST) y once arreglos de la guía y del filtro (orden de los pasos, `upstream/main`, filtro sin efectos sobre el repositorio, ids de lección sin choques).
- Corrida de cinco etapas con capa limpia, aprobada en las cinco.

## v1.2 · 6 de noviembre de 2026 · blindaje del pipeline

- `herramientas/blindaje.py`: 15 ataques al pipeline, con un control positivo. Línea base: resistía 5 de 14; ahora resiste 15 de 15.
- Caja de arena: sin lectura de la carpeta personal, entorno mínimo sin secretos y tope de memoria por huella física.
- Compuerta: 8 evasiones conocidas cerradas sin romper el código legítimo.
- Inyección de instrucciones: cuarentena en el perfil y la limpieza, rechazo en el filtro de aportes, batería `baterias/inyeccion/` y regla común 7.
- Integridad: manifiesto sellado antes de cualquier agente y comprobado al final; las baterías solo crecen.
- Cadena de suministro: dependencias con huella (`--require-hashes`) y acciones de GitHub fijadas a su commit.
- Auditoría de independencia: 16 agentes en 4 corridas, 0 accesos prohibidos. Lecciones L25 a L33.

## v1.3 · 6 de noviembre de 2026 · SGSI con la tríada C·I·D

- `sgsi/`: 16 activos valorados en confidencialidad, integridad y disponibilidad; 27 riesgos; 39 controles del repositorio y la Declaración de Aplicabilidad de los 93 controles del Anexo A de ISO/IEC 27001:2022 (64 aplican, 29 se excluyen con su justificación).
- `herramientas/sgsi.py`: lo comprueba sin IA, con la regla de la tríada (C sin reversa → preventivo; I se corrige → detectivo; D se restablece → correctivo), el impacto tomado del activo, la cobertura de 6.1.2 c 1 y la etiqueta C·I·D de cada corrida. `--autoprueba`: 21 de 21 SGSI dañados atrapados. `--efectividad`: 27 controles operando y 12 documentales.
- Controles nuevos que salieron de la valoración: vigilancia diaria de `main` y de vulnerabilidades conocidas en las dependencias (OSV), escaneo de secretos y de permisos de los flujos en cada aporte, reporte privado de vulnerabilidades (`SECURITY.md`) y retención mínima de los datos crudos.
- Lección L42: el filtro corría en Linux, donde no hay `sandbox-exec`; B11 y B12 cedían y todo aporte que tocara `herramientas/` habría fallado. El filtro y la vigilancia corren ahora en macOS, y `sgsi.py` lo exige.
- Lección L43: la efectividad del SGSI mostró que en GitHub Actions el banco de blindaje se cortaba en B18 (la prueba exigía los CSV de SECOP, que no se publican) y el filtro pasaba igual. B18 ya no los necesita, un `SystemExit` en una prueba queda como ERROR y el filtro exige que el banco termine.
- Lección L44: el filtro rechazaba todo cambio al banco de ataques, porque trae a propósito frases con forma de orden. Ahora un archivo que ya las tenía solo falla si el cambio agrega una nueva.
- Riesgo que queda a decisión del dueño: R16, referencias legales inventadas por la IA que `validar_ficha.py` deja pasar (residual 15, por encima del criterio de 10).

## v1.4 · 6 de noviembre de 2026 · presentación y color con estándares validados

- Subagente 12, **Presentador** (`agentes/12-presentador.md`): propone la presentación como `presentacion.json` (respuesta primero, SCQA, títulos que afirman con su cifra, una evidencia por lámina, método y límites, recomendación) sin escribir números: usa marcadores `{id}` con su cálculo. `herramientas/verificar_presentacion.py` calcula y escribe cada cifra desde el resultado aprobado y arma las láminas solo si todo aprueba; `--autoprueba` con 4 casos buenos y 29 mutantes. Dos rondas de revisión ciega: 13 huecos en la primera versión (NaN, constantes anidadas, números pegados o con palabras, JSON mal formado, celdas sin barrer) y 10 en la segunda (marcadores pegados, símbolos numéricos raros, monedas junto a un marcador, redondeos que muestran 0 o 100 %, falsos positivos); quedaron cubiertos por el diseño con marcadores y por mutantes, salvo los de sentido, que se documentan como límite.
- `herramientas/gobernanza.py`: la expresión de cédulas y celulares ya no tiene retroceso cúbico (una nota con miles de espacios tardaba 20 s; ahora, milisegundos), sin cambiar lo que detecta.
- Graficador: color y forma medidos sin IA (`herramientas/color.py`): siete colores o menos, contraste WCAG, simulación de daltonismo, un solo eje, sin 3D, tortas de cinco porciones o menos y escala logarítmica declarada; batería `baterias/grafico/`.
- Directrices D29 y D30, con sus fuentes (Minto, Alley, Knaflic, FT Visual Vocabulary, Cleveland y McGill, Datawrapper, WCAG 2.2, Okabe-Ito, AI Index, METR y la lección de las gráficas del lanzamiento de GPT-5).

## Aportes del grupo

Cada aporte entra sin nombre hasta que quien lo propuso acepta aparecer (la casilla del pull request o del formulario).

### 6 de noviembre de 2026

- **Fórmulas de Excel exportadas como texto (L40).** `reglas_base.leer_csv` se detiene ante una celda que empieza por «=» (`=DAY(J2)`) en vez de leerla como texto. Con 168 fórmulas sembradas en `ejemplo/datos/ventas.csv`, las que cambiaban sin aviso las cifras de las reglas pasaron de 49 a 0; en los 11 CSV del repositorio (241.742 filas) no hubo ninguna falsa alarma. Caso nuevo en `baterias/failfast/`. Propuesto por un participante del curso; su usuario se agrega cuando acepte aparecer.
- **Por qué no cruza un valor entre tablas (L41).** El perfil separa los que no cruzan por espacios dobles o invisibles (U+00A0) dentro del valor y por tildes, puntuación (S.A.S. / SAS) o ceros a la izquierda (001 / 1), y cuenta los que no tienen ninguna de esas causas. En la prueba explicó 100 de 100 casos con esas causas y ninguno de los valores que de verdad faltaban. Batería nueva `baterias/cruces/`. La búsqueda de nombres parecidos del aporte original no entró: marcaba como parecidos productos distintos (Triple 15 / Triple 18) y tardaba 141 s con 20.000 valores distintos, frente a menos de 2 s de lo demás. Propuesto por un participante del curso; su usuario se agrega cuando acepte aparecer.
- **Fechas que no existen en el calendario (L45).** Propuesto por **JESUSDF77** (issue #8). El perfil contaba `2026-13-04` como fecha válida y la mostraba como fin del rango; con 5 fechas del semestre en mes 13, la cifra de R1 bajaba 178.151.800 sin error. Ahora las cuenta aparte (`fechas_imposibles`), las deja fuera del rango y avisa en el resumen: 5 de 5 sembradas detectadas, 0 falsas alarmas en 7 columnas de fecha reales (371.763 valores). Batería nueva `baterias/fechas/`. Lo demás del issue ya estaba cubierto: la ingesta rechaza la fecha inválida (FAILFAST de tipos) y el perfil reporta la lectura ambigua.
- **Montos con punto de miles (L46).** Propuesto por **catalinaguerrero921-cell** (issue #10). `float("78.000")` da 78,0: el monto se dividía por mil sin error. `leer_csv` se detiene si una columna solo numérica trae punto de miles inequívoco o mezclado con enteros largos. Con 1 a 5 montos sembrados en `subtotal`, los cambios silenciosos en la cifra de las reglas bajaron de 13 a 1 de 100; 0 falsas alarmas en los 11 CSV del repositorio (241.742 filas). El dueño la acotó a columnas numéricas: tal como venía, detenía la lectura de SECOP por 3 valores con forma de monto en `referencia_del_contrato`. Costo: +0,7 s por lectura de 91.072 filas.
- **Módulos que ejecutan código sin pasar por la compuerta (L47).** Propuesto en el issue #9 (su usuario se agrega cuando acepte aparecer): `runpy` ejecutaba un archivo que la compuerta nunca revisó. Al medir la familia aparecieron 13 casos más que también pasaban: `code`, `timeit`, `cProfile`, `profile`, `pdb`, `trace`, `doctest`, `zipimport`, `pydoc`, `asyncio.create_subprocess_*` y `ProcessPoolExecutor`. Las 14 muestras ahora se bloquean (antes 0), los hilos y `asyncio` sin procesos siguen pasando, y en los 30 archivos de código real de las corridas no hay falsas alarmas nuevas. Batería de seguridad: de 29 a 45 casos.
- **Lectura válida para cualquier fuente (L49).** Ajuste del dueño tras re-validar L40, L45 y L46 con 12 conjuntos de datos.gov.co de otros dominios (550.000 filas): 0 falsas alarmas. En columnas donde el punto ya es decimal (`12.5`), `1.250` se lee como decimal y no detiene la lectura, y la revisión se hace solo donde hay un «=» o un punto: el sobrecosto en esas 12 fuentes bajó de +3,19 s a +1,14 s. Casos nuevos que deben leerse en `baterias/failfast/se_leen/`.
- **Llaves repetidas con desempate declarado (L50).** Propuesto por **nazuluaga** (PR #11) como regla para el Limpiador; el dueño la volvió verificable. La operación `repetidos` conservaba la primera fila del archivo y el plan no podía pedir «la más reciente»: con los datos de ejemplo, 2 clientes quedaban en una región vieja (94.793.600 en ventas). Ahora acepta `desempate` (columna y `conservar`: `ultimo` o `primero`, con orden numérico si la columna es numérica) y avisa cuando hay valores distintos sin desempate o empates. Con el desempate por `fecha_actualizacion`, 0 clientes mal asignados. Compatible: la limpieza de la corrida sellada de SECOP sale idéntica (misma huella). Batería nueva `baterias/limpieza/`.
- **Fuentes de millones de filas (L52).** De un aporte que no pudo entrar por el formulario (reglas de negocio para bases de clientes de más de 5 millones de registros) se tomó solo la idea de procesar por partes. `leer_csv` carga toda la fuente y la caja de las reglas corta a los 1.536 MB: con 5 millones de filas se cortaba a los 7 s. `recorrer_csv` da las mismas filas y las mismas detenciones una por una: con esos 5 millones de filas terminó en 36 s con la suma exacta, y coincide con `leer_csv` en las 23 fuentes reales y en 100 copias sembradas. Lo demás del aporte no entró: reemplazaba el glosario del ejemplo, borraba filas, deduplicaba por lote (un repetido entre dos lotes no se ve), pasaba las fechas a DD/MM/AAAA, las corruptas a NaT sin aviso, y pedía Parquet, que la compuerta bloquea.
- **Encuestas con factor de expansión (L53).** Propuesto en el PR #17 (su usuario se agrega cuando acepte aparecer). En la GEIH 2025, Bogotá es el 3,5 % de las filas y el 17,1 % de los hogares ponderados: contar filas da cifras de la muestra. El perfil reconoce el factor de expansión (`FEX_C18`, `factor_expansion`, `pweight`…) y avisa; la ficha del Especificador pondera toda cifra de población con él. 7 de 7 casos de la batería nueva `baterias/perfil/` (el perfil anterior fallaba los 3 factores); 0 falsas alarmas en las 308 columnas de 23 fuentes reales.
