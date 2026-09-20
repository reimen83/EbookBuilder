import os

from reportlab.lib.utils import ImageReader
from reportlab.platypus import Flowable, PageBreak
from PIL import Image
from PIL import ImageChops
from PIL import ImageDraw

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
    def __init__(
        self,
        image,
        page_width,
        page_height,
        background_color=None,
        text_color=None,
        protected_regions=None,
    ):
        super().__init__()
        self.image = ImageReader(
            self.recolorir_fundo(
                image,
                background_color,
                text_color=text_color,
                protected_regions=protected_regions,
            )
            if background_color is not None
            else image
        )
        self.page_width = page_width
        self.page_height = page_height

    @staticmethod
    def recolorir_fundo(
        image,
        background_color,
        text_color=None,
        tolerancia=18,
        limiar_texto_claro=185,
        protected_regions=None,
    ):
        """Troca apenas o fundo uniforme identificado pelas bordas da página."""
        if background_color is None:
            return image

        imagem = image.convert("RGBA")
        largura, altura = imagem.size
        pontos_borda = [
            imagem.getpixel((0, 0)),
            imagem.getpixel((largura - 1, 0)),
            imagem.getpixel((0, altura - 1)),
            imagem.getpixel((largura - 1, altura - 1)),
        ]
        fundo_origem = max(set(pontos_borda), key=pontos_borda.count)
        alvo = tuple(int(c * 255) if 0 <= c <= 1 else int(c) for c in background_color)
        alvo_texto = (
            tuple(int(c * 255) if 0 <= c <= 1 else int(c) for c in text_color)
            if text_color is not None
            else None
        )
        rgb = imagem.convert("RGB")
        protecao = Image.new("L", rgb.size, 255)
        if protected_regions:
            desenho = ImageDraw.Draw(protecao)
            for x0, top, x1, bottom in protected_regions:
                desenho.rectangle(
                    (
                        max(0, int(x0)),
                        max(0, int(top)),
                        min(largura - 1, int(x1)),
                        min(altura - 1, int(bottom)),
                    ),
                    fill=0,
                )
        origem = Image.new("RGB", rgb.size, fundo_origem[:3])
        diferenca = ImageChops.difference(rgb, origem)
        mascara = Image.new("L", rgb.size, 255)
        limiar = 255 if tolerancia >= 255 else tolerancia
        for canal in diferenca.split():
            canal_mascara = canal.point(
                lambda valor: 255 if valor <= limiar else 0,
            )
            mascara = ImageChops.multiply(mascara, canal_mascara)
        fundo_novo = Image.new("RGB", rgb.size, alvo)
        resultado = Image.composite(fundo_novo, rgb, mascara).convert("RGBA")

        fundo_luminancia = (
            0.2126 * alvo[0] + 0.7152 * alvo[1] + 0.0722 * alvo[2]
        )
        if alvo_texto is not None and fundo_luminancia >= 150:
            pixels_origem = rgb.load()
            pixels_resultado = resultado.load()
            for y in range(altura):
                for x in range(largura):
                    if (
                        mascara.getpixel((x, y)) == 255
                        or protecao.getpixel((x, y)) == 0
                    ):
                        continue
                    pixel = pixels_origem[x, y]
                    luminancia = (
                        0.2126 * pixel[0]
                        + 0.7152 * pixel[1]
                        + 0.0722 * pixel[2]
                    )
                    distancia_fundo = sum(
                        abs(pixel[indice] - fundo_origem[indice])
                        for indice in range(3)
                    )
                    if luminancia >= limiar_texto_claro and distancia_fundo >= tolerancia * 2:
                        pixels_resultado[x, y] = (*alvo_texto, pixels_resultado[x, y][3])

        resultado.putalpha(imagem.getchannel("A"))
        return resultado

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

    def _regioes_protegidas(self, pagina, tamanho_imagem, margem=4):
        """Mapeia retângulos de design do PDF para coordenadas da imagem."""
        largura, altura = tamanho_imagem
        escala_x = largura / pagina.width
        escala_y = altura / pagina.height
        regioes = []
        for retangulo in getattr(pagina, "rects", []):
            largura_retangulo = retangulo["x1"] - retangulo["x0"]
            altura_retangulo = retangulo["bottom"] - retangulo["top"]
            if largura_retangulo < 24 or altura_retangulo < 12:
                continue
            if largura_retangulo >= pagina.width * 0.95:
                continue
            regioes.append(
                (
                    retangulo["x0"] * escala_x - margem,
                    retangulo["top"] * escala_y - margem,
                    retangulo["x1"] * escala_x + margem,
                    retangulo["bottom"] * escala_y + margem,
                )
            )
        return regioes

    def _preservar_pagina_como_imagem(
        self,
        pagina,
        background_color=None,
        text_color=None,
        protected_regions=None,
    ):
        imagem = pagina.to_image(resolution=150).original
        protected_regions = self._regioes_protegidas(pagina, imagem.size)
        return [
            PdfPageImage(
                imagem,
                pagina.width,
                pagina.height,
                background_color=background_color,
                text_color=text_color,
                protected_regions=protected_regions,
            ),
            PageBreak(),
        ]

    def parse(self, caminho_pdf):
        if pdfplumber is None:
            raise ImportError("A biblioteca 'pdfplumber' não está instalada.")

        conteudo = []
        background_color = None
        text_color = None
        if self.renderer is not None:
            cor_fundo = self.renderer.theme_cfg.get("cor_fundo")
            cor_texto = self.renderer.theme_cfg.get("cor_texto")
            if cor_fundo is not None:
                background_color = (cor_fundo.red, cor_fundo.green, cor_fundo.blue)
            if cor_texto is not None:
                text_color = (cor_texto.red, cor_texto.green, cor_texto.blue)
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
                conteudo.extend(
                    self._preservar_pagina_como_imagem(
                        pagina,
                        background_color=background_color,
                        text_color=text_color,
                    )
                )

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
