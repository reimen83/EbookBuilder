from pathlib import Path

from PIL import Image

from pdf_cache import PdfPageCache


def test_cache_de_paginas_invalida_por_parametros(tmp_path: Path):
    cache = PdfPageCache(tmp_path)
    source = tmp_path / "origem.pdf"
    source.write_bytes(b"pdf")
    source_key = cache.source_key(source)

    imagem = Image.new("RGB", (4, 4), "white")
    path = cache.page_path(source_key, 0, 150, None, None, True)
    cache.save(imagem, path)

    assert cache.is_valid(path)
    assert cache.page_path(source_key, 0, 300, None, None, True) != path
