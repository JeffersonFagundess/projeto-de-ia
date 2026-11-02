"""Reprodução nativa de WAVs, sem dependência de áudio em tempo de execução."""

import os
from pathlib import Path

PASTA = Path(__file__).parent / "assets"
LICENCA = PASTA / "LICENSE-KENNEY-CC0.txt"
EFEITOS = {
    "alternar": PASTA / "alternar.wav",
    "clique": PASTA / "clique.wav",
    "dica": PASTA / "dica.wav",
    "derrota": PASTA / "erro.wav",
    "empate": PASTA / "fim.wav",
    "erro": PASTA / "erro.wav",
    "mover": PASTA / "mover.wav",
    "selecionar": PASTA / "selecionar.wav",
    "vitoria": PASTA / "dica.wav",
}

try:
    import winsound
except ImportError:  # pragma: no cover - caminho usado fora do Windows
    winsound = None


def tocar(nome):
    """Inicia um efeito sem aguardar o fim; falhas de áudio não afetam o jogo."""
    arquivo = EFEITOS.get(nome)
    if os.name != "nt" or winsound is None or arquivo is None or not arquivo.is_file():
        return False
    try:
        winsound.PlaySound(
            str(arquivo),
            winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
        )
        return True
    except RuntimeError:
        return False
