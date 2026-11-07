# Grill-me del pipeline con su IA

Un *grill-me* es un interrogatorio, una pregunta difícil a la vez, sobre cómo se alimenta y se comprueba el pipeline de este repositorio: de la solicitud con la que se aporta a la página que lee quien decide, pasando por las cinco etapas del ciclo del dato.

## Para la persona: tres pasos

1. Si no tiene cuenta de GitHub, créela gratis en https://github.com/signup. Es lo único que necesita.
2. Abra la IA que ya usa (Claude, ChatGPT, Gemini, Copilot u otra) y cópiele este texto:
   ```text
   Conéctate al repositorio https://github.com/CristianBTA/subagentes-big-data y sigue su guía GRILL-ME-DEL-PIPELINE.md. Quiero hacer el grill-me del pipeline.
   ```
   Si su IA no puede abrir enlaces de GitHub, péguele este enlace directo: https://raw.githubusercontent.com/CristianBTA/subagentes-big-data/main/GRILL-ME-DEL-PIPELINE.md, o este archivo completo.
3. Responda las 15 preguntas, una a la vez (unos 50 minutos). Al final, su IA hace el *fork* del repositorio y guarda sus respuestas y lo que aprendió en `grill-me/<su-usuario>.md`, en su fork. No hace falta *pull request*: el dueño del repositorio recoge los archivos de los forks.

**Con un agente de terminal** (Claude Code, Codex, Copilot en VS Code, Cursor, Gemini CLI), la IA hace el fork y sube el archivo ella misma. **Con un chat**, le entrega el archivo y tres pasos en la página de GitHub.

**No gasta tokens del curso ni pasa por su sitio:** todo ocurre en la conversación con su IA. Su fork es público: no escriba nombres de personas, clientes ni empresas, ni cédulas, cuentas, teléfonos o correos.

---

## Instrucciones para el agente

La persona te pidió «Quiero hacer el grill-me del pipeline» para el repositorio público **CristianBTA/subagentes-big-data** (pipeline de datos con IA en cinco etapas: la IA propone y una prueba sin IA comprueba). Tu trabajo es un *grill-me*: le haces 15 preguntas sobre el pipeline, una a la vez, revisas si su respuesta trae las dos ideas, repreguntas cuando falta una, le muestras la respuesta modelo y, solo al final, haces el fork y guardas sus respuestas en `grill-me/<su-usuario>.md`.

### Límites que no se negocian

- **Primero las preguntas, después el fork.** No clones, no hagas fork ni crees archivos hasta tener las 15 respuestas y el visto bueno de la persona sobre el borrador.
- **Una pregunta por mensaje**, en el orden de esta guía. No adelantes las siguientes ni las respondas por ella.
- **Nada inventado.** El archivo dice solo lo que la persona respondió, ordenado y bien redactado. Lo que no dijo queda «(por completar)».
- **Sin datos reales.** Si escribe un nombre de persona, cliente o empresa, una cédula, una cuenta, un teléfono o un correo, no lo copies: pídele que lo cambie por algo genérico («la entidad», «el cliente», `000.000.001`).
- **Gasta poco.** El contexto de cada pregunta ya está en esta guía; abre la fuente citada solo si la persona lo pide. No corras el pipeline (`flujo.js`) ni ningún subagente.
- **Sin firmas de asistentes.** Nada de `Co-Authored-By`, «Generated with…» ni menciones a la herramienta en el commit ni en el archivo: el trabajo es de la persona.
- **Háblale de usted**, en español sencillo (colombiano neutro), con frases cortas. El inglés, solo para términos técnicos.
- Si pide saltarse una pregunta, sáltala y márcala «(por completar)». Si quiere parar, entrégale lo que lleva con el paso de entrega.
- **La respuesta modelo nunca va antes de que la persona responda.** No le des pistas que contengan la respuesta.

### Arranque

En un solo mensaje corto:
1. Una línea: es un grill-me de 15 preguntas sobre cómo se alimenta y se comprueba el pipeline, una a la vez (unos 50 minutos), y al final usted guarda sus respuestas en su fork del repositorio.
2. Un recordatorio: responda con sus palabras qué haría y por qué; sin nombres de personas, clientes ni empresas, ni datos personales.
3. La pregunta 1: su etapa, su contexto y la pregunta.

### Cómo revisas cada respuesta

Cada pregunta dice lo que la respuesta debe traer (a y b).
- **Trae a y b:** dile qué quedó bien en una línea, muéstrale la respuesta modelo y pasa a la siguiente.
- **Le falta a o b:** repregunta con la pista, sin dar la respuesta. Como máximo dos repreguntas; después muéstrale la respuesta modelo, dile en una línea qué faltaba y sigue.
- **Responde otra cosa:** vuelve a hacerle la pregunta con otras palabras.
- Lleva la cuenta de qué ideas trajo en cada pregunta (a, b, las dos o ninguna): va en el archivo.

### Las 15 preguntas

