def build_preview_signature(fonte, capa, titulo, subtitulo, tema, variacao):
    """Retorna a identidade dos dados que determinam uma capa de preview."""
    return (fonte, capa, titulo, subtitulo, tema, variacao)
