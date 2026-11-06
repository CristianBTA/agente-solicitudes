import xml.etree.ElementTree as ET

def construir_tarjeta_usuario(nombre, cargo, correo):
    div = ET.Element("div", attrib={"class": "perfil"})
    h3 = ET.SubElement(div, "h3")
    h3.text = nombre
    p = ET.SubElement(div, "p")
    p.text = f"Cargo: {cargo}"
    a = ET.SubElement(div, "a", attrib={"href": f"mailto:{correo}"})
    a.text = "Contactar"
    return ET.tostring(div, encoding="unicode")
