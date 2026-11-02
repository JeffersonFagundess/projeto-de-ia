"""Cartão animado reutilizável para o encerramento de uma partida."""

import tkinter as tk
from typing import ClassVar

from projeto_ia.style import palette as t
from projeto_ia.style.controls import Botao
from projeto_ia.style.fonts import fonte


class AnimacaoResultado:
    """Sobrepõe o tabuleiro sem criar uma nova janela modal."""

    CORES: ClassVar = {
        "vitoria": (t.CIANO, "✦"),
        "derrota": (t.CORAL, "×"),
        "empate": (t.PRATA, "="),
    }

    def __init__(self, canvas):
        self.canvas = canvas
        self.cartao = None
        self.janela_cartao = None
        self.temporizadores = []
        self.particulas = []

    def mostrar(self, tipo, titulo, mensagem, ao_recomecar):
        self.ocultar()
        cor, simbolo = self.CORES[tipo]
        tamanho = int(float(self.canvas.cget("width")))
        centro = tamanho / 2
        self.canvas.create_rectangle(
            0, 0, tamanho, tamanho, fill=t.FUNDO, stipple="gray50",
            outline="", tags="resultado",
        )
        self._criar_particulas(tipo, tamanho, cor)

        self.cartao = tk.Frame(
            self.canvas, width=302, height=202, bg=t.ELEVADO,
            highlightthickness=2, highlightbackground=cor,
        )
        self.cartao.pack_propagate(False)
        tk.Label(
            self.cartao, text=simbolo, bg=t.ELEVADO, fg=cor,
            font=fonte(26, True),
        ).pack(pady=(13, 0))
        tk.Label(
            self.cartao, text=titulo, bg=t.ELEVADO, fg=t.TEXTO,
            font=fonte(19, True),
        ).pack(pady=(0, 4))
        tk.Label(
            self.cartao, text=mensagem, bg=t.ELEVADO, fg=t.SUAVE,
            font=fonte(9), wraplength=260, justify="center",
        ).pack()
        botao = Botao(
            self.cartao, "Jogar novamente", ao_recomecar, principal=True,
            largura=204, altura=36, icone="reiniciar",
        )
        botao.pack(side="bottom", pady=(5, 14))
        self.janela_cartao = self.canvas.create_window(
            centro, tamanho+110, window=self.cartao, width=302, height=202,
            tags="resultado",
        )
        self._entrada(0, tamanho+110, centro, botao)
        self._animar_particulas(tipo, 0)

    def _entrada(self, quadro, inicio, destino, botao):
        progresso = min(1, quadro/12)
        suave = 1-(1-progresso)**3
        y = inicio+(destino-inicio)*suave
        self.canvas.coords(self.janela_cartao, self.canvas.winfo_reqwidth()/2, y)
        if quadro < 12:
            self._agendar(18, self._entrada, quadro+1, inicio, destino, botao)
        else:
            botao.focus_set()

    def _criar_particulas(self, tipo, tamanho, cor):
        for indice in range(18):
            x = 12+(indice*47) % (tamanho-24)
            deslocamento = (indice % 5)-2
            if tipo == "vitoria":
                y = tamanho-8-(indice % 4)*11
                item = self.canvas.create_rectangle(
                    x-2, y-5, x+2, y+5,
                    fill=(cor, "#FFE08A", t.PRATA)[indice % 3],
                    outline="", tags="resultado",
                )
                dy = -2.5-(indice % 4)*.45
            elif tipo == "derrota":
                y = 8+(indice % 5)*9
                item = self.canvas.create_line(
                    x-4, y-4, x+4, y+4, fill=cor, width=2,
                    tags="resultado",
                )
                dy = 1.5+(indice % 4)*.38
            else:
                y = 15+(indice % 6)*55
                item = self.canvas.create_oval(
                    x-2, y-2, x+2, y+2, fill=cor, outline="",
                    tags="resultado",
                )
                dy = .15 if indice % 2 else -.15
            self.particulas.append([item, deslocamento*.12, dy])

    def _animar_particulas(self, tipo, quadro):
        if quadro >= 46:
            return
        for indice, (item, dx, dy) in enumerate(self.particulas):
            self.canvas.move(item, dx, dy)
            if tipo == "vitoria":
                # A desaceleração dá um arco curto aos confetes.
                self.particulas[indice][2] += .065
        self._agendar(36, self._animar_particulas, tipo, quadro+1)

    def _agendar(self, atraso, funcao, *argumentos):
        identificador = self.canvas.after(atraso, funcao, *argumentos)
        self.temporizadores.append(identificador)

    def ocultar(self):
        for identificador in self.temporizadores:
            try:
                self.canvas.after_cancel(identificador)
            except tk.TclError:
                continue
        self.temporizadores.clear()
        if self.cartao is not None:
            self.cartao.destroy()
            self.cartao = None
        self.janela_cartao = None
        self.particulas.clear()
        self.canvas.delete("resultado")
