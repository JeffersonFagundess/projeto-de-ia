"""Ponto único de entrada para as interfaces e modos preservados."""

import argparse
import sys
from pathlib import Path


SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Projeto de IA para jogos")
    parser.add_argument(
        "--modo",
        choices=("jogo", "estudo", "especialista", "terminal"),
        default="jogo",
        help="interface a iniciar (padrão: jogo)",
    )
    modo = parser.parse_args(argv).modo
    try:
        if modo == "jogo":
            from projeto_ia.ui.app import main as iniciar
        elif modo == "estudo":
            from projeto_ia.ui.study import main as iniciar
        elif modo == "especialista":
            from projeto_ia.expert.gui import main as iniciar
        else:
            from projeto_ia.expert.cli import main as iniciar
    except ModuleNotFoundError as erro:
        if modo == "estudo":
            raise SystemExit(
                "O estudo é opcional. Instale-o com: python -m pip install -e \".[study]\""
            ) from erro
        raise
    iniciar()


if __name__ == "__main__":
    main()
