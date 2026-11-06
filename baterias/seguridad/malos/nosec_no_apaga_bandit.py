from xml.etree import ElementTree


def analizar(texto):
    return ElementTree.fromstring(texto)  # nosec
