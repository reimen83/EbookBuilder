from types import SimpleNamespace

from PIL import Image

import gui as gui_module
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


def test_aplicar_preview_configura_ctk_image_publico(monkeypatch):
    configuracoes = []
    imagem_ctk = object()

    class LabelFalso:
        def configure(self, **kwargs):
            configuracoes.append(kwargs)

    gui = object.__new__(EbookBuilderGUI)
    gui._preview_generation = 1
    gui.lbl_imagem_preview = LabelFalso()
    gui.preview_ctk_image = None

    monkeypatch.setattr(gui_module.ctk, "CTkImage", lambda **kwargs: imagem_ctk)
    gui._aplicar_preview(1, Image.new("RGB", (80, 120), "navy"))

    assert gui.preview_ctk_image is imagem_ctk
    assert configuracoes[-1] == {"image": imagem_ctk, "text": ""}


def test_aplicar_preview_limpa_imagem_sem_usar_none():
    configuracoes = []

    class LabelFalso:
        def configure(self, **kwargs):
            configuracoes.append(kwargs)

    gui = object.__new__(EbookBuilderGUI)
    gui._preview_generation = 1
    gui.lbl_imagem_preview = LabelFalso()
    gui.preview_ctk_image = object()

    gui._aplicar_preview(1, None)

    assert gui.preview_ctk_image is None
    assert configuracoes == [
        {"image": None},
        {"text": "Nenhuma imagem de capa foi gerada."},
    ]
