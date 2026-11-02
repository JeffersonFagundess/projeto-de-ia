"""Gera todos os finais do estudo e os rótulos exatos a partir das regras."""

import csv

from projeto_ia.damas.dataset import CAMINHO_DADOS, COLUNAS_FEATURES, COLUNA_ALVO, linha_do_estado
from projeto_ia.damas.solver import enumerar_estados, resolver


def main():
    respostas = resolver()
    estados = sorted(enumerar_estados())
    CAMINHO_DADOS.parent.mkdir(parents=True, exist_ok=True)
    with CAMINHO_DADOS.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=[*COLUNAS_FEATURES, COLUNA_ALVO])
        escritor.writeheader()
        for estado in estados:
            escritor.writerow({**linha_do_estado(estado), COLUNA_ALVO: respostas[estado]})
    print(f"{len(estados)} posições gravadas em {CAMINHO_DADOS}")


if __name__ == "__main__":
    main()
