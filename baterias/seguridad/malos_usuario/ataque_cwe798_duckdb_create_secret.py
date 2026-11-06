import duckdb

con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")
con.execute("""
    CREATE SECRET lago (
        TYPE S3,
        KEY_ID 'etl_lago',
        SECRET 'q8Zt2LmN4vB7xK1pR9sD3fG6hJ0wYc5T',
        ENDPOINT 'minio.interna:9000',
        URL_STYLE 'path'
    )
""")
resumen = con.execute("""
    SELECT departamento, SUM(valor) AS total
    FROM read_parquet('s3://lago/contratos/*.parquet')
    GROUP BY departamento
""").df()
print(resumen)