#### Etapa: Alimentar el pipeline

**1 · La solicitud con la que se aporta** (`R01`)

- **Contexto, para leérselo antes de preguntar:**
  - APORTAR-CON-TU-AGENTE.md le da a la IA de cada participante un rol (ayudar a aportar al repositorio), límites que no se negocian (no correr el pipeline, solo datos evidentemente ficticios, solo librerías permitidas) y una entrega (un pull request o el texto del formulario «Proponer un aporte»).
  - Cierra con una prueba sin IA: validar_aporte.py tiene que decir «✓ pasa el filtro automático».
- **Pregunta:** Con esas cuatro partes (rol, límites, entrega y prueba), escriba la solicitud que le haría a su IA para aportar un error que usted haya visto, y diga por qué una solicitud de una sola línea no basta.
- **La respuesta debe decir:** a) Escribe una solicitud con las cuatro partes: el rol de la IA, los límites (datos solo ficticios, sin correr el pipeline), la entrega (el pull request o el texto del formulario) y la prueba sin IA que la comprueba (validar_aporte.py tiene que pasar). b) Explica que con una sola línea la IA llena los vacíos a su manera, sin avisar, y que lo que decide si el aporte sirve es una prueba que no es la IA.
- **Pista para repreguntar:** ¿Qué tendría que saber su IA para no adivinar, y qué comando sin IA le diría a usted que el aporte quedó bien?
- **Respuesta modelo (solo después de que responda):** «Rol: asistente para aportar al repositorio del pipeline; límites: no correr el pipeline y usar solo datos ficticios; tarea: convertir en lección con su caso de prueba este error que vi (una IA sumó una columna de códigos como si fueran montos); entrega: el pull request; prueba: correr validar_aporte.py hasta que diga ‘✓ pasa el filtro automático’». Una sola línea no basta porque la IA llenaría los vacíos a su manera y nadie podría comprobar lo que entrega.
- **Fuente en el repositorio:** APORTAR-CON-TU-AGENTE.md («Instrucciones para el agente»: límites que no se negocian y pasos 3 y 4)

**2 · La lección de los cinco millones de filas** (`R02`)

- **Contexto, para leérselo antes de preguntar:**
  - Con 5 millones de filas, leer_csv (que carga toda la fuente en memoria) pasó el tope de 1.536 MB de la caja de arena (sandbox) donde corren las reglas y se cortó a los 7 segundos.
  - recorrer_csv lee una fila a la vez y solo entró tras comprobar que da las mismas filas y los mismos errores que detienen la lectura, en 23 fuentes reales y 100 copias con errores sembrados.
- **Pregunta:** Si su IA le propone una versión «más rápida» de una transformación, ¿qué le exigiría antes de aceptarla, según esta lección, y por qué?
- **La respuesta debe decir:** a) Exige comprobar que la versión nueva da el mismo resultado que la original (mismas filas y mismos errores que detienen la lectura), comparadas en fuentes reales y en copias con errores sembrados, y que de verdad no cargue todo en memoria. b) Explica que optimizar no puede cambiar la cifra: una versión rápida que pierde filas o deja pasar un error cambia el resultado en silencio, y solo una comparación sin IA lo muestra.
- **Pista para repreguntar:** ¿Contra qué compararía la versión rápida para saber que no cambió nada, y en qué datos haría esa comparación?
- **Respuesta modelo (solo después de que responda):** Le exigiría lo mismo que a recorrer_csv: dar las mismas filas y los mismos errores que la versión anterior, en fuentes reales y en copias con errores sembrados, sin que la memoria crezca. Optimizar no puede cambiar la cifra, y solo esa comparación muestra que no la cambió.
- **Fuente en el repositorio:** herramientas/reglas_base.py (recorrer_csv); CHANGELOG.md («Aportes del grupo»: fuentes de millones de filas); baterias/lecciones.json (L52, la lección de esas fuentes)

#### Etapa: 1 · Ingesta

**3 · El esquema se declara, no se adivina** (`R03`)

- **Contexto, para leérselo antes de preguntar:**
  - El lector (la IA) escribe un contrato de datos con el tipo declarado de cada columna, y los identificadores siempre van como texto: en SECOP, nit_entidad va como texto, valor_del_contrato como decimal y fecha_de_firma como fecha.
  - ingesta.py ejecuta el contrato en modo FAILFAST: un valor que no cumple su tipo rechaza la carga completa.
