import hashlib
import os
import time
from pathlib import Path


class CoverCache:
    """Armazena imagens de capa remotas para reutilização local controlada."""

    DEFAULT_MAX_AGE_SECONDS = 30 * 24 * 60 * 60
    DEFAULT_MAX_ENTRIES = 100
    DEFAULT_MAX_BYTES = 100 * 1024 * 1024

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

    def _cache_files(self):
        if not self.cache_dir.is_dir():
            return []
        try:
            return [
                path
                for path in self.cache_dir.glob("*.jpg")
                if path.is_file()
            ]
        except OSError as exc:
            print(f"[Aviso Cache]: Falha ao listar capas ({exc}).")
            return []

    @staticmethod
    def _modified_at(path):
        try:
            return path.stat().st_mtime
        except OSError:
            return 0.0

    def get(self, url):
        """Retorna bytes armazenados ou None quando não há cache válido."""
        cache_path = self.path_for_url(url)
        try:
            if cache_path.is_file() and cache_path.stat().st_size > 0:
                dados = cache_path.read_bytes()
                # O mtime funciona como último acesso para a política de retenção.
                cache_path.touch()
                return dados
        except OSError as exc:
            print(f"[Aviso Cache]: Falha ao ler capa em cache ({exc}).")
        return None

    def save(self, url, image_bytes):
        """Salva atomicamente uma imagem processada e aplica a retenção padrão."""
        cache_path = self.path_for_url(url)
        temporary_path = cache_path.with_suffix(".tmp")
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            temporary_path.write_bytes(image_bytes)
            temporary_path.replace(cache_path)
            self.cleanup()
            return cache_path
        except OSError as exc:
            print(f"[Aviso Cache]: Falha ao salvar capa ({exc}).")
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
            return None

    def cleanup(
        self,
        max_age_seconds=DEFAULT_MAX_AGE_SECONDS,
        max_entries=DEFAULT_MAX_ENTRIES,
        max_bytes=DEFAULT_MAX_BYTES,
        now=None,
    ):
        """Remove capas expiradas e excedentes, retornando estatísticas da limpeza.

        A retenção considera o mtime como último acesso. Primeiro são removidos
        arquivos mais antigos que `max_age_seconds`; em seguida, os mais antigos
        são removidos até respeitar `max_entries` e `max_bytes`.
        """
        files = self._cache_files()
        removed = 0
        removed_bytes = 0
        now = time.time() if now is None else now

        if max_age_seconds is not None:
            cutoff = now - max(0, max_age_seconds)
            for path in list(files):
                if self._modified_at(path) < cutoff:
                    size = self._remove_file(path)
                    if size is not None:
                        removed += 1
                        removed_bytes += size
                        files.remove(path)

        files.sort(key=self._modified_at, reverse=True)
        current_bytes = sum(self._file_size(path) for path in files)
        while (
            len(files) > max_entries
            or current_bytes > max_bytes
        ):
            path = files.pop()
            size = self._remove_file(path)
            if size is not None:
                removed += 1
                removed_bytes += size
                current_bytes -= size

        return {
            "removed": removed,
            "removed_bytes": removed_bytes,
            "remaining": len(files),
            "remaining_bytes": current_bytes,
        }

    @staticmethod
    def _file_size(path):
        try:
            return path.stat().st_size
        except OSError:
            return 0

    @staticmethod
    def _remove_file(path):
        try:
            size = path.stat().st_size
            path.unlink()
            return size
        except OSError as exc:
            print(f"[Aviso Cache]: Falha ao remover capa {path.name} ({exc}).")
            return None

    def clear(self):
        """Remove todas as capas do cache e retorna estatísticas da operação."""
        return self.cleanup(max_age_seconds=None, max_entries=0, max_bytes=0)
