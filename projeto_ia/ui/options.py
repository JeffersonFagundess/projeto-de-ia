"""Alternativas ilustradas da pessoa da vez, abertas sob demanda."""

import tkinter as tk
from tkinter import ttk

from .board import Tabuleiro
from . import theme as t
from .widgets import Botao


def mostrar_opcoes(root, estado, analise, ao_escolher, texto_resultado, rodape="Os resultados supõem boas jogadas dos dois lados depois."):
    janela = tk.Toplevel(root)
    janela.title("Todas as jogadas desta vez")
    janela.geometry("580x610")
    janela.minsize(580, 500)
    janela.configure(bg=t.FUNDO)
    cor = "vermelhas" if estado.vez == "V" else "pretas"
    tk.Label(janela, text=f"O que as {cor} podem fazer?", font=("Segoe UI Semibold", 18),
             bg=t.FUNDO, fg=t.TEXTO).pack(anchor="w", padx=20, pady=(16, 5))
    tk.Label(janela, text="Cada desenho é uma jogada possível. A seta mostra o movimento.\nDepois de jogar, você poderá explorar as respostas da outra cor.",
             font=("Segoe UI", 10), bg=t.FUNDO, fg=t.SUAVE, justify="left").pack(anchor="w", padx=20, pady=(0, 12))
    area = tk.Frame(janela, bg=t.FUNDO)
    area.pack(fill="both", expand=True, padx=16)
    canvas = tk.Canvas(area, bg=t.FUNDO, highlightthickness=0)
    estilo = ttk.Style(janela)
    estilo.theme_use("clam")
    estilo.configure("Damas.Vertical.TScrollbar",troughcolor=t.FUNDO,
                     background=t.LINHA,arrowcolor=t.SUAVE,bordercolor=t.FUNDO,
                     lightcolor=t.LINHA,darkcolor=t.LINHA)
    estilo.map("Damas.Vertical.TScrollbar",background=[("active", "#3C586F")])
    barra = ttk.Scrollbar(area, command=canvas.yview, style="Damas.Vertical.TScrollbar")
    barra.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    canvas.configure(yscrollcommand=barra.set)
    conteudo = tk.Frame(canvas, bg=t.FUNDO)
    janela_canvas = canvas.create_window((0, 0), window=conteudo, anchor="nw")
    conteudo.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfigure(janela_canvas, width=e.width))
    conteudo.grid_columnconfigure(0, weight=1)
    conteudo.grid_columnconfigure(1, weight=1)

    def testar(lance):
        janela.destroy()
        ao_escolher(lance)

    janela.bind("<MouseWheel>", lambda evento: canvas.yview_scroll(int(-evento.delta / 120), "units"))
    for numero, (lance, resultado) in enumerate(analise):
        card = tk.Frame(conteudo, bg=t.PAINEL, padx=12, pady=12,
                        highlightthickness=1,highlightbackground=t.LINHA)
        card.grid(row=numero // 2, column=numero % 2, sticky="nsew", padx=5, pady=5)
        tk.Label(card, text=f"Opção {numero+1}", font=("Segoe UI Semibold", 11), bg=t.PAINEL, fg=t.TEXTO).pack(anchor="w", pady=(0, 7))
        board = Tabuleiro(card, tamanho=176)
        board.pack()
        board.exibir(estado, previa=lance)
        texto = texto_resultado(resultado, estado.vez)
        if lance.capturadas:
            texto = f"Captura {len(lance.capturadas)} peça(s)\n" + texto
        tk.Label(card, text=texto, font=("Segoe UI", 10), bg=t.PAINEL, fg=t.SUAVE, wraplength=210, height=3).pack(pady=(6, 3))
        Botao(card,"Testar esta jogada",lambda l=lance:testar(l),principal=True).pack(fill="x")
    tk.Label(janela, text=rodape, font=("Segoe UI", 9),
             bg=t.FUNDO, fg=t.SUAVE,wraplength=540).pack(pady=10)
    janela.transient(root)
    t.titulo_escuro(janela)
    janela.grab_set()
    janela.bind("<Escape>",lambda _e:janela.destroy())