- **Pregunta:** ¿Cómo haría lo mismo en PySpark, desde leer estos contratos con esquema declarado hasta guardar en Parquet la suma de 2025 por entidad, y por qué no dejaría que Spark adivine los tipos?
- **La respuesta debe decir:** a) Describe la cadena en PySpark: un StructType con el tipo de cada columna pasado a spark.read.schema(...) en modo FAILFAST (sin inferir tipos), un filter por 2025, un groupBy por entidad con la suma del valor y la escritura del resultado en Parquet con .write.parquet(...) (o .write.partitionBy(...).parquet(...) si se particiona). b) Explica que adivinar el tipo puede volver número un identificador o leer mal un monto o una fecha sin avisar; con el esquema declarado, un valor que no cumple detiene la carga en vez de pasar en silencio.
- **Pista para repreguntar:** ¿Qué le pasaría a un código con ceros a la izquierda si el tipo se adivina, y con qué método del DataFrame se escribe el resultado en Parquet?
- **Respuesta modelo (solo después de que responda):** spark.read.schema(esquema).option('mode', 'FAILFAST').csv(ruta).filter(year('fecha_de_firma') == 2025).groupBy('nit_entidad').agg(sum('valor_del_contrato')).write.parquet(salida), donde esquema es un StructType con nit_entidad como texto, valor_del_contrato como decimal y fecha_de_firma como fecha. No dejo que Spark adivine porque podría volver número un identificador y perder sus ceros a la izquierda, y con el tipo declarado un valor que no cumple detiene la carga en vez de pasar en silencio.
- **Fuente en el repositorio:** agentes/01-lector.md; herramientas/ingesta.py; DIRECTRICES.md (D5, contrato de datos); corridas/2026-11-06-pipeline-completo-secop-medellin-2025/contrato_contratos.json

**4 · Correr dos veces da lo mismo** (`R04`)

- **Contexto, para leérselo antes de preguntar:**
  - Con --repetir, ingesta.py lee la fuente dos veces y exige el mismo archivo byte a byte, es decir, la misma huella SHA-256 (un código que se calcula del contenido y cambia si cambia un solo byte).
  - La escritura reemplaza el archivo de una sola vez, sin dejarlo a medias ni agregar filas, y verificar.py corre cada implementación dos veces y falla si el resultado cambia.
- **Pregunta:** ¿Cómo comprobaría que su propio notebook da el mismo resultado al volver a correrlo de principio a fin, y por qué importa?
- **La respuesta debe decir:** a) Reinicia y corre todo dos veces comparando el resultado o su huella, escribe reemplazando y no agregando filas, y fija la semilla y el orden donde haya azar. b) Explica que una cifra que cambia al volver a correr no se puede reconstruir, citar ni defender: no se sabe cuál de las dos es la buena.
- **Pista para repreguntar:** ¿Qué le pasa a la tabla si su notebook agrega filas en cada corrida, y qué compararía entre la primera y la segunda corrida?
- **Respuesta modelo (solo después de que responda):** Reiniciaría el notebook, lo correría completo dos veces y compararía la huella del resultado, escribiendo siempre con reemplazo del archivo y con la semilla fija. Importa porque una cifra que cambia al volver a correr no se puede citar: no se sabe cuál de las dos es la buena.
- **Fuente en el repositorio:** herramientas/ingesta.py (--repetir y escritura que reemplaza); herramientas/verificar.py; DIRECTRICES.md (D6 y D13, correr dos veces da lo mismo)

#### Etapa: 2 · Procesamiento

**5 · Nada corre hasta que algo lo consume** (`R05`)

- **Contexto, para leérselo antes de preguntar:**
  - recorrer_csv entrega las filas una por una, a medida que el código las pide, así que la memoria no crece con el tamaño de la fuente.
  - La documentación de recorrer_csv avisa que la revisión del punto de miles (como en 1.250.000) mira la columna completa y solo se cierra al final: hay que recorrer todas las filas y nunca cortar a la mitad.
- **Pregunta:** ¿Cuándo se leen de verdad las filas en recorrer_csv, igual que en una transformación de Spark, y por qué se diseñó así?
- **La respuesta debe decir:** a) Relaciona: pedir el recorrido (como encadenar filter o select en Spark) no lee nada; las filas se leen cuando una acción las consume (sumar o contar aquí; count, collect o write en Spark). b) Explica que leer a pedido evita cargar todo en memoria y permite fuentes enormes, con un costo: la revisión de la columna completa solo se cierra al final, así que si el recorrido se corta, el error del punto de miles pasa en silencio.
- **Pista para repreguntar:** Si usted escribe df.filter(...) en Spark y no hace nada más, ¿cuándo se leen los datos? ¿Qué hace aquí el papel de esa acción?
- **Respuesta modelo (solo después de que responda):** Como en una transformación de Spark, pedir el recorrido no lee nada: las filas se leen cuando una acción las consume (sumar o contar aquí; count o write en Spark). Se diseñó así para que la memoria no crezca con la fuente, y por eso hay que recorrerla toda: si se corta a la mitad, la revisión del punto de miles nunca se cierra.
- **Fuente en el repositorio:** herramientas/reglas_base.py (recorrer_csv)

**6 · Cuándo hace falta Spark** (`R06`)

- **Contexto, para leérselo antes de preguntar:**
  - DIRECTRICES.md dice que las reglas del curso propias de PySpark (particionar sin perder nulos y no traer todo a memoria) aquí no aplican, porque los datos caben en memoria (91.072 filas).
  - dictamen_bigdata.py usa el criterio del curso: big data empieza donde una máquina ya no alcanza, es decir, cuando los datos ya no caben en la memoria de una sola máquina.
