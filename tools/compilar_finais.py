"""Compila a base auditável de finais para o formato usado pelo jogo."""

from time import perf_counter

from projeto_ia.damas.endgame_table import compilar_finais


def main():
    inicio = perf_counter()
    destino = compilar_finais()
    tamanho = destino.stat().st_size / 1024
    print(
        f"Tabela compacta criada em {destino} "
        f"({tamanho:.1f} KiB, {perf_counter()-inicio:.2f} s)."
    )


if __name__ == "__main__":
    main()
