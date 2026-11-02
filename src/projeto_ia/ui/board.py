"""Tabuleiro clicável e animação dos movimentos, sem notação obrigatória."""

import tkinter as tk
from math import cos, pi

from projeto_ia.damas.game import CASAS, INDICE
from projeto_ia.style import palette as t
from projeto_ia.style.fonts import fonte
from projeto_ia.style.icons import desenhar_peca
from projeto_ia.style.images import carregar_pecas

from .result_overlay import AnimacaoResultado


class Tabuleiro(tk.Canvas):
    def __init__(self, pai, tamanho=352, ao_clicar=None):
        super().__init__(pai, width=tamanho, height=tamanho, bg=t.PAINEL, highlightthickness=0)
        self.passo = tamanho / 8
        self.imagens = carregar_pecas(self, round(self.passo))
        self.ao_clicar = ao_clicar
        self.temporizador = None
        self.temporizador_previa = None
        self.fase_previa = 0
        self.casa_origem = None
        self.casa_previa = None
        self.casa_resposta = None
        self.cores_casas = {}
        self.dicas_casas = {}
        self.casa_sobre = None
        self.temporizador_dica = None
        self.janela_dica = None
        self.resultado = AnimacaoResultado(self)
        self.bind("<Button-1>", self._clique)
        self.bind("<Motion>", self._movimento_mouse)
        self.bind("<B1-Motion>", self._movimento_mouse)
        self.bind("<Leave>", lambda _evento: self._ocultar_dica())

    def _clique(self, evento):
        casa = INDICE.get((int(evento.y // self.passo), int(evento.x // self.passo)))
        if casa is not None and self.ao_clicar and self.temporizador is None:
            self.ao_clicar(casa)

    def centro(self, casa):
        linha, coluna = CASAS[casa]
        return (coluna + 0.5) * self.passo, (linha + 0.5) * self.passo

    def exibir(self, estado, selecionada=None, destinos=(), caminhos=(),
               previa=None, percentuais=None, resposta=None,
               percentual_resposta=None, explicacoes=None):
        self._cancelar_previa()
        self.resultado.ocultar()
        self.delete("all")
        self.dicas_casas = explicacoes or {}
        self.cores_casas = {}
        verdes = {casa for caminho in caminhos for casa in caminho}
        for linha in range(8):
            for coluna in range(8):
                casa = INDICE.get((linha, coluna))
                cor = t.TABULEIRO_CLARO if (linha + coluna) % 2 == 0 else t.TABULEIRO_ESCURO
                if casa in verdes or casa in destinos:
                    cor = t.TABULEIRO_DESTINO
                if casa is not None:
                    self.cores_casas[casa] = cor
                x, y = coluna * self.passo, linha * self.passo
                self.create_rectangle(
                    x,y,x+self.passo,y+self.passo,fill=cor,outline=cor,
                    tags=("casa",f"casa_{casa}") if casa is not None else "casa",
                )
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
                    desenhar_peca(self,x,y,r,cor == "vermelha",dama,tag)
                if casa == selecionada:
                    self.create_oval(x-r-3, y-r-3, x+r+3, y+r+3, outline=t.CIANO, width=3)
        self.casa_origem = previa.caminho[0] if previa else None
        self.casa_previa = previa.caminho[-1] if previa else None
        self.casa_resposta = resposta.caminho[-1] if resposta else None
        if self.casa_origem is not None:
            self._desenhar_origem(self.casa_origem)
        if self.casa_previa is not None:
            self._desenhar_pulso(self.casa_previa,principal=True)
        if self.casa_resposta is not None:
            self._desenhar_pulso(self.casa_resposta,principal=False)
        for casa,percentual in (percentuais or {}).items():
            self._desenhar_percentual(casa,percentual,t.CIANO,"superior")
        if resposta and percentual_resposta is not None:
            self._desenhar_percentual(
                resposta.caminho[-1],percentual_resposta,t.CORAL,"inferior",
            )
        if previa:
            self._animar_previa()

    def _desenhar_origem(self, casa):
        x,y = self.centro(casa)
        raio = self.passo*.41
        self.create_oval(
            x-raio,y-raio,x+raio,y+raio,outline="#A5FFCF",width=2,
            tags=("indicador_previa","pulso_origem","pulso_origem_externo"),
        )
        raio -= 4
        self.create_oval(
            x-raio,y-raio,x+raio,y+raio,outline="#4EAE9E",width=1,
            tags=("indicador_previa","pulso_origem","pulso_origem_interno"),
        )

    def _desenhar_pulso(self, casa, principal):
        linha,coluna = CASAS[casa]
        x1,y1 = coluna*self.passo,linha*self.passo
        x2,y2 = x1+self.passo,y1+self.passo
        cor = "#A5FFCF" if principal else "#FF9AA5"
        tipo = "principal" if principal else "resposta"
        self.create_rectangle(
            x1+2,y1+2,x2-2,y2-2,outline=cor,width=2,
            dash=None if principal else (4,3),
            tags=("indicador_previa",f"pulso_{tipo}",f"pulso_{tipo}_externo"),
        )
        self.create_rectangle(
            x1+6,y1+6,x2-6,y2-6,outline=cor,width=1,
            tags=("indicador_previa",f"pulso_{tipo}",f"pulso_{tipo}_interno"),
        )

    def _desenhar_percentual(self, casa, percentual, cor, posicao):
        linha,coluna = CASAS[casa]
        direita = (coluna+1)*self.passo-3
        topo = linha*self.passo+(3 if posicao == "superior" else self.passo-20)
        esquerda = direita-34
        self.create_rectangle(
            esquerda,topo,direita,topo+17,fill=t.TERMINAL,
            outline=cor,width=1,tags="indicador_previa",
        )
        self.create_text(
            direita-4,topo+8,text=f"{percentual}%",fill=cor,
            font=fonte(7,True),anchor="e",tags="indicador_previa",
        )

    def _animar_previa(self):
        self.fase_previa = (self.fase_previa+1) % 32
        pulso = (1-cos(2*pi*self.fase_previa/32))/2
        if self.casa_origem is not None:
            fundo = self.cores_casas[self.casa_origem]
            self.itemconfigure(
                f"casa_{self.casa_origem}",
                fill=self._misturar(fundo,"#67E8D2",.06+pulso*.06),
            )
            self.itemconfigure("pulso_origem_externo",width=1+round(2*pulso))
        if self.casa_previa is not None:
            fundo = self.cores_casas[self.casa_previa]
            self.itemconfigure(
                f"casa_{self.casa_previa}",
                fill=self._misturar(fundo,"#A5FFCF",.18+pulso*.14),
            )
            self.itemconfigure("pulso_principal_externo",width=1+round(2*pulso))
            self.itemconfigure("pulso_principal_interno",width=1+round(pulso))
        if self.casa_resposta is not None:
            fundo = self.cores_casas[self.casa_resposta]
            self.itemconfigure(
                f"casa_{self.casa_resposta}",
                fill=self._misturar(fundo,"#FF7485",.10+pulso*.10),
            )
            self.itemconfigure("pulso_resposta_externo",width=1+round(2*pulso))
        self.temporizador_previa = self.after(55,self._animar_previa)

    def _movimento_mouse(self, evento):
        casa = INDICE.get((int(evento.y//self.passo),int(evento.x//self.passo)))
        if casa == self.casa_sobre:
            return
        self._ocultar_dica(limpar_casa=False)
        self.casa_sobre = casa
        texto = self.dicas_casas.get(casa)
        if texto:
            self.temporizador_dica = self.after(
                350,self._mostrar_dica,texto,evento.x_root,evento.y_root,
            )

    def _mostrar_dica(self, texto, x, y):
        self.temporizador_dica = None
        self.janela_dica = tk.Toplevel(self)
        self.janela_dica.overrideredirect(True)
        self.janela_dica.attributes("-topmost",True)
        tk.Label(
            self.janela_dica,text=texto,bg="#223950",fg=t.TEXTO,
            font=fonte(9),padx=10,pady=8,justify="left",anchor="w",
            wraplength=330,
        ).pack()
        self.janela_dica.update_idletasks()
        largura = self.janela_dica.winfo_reqwidth()
        altura = self.janela_dica.winfo_reqheight()
        esquerda = min(x+14,self.winfo_screenwidth()-largura-8)
        topo = min(y+18,self.winfo_screenheight()-altura-8)
        self.janela_dica.geometry(f"+{max(8,esquerda)}+{max(8,topo)}")

    def _ocultar_dica(self, limpar_casa=True):
        if self.temporizador_dica is not None:
            self.after_cancel(self.temporizador_dica)
            self.temporizador_dica = None
        if self.janela_dica is not None:
            self.janela_dica.destroy()
            self.janela_dica = None
        if limpar_casa:
            self.casa_sobre = None

    @staticmethod
    def _misturar(inicio, fim, proporcao):
        canais = []
        for indice in (1,3,5):
            a = int(inicio[indice:indice+2],16)
            b = int(fim[indice:indice+2],16)
            canais.append(round(a+(b-a)*proporcao))
        return "#"+"".join(f"{canal:02X}" for canal in canais)

    def _cancelar_previa(self):
        self._ocultar_dica()
        if self.temporizador_previa is not None:
            self.after_cancel(self.temporizador_previa)
            self.temporizador_previa = None
        self.casa_origem = None
        self.casa_previa = None
        self.casa_resposta = None

    def cancelar(self):
        self._cancelar_previa()
        if self.temporizador is not None:
            self.after_cancel(self.temporizador)
            self.temporizador = None
        self.resultado.ocultar()

    def mostrar_resultado(self, tipo, titulo, mensagem, ao_recomecar):
        self.resultado.mostrar(tipo, titulo, mensagem, ao_recomecar)

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
