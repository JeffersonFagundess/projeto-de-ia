"""Mede o núcleo da busca antes de qualquer migração para código nativo."""

import argparse
import cProfile
import pstats

from projeto_ia.damas.assistant import analisar_turno
from projeto_ia.damas.full_game import inicial


def main(argv=None):
    parser = argparse.ArgumentParser(description="Perfil da busca da partida inicial")
    parser.add_argument("--segundos", type=float, default=1.0)
    parser.add_argument("--linhas", type=int, default=20)
    opcoes = parser.parse_args(argv)

    perfil = cProfile.Profile()
    perfil.enable()
    analise = analisar_turno(
        inicial(),
        com_ajuda=True,
        segundos=max(.05, opcoes.segundos),
        variar=False,
    )
    perfil.disable()

    print(
        f"Busca: {analise.nos:,} nós; profundidade {analise.profundidade}; "
        f"nota {analise.nota:+.2f}.".replace(",", ".")
    )
    pstats.Stats(perfil).strip_dirs().sort_stats("tottime").print_stats(
        max(5, opcoes.linhas),
    )


if __name__ == "__main__":
    main()
