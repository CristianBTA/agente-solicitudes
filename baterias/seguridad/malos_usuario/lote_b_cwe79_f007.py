def generar_etiqueta_svg(etiqueta, valor):
    svg = f"""
    <svg width="200" height="50">
        <text x="10" y="25" font-family="sans-serif">{etiqueta}: {valor}</text>
    </svg>
    """
    return svg.strip()