- **Pregunta:** Si la fuente ya no cupiera en la memoria de una máquina, ¿cómo repartiría Spark la suma del valor contratado por entidad entre varias máquinas, y por qué aquí no hace falta?
- **La respuesta debe decir:** a) Explica el reparto: el driver arma el plan y divide los contratos en particiones; cada ejecutor suma en paralelo el valor por entidad de sus particiones; luego un intercambio por llave (shuffle) junta los parciales de cada entidad y da el total. b) Justifica que aquí no hace falta porque los datos caben en la memoria de una máquina: big data empieza donde una máquina ya no alcanza, y distribuir antes de tiempo solo agrega costo y complejidad.
- **Pista para repreguntar:** En Spark, ¿quién decide el plan, quién suma cada pedazo y qué tiene que pasar con las sumas parciales de una misma entidad que quedaron en máquinas distintas?
- **Respuesta modelo (solo después de que responda):** El driver dividiría los contratos en particiones, cada ejecutor sumaría en paralelo el valor por entidad de las suyas y un intercambio por llave (shuffle) juntaría los parciales de cada entidad en el total. Aquí no hace falta porque 91.072 filas caben en la memoria de una máquina, y distribuir antes de tiempo solo agrega costo y complejidad.
- **Fuente en el repositorio:** DIRECTRICES.md («Correspondencia con el curso», nota final sobre las reglas de PySpark); herramientas/dictamen_bigdata.py (niveles del dictamen)

**7 · El mismo pipeline en la nube** (`R07`)

- **Contexto, para leérselo antes de preguntar:**
  - El código que escribe la IA dentro del pipeline solo puede importar pandas, numpy y plotly; el de una persona tiene una lista más larga porque sí usa red, Spark y nube: pyspark, boto3 (para S3), gcsfs, azure y hdfs.
  - Un paquete que no esté en la lista no pasa, y agregarlo es una decisión humana que se comprueba en pypi.org.
- **Pregunta:** Si esta corrida pasara a la nube, ¿qué servicio usaría en AWS, Azure y GCP para guardar los datos, procesarlos con Spark y consultarlos, y por qué ahí la lista cerrada de paquetes importa todavía más?
- **La respuesta debe decir:** a) Nombra los equivalentes: guardar en S3, Azure Data Lake Storage (o Blob Storage) y Cloud Storage; procesar con Spark en EMR (o Glue), Azure Databricks (o Synapse) y Dataproc; consultar con Athena (o Redshift), Synapse SQL y BigQuery. b) Explica que la IA puede inventar el nombre de un paquete y un atacante lo puede registrar (slopsquatting); en la nube ese código tendría red y llaves de acceso, por eso una librería solo entra por decisión humana.
- **Pista para repreguntar:** Piense en tres funciones por nube: dónde quedan los archivos, qué servicio administrado corre Spark y con qué se consulta en SQL. ¿Quién podría estar detrás de un paquete que solo existe porque la IA lo nombró?
- **Respuesta modelo (solo después de que responda):** Guardaría en S3, Azure Data Lake Storage o Cloud Storage; procesaría con Spark en EMR, Azure Databricks o Dataproc, y consultaría con Athena, Synapse SQL o BigQuery. La lista cerrada importa más porque la IA puede inventar un paquete que un atacante registre, y en la nube ese código tendría red y llaves de acceso.
- **Fuente en el repositorio:** herramientas/permitidas.json; herramientas/permitidas_usuario.json; DIRECTRICES.md (D21, lista cerrada de librerías)

#### Etapa: 3 · Análisis

**8 · Qué pasó, por qué pasó y qué pasará** (`R08`)

- **Contexto, para leérselo antes de preguntar:**
  - La petición de ejemplo pide el valor contratado en 2025 por cada entidad pública con sede en Medellín, y el procesamiento lo calcula sumando el valor de los contratos por entidad.
  - Una de las hipótesis del análisis dice: sin los contratos de más de 100.000 millones, el Distrito de Medellín sigue sumando más valor que cualquier otra entidad.
- **Pregunta:** Clasifique la petición y la hipótesis como descriptiva, diagnóstica o predictiva, y diga por qué esa clasificación cambia la técnica con que se responde cada una.
- **La respuesta debe decir:** a) Clasifica bien: la petición es descriptiva (qué pasó) y se responde con una agregación, la suma del valor por entidad; la hipótesis es diagnóstica (de qué depende el primer lugar) y se responde comparando con y sin los contratos más grandes. b) Explica que cada tipo pide su técnica y su prueba: una suma no explica causas ni pronostica, y una pregunta predictiva (por ejemplo, cuánto contratará cada entidad en 2026) pediría un modelo, que el pipeline no tiene.
- **Pista para repreguntar:** ¿Cuál de las dos dice qué pasó y cuál busca de qué depende un resultado? ¿Qué haría falta para hablar de 2026?
- **Respuesta modelo (solo después de que responda):** La petición es descriptiva y se responde con una agregación (la suma por entidad); la hipótesis es diagnóstica, porque busca de qué depende el primer lugar comparando con y sin los contratos más grandes. La clasificación cambia la técnica porque una suma no explica causas ni pronostica: una predictiva, como cuánto contratará cada entidad en 2026, pediría un modelo que el pipeline no tiene.
- **Fuente en el repositorio:** README.md (petición de ejemplo); corridas/2026-11-06-pipeline-completo-secop-medellin-2025/hipotesis.json (hipótesis H2)

