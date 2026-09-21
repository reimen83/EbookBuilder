import hashlib
import os
from pathlib import Path


class PdfPageCache:
    """Cache persistente das páginas rasterizadas de PDFs."""

    VERSION = "1"

    def __init__(self, cache_dir=None):
        self.cache_dir = Path(cache_dir) if cache_dir else (
            Path.home() / ".cache" / "ebookbuilder" / "pdf-pages"
        )

    @staticmethod
    def _color_key(color):
        return ",".join(str(value) for value in (color or ()))

    def source_key(self, source_path):
        digest = hashlib.sha256()
        with open(source_path, "rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def page_path(
        self,
        source_key,
        page_number,
        render_dpi,
        background_color,
        text_color,
        preserve_original,
    ):
        params = "|".join(
            (
                self.VERSION,
                source_key,
                str(page_number),
                str(render_dpi),
                self._color_key(background_color),
                self._color_key(text_color),
                str(preserve_original),
            )
        )
        key = hashlib.sha256(params.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{key}.png"

    def is_valid(self, path):
        return path.is_file() and path.stat().st_size > 0

    def save(self, image, path):
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        image.save(temporary, format="PNG", optimize=False)
        os.replace(temporary, path)
        return path
