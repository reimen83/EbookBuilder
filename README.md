# 📄 PDF Editor & ReportLab Suite

Uma aplicação desktop desenvolvida em Python para conversão, edição e recompilação de documentos PDF utilizando **ReportLab** e **pdfplumber**.

## 🚀 Funcionalidades

- **PDF → Python (.py):** Extrai a estrutura e o conteúdo de arquivos PDF existentes, transformando-os em um script Python editável baseado na biblioteca ReportLab.
- **Python (.py) → PDF Final:** Recompila o código Python modificado gerando um novo documento PDF estilizado.
- **Interface Gráfica (GUI):** Interface intuitiva construída com Tkinter, facilitando a navegação entre a extração e a recompilação.
- **Abertura Rápida de Editor:** Botão integrado para abrir o script diretamente no editor padrão do sistema.

## 🛠️ Tecnologias Utilizadas

- **Python 3**
- **Tkinter** (Interface gráfica)
- **ReportLab** (Geração e estilização de PDF)
- **pdfplumber** (Extração de texto e estrutura de PDF)
- **PyInstaller** (Compilação para executável desktop)

## 🔧 Como Executar

### Pré-requisitos

Instale as dependências executando:
pip install reportlab pdfplumber

### Executando a Aplicação
python3 pdf_to_reportlab_gui.py

---
*Desenvolvido por Reinaldo H Neto.*
