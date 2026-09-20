import subprocess

import pytest

import atualizar


def test_atualizar_recusa_alteracoes_locais(monkeypatch, tmp_path):
    respostas = iter(["/repo\n", "M gui.py\n"])

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 0, next(respostas), "")

    monkeypatch.setattr(atualizar.subprocess, "run", fake_run)

    with pytest.raises(atualizar.AtualizacaoError, match="alterações locais"):
        atualizar.atualizar_repositorio(tmp_path)


def test_atualizar_faz_fast_forward_e_informa_mudanca(monkeypatch, tmp_path):
    respostas = iter(
        [
            "/repo\n",
            "\n",
            "abc123456789\n",
            "",
            "Already up to date.\n",
            "def987654321\n",
        ]
    )
    comandos = []

    def fake_run(comando, **kwargs):
        comandos.append(comando)
        return subprocess.CompletedProcess(comando, 0, next(respostas), "")

    monkeypatch.setattr(atualizar.subprocess, "run", fake_run)

    resultado = atualizar.atualizar_repositorio(tmp_path)

    assert resultado.alterado is True
    assert "abc12345" in resultado.mensagem
    assert "def98765" in resultado.mensagem
    assert comandos == [
        ["git", "rev-parse", "--show-toplevel"],
        ["git", "status", "--porcelain"],
        ["git", "rev-parse", "HEAD"],
        ["git", "fetch", "origin", "main"],
        ["git", "pull", "--ff-only", "origin", "main"],
        ["git", "rev-parse", "HEAD"],
    ]


def test_atualizar_identifica_repositorio_atualizado(monkeypatch, tmp_path):
    respostas = iter(["/repo\n", "\n", "abc123\n", "", "", "abc123\n"])

    def fake_run(comando, **kwargs):
        return subprocess.CompletedProcess(comando, 0, next(respostas), "")

    monkeypatch.setattr(atualizar.subprocess, "run", fake_run)

    resultado = atualizar.atualizar_repositorio(tmp_path)

    assert resultado.alterado is False
    assert resultado.mensagem == "O projeto já estava atualizado."
