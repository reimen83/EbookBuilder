import io
import os
from xml.sax.saxutils import escape

import requests
from PIL import Image, ImageEnhance, ImageFilter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Paragraph

from cover_cache import CoverCache
from themes import ThemeEngine


def upscale_cover_image(image_bytes, target_width=1600, target_height=2560):
    """
    Aplica upscale determinístico (sem IA) em capas baixadas via URL.
    Utiliza interpolação Lanczos e filtro Unsharp Mask para recuperar a nitidez.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        width, height = img.size

        if width < target_width or height < target_height:
            ratio = min(target_width / width, target_height / height)
            new_size = (int(width * ratio), int(height * ratio))

            img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
            img_sharp = img_resized.filter(
                ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=3)
            )

            enhancer = ImageEnhance.Sharpness(img_sharp)
            img_final = enhancer.enhance(1.2)

            output = io.BytesIO()
            img_final.save(output, format="JPEG", quality=95)
            return output.getvalue()

        return image_bytes
    except Exception as e:
        print(f"[Aviso Upscale]: Falha ao processar imagem ({e}). Usando original.")
        return image_bytes


class CapaHandler:
    def __init__(
        self,
        origem_capa=None,
        titulo="",
        sub_titulo="",
        tema="modern",
        variacao_capa=None,
        cover_cache=None,
    ):
        self.titulo = titulo.strip()
        self.sub_titulo = sub_titulo.strip()
        self.tema = tema
        self.tema_config = ThemeEngine.obter_estilos(tema)
        self.cover_cache = cover_cache or CoverCache()

        # Trata se foi passado a URL direta ou o ID da variação do tema
        alvo_capa = origem_capa if origem_capa else variacao_capa
        self.origem_capa = ThemeEngine.obter_url_capa(
            tema=self.tema, variacao_id_ou_url=alvo_capa
        )

    @staticmethod
    def _quebrar_texto(texto, fonte, tamanho, largura):
        linhas = []
        for paragrafo in texto.splitlines() or [""]:
            atual = ""
            for palavra in paragrafo.split() or [""]:
                candidato = f"{atual} {palavra}".strip()
                if atual and stringWidth(candidato, fonte, tamanho) > largura:
                    linhas.append(atual)
                    atual = ""
                while palavra and stringWidth(
                    f"{atual}{palavra}", fonte, tamanho
                ) > largura:
                    corte = len(palavra)
                    while corte > 1 and stringWidth(
                        f"{atual}{palavra[:corte]}", fonte, tamanho
                    ) > largura:
                        corte -= 1
                    linhas.append(f"{atual}{palavra[:corte]}")
                    atual = ""
                    palavra = palavra[corte:]
                atual = f"{atual}{palavra}".strip()
            if atual:
                linhas.append(atual)
        return linhas or [""]

    def desenhar_capa(self, canvas_obj, doc):
        canvas_obj.saveState()
        largura, altura = A4
        sucesso_imagem = False

        if self.origem_capa:
            origem_str = str(self.origem_capa).strip()
            if origem_str.startswith(("http://", "https://")):
                try:
                    image_upscaled_bytes = self.cover_cache.get(origem_str)
                    if image_upscaled_bytes is None:
                        res = requests.get(origem_str, timeout=5)
                        if res.status_code == 200:
                            image_upscaled_bytes = upscale_cover_image(res.content)
                            self.cover_cache.save(origem_str, image_upscaled_bytes)

                    if image_upscaled_bytes:
                        from reportlab.lib.utils import ImageReader
                        img_data = io.BytesIO(image_upscaled_bytes)
                        img = ImageReader(img_data)
                        canvas_obj.drawImage(
                            img, 0, 0, width=largura, height=altura, preserveAspectRatio=False
                        )
                        sucesso_imagem = True
                except Exception as e:
                    print(f"[Aviso] Falha ao baixar imagem: {e}")

            elif os.path.isfile(origem_str):
                try:
                    canvas_obj.drawImage(
                        os.fspath(origem_str),
                        0,
                        0,
                        width=largura,
                        height=altura,
                        preserveAspectRatio=False,
                    )
                    sucesso_imagem = True
                except Exception as e:
                    print(f"[Aviso] Falha ao carregar imagem local: {e}")

        if not sucesso_imagem:
            cor_fundo_capa = (
                self.tema_config["cor_fundo"]
                if self.tema in ["dark_tech", "music_prod", "ai_productivity"]
                else colors.HexColor("#0F172A")
            )
            canvas_obj.setFillColor(cor_fundo_capa)
            canvas_obj.rect(0, 0, largura, altura, fill=True, stroke=False)

        if self.titulo or self.sub_titulo:
            centro_x = largura / 2.0
            pos_y_bloco = altura * 0.42

            largura_card = largura * 0.84
            altura_card = 210
            x_card = (largura - largura_card) / 2.0
            y_card = pos_y_bloco - (altura_card / 2.0)

            canvas_obj.setFillColor(self.tema_config["cor_card_capa"])
            canvas_obj.setFillAlpha(0.88)
            canvas_obj.roundRect(x_card, y_card, largura_card, altura_card, 12, fill=True, stroke=False)
            canvas_obj.setFillAlpha(1.0)

            canvas_obj.setFillColor(self.tema_config["cor_primaria"])
            canvas_obj.rect(x_card + 30, y_card + altura_card - 8, largura_card - 60, 4, fill=True, stroke=False)

            if self.titulo:
                tamanho_titulo = 23
                linhas_titulo = self._quebrar_texto(
                    self.titulo.upper(),
                    self.tema_config["font_bold"],
                    tamanho_titulo,
                    largura_card - 60,
                )
                limite_linhas = 3
                if len(linhas_titulo) > limite_linhas:
                    tamanho_titulo = 19
                    linhas_titulo = self._quebrar_texto(
                        self.titulo.upper(),
                        self.tema_config["font_bold"],
                        tamanho_titulo,
                        largura_card - 60,
                    )
                linhas_titulo = linhas_titulo[:limite_linhas]
                if len(linhas_titulo) == limite_linhas and len(
                    self._quebrar_texto(
                        self.titulo.upper(),
                        self.tema_config["font_bold"],
                        tamanho_titulo,
                        largura_card - 60,
                    )
                ) > limite_linhas:
                    linhas_titulo[-1] = f"{linhas_titulo[-1].rstrip(' .')}..."

                titulo = Paragraph(
                    "<br/>".join(escape(linha) for linha in linhas_titulo),
                    ParagraphStyle(
                        "CoverTitle",
                        fontName=self.tema_config["font_bold"],
                        fontSize=tamanho_titulo,
                        leading=tamanho_titulo + 4,
                        textColor=colors.HexColor("#FFFFFF"),
                        alignment=TA_CENTER,
                    ),
                )
                _, altura_titulo = titulo.wrap(largura_card - 60, 90)
                titulo.drawOn(
                    canvas_obj,
                    x_card + 30,
                    y_card + altura_card - 72 - altura_titulo,
                )

            canvas_obj.setFillColor(self.tema_config["cor_linha"])
            canvas_obj.rect(centro_x - 45, y_card + altura_card - 85, 90, 2, fill=True, stroke=False)

            if self.sub_titulo:
                canvas_obj.setFillColor(self.tema_config["cor_subtitulo_capa"])
                largura_subtitulo = largura_card - 60
                linhas = self._quebrar_texto(
                    self.sub_titulo,
                    self.tema_config["font_base"],
                    13,
                    largura_subtitulo,
                )
                limite_linhas = 6
                if len(linhas) > limite_linhas:
                    linhas = linhas[:limite_linhas]
                    linhas[-1] = f"{linhas[-1].rstrip(' .')}..."

                subtitulo = Paragraph(
                    "<br/>".join(escape(linha) for linha in linhas),
                    ParagraphStyle(
                        "CoverSubtitle",
                        fontName=self.tema_config["font_base"],
                        fontSize=13,
                        leading=16,
                        textColor=self.tema_config["cor_subtitulo_capa"],
                        alignment=TA_CENTER,
                    ),
                )
                _, altura_subtitulo = subtitulo.wrap(largura_subtitulo, 100)
                subtitulo.drawOn(
                    canvas_obj,
                    x_card + 30,
                    y_card + 25 + max(0, (80 - altura_subtitulo) / 2),
                )

        canvas_obj.restoreState()

    def desenhar_fundo_paginas(self, canvas_obj, doc):
        canvas_obj.saveState()
        largura, altura = A4
        canvas_obj.setFillColor(self.tema_config["cor_fundo"])
        canvas_obj.rect(0, 0, largura, altura, fill=True, stroke=False)
        canvas_obj.restoreState()
