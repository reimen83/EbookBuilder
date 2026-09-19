import os

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


class ThemeEngine:
    # Coleção de variações de capas organizadas por tema
    VARIACAO_CAPAS = {
        "music_prod": [
            {
                "id": "studio_1",
                "nome": "Estúdio & Mesa de Som",
                "url": "https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?q=80&w=1000",
            },
            {
                "id": "guitar_1",
                "nome": "Guitarra & Leds",
                "url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?q=80&w=1000",
            },
            {
                "id": "headphones_1",
                "nome": "Headphones Neon",
                "url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?q=80&w=1000",
            },
        ],
        "finance_gold": [
            {
                "id": "gold_1",
                "nome": "Gráficos & Ouro",
                "url": "https://images.unsplash.com/photo-1559526324-4b87b5e36e44?q=80&w=1000",
            },
            {
                "id": "market_2",
                "nome": "Mercado Financeiro Dark",
                "url": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=1000",
            },
            {
                "id": "coins_3",
                "nome": "Investimentos Clássico",
                "url": "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?q=80&w=1000",
            },
        ],
        "ai_productivity": [
            {
                "id": "abstract_ai",
                "nome": "Rede Neural Abstrata",
                "url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1000",
            },
            {
                "id": "cyber_desk",
                "nome": "Futurista Minimalista",
                "url": "https://images.unsplash.com/photo-1531297484001-80022131f5a1?q=80&w=1000",
            },
        ],
        "health_wellness": [
            {
                "id": "nature_1",
                "nome": "Folhas & Natureza",
                "url": "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?q=80&w=1000",
            },
            {
                "id": "yoga_2",
                "nome": "Bem-Estar & Zen",
                "url": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?q=80&w=1000",
            },
        ],
        "self_help": [
            {
                "id": "zen_1",
                "nome": "Meditação & Foco",
                "url": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?q=80&w=1000",
            },
            {
                "id": "mountain_2",
                "nome": "Horizonte & Conquista",
                "url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=1000",
            },
        ],
        "dark_tech": [
            {
                "id": "code_1",
                "nome": "Matriz de Código",
                "url": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?q=80&w=1000",
            },
            {
                "id": "hardware_2",
                "nome": "Circuito Neon",
                "url": "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=1000",
            },
        ],
        "editorial": [
            {
                "id": "book_1",
                "nome": "Livro & Papel Clássico",
                "url": "https://images.unsplash.com/photo-1457369804613-52c61a468e7d?q=80&w=1000",
            },
            {
                "id": "typewriter_2",
                "nome": "Máquina de Escrever",
                "url": "https://images.unsplash.com/photo-1488190211105-8b0e65b80b4e?q=80&w=1000",
            },
        ],
        "modern": [
            {
                "id": "arch_1",
                "nome": "Arquitetura Moderna",
                "url": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=1000",
            },
            {
                "id": "gradient_2",
                "nome": "Geométrico Suave",
                "url": "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?q=80&w=1000",
            },
        ],
    }

    @classmethod
    def obter_opcoes_capa_por_tema(cls, tema="modern"):
        """Retorna a lista de capas disponíveis para o tema selecionado."""
        return cls.VARIACAO_CAPAS.get(tema, cls.VARIACAO_CAPAS["modern"])

    @classmethod
    def obter_url_capa(cls, tema="modern", variacao_id_ou_url=None):
        """
        Retorna a URL final da capa com base no tema e no ID da variação ou URL enviada.
        """
        if not variacao_id_ou_url:
            capas = cls.obter_opcoes_capa_por_tema(tema)
            return capas[0]["url"]

        if str(variacao_id_ou_url).startswith(("http://", "https://")) or os.path.exists(str(variacao_id_ou_url)):
            return variacao_id_ou_url

        capas = cls.obter_opcoes_capa_por_tema(tema)
        for capa in capas:
            if capa["id"] == variacao_id_ou_url or capa["nome"] == variacao_id_ou_url:
                return capa["url"]

        return capas[0]["url"]

    @staticmethod
    def obter_estilos(nome_tema="modern"):
        styles = getSampleStyleSheet()

        if nome_tema == "editorial":
            font_base = "Times-Roman"
            font_bold = "Times-Bold"
            cor_fundo = colors.HexColor("#FFFFFF")
            cor_primaria = colors.HexColor("#7C2D12")
            cor_titulo = colors.HexColor("#451A03")
            cor_texto = colors.HexColor("#292524")
            cor_linha = colors.HexColor("#D6D3D1")
            cor_header_footer = colors.HexColor("#78716C")
            cor_subtitulo_capa = colors.HexColor("#FDE68A")
            cor_card_capa = colors.HexColor("#1C100B")

        elif nome_tema == "dark_tech":
            font_base = "Helvetica"
            font_bold = "Helvetica-Bold"
            cor_fundo = colors.HexColor("#090D16")
            cor_primaria = colors.HexColor("#06B6D4")
            cor_titulo = colors.HexColor("#38BDF8")
            cor_texto = colors.HexColor("#E2E8F0")
            cor_linha = colors.HexColor("#0EA5E9")
            cor_header_footer = colors.HexColor("#64748B")
            cor_subtitulo_capa = colors.HexColor("#38BDF8")
            cor_card_capa = colors.HexColor("#060B13")

        elif nome_tema == "music_prod":
            font_base = "Helvetica"
            font_bold = "Helvetica-Bold"
            cor_fundo = colors.HexColor("#12131C")
            cor_primaria = colors.HexColor("#F59E0B")
            cor_titulo = colors.HexColor("#FBBF24")
            cor_texto = colors.HexColor("#F1F5F9")
            cor_linha = colors.HexColor("#8B5CF6")
            cor_header_footer = colors.HexColor("#94A3B8")
            cor_subtitulo_capa = colors.HexColor("#FBBF24")
            cor_card_capa = colors.HexColor("#0D0E15")

        elif nome_tema == "finance_gold":
            font_base = "Helvetica"
            font_bold = "Helvetica-Bold"
            cor_fundo = colors.HexColor("#FFFFFF")
            cor_primaria = colors.HexColor("#059669")
            cor_titulo = colors.HexColor("#0F172A")
            cor_texto = colors.HexColor("#1E293B")
            cor_linha = colors.HexColor("#D97706")
            cor_header_footer = colors.HexColor("#64748B")
            cor_subtitulo_capa = colors.HexColor("#6EE7B7")
            cor_card_capa = colors.HexColor("#0B1320")

        elif nome_tema == "health_wellness":
            font_base = "Helvetica"
            font_bold = "Helvetica-Bold"
            cor_fundo = colors.HexColor("#F8FAFC")
            cor_primaria = colors.HexColor("#16A34A")
            cor_titulo = colors.HexColor("#14532D")
            cor_texto = colors.HexColor("#1F2937")
            cor_linha = colors.HexColor("#86EFAC")
            cor_header_footer = colors.HexColor("#6B7280")
            cor_subtitulo_capa = colors.HexColor("#A7F3D0")
            cor_card_capa = colors.HexColor("#0A1910")

        elif nome_tema == "self_help":
            font_base = "Times-Roman"
            font_bold = "Times-Bold"
            cor_fundo = colors.HexColor("#FFFBEB")
            cor_primaria = colors.HexColor("#C2410C")
            cor_titulo = colors.HexColor("#7C2D12")
            cor_texto = colors.HexColor("#292524")
            cor_linha = colors.HexColor("#FDBA74")
            cor_header_footer = colors.HexColor("#78716C")
            cor_subtitulo_capa = colors.HexColor("#FED7AA")
            cor_card_capa = colors.HexColor("#180C07")

        elif nome_tema == "ai_productivity":
            font_base = "Helvetica"
            font_bold = "Helvetica-Bold"
            cor_fundo = colors.HexColor("#0F172A")
            cor_primaria = colors.HexColor("#7C3AED")
            cor_titulo = colors.HexColor("#38BDF8")
            cor_texto = colors.HexColor("#F1F5F9")
            cor_linha = colors.HexColor("#06B6D4")
            cor_header_footer = colors.HexColor("#94A3B8")
            cor_subtitulo_capa = colors.HexColor("#C084FC")
            cor_card_capa = colors.HexColor("#090D1A")

        else:  # 'modern'
            font_base = "Helvetica"
            font_bold = "Helvetica-Bold"
            cor_fundo = colors.HexColor("#FFFFFF")
            cor_primaria = colors.HexColor("#2563EB")
            cor_titulo = colors.HexColor("#0F172A")
            cor_texto = colors.HexColor("#334155")
            cor_linha = colors.HexColor("#2563EB")
            cor_header_footer = colors.HexColor("#64748B")
            cor_subtitulo_capa = colors.HexColor("#BFDBFE")
            cor_card_capa = colors.HexColor("#0B1528")

        h1_style = ParagraphStyle(
            "ThemeH1",
            parent=styles["Normal"],
            fontName=font_bold,
            fontSize=18,
            leading=22,
            textColor=cor_titulo,
            spaceBefore=16,
            spaceAfter=8,
        )

        h2_style = ParagraphStyle(
            "ThemeH2",
            parent=styles["Normal"],
            fontName=font_bold,
            fontSize=13,
            leading=17,
            textColor=cor_primaria,
            spaceBefore=12,
            spaceAfter=6,
        )

        body_style = ParagraphStyle(
            "ThemeBody",
            parent=styles["Normal"],
            fontName=font_base,
            fontSize=9.5,
            leading=14,
            textColor=cor_texto,
            spaceAfter=8,
        )

        bullet_style = ParagraphStyle(
            "ThemeBullet",
            parent=body_style,
            leftIndent=15,
            bulletIndent=5,
            spaceAfter=4,
        )

        table_col_style = ParagraphStyle(
            "ThemeTableCol",
            parent=body_style,
            fontSize=9.5,
            leading=14,
            spaceAfter=0,
        )

        return {
            "font_base": font_base,
            "font_bold": font_bold,
            "cor_fundo": cor_fundo,
            "cor_primaria": cor_primaria,
            "cor_titulo": cor_titulo,
            "cor_texto": cor_texto,
            "cor_linha": cor_linha,
            "cor_header_footer": cor_header_footer,
            "cor_subtitulo_capa": cor_subtitulo_capa,
            "cor_card_capa": cor_card_capa,
            "h1": h1_style,
            "h2": h2_style,
            "body": body_style,
            "bullet": bullet_style,
            "table_col": table_col_style,
        }
