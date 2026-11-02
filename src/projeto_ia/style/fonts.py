"""Tipografia e localização das fontes locais da interface."""

from pathlib import Path

FAMILIA = "Segoe UI"
FAMILIA_FORTE = "Segoe UI Semibold"
FAMILIA_MONO = "Cascadia Mono"

PASTA_FONTES = Path(__file__).parent / "assets" / "fonts"
FONT_AWESOME = PASTA_FONTES / "font-awesome-7-free-solid-900.otf"
LICENCA_FONT_AWESOME = PASTA_FONTES / "LICENSE-FONT-AWESOME.txt"


def fonte(tamanho=10, forte=False):
    return (FAMILIA_FORTE if forte else FAMILIA, tamanho)


def mono(tamanho=9, forte=False):
    return (FAMILIA_MONO, tamanho, "bold" if forte else "normal")
