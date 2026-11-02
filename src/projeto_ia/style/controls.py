"""Controles reutilizáveis com foco, teclado e estados consistentes."""

import tkinter as tk

from projeto_ia.sounds import tocar

from . import palette as p
from .fonts import fonte
from .images import carregar_variantes_icone


def arredondado(canvas, x1, y1, x2, y2, raio=p.RAIO_CONTROLE, **kw):
    return canvas.create_polygon(
        x1+raio,y1, x2-raio,y1, x2,y1, x2,y1+raio,
        x2,y2-raio, x2,y2, x2-raio,y2, x1+raio,y2,
        x1,y2, x1,y2-raio, x1,y1+raio, x1,y1,
        smooth=True, splinesteps=24, **kw,
    )


class Botao(tk.Canvas):
    """Botão acionável por clique, Enter e espaço."""

    def __init__(self, pai, texto, comando, principal=False, largura=140,
                 altura=40, icone=None):
        super().__init__(pai, width=largura, height=altura, bg=pai.cget("bg"),
                         highlightthickness=0, bd=0, takefocus=1, cursor="hand2")
        self.texto, self.comando, self.icone = texto, comando, icone
        self.imagens_icone = carregar_variantes_icone(self, icone) if icone else {}
        self.principal, self.estado, self.sobre = principal, "normal", False
        self.bind("<Configure>", self._desenhar)
        self.bind("<Enter>", lambda _e: self._hover(True))
        self.bind("<Leave>", lambda _e: self._hover(False))
        self.bind("<Button-1>", self._ativar)
        self.bind("<Return>", self._ativar)
        self.bind("<space>", self._ativar)
        self.bind("<FocusIn>", self._desenhar)
        self.bind("<FocusOut>", self._desenhar)

    def configure(self, cnf=None, **kw):
        if isinstance(cnf, dict):
            kw = {**cnf, **kw}
        if "state" in kw:
            self.estado = kw.pop("state")
            super().configure(takefocus=self.estado != "disabled",
                              cursor="hand2" if self.estado != "disabled" else "")
        if "text" in kw:
            self.texto = kw.pop("text")
        if "icon" in kw:
            self.icone = kw.pop("icon")
            self.imagens_icone = carregar_variantes_icone(self, self.icone) if self.icone else {}
        if kw:
            super().configure(**kw)
        self._desenhar()

    config = configure

    def cget(self, chave):
        if chave == "state":
            return self.estado
        if chave == "text":
            return self.texto
        return super().cget(chave)

    def _hover(self, ativo):
        self.sobre = ativo
        self._desenhar()

    def _ativar(self, _evento=None):
        if self.estado != "disabled":
            self.focus_set()
            tocar("clique")
            self.comando()
        return "break"

    def _desenhar(self, _evento=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if self.estado == "disabled":
            fundo, texto, borda = p.ELEVADO, p.DESABILITADO, p.LINHA
        elif self.principal:
            fundo = "#91F5E2" if self.sobre else p.CIANO
            texto, borda = p.FUNDO, fundo
        else:
            fundo = "#223950" if self.sobre else p.ELEVADO
            texto, borda = p.TEXTO, p.LINHA
        if self.focus_get() == self and self.estado != "disabled":
            borda = p.TEXTO
        arredondado(self, 1, 1, w-1, h-1, fill=fundo, outline=borda, width=2)
        if self.icone:
            largura_texto = max(1, len(self.texto)) * 5.8
            inicio = (w - largura_texto - 20) / 2
            variante = "desabilitado" if self.estado == "disabled" else "escuro" if self.principal else "claro"
            self.create_image(inicio+8, h/2, image=self.imagens_icone[variante])
            self.create_text(inicio+20, h/2, text=self.texto, fill=texto,
                             font=fonte(10, True), anchor="w")
        else:
            self.create_text(w/2, h/2, text=self.texto, fill=texto, font=fonte(10, True))


class BotaoOlho(tk.Canvas):
    """Alternador de dica com os ícones oficiais do Font Awesome."""

    def __init__(self, pai, comando, aberto=True):
        super().__init__(pai, width=48, height=30, bg=pai.cget("bg"), bd=0,
                         highlightthickness=0, takefocus=1, cursor="hand2")
        self.comando = comando
        self.aberto = aberto
        self.imagens_icone = {
            nome: carregar_variantes_icone(self, nome)
            for nome in ("olho_aberto", "olho_fechado")
        }
        self.estado = "normal"
        self.sobre = False
        self.bind("<Enter>", lambda _e: self._hover(True))
        self.bind("<Leave>", lambda _e: self._hover(False))
        self.bind("<Button-1>", self._ativar)
        self.bind("<Return>", self._ativar)
        self.bind("<space>", self._ativar)
        self.bind("<FocusIn>", self._desenhar)
        self.bind("<FocusOut>", self._desenhar)
        self.bind("<Configure>", self._desenhar)

    def definir(self, aberto):
        self.aberto = bool(aberto)
        self._desenhar()

    def configure(self, cnf=None, **kw):
        if isinstance(cnf, dict):
            kw = {**cnf, **kw}
        if "state" in kw:
            self.estado = kw.pop("state")
            super().configure(takefocus=self.estado != "disabled",
                              cursor="hand2" if self.estado != "disabled" else "")
        if kw:
            super().configure(**kw)
        self._desenhar()

    config = configure

    def _hover(self, ativo):
        self.sobre = ativo
        self._desenhar()

    def _ativar(self, _evento=None):
        if self.estado != "disabled":
            self.focus_set()
            tocar("alternar")
            self.comando()
        return "break"

    def _desenhar(self, _evento=None):
        self.delete("all")
        borda = p.TEXTO if self.focus_get() == self else p.LINHA
        fundo = "#214052" if self.sobre and self.estado != "disabled" else p.ELEVADO
        arredondado(self, 1, 1, 47, 29, raio=8, fill=fundo, outline=borda, width=1)
        nome = "olho_aberto" if self.aberto else "olho_fechado"
        variante = "desabilitado" if self.estado == "disabled" else "ciano" if self.aberto else "suave"
        self.create_image(24, 15, image=self.imagens_icone[nome][variante])


class Escolha(tk.Frame):
    """Seleção de duas opções visíveis, com API similar à Combobox."""

    def __init__(self, pai, opcoes, largura=125):
        super().__init__(pai, bg=p.FUNDO, padx=3, pady=3,
                         highlightthickness=1, highlightbackground=p.LINHA)
        self.indice = 0
        self.botoes = []
        for indice, opcao in enumerate(opcoes):
            botao = Botao(self, opcao, lambda i=indice: self._escolher(i),
                          largura=largura, altura=32)
            botao.pack(side="left")
            self.botoes.append(botao)
        self.current(0)

    def current(self, indice=None):
        if indice is None:
            return self.indice
        self.indice = indice
        for numero, botao in enumerate(self.botoes):
            botao.principal = numero == indice
            botao._desenhar()

    def _escolher(self, indice):
        if indice != self.indice:
            self.current(indice)
            self.event_generate("<<ComboboxSelected>>")
