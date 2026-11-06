import duckdb

con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")
con.execute("SET s3_endpoint='minio.interna:9000'")
con.execute("SET s3_url_style='path'")
con.execute("SET s3_access_key_id='etl_lago'")
con.execute("SET s3_secret_access_key='q8Zt2LmN4vB7xK1pR9sD3fG6hJ0wYc5T'")
resumen = con.execute("""
    SELECT departamento, SUM(valor) AS total
    FROM read_parquet('s3://lago/contratos/*.parquet')
    GROUP BY departamento
""").df()
print(resumen)
