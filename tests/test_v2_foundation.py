from pathlib import Path

from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.core.flowables import CTAButton, CalloutBox
from app.data.project_manager import ProjectManager
from app.utils.metadata import inject_pdf_metadata


def test_project_manager_persiste_configuracao_e_historico(tmp_path: Path):
    manager = ProjectManager(tmp_path / "projects.db")
    project_id = manager.save_project("Livro", {"tema": "modern"})
    manager.save_project("Livro", {"tema": "dark_tech"}, project_id=project_id)

    project = manager.get_project(project_id)
    assert project["settings"]["tema"] == "dark_tech"
    assert manager.list_projects()[0]["id"] == project_id


def test_flowables_v2_calculam_tamanho():
    callout = CalloutBox("Texto", title="Dica")
    button = CTAButton("Saiba mais", url="https://example.test")
    assert callout.wrap(400, 800)[1] > 0
    assert button.wrap(400, 800) == (150, 34)


def test_inject_pdf_metadata_adiciona_campos_padrao_e_xmp(tmp_path: Path):
    path = tmp_path / "metadata.pdf"
    document = canvas.Canvas(str(path), pagesize=A4)
    document.drawString(50, 700, "Conteúdo")
    document.save()

    inject_pdf_metadata(
        path,
        title="Livro de teste",
        author="Autor",
        keywords=["ebook", "teste"],
        subject="Demonstração",
    )

    reader = PdfReader(str(path))
    assert reader.metadata.title == "Livro de teste"
    assert reader.metadata.author == "Autor"
    assert reader.xmp_metadata.dc_title["x-default"] == "Livro de teste"
