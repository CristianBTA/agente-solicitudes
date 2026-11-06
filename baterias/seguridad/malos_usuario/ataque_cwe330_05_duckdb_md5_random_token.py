import duckdb

con = duckdb.connect("portal.duckdb")
con.execute("""
    CREATE OR REPLACE TABLE enlaces_descarga AS
    SELECT
        id_cliente,
        md5(random()::VARCHAR) AS token,
        now() + INTERVAL 7 DAY AS vence
    FROM read_parquet('curado/clientes/*.parquet')
""")
con.execute("COPY enlaces_descarga TO 'salida/enlaces_descarga.csv' (HEADER)")
con.close()
