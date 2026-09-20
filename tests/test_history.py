from history import HistoryStore


def test_history_store_salva_e_lista_itens_mais_recentes(tmp_path):
    store = HistoryStore(tmp_path / "history.json")

    primeiro = store.registrar(
        origem="/tmp/origem1.md",
        saida="/tmp/saida1.pdf",
        titulo="Livro 1",
        subtitulo="Sub 1",
        tema="modern",
        variacao="arch_1",
    )
    segundo = store.registrar(
        origem="/tmp/origem2.md",
        saida="/tmp/saida2.pdf",
        titulo="Livro 2",
        subtitulo="Sub 2",
        tema="editorial",
        variacao="arch_2",
    )

    assert primeiro["destino"] == "/tmp/saida1.pdf"
    assert segundo["destino"] == "/tmp/saida2.pdf"
    assert store.listar(1)[0]["destino"] == "/tmp/saida2.pdf"


def test_history_store_registra_e_lista_projetos_recentes(tmp_path):
    store = HistoryStore(tmp_path / "history.json")

    projeto = store.registrar_projeto(
        origem="/tmp/arquivo.md",
        destino="/tmp/projeto",
        titulo="Projeto recente",
        subtitulo="Detalhes",
        tema="modern",
        variacao="arch_1",
    )

    assert projeto["tipo"] == "projeto"
    assert store.listar_projetos(1)[0]["origem"] == "/tmp/arquivo.md"


def test_history_store_rejeita_origem_ou_destino_vazios(tmp_path):
    store = HistoryStore(tmp_path / "history.json")

    try:
        store.registrar("", "/tmp/saida.pdf")
        assert False, "Deveria ter levantado ValueError"
    except ValueError:
        pass
