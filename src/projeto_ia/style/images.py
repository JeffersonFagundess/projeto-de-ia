"""Ponto único para localizar e carregar imagens da interface."""

import tkinter as tk
from pathlib import Path

PASTA = Path(__file__).parent / "assets" / "images"
PASTA_ICONES = PASTA / "icons"
PASTA_PECAS = PASTA / "pieces"
ICONE_ICO = PASTA / "damas.ico"
ICONE_PNG = PASTA / "damas.png"
TAMANHOS_PECAS = (22, 40, 48)
VARIANTES_ICONES = {
    "adicionar": ("claro", "escuro", "desabilitado"),
    "desfazer": ("claro", "escuro", "desabilitado"),
    "jogar": ("claro", "escuro", "desabilitado"),
    "olho_aberto": ("ciano", "desabilitado"),
    "olho_fechado": ("suave", "desabilitado"),
    "terminal": ("suave",),
}


def carregar_icone(master):
    return tk.PhotoImage(master=master, file=str(ICONE_PNG))


def caminho_peca(cor, tipo, tamanho):
    return PASTA_PECAS / f"{cor}_{tipo}_{tamanho}.png"


def carregar_pecas(master, tamanho):
    """Mantém as referências dos quatro sprites usados por um tabuleiro."""
    imagens = {}
    for cor in ("vermelha", "preta"):
        for tipo in ("peca", "dama"):
            arquivo = caminho_peca(cor, tipo, tamanho)
            if arquivo.is_file():
                imagens[cor, tipo] = tk.PhotoImage(master=master, file=str(arquivo))
    return imagens


def caminho_icone(nome, variante):
    return PASTA_ICONES / f"{nome}_{variante}.png"


def carregar_icone_fa(master, nome, variante):
    return tk.PhotoImage(master=master, file=str(caminho_icone(nome, variante)))


def carregar_variantes_icone(master, nome):
    return {
        variante: carregar_icone_fa(master, nome, variante)
        for variante in VARIANTES_ICONES[nome]
    }
