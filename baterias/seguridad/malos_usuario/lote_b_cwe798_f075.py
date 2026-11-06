import mysql.connector

def abrir_conexion_ventas():
    con = mysql.connector.connect(
        host="mysql-dw.internal",
        user="report_user",
        password="ReportPassword#2024",
        database="ventas_consolidado"
    )
    return con
