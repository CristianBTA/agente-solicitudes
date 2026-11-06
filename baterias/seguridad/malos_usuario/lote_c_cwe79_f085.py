from string import Template

def armar_fila_proveedor(razon_social, rubro):
    plantilla = Template("<tr><td>$empresa</td><td>$actividad</td></tr>")
    return plantilla.substitute(empresa=razon_social, actividad=rubro)
