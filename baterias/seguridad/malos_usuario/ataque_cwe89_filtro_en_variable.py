def filtrar_eventos_red(df_eventos, tipo_incidencia):
    columnas = ["id_sensor", "voltaje", "timestamp"]
    condicion = f"tipo_alerta = '{tipo_incidencia}' AND estado = 'ACTIVO'"
    df_filtrado = df_eventos.filter(condicion)
    return df_filtrado.select(*columnas)
