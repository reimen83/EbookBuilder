from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Flowable, Paragraph, Table, TableStyle


class CalloutBox(Flowable):
    """Caixa visual para dicas, avisos, citações e notas editoriais."""

    def __init__(
        self,
        text,
        title=None,
        background=colors.HexColor("#EFF6FF"),
        border=colors.HexColor("#2563EB"),
        text_color=colors.HexColor("#1E293B"),
        width=6.2 * inch,
        padding=10,
    ):
        super().__init__()
        self.text = text
        self.title = title
        self.background = background
        self.border = border
        self.text_color = text_color
        self.box_width = width
        self.padding = padding
        self._paragraph = None

    def wrap(self, available_width, available_height):
        style = ParagraphStyle(
            "Callout",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=self.text_color,
        )
        content = f"<b>{self.title}</b><br/>{self.text}" if self.title else self.text
        self._paragraph = Paragraph(content, style)
        width = min(self.box_width, available_width)
        paragraph_width, paragraph_height = self._paragraph.wrap(
            width - 2 * self.padding,
            available_height,
        )
        self.width = width
        self.height = paragraph_height + 2 * self.padding
        return self.width, self.height

    def draw(self):
        self.canv.saveState()
        self.canv.setFillColor(self.background)
        self.canv.setStrokeColor(self.border)
        self.canv.setLineWidth(1)
        self.canv.roundRect(0, 0, self.width, self.height, 8, fill=1, stroke=1)
        self._paragraph.drawOn(self.canv, self.padding, self.padding)
        self.canv.restoreState()


class CTAButton(Flowable):
    """Botão de call-to-action com hyperlink opcional."""

    def __init__(
        self,
        label,
        url=None,
        background=colors.HexColor("#2563EB"),
        text_color=colors.white,
        width=150,
        height=34,
    ):
        super().__init__()
        self.label = label
        self.url = url
        self.background = background
        self.text_color = text_color
        self.width = width
        self.height = height

    def wrap(self, available_width, available_height):
        return min(self.width, available_width), self.height

    def draw(self):
        self.canv.saveState()
        self.canv.setFillColor(self.background)
        self.canv.roundRect(0, 0, self.width, self.height, 7, fill=1, stroke=0)
        self.canv.setFillColor(self.text_color)
        self.canv.setFont("Helvetica-Bold", 10)
        self.canv.drawCentredString(self.width / 2, self.height / 2 - 3, self.label)
        if self.url:
            self.canv.linkURL(self.url, (0, 0, self.width, self.height), relative=0)
        self.canv.restoreState()


class DeviceMockup(Flowable):
    """Coloca uma imagem em um frame vetorial simples de telefone ou tablet."""

    def __init__(self, image, device="tablet", width=260, height=390):
        super().__init__()
        self.image = image
        self.device = device
        self.width = width
        self.height = height

    def wrap(self, available_width, available_height):
        scale = min(available_width / self.width, available_height / self.height, 1)
        self.width *= scale
        self.height *= scale
        return self.width, self.height

    def draw(self):
        self.canv.saveState()
        radius = 18 if self.device == "phone" else 10
        self.canv.setFillColor(colors.HexColor("#111827"))
        self.canv.roundRect(0, 0, self.width, self.height, radius, fill=1, stroke=0)
        margin = 8
        self.canv.drawImage(
            self.image,
            margin,
            margin,
            self.width - 2 * margin,
            self.height - 2 * margin,
            preserveAspectRatio=True,
            anchor="c",
            mask="auto",
        )
        self.canv.restoreState()
