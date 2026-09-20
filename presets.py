"""Persistência isolada de presets do EbookBuilder."""

import json
import os
from pathlib import Path


class PresetStore:
    """Armazena configurações nomeadas em um único arquivo JSON do usuário."""

    def __init__(self, caminho=None):
        self.caminho = Path(caminho) if caminho else self._caminho_padrao()

    @staticmethod
    def _caminho_padrao():
        base = os.environ.get("APPDATA") if os.name == "nt" else os.environ.get("XDG_CONFIG_HOME")
        diretorio = Path(base) if base else Path.home() / ".config"
        return diretorio / "EbookBuilder" / "presets.json"

    def _ler(self):
        if not self.caminho.exists():
            return {}
        try:
            dados = json.loads(self.caminho.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Não foi possível ler os presets: {exc}") from exc
        if not isinstance(dados, dict):
            raise ValueError("O arquivo de presets precisa conter um objeto JSON.")
        return dados

    def listar(self):
        return sorted(self._ler())

    def salvar(self, nome, configuracao):
        nome = str(nome).strip()
        if not nome:
            raise ValueError("Informe um nome para o preset.")
        if not isinstance(configuracao, dict):
            raise TypeError("A configuração do preset precisa ser um dicionário.")
        dados = self._ler()
        dados[nome] = dict(configuracao)
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        temporario = self.caminho.with_suffix(".tmp")
        temporario.write_text(
            json.dumps(dados, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporario.replace(self.caminho)

    def carregar(self, nome):
        dados = self._ler()
        try:
            configuracao = dados[str(nome)]
        except KeyError as exc:
            raise KeyError(f"Preset não encontrado: {nome}") from exc
        if not isinstance(configuracao, dict):
            raise ValueError(f"Preset inválido: {nome}")
        return dict(configuracao)
