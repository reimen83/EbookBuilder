import os
import tempfile

import pypdfium2 as pdfium
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.platypus import PageBreak, SimpleDocTemplate, Spacer

from covers import CapaHandler
from document_readers import DocumentReader
from pagination import NumberedCanvas
from parsers import SmartParser
from renderer import MarkdownRenderer
from themes import ThemeEngine


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
        self.arquivo_fonte = os.fspath(arquivo_fonte)
        self.arquivo_saida = os.fspath(arquivo_saida)
        self.capa_url = os.fspath(capa_url) if capa_url else capa_url
        self.variacao_capa = variacao_capa
        self.tema = tema
        self.theme_cfg = ThemeEngine.obter_estilos(self.tema)
        self.renderer = MarkdownRenderer(self.theme_cfg)
        self.document_reader = DocumentReader(self.renderer, SmartParser)

        titulo_auto, subtitulo_auto = SmartParser.extrair_titulos_documento(arquivo_fonte)
        self.titulo_ebook = titulo_ebook.strip() if titulo_ebook.strip() else titulo_auto
        self.sub_titulo_ebook = (
            sub_titulo_ebook.strip() if sub_titulo_ebook.strip() else subtitulo_auto
        )

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

    def _criar_capa_handler(self):
        return CapaHandler(
            origem_capa=self.capa_url,
            variacao_capa=self.variacao_capa,
            titulo=self.titulo_ebook,
            sub_titulo=self.sub_titulo_ebook,
            tema=self.tema,
        )

    def _criar_documento(self, path):
        return SimpleDocTemplate(
            str(path),
            pagesize=A4,
            leftMargin=54,
            rightMargin=54,
            topMargin=72,
            bottomMargin=72,
        )

    def _criar_canvas_com_tema(self, *args, **kwargs):
        canvas_inst = NumberedCanvas(*args, **kwargs)
        canvas_inst.tema_nome = self.tema
        return canvas_inst

    def _carregar_conteudo(self):
        if not os.path.exists(self.arquivo_fonte):
            raise FileNotFoundError(f"Arquivo não encontrado: {self.arquivo_fonte}")

        extensao = os.path.splitext(self.arquivo_fonte)[1].lower()
        if extensao == ".txt":
            with open(self.arquivo_fonte, "r", encoding="utf-8") as f:
                texto = f.read()
            return self._parse_markdown(SmartParser.inferir_estrutura(texto))

        if extensao in [".md", ".markdown", ".docx", ".pdf"]:
            return self.document_reader.parse_file(self.arquivo_fonte)

        raise ValueError(f"Extensão não suportada: {extensao}")

    def analisar_documento(self):
        if not os.path.exists(self.arquivo_fonte):
            raise FileNotFoundError(f"Arquivo não encontrado: {self.arquivo_fonte}")

        extensao = os.path.splitext(self.arquivo_fonte)[1].lower()
        relatorio = {
            "formato": extensao.lstrip(".").upper(),
            "paginas_detectadas": None,
            "paginas_com_texto": None,
            "paginas_com_imagens": None,
            "colunas_detectadas": None,
        }

        if extensao == ".pdf":
            import pdfplumber

            paginas_texto = 0
            paginas_imagens = 0
            colunas = 0
            with pdfplumber.open(self.arquivo_fonte) as pdf:
                relatorio["paginas_detectadas"] = len(pdf.pages)
                for pagina in pdf.pages:
                    if pagina.extract_text():
                        paginas_texto += 1
                    if pagina.images:
                        paginas_imagens += 1
                    palavras = pagina.extract_words() or []
                    meio = pagina.width / 2
                    if (
                        sum(p["x0"] < meio for p in palavras) >= 8
                        and sum(p["x0"] >= meio for p in palavras) >= 8
                    ):
                        colunas += 1
            relatorio["paginas_com_texto"] = paginas_texto
            relatorio["paginas_com_imagens"] = paginas_imagens
            relatorio["colunas_detectadas"] = colunas
        else:
            relatorio["paginas_detectadas"] = 1

        return relatorio

    def compilar(self, analise=None):
        conteudo_flowables = self._carregar_conteudo()
        doc = self._criar_documento(self.arquivo_saida)
        capa_handler = self._criar_capa_handler()

        story = [Spacer(1, 400), PageBreak()]
        story.extend(conteudo_flowables)

        doc.build(
            story,
            onFirstPage=capa_handler.desenhar_capa,
            onLaterPages=capa_handler.desenhar_fundo_paginas,
            canvasmaker=self._criar_canvas_com_tema,
        )
        relatorio = dict(analise or self.analisar_documento())
        relatorio["arquivo_saida"] = self.arquivo_saida
        relatorio["tamanho_saida_bytes"] = os.path.getsize(self.arquivo_saida)
        relatorio["paginas_geradas"] = len(PdfReader(self.arquivo_saida).pages)
        return relatorio

    def gerar_preview_capa_fast(self, dpi=100):
        file_descriptor, tmp_pdf_path = tempfile.mkstemp(
            prefix="ebookbuilder_preview_",
            suffix=".pdf",
        )
        os.close(file_descriptor)

        try:
            doc = self._criar_documento(tmp_pdf_path)
            capa_handler = self._criar_capa_handler()
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