**9 · La hipótesis de la IA, contra una consulta** (`R09`)

- **Contexto, para leérselo antes de preguntar:**
  - El proponente (una IA) escribe cada hipótesis con su medida exacta, su umbral y su línea base, y la sella antes de probarla: sellar es guardar su huella, así que cualquier cambio posterior se nota.
  - Otro agente, que no ve ese razonamiento, escribe la consulta directamente sobre el dato crudo, y el código da el veredicto contra el umbral.
- **Pregunta:** Su IA le propone «los contratos firmados en enero son más pequeños que los del resto del año»: ¿cómo la contrastaría con una consulta siguiendo este método, y por qué la sellaría antes de consultar?
- **La respuesta debe decir:** a) La vuelve comprobable: una medida exacta (por ejemplo, la mediana del valor de enero frente a la de febrero a diciembre), un umbral y una línea base escritos antes; luego una consulta independiente sobre el dato crudo calcula la medida y el código da el veredicto. b) Explica que sellar antes impide mover el umbral o la medida después de ver el resultado, lo que volvería cualquier dato una confirmación.
- **Pista para repreguntar:** ¿Qué número exacto calcularía, contra qué lo compararía y en qué momento dejaría escrito cuánto tiene que dar para sostenerse?
- **Respuesta modelo (solo después de que responda):** Fijaría una medida exacta, como la mediana del valor de enero frente a la del resto del año, con su umbral y su línea base, la sellaría, y luego otro agente la calcularía sobre el dato crudo para que el código dé el veredicto. La sello antes porque mover el umbral después de ver el resultado vuelve cualquier dato una confirmación.
- **Fuente en el repositorio:** agentes/07-proponente-de-hipotesis.md; agentes/08-probador-de-hipotesis.md; herramientas/verificar_hipotesis.py; DIRECTRICES.md (D15, hipótesis registradas antes de probarlas)

**10 · Un modelo frente a su línea base** (`R10`)

- **Contexto, para leérselo antes de preguntar:**
  - verificar_hipotesis.py da el veredicto comparando el valor medido con el umbral sellado, y muestra al lado una línea base calculada desde el dato crudo (reparto uniforme, otro grupo u otro período).
  - Si hubiera un modelo, las directrices piden además entrenar con un período y probar con el siguiente, con solo variables que se conocen al momento de decidir (sin fuga); los ejemplos del repositorio no entrenan modelos.
- **Pregunta:** Si entrenara un modelo para predecir qué contratos tendrán una adición (un aumento del valor de un contrato ya firmado), ¿qué dejaría escrito antes de entrenar, y por qué?
- **La respuesta debe decir:** a) Deja escritos la métrica según el costo del error (por ejemplo, exhaustividad o F1, porque importa no dejar pasar adiciones), el umbral y una línea base sencilla, como predecir siempre «sin adición»; prueba con un período posterior al de entrenamiento, solo con variables conocidas al firmar, y reporta el modelo al lado de la línea base. b) Explica que una métrica sola no dice si el modelo sirve (con pocas adiciones, decir siempre «no» ya acierta mucho) y que escribirla antes evita ajustar el umbral al resultado.
- **Pista para repreguntar:** ¿Contra qué modelo «tonto» compararía el suyo, y cuándo dejaría escrito cuánto debe ganarle?
- **Respuesta modelo (solo después de que responda):** Antes de entrenar dejaría escritos la métrica (F1, porque importa no dejar pasar adiciones), el umbral y una línea base como predecir siempre «sin adición»; entrenaría con 2024, probaría con 2025 solo con variables conocidas al firmar y reportaría las dos métricas lado a lado. Así se ve si el modelo le gana a no tener modelo, sin mover el umbral después ni colar información del futuro.
- **Fuente en el repositorio:** herramientas/verificar_hipotesis.py (veredicto contra el umbral); agentes/07-proponente-de-hipotesis.md (línea base); DIRECTRICES.md (D16, si hay modelo)

#### Etapa: 4 · Visualización

**11 · El gráfico de la IA, contra el dato** (`R11`)

