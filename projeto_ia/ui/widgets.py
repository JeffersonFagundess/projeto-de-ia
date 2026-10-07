"""Controles de apresentação com foco de teclado, estados e cores consistentes."""

import tkinter as tk

from . import theme as t


def arredondado(canvas, x1, y1, x2, y2, raio=10, **kw):
    return canvas.create_polygon(
        x1+raio,y1, x2-raio,y1, x2,y1, x2,y1+raio,
        x2,y2-raio, x2,y2, x2-raio,y2, x1+raio,y2,
        x1,y2, x1,y2-raio, x1,y1+raio, x1,y1,
        smooth=True, splinesteps=24, **kw,
    )


class Botao(tk.Canvas):
    """Botão arredondado acionável por clique, Enter e espaço."""

    def __init__(self, pai, texto, comando, principal=False, largura=140, altura=40):
        super().__init__(pai, width=largura, height=altura, bg=pai.cget("bg"),
                         highlightthickness=0, bd=0, takefocus=1, cursor="hand2")
        self.texto, self.comando = texto, comando
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
            self.comando()
        return "break"

    def _desenhar(self, _evento=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if self.estado == "disabled":
            fundo, texto, borda = t.ELEVADO, t.DESABILITADO, t.LINHA
        elif self.principal:
            fundo = "#91F5E2" if self.sobre else t.CIANO
            texto, borda = t.FUNDO, fundo
        else:
            fundo = "#223950" if self.sobre else t.ELEVADO
            texto, borda = t.TEXTO, t.LINHA
        if self.focus_get() == self and self.estado != "disabled":
            borda = t.TEXTO
        arredondado(self, 1, 1, w-1, h-1, fill=fundo, outline=borda, width=2)
        self.create_text(w/2, h/2, text=self.texto, fill=texto,
                         font=("Segoe UI Semibold", 10))


class Escolha(tk.Frame):
    """Seleção de duas opções visíveis, com API current igual à combobox."""

    def __init__(self, pai, opcoes, largura=125):
        super().__init__(pai, bg=t.FUNDO, padx=3, pady=3,
                         highlightthickness=1, highlightbackground=t.LINHA)
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


def mostrar_informacao(root, titulo, texto):
    janela = tk.Toplevel(root)
    janela.withdraw()
    janela.title(titulo)
    janela.configure(bg=t.PAINEL)
    janela.resizable(False, False)
    janela.transient(root)
    tk.Label(janela, text=titulo, bg=t.PAINEL, fg=t.TEXTO,
             font=("Segoe UI Semibold", 19)).pack(anchor="w", padx=26, pady=(24, 16))
    tk.Frame(janela, height=2, bg=t.CIANO).pack(fill="x", padx=26)
    tk.Label(janela, text=texto, bg=t.PAINEL, fg=t.SUAVE, font=("Segoe UI", 11),
             wraplength=490, justify="left").pack(anchor="w", padx=26, pady=20)
    fechar = Botao(janela, "Entendi", janela.destroy, principal=True)
    fechar.pack(fill="x", padx=26, pady=(0, 24))
    janela.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width()-janela.winfo_reqwidth())//2
    y = root.winfo_rooty() + max(0, (root.winfo_height()-janela.winfo_reqheight())//2)
    janela.geometry(f"+{max(0,x)}+{max(0,y)}")
    janela.deiconify()
    t.titulo_escuro(janela)
    janela.grab_set()
    fechar.focus_set()
    janela.bind("<Escape>", lambda _e: janela.destroy())
    return janela
