import pytest

from presets import PresetStore


def test_preset_store_salva_lista_e_carrega(tmp_path):
    store = PresetStore(tmp_path / "presets.json")
    configuracao = {"tema": "editorial", "titulo": "Meu livro", "variacao": "book_1"}

    store.salvar("Editorial clássico", configuracao)

    assert store.listar() == ["Editorial clássico"]
    assert store.carregar("Editorial clássico") == configuracao


def test_preset_store_sobrescreve_preset_existente(tmp_path):
    store = PresetStore(tmp_path / "presets.json")
    store.salvar("Projeto", {"tema": "modern"})
    store.salvar("Projeto", {"tema": "editorial"})

    assert store.carregar("Projeto") == {"tema": "editorial"}


def test_preset_store_rejeita_nome_vazio(tmp_path):
    with pytest.raises(ValueError, match="nome"):
        PresetStore(tmp_path / "presets.json").salvar(" ", {})


def test_preset_store_rejeita_json_invalido(tmp_path):
    caminho = tmp_path / "presets.json"
    caminho.write_text("{invalido", encoding="utf-8")

    with pytest.raises(ValueError, match="ler"):
        PresetStore(caminho).listar()