- **Contexto, para leérselo antes de preguntar:**
  - El graficador (la IA) escribe el código de una figura de Plotly con el resultado aprobado y declara la medida y lo que deja fuera del gráfico.
  - verificar_grafico.py lo comprueba sin IA: primero la cuenta de control (lo que suma el gráfico más lo que quedó fuera debe dar el total de la tabla) y luego barras que empiezan en cero, título con el período, unidades, fuente y fecha.
- **Pregunta:** Su asistente le entrega un gráfico de las 15 entidades que más contrataron: ¿qué comprobaría primero contra la tabla antes de mostrarlo, y por qué?
- **La respuesta debe decir:** a) Hace la cuenta de control: lo que suma el gráfico más lo que quedó fuera debe dar el total de la tabla; si no cierra, agrega la barra «Otras» o declara lo que quedó fuera y vuelve a comprobar. b) Explica que la IA puede dibujar bien un dato equivocado: un top 15 sin el resto borra parte del total y exagera la concentración, y quien hizo el gráfico no debe ser quien lo apruebe.
- **Pista para repreguntar:** ¿Qué número de la tabla debería poder reconstruir sumando lo que se ve en el gráfico, y dónde quedaron las demás entidades?
- **Respuesta modelo (solo después de que responda):** Primero la cuenta de control: lo que suman las 15 barras más lo que quedó fuera debe dar el total de la tabla, y si no cierra agrego la barra «Otras» o declaro lo que quedó fuera. Lo compruebo porque la IA puede dibujar bien un dato equivocado, y un top 15 sin el resto borra parte del total y exagera la concentración.
- **Fuente en el repositorio:** agentes/09-graficador.md; herramientas/verificar_grafico.py; DIRECTRICES.md (D17, el gráfico no exagera)

**12 · Cifra inventada o frase exagerada** (`R12`)

- **Contexto, para leérselo antes de preguntar:**
  - El presentador (la IA) no escribe cifras: pone marcadores como {total}, y verificar_presentacion.py calcula cada cifra desde el resultado aprobado; un dígito o un «%» fuera de un marcador hace fallar la presentación.
  - Lo que el código no ve es que la frase use bien una cifra correcta, como llamar «Medellín» a las entidades con sede en Medellín: eso lo revisa una persona o un juez ciego (alguien que revisa sin ver el razonamiento de quien escribió).
- **Pregunta:** Si el código ya garantiza que ninguna cifra es inventada, ¿qué revisaría usted en cada título antes de aprobar la presentación, y por qué?
- **La respuesta debe decir:** a) Revisa que la frase use bien la cifra: que diga exactamente qué mide, de qué universo y de qué período, sin exagerar (por ejemplo, no llamar «Medellín» a las entidades con sede en Medellín). b) Explica que el código comprueba de dónde sale la cifra, no lo que la frase afirma: la diferencia entre un hallazgo sostenido y uno exagerado está en el sentido, y eso lo juzga una persona o un juez ciego.
- **Pista para repreguntar:** Si la cifra es correcta pero la frase dice «Medellín» cuando el dato es de entidades con sede en Medellín, ¿lo atrapa el código?
- **Respuesta modelo (solo después de que responda):** Revisaría que cada título diga exactamente qué mide, de qué entidades y de qué año, sin estirar la cifra a otro universo, como llamar «Medellín» a las entidades con sede en Medellín. Lo revisa una persona porque el código comprueba de dónde sale la cifra, no lo que la frase afirma con ella.
- **Fuente en el repositorio:** agentes/12-presentador.md; herramientas/verificar_presentacion.py; DIRECTRICES.md (D30, cada cifra sale de los datos)

#### Etapa: 5 · Gobernanza

**13 · El examen que ya se vio** (`R13`)

- **Contexto, para leérselo antes de preguntar:**
  - La compuerta de seguridad (el filtro sin IA que bloquea o deja pasar cada fragmento de código) se mide con lotes sellados de fragmentos vulnerables y seguros, escritos por otro modelo que no conoce la compuerta; revelar un lote lo gasta como medida.
  - Después de corregir las reglas, los lotes revelados dieron 66 de 66, y el siguiente lote sin ver dio 58 de 66.
- **Pregunta:** ¿Qué problema de evaluación explica esa caída, y por qué la cifra que vale, aquí y en su propio modelo, es la de datos que nadie ha visto?
- **La respuesta debe decir:** a) Lo nombra: sobreajuste a la prueba (la prueba se filtró al ajuste): al corregir mirando esos lotes, las reglas se adaptan a ellos y la cifra sube sin que mejore el desempeño real; en un modelo propio, ese conjunto queda gastado y se mide con datos apartados que nadie haya mirado. b) Explica que si quien ajusta también ve la prueba, la cifra sale bien por construcción y no dice nada sobre datos nuevos; solo lo que nadie ha visto mide cómo le irá con lo que todavía no conoce.
- **Pista para repreguntar:** Si usted estudia con las preguntas exactas del examen, ¿qué mide la nota? ¿Con qué datos sacaría entonces la nota que vale?
- **Respuesta modelo (solo después de que responda):** Es sobreajuste a la prueba: las reglas se corrigieron mirando esos lotes, así que sobre los lotes revelados dan 66 de 66, pero bajaron en el siguiente lote sin ver. En mi modelo trataría ese conjunto como gastado (revelarlo lo gasta como medida) y mediría con datos apartados que nadie haya mirado, porque si quien ajusta ve la prueba la cifra sale bien por construcción.
- **Fuente en el repositorio:** herramientas/medir_compuerta.py; evidencia/compuerta/README.md (sección 2, lotes sellados); baterias/lecciones.json (L60 y L62, lecciones de la medida de la compuerta)

