# Para agentes de IA en este repositorio

Si ayudas a una persona a **aportar** a este repositorio, sigue [`APORTAR-CON-TU-AGENTE.md`](APORTAR-CON-TU-AGENTE.md): no corras el pipeline, no incluyas datos reales, trae la prueba del aporte, corre `herramientas/validar_aporte.py` y no agregues firmas de asistentes.

Si escribes código para una persona, revísalo con `herramientas/comprobar.py --perfil usuario <archivo>` antes de entregarlo: 0 pasa, 1 no pasa, 2 no se pudo revisar (nunca se da por bueno). La conexión con cada herramienta está en [`conexion/`](conexion/README.md).

Las muestras de código de usuario (con red, archivos o base de datos) van en `baterias/seguridad/malos_usuario/` si deben bloquearse y en `buenos_usuario/` si deben pasar; se prueban con `herramientas/baterias.py`.

Los subagentes del pipeline no siguen este archivo (los que lanza `orquestar.mjs` con agy o Codex lo dicen al inicio de su instrucción): cada uno sigue su ficha en [`agentes/`](agentes/README.md) y las [reglas comunes](agentes/00-reglas-comunes.md).
