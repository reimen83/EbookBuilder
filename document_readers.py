try:
    import docx
except ImportError:
    docx = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


class DocumentReader:
    """Lê documentos DOCX e PDF e os converte em flowables."""

    def __init__(self, renderer, smart_parser):
        self.renderer = renderer
        self.smart_parser = smart_parser

    def parse_docx(self, caminho_docx):
        if docx is None:
            raise ImportError("A biblioteca 'python-docx' não está instalada.")
        doc_word = docx.Document(caminho_docx)
        texto_unificado = "\n".join([p.text for p in doc_word.paragraphs])
        texto_estruturado = self.smart_parser.inferir_estrutura(texto_unificado)
        return self.renderer._parse_markdown(texto_estruturado)

    def parse_pdf(self, caminho_pdf):
        if pdfplumber is None:
            raise ImportError("A biblioteca 'pdfplumber' não está instalada.")
        texto_completo = []
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                tabelas = pagina.extract_tables()
                if tabelas:
                    for tab in tabelas:
                        for linha in tab:
                            if linha and len(linha) >= 2 and (linha[0] or linha[1]):
                                col_a = (linha[0] or "").replace("\n", " ").strip()
                                col_b = (linha[1] or "").replace("\n", " ").strip()
                                if col_a or col_b:
                                    texto_completo.append(f"{col_a} | {col_b}")
                else:
                    texto_pag = pagina.extract_text()
                    if texto_pag:
                        texto_completo.append(texto_pag)

        texto_unificado = "\n\n".join(texto_completo)
        texto_formatado = self.smart_parser.inferir_estrutura(texto_unificado)
        return self.renderer._parse_markdown(texto_formatado)
