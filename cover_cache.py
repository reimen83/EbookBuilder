import hashlib
import os
from pathlib import Path


class CoverCache:
    """Armazena imagens de capa remotas processadas para reutilização local."""

    def __init__(self, cache_dir=None):
        self.cache_dir = Path(cache_dir) if cache_dir else self.default_cache_dir()

    @staticmethod
    def default_cache_dir():
        if os.name == "nt":
            base_dir = os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
            return Path(base_dir) / "EbookBuilder" / "covers"
        return Path.home() / ".cache" / "ebookbuilder" / "covers"

    def path_for_url(self, url):
        digest = hashlib.sha256(str(url).encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.jpg"

    def get(self, url):
        """Retorna bytes armazenados ou None quando não há cache válido."""
        cache_path = self.path_for_url(url)
        try:
            if cache_path.is_file() and cache_path.stat().st_size > 0:
                return cache_path.read_bytes()
        except OSError as exc:
            print(f"[Aviso Cache]: Falha ao ler capa em cache ({exc}).")
        return None

    def save(self, url, image_bytes):
        """Salva atomicamente uma imagem processada e retorna seu caminho."""
        cache_path = self.path_for_url(url)
        temporary_path = cache_path.with_suffix(".tmp")
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            temporary_path.write_bytes(image_bytes)
            temporary_path.replace(cache_path)
            return cache_path
        except OSError as exc:
            print(f"[Aviso Cache]: Falha ao salvar capa ({exc}).")
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
            return None
