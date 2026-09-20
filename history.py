"""Persistência local do histórico de conversões do EbookBuilder."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path


class HistoryStore:
    """Armazena o histórico local de projetos e conversões do EbookBuilder."""

    def __init__(self, caminho=None):
        self.caminho = Path(caminho) if caminho else self._caminho_padrao()

    @staticmethod
    def _caminho_padrao():
        base = os.environ.get("APPDATA") if os.name == "nt" else os.environ.get("XDG_CONFIG_HOME")
        diretorio = Path(base) if base else Path.home() / ".config"
        return diretorio / "EbookBuilder" / "history.json"

    def _ler(self):
        if not self.caminho.exists():
            return []
        try:
            dados = json.loads(self.caminho.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Não foi possível ler o histórico: {exc}") from exc
        if not isinstance(dados, list):
            raise ValueError("O arquivo de histórico precisa conter uma lista JSON.")
        return dados

    def listar(self, limite=10, tipo="conversao"):
        itens = self._ler()
        filtrados = [item for item in itens if item.get("tipo") == tipo]
        itens_ordenados = sorted(filtrados, key=lambda item: item.get("criado_em", ""), reverse=True)
        return itens_ordenados[:limite]

    def listar_projetos(self, limite=5):
        return self.listar(limite=limite, tipo="projeto")

    def _registrar(self, origem, destino, titulo="", subtitulo="", tema="", variacao=None, tipo="conversao"):
        origem = str(origem).strip()
        destino = str(destino).strip()
        if not origem or not destino:
            raise ValueError("Origem e destino precisam ser informados para registrar o histórico.")

        registro = {
            "tipo": tipo,
            "origem": origem,
            "destino": destino,
            "titulo": str(titulo or "").strip(),
            "subtitulo": str(subtitulo or "").strip(),
            "tema": str(tema or "").strip(),
            "variacao": str(variacao or "").strip(),
            "criado_em": datetime.now(timezone.utc).isoformat(),
        }

        itens = self._ler()
        itens.insert(0, registro)
        itens = itens[:50]

        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        temporario = self.caminho.with_suffix(".tmp")
        temporario.write_text(
            json.dumps(itens, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporario.replace(self.caminho)

        return dict(registro)

    def registrar(self, origem, saida, titulo="", subtitulo="", tema="", variacao=None):
        return self._registrar(
            origem=origem,
            destino=saida,
            titulo=titulo,
            subtitulo=subtitulo,
            tema=tema,
            variacao=variacao,
            tipo="conversao",
        )

    def registrar_projeto(self, origem, destino, titulo="", subtitulo="", tema="", variacao=None):
        return self._registrar(
            origem=origem,
            destino=destino,
            titulo=titulo,
            subtitulo=subtitulo,
            tema=tema,
            variacao=variacao,
            tipo="projeto",
        )
