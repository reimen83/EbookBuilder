# -*- mode: python ; coding: utf-8 -*-
"""Build PyInstaller compartilhado por Linux e Windows."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all


PROJECT_ROOT = Path(SPECPATH).resolve().parent


def collect_package(package_name):
    datas, binaries, hiddenimports = collect_all(package_name)
    return datas, binaries, hiddenimports


datas = []
binaries = []
hiddenimports = []
for package in ("customtkinter", "pdfplumber", "pypdfium2"):
    package_data, package_binaries, package_hiddenimports = collect_package(package)
    datas.extend(package_data)
    binaries.extend(package_binaries)
    hiddenimports.extend(package_hiddenimports)

# O pacote app é descoberto pela Analysis através do diretório raiz do projeto.
# Estes imports são usados de forma condicional por bibliotecas e ficam explícitos
# para evitar diferenças entre os runners Linux e Windows.
hiddenimports.extend(
    [
        "PIL",
        "PIL.Image",
        "reportlab",
        "pdfminer",
        "pdfminer.high_level",
        "pypdfium2",
        "pypdf",
        "customtkinter",
    ]
)

analysis = Analysis(
    [str(PROJECT_ROOT / "gui.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "ruff"],
    noarchive=False,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="EbookBuilder",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name="EbookBuilder",
)
