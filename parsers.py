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
    @staticmethod
    def inferir_estrutura(texto_bruto):
        linhas = texto_bruto.split("\n")
        linhas_processadas = []

        regex_capitulo = re.compile(
            r"^(capítulo|módulo|parte|lição|introdução|conclusão|prefácio)\b",
            re.IGNORECASE,
        )
        regex_numeracao = re.compile(r"^(\d{1,2}\.|\d{1,2}\s*-\s*)")

        for linha in linhas:
            l_str = linha.strip()
            if not l_str:
                linhas_processadas.append("")
                continue

            if "|" in l_str:
                linhas_processadas.append(l_str)
                continue

            if l_str.startswith(("# ", "## ", "### ", "- ", "* ")):
                linhas_processadas.append(l_str)
                continue

            e_curto = len(l_str) <= 60
            e_caixa_alta = l_str.isupper() and len(l_str) > 3
            tem_palavra_chave = bool(regex_capitulo.match(l_str))
            sem_ponto_final = not l_str.endswith((".", ",", ";"))

            if e_curto and (tem_palavra_chave or (e_caixa_alta and sem_ponto_final)):
                linhas_processadas.append(f"# {l_str}")
                continue

            tem_num_secao = bool(regex_numeracao.match(l_str)) and len(l_str) <= 80
            termina_com_dois_pontos = l_str.endswith(":") and e_curto

            if tem_num_secao or termina_com_dois_pontos:
                linhas_processadas.append(f"## {l_str.rstrip(':')}")
                continue

            if l_str.startswith(("—", "–", "•", "1)", "2)", "3)", "a)", "b)")):
                texto_limpo = re.sub(r"^[—–•\d\w\)\-]\s*", "", l_str)
                linhas_processadas.append(f"- {texto_limpo}")
                continue

            linhas_processadas.append(l_str)

        return "\n".join(linhas_processadas)

    @staticmethod
    def extrair_titulos_documento(caminho_arquivo):
        if not caminho_arquivo or not os.path.exists(caminho_arquivo):
            return "", ""

        ext = os.path.splitext(caminho_arquivo)[1].lower()
        titulo_auto, subtitulo_auto = "", ""

        try:
            if ext in [".md", ".markdown", ".txt"]:
                with open(caminho_arquivo, "r", encoding="utf-8", errors="ignore") as f:
                    linhas = [l.strip() for l in f.readlines() if l.strip()]

                for l in linhas:
                    if not titulo_auto and (l.startswith("# ") or l.isupper()):
                        titulo_auto = re.sub(r"^#\s*", "", l)
                    elif titulo_auto and not subtitulo_auto and (l.startswith("## ") or l.startswith("### ")):
                        subtitulo_auto = re.sub(r"^#{2,3}\s*", "", l)
                        break

            elif ext == ".docx" and docx:
                doc_word = docx.Document(caminho_arquivo)
                for p in doc_word.paragraphs:
                    txt = p.text.strip()
                    if not txt:
                        continue
                    if not titulo_auto:
                        titulo_auto = txt
                    elif not subtitulo_auto:
                        subtitulo_auto = txt
                        break

            elif ext == ".pdf" and pdfplumber:
                with pdfplumber.open(caminho_arquivo) as pdf:
                    if len(pdf.pages) > 0:
                        txt_pag1 = pdf.pages[0].extract_text() or ""
                        linhas = [l.strip() for l in txt_pag1.split("\n") if l.strip()]
                        if len(linhas) > 0:
                            titulo_auto = linhas[0]
                        if len(linhas) > 1:
                            subtitulo_auto = linhas[1]

        except Exception as e:
            print(f"[Aviso Parser Titulos]: {e}")

        return titulo_auto, subtitulo_auto

