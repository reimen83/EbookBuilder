import re

from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle


class MarkdownRenderer:
    """Converte Markdown estruturado em flowables do ReportLab."""

    def __init__(self, theme_cfg):
        self.theme_cfg = theme_cfg

    def _converter_inline_formatting(self, texto):
        texto = re.sub(r"\*\*(.*?)\*\*", r"___BOLD___\1___ENDBOLD___", texto)
        texto = re.sub(r"\*(.*?)\*", r"___ITALIC___\1___ENDITALIC___", texto)

        texto = texto.replace("&", "&amp;")
        texto = texto.replace("<", "&lt;")
        texto = texto.replace(">", "&gt;")

        texto = texto.replace("___BOLD___", "<b>").replace("___ENDBOLD___", "</b>")
        texto = texto.replace("___ITALIC___", "<i>").replace("___ENDITALIC___", "</i>")

        return texto

    def _gerar_tabela_flowable(self, linhas_tabela):
        if not linhas_tabela:
            return None

        LARGURA_UTIL = 487.0
        w_col1 = LARGURA_UTIL / 2.0
        w_col2 = LARGURA_UTIL / 2.0

        dados_tabela = []

        for raw_col1, raw_col2 in linhas_tabela:
            p_col1 = Paragraph(self._converter_inline_formatting(raw_col1), self.theme_cfg["table_col"])
            p_col2 = Paragraph(self._converter_inline_formatting(raw_col2), self.theme_cfg["table_col"])
            dados_tabela.append([p_col1, p_col2])

        tabela = Table(dados_tabela, colWidths=[w_col1, w_col2])
        tabela.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("LINEAFTER", (0, 0), (0, -1), 0.75, self.theme_cfg["cor_linha"]),
            ])
        )
        return tabela

    def _parse_markdown(self, texto_md):
        story = []
        linhas = texto_md.split("\n")
        bloco_tabela = []

        for linha in linhas:
            linha_str = linha.strip()

            if "|" in linha_str:
                partes = [p.strip() for p in linha_str.split("|")]
                if len(partes) >= 2:
                    bloco_tabela.append((partes[0], partes[1]))
                    continue

            if bloco_tabela:
                tabela = self._gerar_tabela_flowable(bloco_tabela)
                if tabela:
                    story.append(tabela)
                    story.append(Spacer(1, 8))
                bloco_tabela = []

            if not linha_str:
                continue

            if linha_str.startswith("# "):
                texto = linha_str[2:].strip()
                texto_formatado = self._converter_inline_formatting(texto)
                story.append(Paragraph(texto_formatado, self.theme_cfg["h1"]))
                story.append(
                    HRFlowable(
                        width="100%",
                        thickness=1,
                        color=self.theme_cfg["cor_linha"],
                        spaceAfter=12,
                    )
                )
            elif linha_str.startswith("## "):
                texto = linha_str[3:].strip()
                texto_formatado = self._converter_inline_formatting(texto)
                story.append(Paragraph(texto_formatado, self.theme_cfg["h2"]))
            elif linha_str.startswith("### "):
                texto = linha_str[4:].strip()
                texto_formatado = self._converter_inline_formatting(texto)
                h3_style = ParagraphStyle(
                    "CustomH3",
                    parent=self.theme_cfg["h2"],
                    fontSize=11,
                    textColor=self.theme_cfg["cor_primaria"],
                )
                story.append(Paragraph(texto_formatado, h3_style))
            elif linha_str.startswith(("- ", "* ")):
                texto = linha_str[2:].strip()
                texto_formatado = self._converter_inline_formatting(texto)
                story.append(
                    Paragraph(f"• {texto_formatado}", self.theme_cfg["bullet"])
                )
            else:
                texto_formatado = self._converter_inline_formatting(linha_str)
                story.append(Paragraph(texto_formatado, self.theme_cfg["body"]))

        if bloco_tabela:
            tabela = self._gerar_tabela_flowable(bloco_tabela)
            if tabela:
                story.append(tabela)

        return story
