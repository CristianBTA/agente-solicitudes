def redactar_correo_bienvenida(nombre_empleado, departamento, notas):
    return f"""
    <html>
        <body>
            <h1>Alta de personal</h1>
            <p>Empleado: {nombre_empleado}</p>
            <p>Departamento: {departamento}</p>
            <div>Notas adicionales: {notas}</div>
        </body>
    </html>
    """
