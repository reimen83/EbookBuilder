from pathlib import Path

SUPPORTED_SOURCE_EXTENSIONS = frozenset({".md", ".markdown", ".txt", ".docx", ".pdf"})
SUPPORTED_COVER_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg"})


def validate_source_file(path):
    """Valida e retorna o caminho de um documento de entrada suportado."""
    if not path or not str(path).strip():
        raise ValueError("Selecione um arquivo de fonte.")

    source = Path(path).expanduser()
    if not source.exists():
        raise FileNotFoundError(f"Arquivo de fonte não encontrado: {source}")
    if not source.is_file():
        raise ValueError(f"O caminho da fonte não é um arquivo: {source}")
    if source.suffix.lower() not in SUPPORTED_SOURCE_EXTENSIONS:
        extensoes = ", ".join(sorted(SUPPORTED_SOURCE_EXTENSIONS))
        raise ValueError(f"Formato de fonte não suportado. Use: {extensoes}")

    return source


def validate_cover_file(path):
    """Valida e retorna o caminho de uma imagem de capa local."""
    if not path or not str(path).strip():
        raise ValueError("Selecione uma imagem de capa.")

    cover = Path(path).expanduser()
    if not cover.exists():
        raise FileNotFoundError(f"Imagem de capa não encontrada: {cover}")
    if not cover.is_file():
        raise ValueError(f"O caminho da capa não é um arquivo: {cover}")
    if cover.suffix.lower() not in SUPPORTED_COVER_EXTENSIONS:
        extensoes = ", ".join(sorted(SUPPORTED_COVER_EXTENSIONS))
        raise ValueError(f"Formato de capa não suportado. Use: {extensoes}")

    return cover


def validate_destination_directory(path):
    """Valida e retorna o diretório existente onde o PDF será salvo."""
    if not path or not str(path).strip():
        raise ValueError("Selecione uma pasta de destino.")

    destination = Path(path).expanduser()
    if not destination.exists():
        raise FileNotFoundError(f"Pasta de destino não encontrada: {destination}")
    if not destination.is_dir():
        raise ValueError(f"O destino não é uma pasta: {destination}")

    return destination


def build_output_path(source_path, destination_path=None):
    """Gera o nome padrão do PDF final para uma fonte válida."""
    source = validate_source_file(source_path)
    destination = destination_path or source.parent
    destination = validate_destination_directory(destination)
    return destination / f"{source.stem}_ebook.pdf"
