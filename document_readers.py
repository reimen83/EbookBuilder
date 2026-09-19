import os

from reportlab.platypus import PageBreak

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
            return []

        meio = pagina.width / 2
        esquerda = [word for word in words if word["x0"] < meio]
        direita = [word for word in words if word["x0"] >= meio]
        if len(esquerda) < 8 or len(direita) < 8:
            return None

        linhas = self._agrupar_linhas(words)
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
            line["top"]
            for line in pagina.lines
            if line["height"] == 0
            and line["x0"] <= meio
            and line["x1"] >= meio
        ]
        return resultado, separadores

    def parse(self, caminho_pdf):
        if pdfplumber is None:
            raise ImportError("A biblioteca 'pdfplumber' não está instalada.")

        conteudo = []
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                colunas_extraidas = self._extrair_linhas_de_duas_colunas(pagina)
                if colunas_extraidas is not None:
                    linhas_colunas, separadores = colunas_extraidas
                    tabela_colunas = self.renderer._gerar_colunas_pdf_flowable(
                        linhas_colunas,
                        separadores=separadores,
                    )
                    if tabela_colunas:
                        conteudo.extend([tabela_colunas, PageBreak()])
                    continue

                tabelas = pagina.extract_tables()
                if tabelas:
                    for tabela in tabelas:
                        for linha in tabela:
                            if linha and len(linha) >= 2 and (linha[0] or linha[1]):
                                col_a = (linha[0] or "").replace("\n", " ").strip()
                                col_b = (linha[1] or "").replace("\n", " ").strip()
                                if col_a or col_b:
                                    conteudo.extend(
                                        self.renderer._parse_markdown(f"{col_a} | {col_b}")
                                    )
                else:
                    texto_pagina = pagina.extract_text()
                    if texto_pagina:
                        texto_formatado = self.smart_parser.inferir_estrutura(texto_pagina)
                        conteudo.extend(self.renderer._parse_markdown(texto_formatado))

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
