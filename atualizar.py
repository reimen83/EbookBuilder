#!/usr/bin/env python3
"""Atualização segura de uma cópia local do EbookBuilder."""

from dataclasses import dataclass
from pathlib import Path
import subprocess


class AtualizacaoError(RuntimeError):
    """Erro esperado durante a atualização do código local."""


@dataclass(frozen=True)
class ResultadoAtualizacao:
    repositorio: Path
    alterado: bool
    mensagem: str


def _executar_git(comando, cwd):
    try:
        return subprocess.run(
            ["git", *comando],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise AtualizacaoError("O Git não está instalado ou não está no PATH.") from exc
    except subprocess.CalledProcessError as exc:
        detalhe = (exc.stderr or exc.stdout or "").strip()
        raise AtualizacaoError(
            f"Falha ao executar git {' '.join(comando)}"
            + (f": {detalhe}" if detalhe else ".")
        ) from exc


def atualizar_repositorio(caminho=None, remoto="origin", branch="main"):
    """Atualiza o repositório local com fast-forward, sem apagar alterações."""
    caminho_informado = Path(caminho or ".").expanduser().resolve()
    raiz = _executar_git(["rev-parse", "--show-toplevel"], caminho_informado).stdout.strip()
    if not raiz:
        raise AtualizacaoError("Não foi possível localizar a raiz do repositório.")
    repositorio = Path(raiz)

    estado = _executar_git(["status", "--porcelain"], repositorio).stdout.strip()
    if estado:
        raise AtualizacaoError(
            "A atualização foi interrompida: existem alterações locais não commitadas."
        )

    antes = _executar_git(["rev-parse", "HEAD"], repositorio).stdout.strip()
    _executar_git(["fetch", remoto, branch], repositorio)
    _executar_git(["pull", "--ff-only", remoto, branch], repositorio)
    depois = _executar_git(["rev-parse", "HEAD"], repositorio).stdout.strip()

    if antes == depois:
        return ResultadoAtualizacao(repositorio, False, "O projeto já estava atualizado.")
    return ResultadoAtualizacao(
        repositorio,
        True,
        f"Projeto atualizado de {antes[:8]} para {depois[:8]}.",
    )


def main():
    try:
        resultado = atualizar_repositorio()
    except AtualizacaoError as exc:
        print(f"Erro: {exc}")
        return 1
    print(resultado.mensagem)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
