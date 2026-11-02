"""Catálogo único de ícones Font Awesome e desenhos vetoriais de apoio."""

from . import palette as p

GLIFOS = {
    "avancar": "→",
    "brilho": "✦",
    "ponto": "●",
}

ICONES_FONT_AWESOME = {
    "adicionar": "\uf067",
    "analise": "\uf201",
    "aprofundar": "\uf002",
    "desfazer": "\uf2ea",
    "jogar": "\uf04b",
    "lampada": "\uf0eb",
    "olho_aberto": "\uf06e",
    "olho_fechado": "\uf070",
    "percentual": "\uf295",
    "reiniciar": "\uf2f9",
    "terminal": "\uf120",
}

def glifo(nome):
    """Obtém um símbolo sem espalhar caracteres especiais pela interface."""
    return GLIFOS[nome]


def desenhar_marca(canvas):
    """Desenha a marca do jogo sem depender de imagem externa."""
    canvas.create_oval(2, 2, 40, 40, outline="#255753", width=2)
    canvas.create_oval(8, 8, 34, 34, fill=p.CIANO_ESCURO, outline=p.CIANO, width=2)
    canvas.create_polygon(14, 24, 12, 16, 18, 20, 21, 13,
                          24, 20, 30, 16, 28, 24, fill=p.CIANO)
    canvas.create_line(15, 28, 27, 28, fill=p.CIANO, width=2)


def desenhar_peca(canvas, x, y, raio, vermelha, dama=False, tag=None):
    """Fallback vetorial para um tamanho sem sprite pré-renderizado."""
    tags = () if tag is None else (tag,)
    sombra = raio * .10
    canvas.create_oval(x-raio-sombra, y-raio+sombra, x+raio+sombra,
                       y+raio+sombra*2, fill="#07101B", outline="", tags=tags)
    externo = p.CORAL if vermelha else "#496B86"
    interno = "#A92C4A" if vermelha else "#192F43"
    borda = "#FFB5BA" if vermelha else p.PRATA
    canvas.create_oval(x-raio, y-raio, x+raio, y+raio,
                       fill=externo, outline=borda, width=max(2, int(raio*.10)), tags=tags)
    r2 = raio * .78
    canvas.create_oval(x-r2, y-r2, x+r2, y+r2,
                       fill=interno, outline="#F48694" if vermelha else "#6F94AF",
                       width=max(1, int(raio*.07)), tags=tags)
    r3 = raio * .61
    canvas.create_arc(x-r3, y-r3, x+r3, y+r3, start=195, extent=150,
                      style="arc", outline="#FFC2C6" if vermelha else "#9CBBD0",
                      width=max(1, int(raio*.08)), tags=tags)
    if dama:
        pontos = ((-.43,.20),(-.51,-.28),(-.22,-.08),(0,-.43),
                  (.22,-.08),(.51,-.28),(.43,.20))
        canvas.create_polygon(
            *((x+px*r2, y+py*r2) for px, py in pontos),
            fill="#FFF1B9", outline="", tags=tags,
        )
        canvas.create_line(x-r2*.36, y+r2*.34, x+r2*.36, y+r2*.34,
                           fill="#FFF1B9", width=max(2, int(raio*.09)), tags=tags)
    else:
        centro = raio * .11
        canvas.create_oval(x-centro, y-centro, x+centro, y+centro,
                           fill="#FFB0BA" if vermelha else "#96B7CE",
                           outline="", tags=tags)
