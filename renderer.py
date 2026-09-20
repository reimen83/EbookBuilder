import re

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle


class _SegmentedColumnsTable(Table):
    def __init__(self, *args, divider_segments=None, divider_color=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.divider_segments = divider_segments or []
        self.divider_color = divider_color

    def split(self, availWidth, availHeight):
        fragments = super().split(availWidth, availHeight)
        if len(fragments) <= 1 or not self.divider_segments:
            return fragments

        offset = 0
        for fragment in fragments:
            row_count = len(fragment._rowHeights)
            fragment.divider_color = self.divider_color
            fragment.divider_segments = [
                (max(start - offset, 0), min(end - offset, row_count - 1))
                for start, end in self.divider_segments
                if end >= offset and start < offset + row_count
            ]
            offset += row_count
        return fragments

    def draw(self):
        super().draw()
        if not self.divider_segments:
            return

        canvas = self.canv
        canvas.saveState()
        canvas.setStrokeColor(self.divider_color or colors.black)
        canvas.setLineWidth(0.35)
        gap = 3
        x = self._colWidths[0]
        for inicio, fim in self.divider_segments:
            y_top = self._height - sum(self._rowHeights[:inicio])
            y_bottom = self._height - sum(self._rowHeights[: fim + 1])
            if y_top - y_bottom > gap * 2:
                canvas.line(x, y_bottom + gap, x, y_top - gap)
        canvas.restoreState()


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

    def _gerar_colunas_pdf_flowable(
        self,
        linhas,
        separadores=None,
        divisorias=None,
    ):
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

        cor_divisoria = self.theme_cfg["cor_linha"]
        cor_divisoria = colors.Color(
            cor_divisoria.red,
            cor_divisoria.green,
            cor_divisoria.blue,
            alpha=0.65,
        )
        espaco_divisoria = 8
        espessura_divisoria = 0.35
        estilos = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (0, -1), espaco_divisoria),
            ("LEFTPADDING", (1, 0), (1, -1), espaco_divisoria),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]

        tops = [linha[2] for linha in linhas]
        linhas_com_separador = set()
        divider_segments = []
        if separadores:
            for x0, x1, separador, meio in separadores:
                indice = min(
                    range(len(tops)),
                    key=lambda item: abs(tops[item] - separador),
                )
                linhas_com_separador.add(indice)
                centro_segmento = (x0 + x1) / 2
                atravessa_vao = x0 < meio - 4 and x1 > meio + 4
                if atravessa_vao:
                    inicio, fim = 0, 1
                elif centro_segmento < meio:
                    inicio, fim = 0, 0
                else:
                    inicio, fim = 1, 1
                estilos.append(
                    (
                        "LINEABOVE",
                        (inicio, indice),
                        (fim, indice),
                        espessura_divisoria,
                        cor_divisoria,
                    )
                )

        if divisorias:
            for x0, inicio, fim in divisorias:
                inicio_linha = min(
                    range(len(tops)),
                    key=lambda item: abs(tops[item] - inicio),
                )
                fim_linha = min(
                    range(len(tops)),
                    key=lambda item: abs(tops[item] - fim),
                )
                primeiro = min(inicio_linha, fim_linha)
                ultimo = max(inicio_linha, fim_linha) - 1
                trechos = []
                trecho_inicio = None
                for indice in range(primeiro, ultimo + 1):
                    if indice in linhas_com_separador:
                        if trecho_inicio is not None:
                            trechos.append((trecho_inicio, indice - 1))
                            trecho_inicio = None
                    elif trecho_inicio is None:
                        trecho_inicio = indice
                if trecho_inicio is not None:
                    trechos.append((trecho_inicio, ultimo))

                for trecho_inicio, trecho_fim in trechos:
                    divider_segments.append((trecho_inicio, trecho_fim))

        tabela = _SegmentedColumnsTable(
            dados,
            colWidths=[243.5, 243.5],
            repeatRows=0,
            divider_segments=divider_segments,
            divider_color=cor_divisoria,
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
