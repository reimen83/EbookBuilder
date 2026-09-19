import io
from pathlib import Path
from unittest.mock import Mock

from PIL import Image

import covers
from cover_cache import CoverCache
from covers import CapaHandler


def _imagem_jpeg_bytes():
    imagem = Image.new("RGB", (20, 20), color="navy")
    buffer = io.BytesIO()
    imagem.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_cover_cache_salva_e_recupera_bytes(tmp_path: Path):
    cache = CoverCache(tmp_path / "covers")
    url = "https://example.test/capa.jpg"
    dados = b"imagem-processada"

    caminho = cache.save(url, dados)

    assert caminho is not None
    assert cache.get(url) == dados
    assert cache.get("https://example.test/outra.jpg") is None


def test_capa_handler_reutiliza_cache_sem_nova_requisicao(tmp_path: Path, monkeypatch):
    cache = CoverCache(tmp_path / "covers")
    url = "https://example.test/capa.jpg"
    resposta = Mock(status_code=200, content=_imagem_jpeg_bytes())
    requisicoes = []

    def fake_get(endereco, timeout):
        requisicoes.append((endereco, timeout))
        return resposta

    monkeypatch.setattr(covers.requests, "get", fake_get)
    canvas = Mock()

    CapaHandler(origem_capa=url, cover_cache=cache).desenhar_capa(canvas, None)
    CapaHandler(origem_capa=url, cover_cache=cache).desenhar_capa(canvas, None)

    assert len(requisicoes) == 1
    assert cache.get(url)


def test_capa_handler_faz_fallback_quando_rede_falha(tmp_path: Path, monkeypatch):
    cache = CoverCache(tmp_path / "covers")

    def fake_get(endereco, timeout):
        raise OSError("sem conexão")

    monkeypatch.setattr(covers.requests, "get", fake_get)
    canvas = Mock()

    CapaHandler(origem_capa="https://example.test/capa.jpg", cover_cache=cache).desenhar_capa(canvas, None)

    assert canvas.rect.called
    assert cache.get("https://example.test/capa.jpg") is None
