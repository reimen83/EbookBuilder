from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from themes import ThemeEngine


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.tema_nome = "modern"

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            if self._pageNumber > 1:
                self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        cfg = ThemeEngine.obter_estilos(self.tema_nome)
        largura, altura = A4

        self.setFont(cfg["font_base"], 8)
        self.setFillColor(cfg["cor_header_footer"])

        self.setStrokeColor(cfg["cor_linha"])
        self.setLineWidth(0.5)
        self.line(54, 792, 541, 792)

        self.drawString(54, 36, "EbookBuilder Series")
        self.drawRightString(541, 36, f"Página {self._pageNumber} de {page_count}")
        self.line(54, 48, 541, 48)
        self.restoreState()

