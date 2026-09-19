from preview_state import build_preview_signature


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
