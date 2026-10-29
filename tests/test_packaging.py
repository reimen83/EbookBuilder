from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = PROJECT_ROOT / "packaging" / "ebookbuilder.spec"


def test_pyinstaller_inclui_pillow_tkinter():
    spec = SPEC_PATH.read_text(encoding="utf-8")

    assert '"PIL.ImageTk"' in spec
    assert '"PIL._tkinter_finder"' in spec
