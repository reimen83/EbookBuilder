# EbookBuilder — Gerador local de e-books em PDF

Aplicação desktop desenvolvida em Python para conversão, diagramação, estilização e compilação de documentos em e-books PDF usando ReportLab, CustomTkinter e pdfplumber.

O EbookBuilder foi projetado para processamento local: os arquivos do usuário não precisam ser enviados para um servidor ou abertos em um navegador.

## Funcionalidades

- Conversão de arquivos `.md`, `.docx`, `.txt` e `.pdf` em e-books diagramados.
- Temas visuais e variações de capa.
- Preview da capa antes da compilação.
- Extração de títulos e subtítulos dos documentos.
- Geração de PDF com capa, estilos, cabeçalho, rodapé e paginação.
- Execução como aplicação desktop no Linux e no Windows.

## Execução no Linux a partir do código-fonte

Recomenda-se Python 3.10 ou mais recente.

```bash
sudo apt update
sudo apt install python3 python3-venv python3-tk

git clone https://github.com/reimen83/EbookBuilder.git
cd EbookBuilder

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .

python gui.py
```

Depois da instalação, também é possível executar pelo ponto de entrada do pacote:

```bash
ebookbuilder
```

## Desenvolvimento e testes

Para instalar as ferramentas de desenvolvimento:

```bash
python -m pip install -r requirements-dev.txt
```

Para executar os testes:

```bash
python -m pytest
```

A suíte de testes cobre o parser de conteúdo, a extração de títulos, os temas e a geração básica de PDF.

## Dependências principais

- Python 3
- CustomTkinter e Tkinter
- ReportLab
- pdfplumber
- pypdfium2
- python-docx
- Pillow
- requests
- PyInstaller, utilizado no empacotamento de executáveis

## Temas disponíveis

| Tema | Identificador |
|---|---|
| Produção Musical | `music_prod` |
| Finanças e Negócios | `finance_gold` |
| IA e Produtividade | `ai_productivity` |
| Saúde e Bem-estar | `health_wellness` |
| Desenvolvimento Pessoal | `self_help` |
| Dark Tech | `dark_tech` |
| Editorial | `editorial` |
| Moderno | `modern` |

## Direção do projeto

O projeto continuará prioritariamente como uma aplicação desktop local. A separação entre interface e núcleo de compilação será feita gradualmente para permitir builds confiáveis para Linux e Windows, testes automatizados e funcionamento offline sempre que possível.

## Licença

Consulte o repositório para informações de licença.
