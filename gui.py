import threading
import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

from compiler import EbookCompiler, ThemeEngine
from preview_state import build_preview_signature
from validation import (
    build_output_path,
    validate_cover_file,
    validate_destination_directory,
    validate_source_file,
)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

DEFAULT_THEME = "modern"
PREVIEW_MAX_WIDTH = 460
PREVIEW_MAX_HEIGHT = 650


@dataclass(frozen=True)
class EbookFormConfig:
    origem: str
    destino: str
    titulo: str
    subtitulo: str
    capa: str
    tema: str
    variacao: str | None = None

    @property
    def tema_ativo(self) -> str:
        return self.tema or DEFAULT_THEME

    @property
    def capa_ativa(self) -> str:
        return self.capa.strip()

    @property
    def titulo_ativo(self) -> str:
        return self.titulo.strip()

    @property
    def subtitulo_ativo(self) -> str:
        return self.subtitulo.strip()


class EbookBuilderGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("EbookBuilder — Gerador de E-books com Preview em Tempo Real")
        
        # Define tamanho padrão e LIMITE MÍNIMO para evitar quebras ao redimensionar
        self.geometry("1180x850")
        self.minsize(980, 650)
        self.resizable(True, True)

        self.caminho_arquivo_fonte = tk.StringVar()
        self.pasta_destino = tk.StringVar()
        self.titulo_ebook = tk.StringVar()
        self.sub_titulo_ebook = tk.StringVar()
        self.caminho_capa_local = tk.StringVar()
        self.url_capa = tk.StringVar()

        self.preview_ctk_image = None
        self._preview_generation = 0
        self._preview_signature = None
        self._preview_thread = None

        self.mapa_temas = {
            "🎛️ Produção Musical (Studio Dark)": "music_prod",
            "💰 Finanças & Negócios (Gold & Slate)": "finance_gold",
            "🤖 IA & Produtividade (Cyber Violet)": "ai_productivity",
            "🌿 Saúde & Fitness (Earthy Sage)": "health_wellness",
            "🧠 Desenvolv. Pessoal (Warm Terracotta)": "self_help",
            "⚡ Dark Tech (Obsidian Slate & Cyan)": "dark_tech",
            "📜 Editorial (Livro Classic - Serif)": "editorial",
            "🔹 Moderno (Corporate Clean)": "modern",
        }

        self.mapa_variacoes_atuais = {}

        self._criar_menu_contexto()
        self._construir_interface()
        self.bind("<Button-1>", lambda event: self._fechar_menu_contexto())

    def _criar_menu_contexto(self):
        self.menu_contexto = tk.Menu(self, tearoff=0)
        self.menu_contexto.add_command(label="Recortar", command=lambda: self._executar_acao_menu("cut"))
        self.menu_contexto.add_command(label="Copiar", command=lambda: self._executar_acao_menu("copy"))
        self.menu_contexto.add_command(label="Colar", command=lambda: self._executar_acao_menu("paste"))
        self.menu_contexto.add_separator()
        self.menu_contexto.add_command(label="Selecionar Tudo", command=lambda: self._executar_acao_menu("select_all"))

    def _exibir_menu_contexto(self, event):
        self.widget_focado = event.widget
        try:
            self.menu_contexto.tk_popup(event.x_root, event.y_root)
            self.menu_contexto.focus_set()
        finally:
            self.menu_contexto.grab_release()

    def _fechar_menu_contexto(self):
        try:
            self.menu_contexto.unpost()
        except Exception:
            pass

    def _executar_acao_menu(self, acao):
        if not hasattr(self, "widget_focado") or not self.widget_focado:
            return
        w = self.widget_focado
        try:
            if acao == "cut": w.event_generate("<<Cut>>")
            elif acao == "copy": w.event_generate("<<Copy>>")
            elif acao == "paste": w.event_generate("<<Paste>>")
            elif acao == "select_all": w.event_generate("<<SelectAll>>")
        except Exception:
            pass
        finally:
            self._fechar_menu_contexto()

    def _adicionar_suporte_clique_direito(self, entry_widget):
        target = getattr(entry_widget, "_entry", entry_widget)
        target.bind("<Button-3>", self._exibir_menu_contexto)

    def _construir_interface(self):
        # Ajuste proporcional das colunas: Esquerda (40%) e Direita/Preview (60%)
        self.grid_columnconfigure(0, weight=4)
        self.grid_columnconfigure(1, weight=6)
        self.grid_rowconfigure(0, weight=1)

        # ==================== PAINEL ESQUERDO ====================
        frame_esquerda = ctk.CTkScrollableFrame(self, label_text="Configurações do E-book")
        frame_esquerda.grid(row=0, column=0, sticky="nsew", padx=(15, 7), pady=15)

        lbl_titulo = ctk.CTkLabel(frame_esquerda, text="EbookBuilder", font=ctk.CTkFont(size=24, weight="bold"), text_color="#F59E0B")
        lbl_titulo.pack(anchor="w", padx=10, pady=(5, 0))

        lbl_subtitulo = ctk.CTkLabel(frame_esquerda, text="Transforme textos em e-books estilizados e diagramados.", font=ctk.CTkFont(size=12), text_color="#94A3B8")
        lbl_subtitulo.pack(anchor="w", padx=10, pady=(0, 10))

        # 1. ORIGEM E DESTINO
        frame_fonte = ctk.CTkFrame(frame_esquerda)
        frame_fonte.pack(fill="x", padx=5, pady=6)
        ctk.CTkLabel(frame_fonte, text="1. Arquivos (Origem e Destino)", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(8, 4))

        box_fonte = ctk.CTkFrame(frame_fonte, fg_color="transparent")
        box_fonte.pack(fill="x", padx=10, pady=(0, 4))
        entry_fonte = ctk.CTkEntry(box_fonte, textvariable=self.caminho_arquivo_fonte, placeholder_text="Arquivo de conteúdo (.md, .docx, .pdf, .txt)...")
        entry_fonte.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self._adicionar_suporte_clique_direito(entry_fonte)
        ctk.CTkButton(box_fonte, text="Procurar", width=90, command=self._procurar_fonte).pack(side="right")

        box_destino = ctk.CTkFrame(frame_fonte, fg_color="transparent")
        box_destino.pack(fill="x", padx=10, pady=(0, 8))
        entry_destino = ctk.CTkEntry(box_destino, textvariable=self.pasta_destino, placeholder_text="Pasta onde o E-book será salvo...")
        entry_destino.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self._adicionar_suporte_clique_direito(entry_destino)
        ctk.CTkButton(box_destino, text="Destino", width=90, command=self._procurar_destino).pack(side="right")

        # 2. TÍTULOS
        frame_titulos = ctk.CTkFrame(frame_esquerda)
        frame_titulos.pack(fill="x", padx=5, pady=6)
        ctk.CTkLabel(frame_titulos, text="2. Título e Subtítulo da Capa", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(8, 2))

        ctk.CTkLabel(
            frame_titulos,
            text="💡 Título (Opcional: Deixe em branco para extrair do documento)",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        ).pack(anchor="w", padx=10, pady=(2, 2))

        self.entry_titulo = ctk.CTkEntry(
            frame_titulos,
            textvariable=self.titulo_ebook,
            placeholder_text="Digite o título manualmente se desejar..."
        )
        self.entry_titulo.pack(fill="x", padx=10, pady=(0, 8))
        self._adicionar_suporte_clique_direito(self.entry_titulo)

        ctk.CTkLabel(
            frame_titulos,
            text="💡 Subtítulo (Opcional: Deixe em branco para extrair do documento)",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        ).pack(anchor="w", padx=10, pady=(2, 2))

        self.entry_subtitulo = ctk.CTkEntry(
            frame_titulos,
            textvariable=self.sub_titulo_ebook,
            placeholder_text="Digite o subtítulo manualmente se desejar..."
        )
        self.entry_subtitulo.pack(fill="x", padx=10, pady=(0, 8))
        self._adicionar_suporte_clique_direito(self.entry_subtitulo)

        # 3. CAPA PERSONALIZADA
        frame_capa = ctk.CTkFrame(frame_esquerda)
        frame_capa.pack(fill="x", padx=5, pady=6)
        ctk.CTkLabel(frame_capa, text="3. Imagem de Capa Personalizada (Opcional)", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(8, 4))

        entry_url = ctk.CTkEntry(frame_capa, textvariable=self.url_capa, placeholder_text="URL da Imagem (Ex: Unsplash)...")
        entry_url.pack(fill="x", padx=10, pady=(0, 6))
        self._adicionar_suporte_clique_direito(entry_url)

        box_capa_local = ctk.CTkFrame(frame_capa, fg_color="transparent")
        box_capa_local.pack(fill="x", padx=10, pady=(0, 8))
        entry_capa_local = ctk.CTkEntry(box_capa_local, textvariable=self.caminho_capa_local, placeholder_text="OU imagem no computador...")
        entry_capa_local.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self._adicionar_suporte_clique_direito(entry_capa_local)
        ctk.CTkButton(box_capa_local, text="Procurar", width=90, command=self._procurar_capa_local).pack(side="right")

        # 4. TEMAS E VARIAÇÕES
        frame_tema = ctk.CTkFrame(frame_esquerda)
        frame_tema.pack(fill="x", padx=5, pady=6)
        
        ctk.CTkLabel(frame_tema, text="4. Tema Visual do PDF", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(8, 4))
        self.combo_tema = ctk.CTkOptionMenu(
            frame_tema,
            values=list(self.mapa_temas.keys()),
            fg_color="#1E293B",
            button_color="#2563EB",
            command=self._ao_alterar_tema
        )
        self.combo_tema.pack(fill="x", padx=10, pady=(0, 8))

        # 5. VARIAÇÃO DE CAPA DO TEMA
        ctk.CTkLabel(frame_tema, text="5. Variação da Capa (Background)", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(4, 4))
        self.combo_variacao = ctk.CTkOptionMenu(
            frame_tema,
            values=["Carregando..."],
            fg_color="#0F172A",
            button_color="#3B82F6",
            command=lambda choice: self._executar_preview_direto()
        )
        self.combo_variacao.pack(fill="x", padx=10, pady=(0, 8))

        self._atualizar_opcoes_variacao(self.mapa_temas[self.combo_tema.get()])

        # BOTÃO PREVIEW
        self.btn_preview = ctk.CTkButton(frame_esquerda, text="🔄 Atualizar Pré-visualização", font=ctk.CTkFont(size=13, weight="bold"), fg_color="#3B82F6", hover_color="#2563EB", command=lambda: self._executar_preview_direto(force=True))
        self.btn_preview.pack(fill="x", padx=5, pady=(8, 4))

        # BOTÃO GERAR COMPLETO
        self.btn_gerar = ctk.CTkButton(frame_esquerda, text="🚀 GERAR E-BOOK COMPLETO", font=ctk.CTkFont(size=15, weight="bold"), fg_color="#10B981", hover_color="#059669", height=45, command=self._iniciar_compilacao)
        self.btn_gerar.pack(fill="x", padx=5, pady=(4, 8))

        self.lbl_status = ctk.CTkLabel(frame_esquerda, text="Pronto para gerar seu e-book.", font=ctk.CTkFont(size=12), text_color="#94A3B8")
        self.lbl_status.pack(pady=(0, 8))

        # ==================== PAINEL DIREITO: PREVIEW ====================
        frame_direita = ctk.CTkFrame(self)
        frame_direita.grid(row=0, column=1, sticky="nsew", padx=(7, 15), pady=15)

        header_preview = ctk.CTkFrame(frame_direita, fg_color="transparent")
        header_preview.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(header_preview, text="👁️ Preview da Capa em Tempo Real", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        nav_box = ctk.CTkFrame(header_preview, fg_color="transparent")
        nav_box.pack(side="right")

        self.lbl_paginacao = ctk.CTkLabel(nav_box, text="Capa", font=ctk.CTkFont(size=12))
        self.lbl_paginacao.pack(side="left", padx=8)

        self.box_canvas_preview = ctk.CTkFrame(frame_direita, fg_color="#0F172A")
        self.box_canvas_preview.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.lbl_imagem_preview = ctk.CTkLabel(
            self.box_canvas_preview,
            text="Clique em 'Atualizar Pré-visualização' para gerar a capa do e-book.",
            text_color="#94A3B8",
            wraplength=350
        )
        self.lbl_imagem_preview.pack(expand=True, fill="both", padx=10, pady=10)

    def _tema_ativo(self):
        return self.mapa_temas.get(self.combo_tema.get(), DEFAULT_THEME)

    def _build_form_config(self):
        return EbookFormConfig(
            origem=self.caminho_arquivo_fonte.get().strip(),
            destino=self.pasta_destino.get().strip(),
            titulo=self.entry_titulo.get().strip(),
            subtitulo=self.entry_subtitulo.get().strip(),
            capa=self.url_capa.get().strip() or self.caminho_capa_local.get().strip(),
            tema=self._tema_ativo(),
            variacao=self._obter_id_variacao_selecionada(),
        )

    def _ao_alterar_tema(self, escolha_tema):
        tema_chave = self.mapa_temas.get(escolha_tema, DEFAULT_THEME)
        self._atualizar_opcoes_variacao(tema_chave)
        self._executar_preview_direto()

    def _atualizar_opcoes_variacao(self, tema_chave):
        capas = ThemeEngine.obter_opcoes_capa_por_tema(tema_chave)
        self.mapa_variacoes_atuais = {c["nome"]: c["id"] for c in capas}

        nomes_variacoes = list(self.mapa_variacoes_atuais.keys())
        self.combo_variacao.configure(values=nomes_variacoes)
        if nomes_variacoes:
            self.combo_variacao.set(nomes_variacoes[0])

    def _obter_id_variacao_selecionada(self):
        nome_selecionado = self.combo_variacao.get()
        return self.mapa_variacoes_atuais.get(nome_selecionado, None)

    def _executar_preview_direto(self, force=False):
        config = self._build_form_config()
        assinatura = build_preview_signature(
            config.origem,
            config.capa_ativa,
            config.titulo_ativo,
            config.subtitulo_ativo,
            config.tema_ativo,
            config.variacao,
        )

        if not force and assinatura == self._preview_signature:
            return

        self._preview_signature = assinatura
        self._preview_generation += 1
        generation = self._preview_generation

        self.lbl_imagem_preview.configure(
            text="⏳ Gerando preview da capa...",
            image=None,
        )

        self._preview_thread = threading.Thread(
            target=self._gerar_preview_bg,
            args=(generation, config),
            daemon=True,
        )
        self._preview_thread.start()

    def _gerar_preview_bg(self, generation, config):
        if generation != self._preview_generation:
            return

        try:
            compiler = EbookCompiler(
                arquivo_fonte=config.origem,
                arquivo_saida="",
                capa_url=config.capa_ativa,
                titulo_ebook=config.titulo_ativo,
                sub_titulo_ebook=config.subtitulo_ativo,
                tema=config.tema_ativo,
                variacao_capa=config.variacao,
            )
            imagens_pil = compiler.gerar_preview_capa_fast(dpi=100)
            imagem = imagens_pil[0].copy() if imagens_pil else None
            if generation != self._preview_generation:
                return
            self.after(0, self._aplicar_preview, generation, imagem)
        except Exception as exc:
            if generation == self._preview_generation:
                self.after(0, self._preview_erro, generation, str(exc))

    def _aplicar_preview(self, generation, imagem):
        if generation != self._preview_generation:
            return
        if imagem is None:
            self.lbl_imagem_preview.configure(
                text="Nenhuma imagem de capa foi gerada.",
                image=None,
            )
            return

        imagem.thumbnail((PREVIEW_MAX_WIDTH, PREVIEW_MAX_HEIGHT), Image.Resampling.LANCZOS)
        self.preview_ctk_image = ctk.CTkImage(
            light_image=imagem,
            dark_image=imagem,
            size=(imagem.width, imagem.height),
        )
        self.lbl_imagem_preview.configure(image=self.preview_ctk_image, text="")

    def _preview_erro(self, generation, mensagem):
        if generation != self._preview_generation:
            return
        self.lbl_imagem_preview.configure(
            text=f"❌ Erro ao gerar capa:\n{mensagem}",
            image=None,
        )

    def _procurar_fonte(self):
        caminho = filedialog.askopenfilename(filetypes=[("Todos os Formatos Suportados", "*.md *.docx *.pdf *.txt")])
        if caminho:
            try:
                fonte = validate_source_file(caminho)
                self.caminho_arquivo_fonte.set(str(fonte))
                if not self.pasta_destino.get():
                    self.pasta_destino.set(str(fonte.parent))
                self._executar_preview_direto()
            except (FileNotFoundError, ValueError) as exc:
                messagebox.showerror("Arquivo inválido", str(exc))

    def _procurar_destino(self):
        pasta = filedialog.askdirectory()
        if pasta:
            try:
                self.pasta_destino.set(str(validate_destination_directory(pasta)))
            except (FileNotFoundError, ValueError) as exc:
                messagebox.showerror("Destino inválido", str(exc))

    def _procurar_capa_local(self):
        caminho = filedialog.askopenfilename(filetypes=[("Imagens", "*.png *.jpg *.jpeg")])
        if caminho:
            try:
                capa = validate_cover_file(caminho)
                self.caminho_capa_local.set(str(capa))
                self.url_capa.set("")
                self._executar_preview_direto()
            except (FileNotFoundError, ValueError) as exc:
                messagebox.showerror("Capa inválida", str(exc))

    def _iniciar_compilacao(self):
        form = self._build_form_config()
        try:
            fonte = validate_source_file(form.origem)
            caminho_saida = build_output_path(fonte, form.destino or fonte.parent)
        except (FileNotFoundError, ValueError) as exc:
            messagebox.showerror("Não é possível gerar o e-book", str(exc))
            return

        self.btn_gerar.configure(state="disabled")
        self.lbl_status.configure(text="⏳ Gerando e-book em PDF...", text_color="#F59E0B")

        threading.Thread(
            target=self._executar_compilacao_bg,
            args=(
                form,
                str(caminho_saida),
            ),
            daemon=True,
        ).start()

    def _executar_compilacao_bg(self, form, saída):
        try:
            EbookCompiler(
                arquivo_fonte=form.origem,
                arquivo_saida=saída,
                capa_url=form.capa_ativa,
                titulo_ebook=form.titulo_ativo,
                sub_titulo_ebook=form.subtitulo_ativo,
                tema=form.tema_ativo,
                variacao_capa=form.variacao,
            ).compilar()
            self.after(0, self._compilacao_sucesso, saída)
        except Exception as e:
            self.after(0, self._compilacao_erro, str(e))

    def _compilacao_sucesso(self, caminho):
        self.btn_gerar.configure(state="normal")
        self.lbl_status.configure(text="✅ E-book gerado com sucesso!", text_color="#10B981")
        messagebox.showinfo("Sucesso", f"Salvo em:\n{caminho}")

    def _compilacao_erro(self, msg):
        self.btn_gerar.configure(state="normal")
        self.lbl_status.configure(text="❌ Erro ao gerar.", text_color="#EF4444")
        messagebox.showerror("Erro", msg)


def main():
    """Inicia a aplicação gráfica do EbookBuilder."""
    EbookBuilderGUI().mainloop()


if __name__ == "__main__":
    main()
