import duckdb

con = duckdb.connect("bodega.duckdb")
con.execute("""
    CREATE OR REPLACE TABLE contratistas_publico AS
    SELECT
        md5(lower(trim(correo))) AS correo_hash,
        sha256(CAST(cedula AS VARCHAR)) AS cedula_hash,
        municipio,
        valor_contrato
    FROM read_csv_auto('contratistas.csv')
""")
total = con.execute("SELECT count(*) FROM contratistas_publico").fetchone()[0]
print(f"{total} filas publicadas")