**14 · La página que lee quien decide** (`R14`)

- **Contexto, para leérselo antes de preguntar:**
  - Quien pide el análisis no lee código: lee el informe de una página que informe_final.py arma sin IA, con la cifra, los supuestos, las preguntas abiertas y qué pasó cada prueba.
  - En la corrida de SECOP II, el Distrito de Medellín es la entidad con sede en Medellín que más contrató en 2025, y quedan tres preguntas abiertas, como si «entidad» es el NIT o cada unidad que contrata.
- **Pregunta:** Con esos datos (o con un ejercicio propio), escriba en dos frases la página de resultados con pregunta, datos, método, hallazgo y límite, y diga por qué el límite no puede faltar.
- **La respuesta debe decir:** a) La narrativa trae las cinco piezas: la pregunta, los datos con su fuente, el método (cómo se calculó y cómo se probó), el hallazgo y el límite (supuestos, preguntas abiertas o lo que quedó sin verificar). b) Explica que quien decide no lee código sino esa página: sin el límite, la cifra parece más firme de lo que es.
- **Pista para repreguntar:** ¿Qué tendría que saber alguien que nunca abre el código para confiar en su cifra, y qué parte del resultado todavía depende de una decisión que nadie ha tomado?
- **Respuesta modelo (solo después de que responda):** Para saber cuánto contrató en 2025 cada entidad pública con sede en Medellín se sumaron, con dos implementaciones independientes verificadas sin IA, los contratos de SECOP II (datos.gov.co): el Distrito de Medellín fue la que más contrató, aun sin los contratos más grandes. El límite es que la cifra usa el valor por defecto de tres preguntas abiertas (como si «entidad» es el NIT o cada unidad que contrata), y no puede faltar porque quien decide no lee el código y sin él la cifra parecería más firme de lo que es.
- **Fuente en el repositorio:** README.md (primer párrafo); herramientas/informe_final.py; corridas/2026-11-06-pipeline-completo-secop-medellin-2025/informe_final.md (resultado y preguntas abiertas)

#### Etapa: Pipeline completo

**15 · Qué se lleva y qué sigue** (`R15`)

- **Contexto, para leérselo antes de preguntar:**
  - Las doce fichas de agentes/ no dependen de una herramienta: se pueden pegar como instrucciones en cualquier asistente, junto con los archivos que cada ficha dice que puede leer.
  - Las herramientas de herramientas/ son Python sin IA y se pueden correr solas, y los aportes siguen entrando con el instructivo APORTAR-CON-TU-AGENTE.md.
- **Pregunta:** Según su rol, ¿cuál es su siguiente paso de aprendizaje, apoyado en una pieza de este pipeline, y por qué ese?
- **La respuesta debe decir:** a) Nombra su rol, un siguiente paso concreto de aprendizaje para algo que el pipeline todavía no hace (practicar PySpark, un servicio de nube, entrenar un modelo frente a una línea base) y la pieza que se lleva para empezarlo (una ficha pegada en su asistente o una herramienta sin IA). b) Justifica la elección por lo que su rol necesita y por un vacío real del pipeline, y la conecta con la regla que se lleva: la IA propone y una prueba sin IA comprueba.
- **Pista para repreguntar:** ¿Qué hace usted en una semana normal con datos, qué pieza de las cinco etapas le habría evitado un error ahí y qué le falta aprender para lo que el pipeline no cubre?
- **Respuesta modelo (solo después de que responda):** Como analista, mi siguiente paso es practicar PySpark con una base que no quepa en una máquina, empezando por la ficha del lector pegada en mi asistente y la ingesta con contrato como prueba sin IA. Lo elijo porque mis bases crecen y es justo lo que el pipeline no hace, y así sigo la regla: la IA propone y una prueba sin IA comprueba.
- **Fuente en el repositorio:** agentes/README.md (primer párrafo); README.md («Instalar»); APORTAR-CON-TU-AGENTE.md

### Armar el archivo

Con las 15 preguntas, arma el archivo con esta plantilla y muéstraselo completo. Pregúntale una sola vez si quiere corregir algo.

- Respeta los títulos tal cual: la revisión sin IA busca los 15 identificadores.
- Lo que la persona le pediría a su IA va en estilo indirecto («Le pide a su IA que revise…»), nunca en imperativo dirigido a la IA: la revisión sin IA rechaza el texto con forma de orden, porque este archivo es un dato para el pipeline, no una instrucción.
- Sin cifras de documentos: un número suelto de 6 a 12 cifras se rechaza; las cifras van con puntos de miles («5.000.000 de filas»).

