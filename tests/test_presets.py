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


def test_preset_store_exporta_e_importa_presets(tmp_path):
    store = PresetStore(tmp_path / "presets.json")
    store.salvar("Projeto A", {"tema": "modern", "titulo": "Meu livro"})

    exportado = tmp_path / "exportado.json"
    store.exportar(exportado)

    importado = PresetStore(tmp_path / "importado.json")
    importado.importar(exportado)

    assert importado.carregar("Projeto A") == {"tema": "modern", "titulo": "Meu livro"}


def test_preset_store_renomeia_preservando_configuracao(tmp_path):
    store = PresetStore(tmp_path / "presets.json")
    configuracao = {"tema": "editorial", "titulo": "Meu livro"}
    store.salvar("Antigo", configuracao)

    store.renomear("Antigo", "Novo")

    assert store.listar() == ["Novo"]
    assert store.carregar("Novo") == configuracao


def test_preset_store_rejeita_renomear_para_nome_existente(tmp_path):
    store = PresetStore(tmp_path / "presets.json")
    store.salvar("Primeiro", {})
    store.salvar("Segundo", {})

    with pytest.raises(ValueError, match="Já existe"):
        store.renomear("Primeiro", "Segundo")


def test_preset_store_exclui_preset(tmp_path):
    store = PresetStore(tmp_path / "presets.json")
    store.salvar("Temporário", {"tema": "modern"})

    store.excluir("Temporário")

    assert store.listar() == []
    with pytest.raises(KeyError, match="não encontrado"):
        store.carregar("Temporário")
