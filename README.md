# 📄 EbookBuilder — PDF Editor & ReportLab Suite

Uma aplicação desktop desenvolvida em Python para conversão, diagramação, estilização e compilação de documentos PDF/E-books utilizando ReportLab, CustomTkinter e pdfplumber.

---

## 🚀 Funcionalidades

- **Automação de Conteúdo para PDF:** Converte arquivos de texto (.md, .docx, .txt, .pdf) em e-books diagramados e estilizados.
- **🎨 Variações Dinâmicas de Capa (ThemeEngine):** Seleção de temas visuais e variações de background em tempo real, permitindo alternar estilos visuais sem quebrar o layout ou a tipografia.
- **👁️ Preview em Tempo Real:** Pré-visualização instantânea da capa e do documento diretamente na interface gráfica antes da compilação final.
- **PDF → Python (.py):** Extrai a estrutura e o conteúdo de arquivos PDF existentes, transformando-os em um script Python editável baseado na biblioteca ReportLab.
- **Python (.py) → PDF Final:** Recompila o código Python modificado gerando um novo documento PDF estilizado.
- **Interface Gráfica Moderna (GUI):** Interface intuitiva e responsiva construída com **CustomTkinter**, facilitando a navegação, seleção de temas e visualização de arquivos.
- **Abertura Rápida de Editor:** Botão integrado para abrir o script diretamente no editor padrão do sistema.

---

## 🛠️ Tecnologias Utilizadas

- **Python 3**
- **CustomTkinter & Tkinter** (Interface gráfica moderna e responsiva)
- **ReportLab** (Geração, diagramação e estilização de PDF)
- **pdfplumber** (Extração de texto e estrutura de PDF)
- **Pillow (PIL)** (Processamento e renderização do preview de imagem)
- **PyInstaller** (Compilação para executável desktop)

---

## 🎨 Temas e Variações de Capa Suportados

| Tema Visual | ID do Tema | Variações de Capa |
| :--- | :--- | :--- |
| **🎛️ Produção Musical** | `music_prod` | Studio Dark, Vintage Analog, Waveform Pattern, Neon Synth |
| **💰 Finanças & Negócios** | `finance_gold` | Gold Accent, Slate Solid, Geometric Corporate, Minimal Dark |
| **🤖 IA & Produtividade** | `ai_productivity` | Cyber Violet Gradient, Tech Grid, Deep Obsidian, Neon Edge |
| **🌿 Saúde & Fitness** | `health_wellness` | Earthy Sage, Organic Soft, Clean Minimal, Botanical Gradient |
| **🧠 Desenvolv. Pessoal** | `self_help` | Warm Terracotta, Warm Sunset, Minimal Cream, Soft Earth |
| **⚡ Dark Tech** | `dark_tech` | Obsidian Cyan, Monokai Dark, Terminal Grid, Clean Obsidian |
| **📜 Editorial** | `editorial` | Classic Cream, Vintage Paper, Clean White, Book Serif |
| **🔹 Moderno** | `modern` | Corporate Blue, Soft Gray, Bold Modern, Minimal Slate |

---

## 🔧 Como Executar

python gui.py

### 1. Pré-requisitos

Instale as dependências executando:
- bash
- pip install reportlab pdfplumber customtkinter pillow

---

- Desenvolvido por Reinaldo H Neto.
