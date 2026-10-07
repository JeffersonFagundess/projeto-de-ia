"""Tabuleiro clicável e animação dos movimentos, sem notação obrigatória."""

import tkinter as tk
from pathlib import Path

from projeto_ia.damas.game import CASAS, INDICE
from . import theme as t


class Tabuleiro(tk.Canvas):
    def __init__(self, pai, tamanho=352, ao_clicar=None):
        super().__init__(pai, width=tamanho, height=tamanho, bg=t.PAINEL, highlightthickness=0)
        self.passo = tamanho / 8
        self.imagens = {}
        for cor in ("vermelha", "preta"):
            for tipo in ("peca", "dama"):
                arquivo = Path(__file__).parent / "assets" / f"{cor}_{tipo}_{int(self.passo)}.png"
                if arquivo.exists():
                    self.imagens[cor, tipo] = tk.PhotoImage(master=self, file=str(arquivo))
        self.ao_clicar = ao_clicar
        self.temporizador = None
        self.bind("<Button-1>", self._clique)

    def _clique(self, evento):
        casa = INDICE.get((int(evento.y // self.passo), int(evento.x // self.passo)))
        if casa is not None and self.ao_clicar and self.temporizador is None:
            self.ao_clicar(casa)

    def centro(self, casa):
        linha, coluna = CASAS[casa]
        return (coluna + 0.5) * self.passo, (linha + 0.5) * self.passo

    def exibir(self, estado, selecionada=None, destinos=(), caminhos=(), previa=None):
        self.delete("all")
        verdes = {casa for caminho in caminhos for casa in caminho}
        if previa:
            verdes.update(previa.caminho)
        for linha in range(8):
            for coluna in range(8):
                casa = INDICE.get((linha, coluna))
                cor = "#30465B" if (linha + coluna) % 2 == 0 else "#182B3E"
                if casa in verdes or casa in destinos:
                    cor = "#89D6B6"
                x, y = coluna * self.passo, linha * self.passo
                self.create_rectangle(x, y, x + self.passo, y + self.passo, fill=cor, outline=cor)
                if self.passo >= 40:
                    tinta = "#315F50" if casa in verdes or casa in destinos else "#91AABD"
                    if coluna == 0:
                        self.create_text(x+5,y+7,text=str(8-linha),fill=tinta,font=("Segoe UI",7))
                    if linha == 7:
                        self.create_text(x+self.passo-6,y+self.passo-7,text=chr(65+coluna),fill=tinta,font=("Segoe UI",7))
        for casa in destinos:
            x, y = self.centro(casa)
            r = self.passo * .12
            self.create_oval(x-r*1.8, y-r*1.8, x+r*1.8, y+r*1.8, outline="#287B60", width=1)
            self.create_oval(x-r, y-r, x+r, y+r, fill="#195540", outline="")
        for casas, cor in ((estado.vermelhas, "vermelha"), (estado.pretas, "preta")):
            for casa in casas:
                x, y = self.centro(casa)
                r = self.passo * .36
                tag = f"peca_{casa}"
                dama = casa in getattr(estado, "damas", set(estado.vermelhas + estado.pretas))
                imagem = self.imagens.get((cor, "dama" if dama else "peca"))
                if imagem:
                    self.create_image(x, y, image=imagem, tags=tag)
                else:
                    self.create_oval(x-r,y-r,x+r,y+r,fill=t.CORAL if cor == "vermelha" else "#263D53",outline=t.PRATA,width=2,tags=tag)
                    if dama:self.create_text(x,y,text="♛",fill="#FFF1B9",font=("Segoe UI",max(9,int(self.passo*.38))),tags=tag)
                if casa == selecionada:
                    self.create_oval(x-r-3, y-r-3, x+r+3, y+r+3, outline=t.CIANO, width=3)
        if previa:
            pontos = [coordenada for casa in previa.caminho for coordenada in self.centro(casa)]
            self.create_line(*pontos, fill="#0C443C", width=max(5,self.passo*.13), arrow=tk.LAST,arrowshape=(14,17,7),joinstyle="round")
            self.create_line(*pontos, fill="#A5FFCF", width=max(2,self.passo*.055), arrow=tk.LAST,arrowshape=(10,12,4),joinstyle="round")

    def cancelar(self):
        if self.temporizador is not None:
            self.after_cancel(self.temporizador)
            self.temporizador = None

    def animar(self, estado, lance, ao_terminar):
        self.cancelar()
        self.exibir(estado, caminhos=(lance.caminho,))
        tag = f"peca_{lance.caminho[0]}"
        segmentos = list(zip(lance.caminho, lance.caminho[1:]))

        def quadro(segmento=0, passo=0):
            origem, destino = segmentos[segmento]
            x1, y1 = self.centro(origem)
            x2, y2 = self.centro(destino)
            self.move(tag, (x2-x1)/12, (y2-y1)/12)
            passo += 1
            if passo == 12:
                if lance.capturadas:
                    self.delete(f"peca_{lance.capturadas[segmento]}")
                segmento, passo = segmento + 1, 0
            if segmento == len(segmentos):
                self.temporizador = None
                ao_terminar()
            else:
                self.temporizador = self.after(28, quadro, segmento, passo)

        self.temporizador = self.after(150, quadro)
