import os

from reportlab.lib.utils import ImageReader
from reportlab.platypus import Flowable, PageBreak

try:
    import docx
except ImportError:
    docx = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


class BaseDocumentParser:
    def __init__(self, renderer, smart_parser):
        self.renderer = renderer
        self.smart_parser = smart_parser

    def parse(self, caminho_arquivo):
        raise NotImplementedError


class PdfPageImage(Flowable):
    def __init__(self, image, page_width, page_height):
        super().__init__()
        self.image = ImageReader(image)
        self.page_width = page_width
        self.page_height = page_height

    def wrap(self, available_width, available_height):
        scale = min(available_width / self.page_width, available_height / self.page_height)
        self.width = self.page_width * scale
        self.height = self.page_height * scale
        return self.width, self.height

    def draw(self):
        self.canv.drawImage(
            self.image,
            0,
            0,
            width=self.width,
            height=self.height,
            preserveAspectRatio=True,
            mask="auto",
        )


class MarkdownParser(BaseDocumentParser):
    def parse(self, caminho_arquivo):
        with open(caminho_arquivo, "r", encoding="utf-8", errors="ignore") as arquivo:
            texto = arquivo.read()
        return self.renderer._parse_markdown(texto)


class DocxParser(BaseDocumentParser):
    def parse(self, caminho_docx):
        if docx is None:
            raise ImportError("A biblioteca 'python-docx' não está instalada.")

        documento = docx.Document(caminho_docx)
        texto_unificado = "\n".join(paragrafo.text for paragrafo in documento.paragraphs)
        texto_estruturado = self.smart_parser.inferir_estrutura(texto_unificado)
        return self.renderer._parse_markdown(texto_estruturado)


class PdfParser(BaseDocumentParser):
    @staticmethod
    def _agrupar_linhas(words, tolerancia=3):
        linhas = []
        for word in sorted(words, key=lambda item: (item["top"], item["x0"])):
            linha = next(
                (item for item in linhas if abs(item["top"] - word["top"]) <= tolerancia),
                None,
            )
            if linha is None:
                linha = {"top": word["top"], "words": []}
                linhas.append(linha)
            linha["words"].append(word)

        return [sorted(linha["words"], key=lambda item: item["x0"]) for linha in linhas]

    def _extrair_linhas_de_duas_colunas(self, pagina):
        words = pagina.extract_words(
            x_tolerance=2,
            y_tolerance=3,
            keep_blank_chars=False,
        )
        if not words:
            return None

        meio = pagina.width / 2
        linhas = self._agrupar_linhas(words)
        linhas_esquerda = 0
        linhas_direita = 0
        linhas_em_duas_colunas = 0
        linhas_cruzando_centro = 0
        for linha in linhas:
            palavras_esquerda = [word for word in linha if word["x1"] <= meio]
            palavras_direita = [word for word in linha if word["x0"] >= meio]
            if (
                palavras_esquerda
                and palavras_direita
                and max(word["x1"] for word in palavras_esquerda) <= meio - 8
                and min(word["x0"] for word in palavras_direita) >= meio + 8
            ):
                linhas_esquerda += 1
                linhas_direita += 1
                linhas_em_duas_colunas += 1
            elif (
                min(word["x0"] for word in linha) < meio - 12
                and max(word["x1"] for word in linha) > meio + 12
            ):
                linhas_cruzando_centro += 1
            elif max(word["x1"] for word in linha) <= meio - 8:
                linhas_esquerda += 1
            elif min(word["x0"] for word in linha) >= meio + 8:
                linhas_direita += 1

        total_linhas = len(linhas)
        if (
            linhas_esquerda < 5
            or linhas_direita < 5
            or linhas_em_duas_colunas < max(5, total_linhas * 0.6)
            or linhas_cruzando_centro > max(1, total_linhas * 0.2)
        ):
            return None

        resultado = []
        for linha in linhas:
            texto_esquerda = " ".join(
                word["text"] for word in linha if word["x0"] < meio
            ).strip()
            texto_direita = " ".join(
                word["text"] for word in linha if word["x0"] >= meio
            ).strip()
            if texto_esquerda or texto_direita:
                resultado.append(
                    (
                        texto_esquerda,
                        texto_direita,
                        min(word["top"] for word in linha),
                    )
                )

        separadores = [
            (line["x0"], line["x1"], line["top"], meio)
            for line in pagina.lines
            if line["height"] == 0
            and line["x1"] - line["x0"] > 80
        ]
        divisorias = [
            (line["x0"], line["top"], line["bottom"])
            for line in pagina.lines
            if line["width"] == 0
            and meio - 4 <= line["x0"] <= meio + 4
        ]
        return resultado, separadores, divisorias

    @staticmethod
    def _preservar_pagina_como_imagem(pagina):
        imagem = pagina.to_image(resolution=150).original
        return [PdfPageImage(imagem, pagina.width, pagina.height), PageBreak()]

    def parse(self, caminho_pdf):
        if pdfplumber is None:
            raise ImportError("A biblioteca 'pdfplumber' não está instalada.")

        conteudo = []
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                colunas_extraidas = self._extrair_linhas_de_duas_colunas(pagina)
                if colunas_extraidas is not None:
                    linhas_colunas, separadores, divisorias = colunas_extraidas
                    tabela_colunas = self.renderer._gerar_colunas_pdf_flowable(
                        linhas_colunas,
                        separadores=separadores,
                        divisorias=divisorias,
                    )
                    if tabela_colunas:
                        conteudo.extend([tabela_colunas, PageBreak()])
                    continue

                # Um PDF já diagramado não deve ser linearizado: a renderização
                # da página preserva tipografia, espaçamentos, tabelas e imagens.
                conteudo.extend(self._preservar_pagina_como_imagem(pagina))

        if conteudo and isinstance(conteudo[-1], PageBreak):
            conteudo.pop()
        return conteudo


class DocumentReader:
    """Lê documentos em diferentes formatos e os converte em flowables."""

    def __init__(self, renderer, smart_parser):
        self.renderer = renderer
        self.smart_parser = smart_parser
        self.parsers = {
            ".md": MarkdownParser(renderer, smart_parser),
            ".markdown": MarkdownParser(renderer, smart_parser),
            ".txt": MarkdownParser(renderer, smart_parser),
            ".docx": DocxParser(renderer, smart_parser),
            ".pdf": PdfParser(renderer, smart_parser),
        }

    def parse_file(self, caminho_arquivo):
        extensao = os.path.splitext(caminho_arquivo)[1].lower()
        parser = self.parsers.get(extensao)
        if parser is None:
            raise ValueError(f"Extensão não suportada: {extensao}")
        return parser.parse(caminho_arquivo)

    def parse_docx(self, caminho_docx):
        return self.parsers[".docx"].parse(caminho_docx)

    def parse_pdf(self, caminho_pdf):
        return self.parsers[".pdf"].parse(caminho_pdf)
