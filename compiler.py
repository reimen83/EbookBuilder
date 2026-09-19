import os
import tempfile
import pypdfium2 as pdfium

from reportlab.lib.pagesizes import A4
from reportlab.platypus import PageBreak, SimpleDocTemplate, Spacer


from themes import ThemeEngine
from parsers import SmartParser
from covers import CapaHandler, upscale_cover_image
from pagination import NumberedCanvas
from renderer import MarkdownRenderer
from document_readers import DocumentReader


class EbookCompiler:
    def __init__(
        self,
        arquivo_fonte,
        arquivo_saida="ebook_final.pdf",
        capa_url=None,
        titulo_ebook="",
        sub_titulo_ebook="",
        tema="music_prod",
        variacao_capa=None,
    ):
        self.arquivo_fonte = arquivo_fonte
        self.arquivo_saida = arquivo_saida
        self.capa_url = capa_url
        self.variacao_capa = variacao_capa
        self.tema = tema
        self.theme_cfg = ThemeEngine.obter_estilos(self.tema)
        self.renderer = MarkdownRenderer(self.theme_cfg)
        self.document_reader = DocumentReader(self.renderer, SmartParser)

        titulo_auto, subtitulo_auto = SmartParser.extrair_titulos_documento(arquivo_fonte)
        self.titulo_ebook = titulo_ebook.strip() if titulo_ebook.strip() else titulo_auto
        self.sub_titulo_ebook = sub_titulo_ebook.strip() if sub_titulo_ebook.strip() else subtitulo_auto

    def _converter_inline_formatting(self, texto):
        return self.renderer._converter_inline_formatting(texto)

    def _gerar_tabela_flowable(self, linhas_tabela):
        return self.renderer._gerar_tabela_flowable(linhas_tabela)

    def _parse_markdown(self, texto_md):
        return self.renderer._parse_markdown(texto_md)

    def _parse_docx(self, caminho_docx):
        return self.document_reader.parse_docx(caminho_docx)

    def _parse_pdf(self, caminho_pdf):
        return self.document_reader.parse_pdf(caminho_pdf)

    def compilar(self):
        if not os.path.exists(self.arquivo_fonte):
            raise FileNotFoundError(f"Arquivo não encontrado: {self.arquivo_fonte}")

        extensao = os.path.splitext(self.arquivo_fonte)[1].lower()

        if extensao in [".md", ".markdown"]:
            with open(self.arquivo_fonte, "r", encoding="utf-8") as f:
                conteudo_flowables = self._parse_markdown(f.read())
        elif extensao == ".txt":
            with open(self.arquivo_fonte, "r", encoding="utf-8") as f:
                conteudo_flowables = self._parse_markdown(SmartParser.inferir_estrutura(f.read()))
        elif extensao == ".docx":
            conteudo_flowables = self._parse_docx(self.arquivo_fonte)
        elif extensao == ".pdf":
            conteudo_flowables = self._parse_pdf(self.arquivo_fonte)
        else:
            raise ValueError(f"Extensão não suportada: {extensao}")

        doc = SimpleDocTemplate(
            self.arquivo_saida,
            pagesize=A4,
            leftMargin=54,
            rightMargin=54,
            topMargin=72,
            bottomMargin=72,
        )

        capa_handler = CapaHandler(
            origem_capa=self.capa_url,
            variacao_capa=self.variacao_capa,
            titulo=self.titulo_ebook,
            sub_titulo=self.sub_titulo_ebook,
            tema=self.tema,
        )

        def criar_canvas_com_tema(*args, **kwargs):
            canvas_inst = NumberedCanvas(*args, **kwargs)
            canvas_inst.tema_nome = self.tema
            return canvas_inst

        story = [Spacer(1, 400), PageBreak()]
        story.extend(conteudo_flowables)

        doc.build(
            story,
            onFirstPage=capa_handler.desenhar_capa,
            onLaterPages=capa_handler.desenhar_fundo_paginas,
            canvasmaker=criar_canvas_com_tema,
        )

    def gerar_preview_capa_fast(self, dpi=100):
        file_descriptor, tmp_pdf_path = tempfile.mkstemp(
            prefix="ebookbuilder_preview_",
            suffix=".pdf",
        )
        os.close(file_descriptor)

        try:
            doc = SimpleDocTemplate(
                tmp_pdf_path,
                pagesize=A4,
                leftMargin=54,
                rightMargin=54,
                topMargin=72,
                bottomMargin=72,
            )

            capa_handler = CapaHandler(
                origem_capa=self.capa_url,
                variacao_capa=self.variacao_capa,
                titulo=self.titulo_ebook,
                sub_titulo=self.sub_titulo_ebook,
                tema=self.tema,
            )

            story = [Spacer(1, 400)]

            doc.build(
                story,
                onFirstPage=capa_handler.desenhar_capa,
                onLaterPages=capa_handler.desenhar_fundo_paginas,
            )

            pdf = pdfium.PdfDocument(tmp_pdf_path)
            page = pdf[0]
            image_pil = page.render(scale=dpi / 72).to_pil()
            pdf.close()

            return [image_pil]
        finally:
            if os.path.exists(tmp_pdf_path):
                try:
                    os.remove(tmp_pdf_path)
                except Exception:
                    pass
