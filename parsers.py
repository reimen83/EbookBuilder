import os
import re

try:
    import docx
except ImportError:
    docx = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


class SmartParser:
    REGEX_CAPITULO = re.compile(
        r"^(capítulo|módulo|parte|lição|introdução|conclusão|prefácio)\b",
        re.IGNORECASE,
    )
    REGEX_NUMERACAO = re.compile(r"^(\d{1,2}\.|\d{1,2}\s*-\s*)")

    @staticmethod
    def _classificar_linha(linha):
        l_str = linha.strip()
        if not l_str:
            return ""

        if "|" in l_str or l_str.startswith(("# ", "## ", "### ", "- ", "* ")):
            return l_str

        e_curto = len(l_str) <= 60
        e_caixa_alta = l_str.isupper() and len(l_str) > 3
        tem_palavra_chave = bool(SmartParser.REGEX_CAPITULO.match(l_str))
        sem_ponto_final = not l_str.endswith((".", ",", ";"))

        if e_curto and (tem_palavra_chave or (e_caixa_alta and sem_ponto_final)):
            return f"# {l_str}"

        tem_num_secao = bool(SmartParser.REGEX_NUMERACAO.match(l_str)) and len(l_str) <= 80
        termina_com_dois_pontos = l_str.endswith(":") and e_curto

        if tem_num_secao or termina_com_dois_pontos:
            return f"## {l_str.rstrip(':')}"

        if l_str.startswith(("—", "–", "•", "1)", "2)", "3)", "a)", "b)")):
            texto_limpo = re.sub(r"^[—–•\d\w\)\-]\s*", "", l_str)
            return f"- {texto_limpo}"

        return l_str

    @staticmethod
    def inferir_estrutura(texto_bruto):
        linhas_processadas = [
            SmartParser._classificar_linha(linha)
            for linha in texto_bruto.split("\n")
        ]
        return "\n".join(linhas_processadas)

    @staticmethod
    def _iterar_linhas_do_documento(caminho_arquivo):
        ext = os.path.splitext(caminho_arquivo)[1].lower()

        if ext in [".md", ".markdown", ".txt"]:
            with open(caminho_arquivo, "r", encoding="utf-8", errors="ignore") as f:
                return [linha.strip() for linha in f.readlines() if linha.strip()]

        if ext == ".docx" and docx:
            documento = docx.Document(caminho_arquivo)
            return [paragrafo.text.strip() for paragrafo in documento.paragraphs if paragrafo.text.strip()]

        if ext == ".pdf" and pdfplumber:
            with pdfplumber.open(caminho_arquivo) as pdf:
                if not pdf.pages:
                    return []
                texto_pag1 = pdf.pages[0].extract_text() or ""
                return [linha.strip() for linha in texto_pag1.split("\n") if linha.strip()]

        return []

    @staticmethod
    def _extrair_primeiros_titulos_da_lista(linhas):
        titulo_auto, subtitulo_auto = "", ""

        for linha in linhas:
            if not titulo_auto and (linha.startswith("# ") or linha.isupper()):
                titulo_auto = re.sub(r"^#\s*", "", linha)
            elif titulo_auto and not subtitulo_auto and (
                linha.startswith("## ") or linha.startswith("### ")
            ):
                subtitulo_auto = re.sub(r"^#{2,3}\s*", "", linha)
                break

        return titulo_auto, subtitulo_auto

    @staticmethod
    def extrair_titulos_documento(caminho_arquivo):
        if not caminho_arquivo or not os.path.exists(caminho_arquivo):
            return "", ""

        try:
            linhas = SmartParser._iterar_linhas_do_documento(caminho_arquivo)
            return SmartParser._extrair_primeiros_titulos_da_lista(linhas)
        except Exception as exc:
            print(f"[Aviso Parser Titulos]: {exc}")
            return "", ""

