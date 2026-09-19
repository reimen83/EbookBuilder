from pathlib import Path

import pytest

from validation import (
    build_output_path,
    validate_cover_file,
    validate_destination_directory,
    validate_source_file,
)


def test_validate_source_file_aceita_extensao_suportada(tmp_path: Path):
    fonte = tmp_path / "capitulo.md"
    fonte.write_text("# Capítulo", encoding="utf-8")

    assert validate_source_file(fonte) == fonte


def test_validate_source_file_rejeita_extensao_desconhecida(tmp_path: Path):
    fonte = tmp_path / "capitulo.rtf"
    fonte.write_text("conteúdo", encoding="utf-8")

    with pytest.raises(ValueError, match="Formato de fonte não suportado"):
        validate_source_file(fonte)


def test_build_output_path_usa_nome_padrao(tmp_path: Path):
    fonte = tmp_path / "meu_livro.txt"
    fonte.write_text("conteúdo", encoding="utf-8")

    assert build_output_path(fonte) == tmp_path / "meu_livro_ebook.pdf"


def test_validate_cover_file_rejeita_arquivo_inexistente(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="Imagem de capa não encontrada"):
        validate_cover_file(tmp_path / "capa.png")


def test_validate_destination_directory_rejeita_arquivo(tmp_path: Path):
    arquivo = tmp_path / "destino.txt"
    arquivo.write_text("não é uma pasta", encoding="utf-8")

    with pytest.raises(ValueError, match="O destino não é uma pasta"):
        validate_destination_directory(arquivo)
