from types import SimpleNamespace

from gui import EbookBuilderGUI
from preview_state import build_preview_signature


def test_rolagem_direciona_evento_para_o_container_mais_proximo():
    calls = []
    canvas_externo = SimpleNamespace(yview_scroll=lambda *args: calls.append(("externo", args)))
    canvas_interno = SimpleNamespace(yview_scroll=lambda *args: calls.append(("interno", args)))
    frame_externo = SimpleNamespace(
        _parent_canvas=canvas_externo,
        _parent_frame=object(),
        master=None,
    )
    frame_interno = SimpleNamespace(
        _parent_canvas=canvas_interno,
        _parent_frame=object(),
        master=frame_externo,
    )
    widget = SimpleNamespace(master=frame_interno)
    gui = object.__new__(EbookBuilderGUI)

    resultado = gui._rolar_configuracoes(
        SimpleNamespace(widget=widget, num=5, delta=0)
    )

    assert resultado == "break"
    assert calls == [("interno", (1, "units"))]


def test_preview_signature_e_deterministica():
    primeira = build_preview_signature(
        "/tmp/livro.md",
        "/tmp/capa.png",
        "Título",
        "Subtítulo",
        "modern",
        "arch_1",
    )
    segunda = build_preview_signature(
        "/tmp/livro.md",
        "/tmp/capa.png",
        "Título",
        "Subtítulo",
        "modern",
        "arch_1",
    )

    assert primeira == segunda


def test_preview_signature_muda_quando_a_capa_muda():
    sem_capa = build_preview_signature("livro.md", "", "", "", "modern", "arch_1")
    com_capa = build_preview_signature(
        "livro.md", "/tmp/capa.png", "", "", "modern", "arch_1"
    )

    assert sem_capa != com_capa
