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

    def _gravar(self, dados):
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        temporario = self.caminho.with_suffix(".tmp")
        temporario.write_text(
            json.dumps(dados, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporario.replace(self.caminho)

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
        self._gravar(dados)

    def carregar(self, nome):
        dados = self._ler()
        try:
            configuracao = dados[str(nome)]
        except KeyError as exc:
            raise KeyError(f"Preset não encontrado: {nome}") from exc
        if not isinstance(configuracao, dict):
            raise ValueError(f"Preset inválido: {nome}")
        return dict(configuracao)

    def renomear(self, nome_atual, novo_nome):
        nome_atual = str(nome_atual).strip()
        novo_nome = str(novo_nome).strip()
        if not nome_atual or not novo_nome:
            raise ValueError("Informe os nomes atual e novo do preset.")

        dados = self._ler()
        if nome_atual not in dados:
            raise KeyError(f"Preset não encontrado: {nome_atual}")
        if novo_nome != nome_atual and novo_nome in dados:
            raise ValueError(f"Já existe um preset chamado: {novo_nome}")

        dados[novo_nome] = dados.pop(nome_atual)
        self._gravar(dados)

    def excluir(self, nome):
        nome = str(nome).strip()
        if not nome:
            raise ValueError("Informe o nome do preset.")

        dados = self._ler()
        if nome not in dados:
            raise KeyError(f"Preset não encontrado: {nome}")

        del dados[nome]
        self._gravar(dados)

    def exportar(self, caminho_arquivo):
        caminho = Path(caminho_arquivo)
        dados = self._ler()
        caminho.parent.mkdir(parents=True, exist_ok=True)
        temporario = caminho.with_suffix(caminho.suffix or ".json")
        temporario.write_text(
            json.dumps(dados, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporario.replace(caminho)
        return caminho

    def importar(self, caminho_arquivo, sobrescrever=False):
        caminho = Path(caminho_arquivo)
        if not caminho.exists():
            raise FileNotFoundError(f"Arquivo de presets não encontrado: {caminho}")
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Não foi possível ler o arquivo para importar: {exc}") from exc
        if not isinstance(dados, dict):
            raise ValueError("O arquivo a importar precisa conter um objeto JSON com presets.")

        existentes = {} if sobrescrever else self._ler()
        for nome, configuracao in dados.items():
            nome = str(nome).strip()
            if not nome:
                continue
            if not isinstance(configuracao, dict):
                raise ValueError(f"Preset inválido em '{nome}': a configuração precisa ser um objeto JSON.")
            existentes[nome] = dict(configuracao)

        self._gravar(existentes)
        return sorted(existentes)
