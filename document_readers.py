import os

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
    def parse(self, caminho_pdf):
        if pdfplumber is None:
            raise ImportError("A biblioteca 'pdfplumber' não está instalada.")

        texto_completo = []
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                tabelas = pagina.extract_tables()
                if tabelas:
                    for tabela in tabelas:
                        for linha in tabela:
                            if linha and len(linha) >= 2 and (linha[0] or linha[1]):
                                col_a = (linha[0] or "").replace("\n", " ").strip()
                                col_b = (linha[1] or "").replace("\n", " ").strip()
                                if col_a or col_b:
                                    texto_completo.append(f"{col_a} | {col_b}")
                else:
                    texto_pagina = pagina.extract_text()
                    if texto_pagina:
                        texto_completo.append(texto_pagina)

        texto_unificado = "\n\n".join(texto_completo)
        texto_formatado = self.smart_parser.inferir_estrutura(texto_unificado)
        return self.renderer._parse_markdown(texto_formatado)


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
