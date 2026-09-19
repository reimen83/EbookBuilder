from pathlib import Path

import pytest
from docx import Document
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

import compiler as compiler_module
from compiler import EbookCompiler, SmartParser, ThemeEngine


def test_inferir_estrutura_reconhece_titulo_secao_e_lista():
    texto = "INTRODUÇÃO\n\n1. Primeira etapa\n\n• Item importante"

    resultado = SmartParser.inferir_estrutura(texto)

    assert "# INTRODUÇÃO" in resultado
    assert "## 1. Primeira etapa" in resultado
    assert "- Item importante" in resultado


def test_extrair_titulos_de_markdown(tmp_path: Path):
    arquivo = tmp_path / "conteudo.md"
    arquivo.write_text("# Meu E-book\n\n## Um subtítulo\n\nTexto", encoding="utf-8")

    titulo, subtitulo = SmartParser.extrair_titulos_documento(str(arquivo))

    assert titulo == "Meu E-book"
    assert subtitulo == "Um subtítulo"


def test_temas_têm_variacoes_e_estilos():
    opcoes = ThemeEngine.obter_opcoes_capa_por_tema("modern")
    estilos = ThemeEngine.obter_estilos("modern")

    assert opcoes
    assert all({"id", "nome", "url"} <= set(opcao) for opcao in opcoes)
    assert estilos["h1"] is not None
    assert estilos["body"] is not None


def test_compilador_rejeita_arquivo_inexistente(tmp_path: Path):
    fonte = tmp_path / "nao-existe.md"
    saida = tmp_path / "saida.pdf"

    compilador = EbookCompiler(str(fonte), str(saida))

    with pytest.raises(FileNotFoundError):
        compilador.compilar()


def test_compilador_gera_pdf_de_markdown(tmp_path: Path):
    fonte = tmp_path / "conteudo.md"
    saida = tmp_path / "saida.pdf"
    fonte.write_text("# Título\n\nUm parágrafo de teste.", encoding="utf-8")

    EbookCompiler(
        arquivo_fonte=str(fonte),
        arquivo_saida=str(saida),
        titulo_ebook="Título",
        sub_titulo_ebook="Subtítulo",
        tema="modern",
    ).compilar()

    assert saida.exists()
    assert saida.stat().st_size > 0
    assert saida.read_bytes().startswith(b"%PDF")


def test_compilador_le_docx(tmp_path: Path):
    fonte = tmp_path / "conteudo.docx"
    documento = Document()
    documento.add_paragraph("Título do documento")
    documento.add_paragraph("Texto de teste em DOCX")
    documento.save(fonte)

    compiler = EbookCompiler(str(fonte), str(tmp_path / "saida.pdf"))
    flowables = compiler._parse_docx(str(fonte))

    assert flowables


def test_compilador_le_pdf(tmp_path: Path):
    fonte = tmp_path / "conteudo.pdf"
    pdf = canvas.Canvas(str(fonte), pagesize=A4)
    pdf.drawString(72, 760, "Título do documento")
    pdf.drawString(72, 740, "Texto de teste em PDF")
    pdf.save()

    compiler = EbookCompiler(str(fonte), str(tmp_path / "saida.pdf"))
    flowables = compiler._parse_pdf(str(fonte))

    assert flowables


def test_preview_usa_temporario_unico_e_limpa_arquivo(tmp_path: Path, monkeypatch):
    capa = tmp_path / "capa.png"
    Image.new("RGB", (40, 40), color="navy").save(capa)
    fonte = tmp_path / "conteudo.md"
    fonte.write_text("# Título", encoding="utf-8")
    caminhos_temporarios = []
    mkstemp_original = compiler_module.tempfile.mkstemp

    def mkstemp_rastreado(*args, **kwargs):
        resultado = mkstemp_original(*args, **kwargs)
        caminhos_temporarios.append(Path(resultado[1]))
        return resultado

    monkeypatch.setattr(compiler_module.tempfile, "mkstemp", mkstemp_rastreado)
    compiler = EbookCompiler(str(fonte), capa_url=str(capa))

    assert compiler.gerar_preview_capa_fast()
    assert len(caminhos_temporarios) == 1
    assert not caminhos_temporarios[0].exists()
