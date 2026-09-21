from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.xmp import XmpInformation


def inject_pdf_metadata(
    source_path,
    title="",
    author="",
    keywords=None,
    subject="",
    copyright_status="",
):
    """Adiciona metadados padrão e XMP sem reprocessar o conteúdo visual."""
    source = Path(source_path)
    temporary = source.with_suffix(".metadata.tmp.pdf")
    reader = PdfReader(str(source))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    metadata = {
        "/Title": title or "",
        "/Author": author or "",
        "/Keywords": ", ".join(keywords or []),
        "/Subject": subject or "",
        "/Copyright": copyright_status or "",
        "/Producer": "EbookBuilder",
    }
    writer.add_metadata(metadata)
    xmp = XmpInformation.create()
    xmp.dc_title = {"x-default": title} if title else {}
    xmp.dc_creator = [author] if author else []
    xmp.dc_subject = keywords or []
    xmp.dc_description = {"x-default": subject} if subject else {}
    xmp.pdf_producer = "EbookBuilder"
    writer.xmp_metadata = xmp
    with temporary.open("wb") as output:
        writer.write(output)
    temporary.replace(source)