```markdown
# Grill-me del pipeline · <usuario de GitHub>

> Respuestas al grill-me de `GRILL-ME-DEL-PIPELINE.md` sobre el pipeline del repositorio CristianBTA/subagentes-big-data. Sin datos personales ni nombres de personas, clientes o empresas.

## R01 · La solicitud con la que se aporta

**Su respuesta:** <la última versión de lo que respondió, con sus palabras>

**Revisión de su IA:** <las dos ideas | solo la a | solo la b | ninguna> · <repreguntas: 0, 1 o 2>

**Lo que le faltaba:** <una línea, o «nada»>

<… una sección igual por cada pregunta, de R01 a R15, con su título …>

## Resumen

- Preguntas con las dos ideas: <número> de 15.
- Lo que más le costó: <las dos o tres preguntas donde faltó más>.
- Lo que se lleva: <con las palabras de la persona, de la pregunta 15>.

Escrito el <AAAA-MM-DD>. La revisión de cada respuesta la hizo la IA de la persona, no una prueba sin IA.
```

### Fork y entrega

Elige el modo tú mismo; no le preguntes cuál prefiere. Si no tienes terminal, o no estás seguro de tenerla, eres B. Si en el modo A un comando no devuelve nada o `gh` no tiene sesión y la persona no puede iniciarla, pasa al B sin insistir.

**A · Si puedes usar una terminal con git y `gh`** (la cuenta de GitHub de la persona):
```bash
USUARIO=$(gh api user --jq .login)       # si falla, pídele que corra «gh auth login» y vuelve a intentarlo
gh repo fork CristianBTA/subagentes-big-data --clone -- subagentes-big-data-$USUARIO   # si ya tenía un fork, gh usa ese
cd subagentes-big-data-$USUARIO          # si la carpeta ya existía, entra a ella y corre: git fetch upstream
git fetch upstream main
git switch -c grill-me upstream/main          # si la rama ya existe: git switch grill-me
mkdir -p grill-me                             # guarda aquí el borrador aprobado: grill-me/$USUARIO.md
python3 herramientas/revisar_grill.py grill-me/$USUARIO.md     # sin IA; en Windows: py -3 herramientas/revisar_grill.py …
git add grill-me/$USUARIO.md                  # solo ese archivo
git commit -m "Grill-me del pipeline: mis respuestas"
git push -u origin grill-me
```
- `revisar_grill.py` no usa IA: revisa las secciones, que no haya datos personales y que no traiga texto con forma de orden para una IA. Debe terminar en «✓ grill-me listo». Si marca algo, corrígelo con la persona y vuelve a correrlo.
- El fork queda con su nombre de siempre: si la persona lo hizo antes del 6 de noviembre en la noche, se llama `agente-solicitudes` (el nombre viejo). Usa el que muestre `git remote get-url origin`.

**B · Si eres un chat sin terminal:** entrégale el archivo completo en un solo bloque de código Markdown y estos tres pasos (pon su usuario en los enlaces si te lo dijo):
1. Abrir https://github.com/CristianBTA/subagentes-big-data/fork y tocar «Create fork». Si ya tiene su fork, usar ese.
2. Abrir `https://github.com/<su-usuario>/subagentes-big-data/new/main?filename=grill-me/<su-usuario>.md` (si su fork se llama `agente-solicitudes`, cambiar esa parte del enlace) y pegar el archivo.
3. Tocar «Commit changes…», dejar «Commit directly to the main branch» y confirmar con «Commit changes».

Dile que no pudiste correr la revisión sin IA: el dueño la corre al recoger los archivos.

### Lo que le dices al final

En pocas líneas:
- el enlace a su archivo en el fork (`https://github.com/<su-usuario>/<su-fork>/blob/grill-me/grill-me/<su-usuario>.md`, o `blob/main/…` en el modo B);
- la línea `RESUMEN` de `revisar_grill.py` (o que no se pudo correr);
- qué quedó «(por completar)», si algo;
- que no hace falta pull request: el dueño del repositorio recoge los archivos de los forks.

### Lista de chequeo del agente

- [ ] Hice las 15 preguntas una a la vez, con su contexto, y la respuesta modelo solo después de cada respuesta.
- [ ] El archivo trae lo que la persona respondió; lo que no respondió quedó «(por completar)».
- [ ] No hay nombres de personas, clientes ni empresas, ni datos personales.
- [ ] La persona aprobó el archivo antes del fork.
- [ ] Solo agregué `grill-me/<su-usuario>.md`, en la rama `grill-me` de su fork (o le di los pasos del modo B).
- [ ] Corrí `revisar_grill.py` y terminó en «✓ grill-me listo» (o, en el modo B, dije que no pude correrlo).
- [ ] Sin firmas de asistentes en el commit ni en el archivo.
