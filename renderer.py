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

        largura_util = 487.0
        w_col1 = largura_util / 2.0
        w_col2 = largura_util / 2.0

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

    def _gerar_colunas_pdf_flowable(self, linhas, separadores=None):
        if not linhas:
            return None

        dados = []
        for coluna_esquerda, coluna_direita, _ in linhas:
            esquerda = self._converter_inline_formatting(coluna_esquerda)
            direita = self._converter_inline_formatting(coluna_direita)
            dados.append(
                [
                    Paragraph(esquerda, self.theme_cfg["body"]) if esquerda else "",
                    Paragraph(direita, self.theme_cfg["body"]) if direita else "",
                ]
            )

        tabela = Table(dados, colWidths=[243.5, 243.5], repeatRows=0)
        estilos = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            (
                "LINEAFTER",
                (0, 0),
                (0, -1),
                0.75,
                self.theme_cfg["cor_linha"],
            ),
        ]

        if separadores:
            tops = [linha[2] for linha in linhas]
            for separador in sorted(set(separadores)):
                indice = min(
                    range(len(tops)),
                    key=lambda item: abs(tops[item] - separador),
                )
                estilos.append(
                    (
                        "LINEABOVE",
                        (0, indice),
                        (-1, indice),
                        0.5,
                        self.theme_cfg["cor_linha"],
                    )
                )

        tabela.setStyle(TableStyle(estilos))
        return tabela

    def _renderizar_tabela_buffer(self, story, blocos_tabela):
        if not blocos_tabela:
            return

        tabela = self._gerar_tabela_flowable(blocos_tabela)
        if tabela:
            story.append(tabela)
            story.append(Spacer(1, 8))

    def _renderizar_paragrafo(self, story, texto, style):
        story.append(Paragraph(self._converter_inline_formatting(texto), style))

    def _renderizar_titulo_h3(self, story, texto):
        h3_style = ParagraphStyle(
            "CustomH3",
            parent=self.theme_cfg["h2"],
            fontSize=11,
            textColor=self.theme_cfg["cor_primaria"],
        )
        self._renderizar_paragrafo(story, texto, h3_style)

    def _renderizar_linha(self, story, linha_str):
        if linha_str.startswith("# "):
            texto = linha_str[2:].strip()
            self._renderizar_paragrafo(story, texto, self.theme_cfg["h1"])
            story.append(
                HRFlowable(
                    width="100%",
                    thickness=1,
                    color=self.theme_cfg["cor_linha"],
                    spaceAfter=12,
                )
            )
            return

        if linha_str.startswith("## "):
            self._renderizar_paragrafo(story, linha_str[3:].strip(), self.theme_cfg["h2"])
            return

        if linha_str.startswith("### "):
            self._renderizar_titulo_h3(story, linha_str[4:].strip())
            return

        if linha_str.startswith(("- ", "* ")):
            self._renderizar_paragrafo(story, f"• {linha_str[2:].strip()}", self.theme_cfg["bullet"])
            return

        self._renderizar_paragrafo(story, linha_str, self.theme_cfg["body"])

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
                self._renderizar_tabela_buffer(story, bloco_tabela)
                bloco_tabela = []

            if not linha_str:
                continue

            self._renderizar_linha(story, linha_str)

        if bloco_tabela:
            self._renderizar_tabela_buffer(story, bloco_tabela)

        return story
