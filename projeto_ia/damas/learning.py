"""Avaliação aprendida para partidas completas. Notas não são probabilidades."""

from functools import lru_cache
import numpy as np
from .game import CASAS, INDICE
from .search_board import compactar, indices, PASSOS, SALTOS
from projeto_ia.paths import RAIZ, MODELO_COMPLETAS

MODELO = MODELO_COMPLETAS
NOMES = tuple(f"{lado}_{item}" for lado in ("vez", "rival") for item in (
    "peoes", "damas", "avanco", "centro", "bordas", "retaguarda", "protegidas", "ameacadas",
))


CENTRO = sum(1 << c for c,(r,col) in enumerate(CASAS) if 2 <= r <= 5 and 2 <= col <= 5)
BORDAS = sum(1 << c for c,(_,col) in enumerate(CASAS) if col in (0,7))
VIZINHAS = tuple(sum(1 << v for v in passo if v >= 0) for passo in PASSOS)


def features_compactas(tab):
    ocupadas = tab.vermelhas | tab.pretas
    valores = []
    for vermelha,casas,rivais in ((True,tab.vermelhas,tab.pretas),(False,tab.pretas,tab.vermelhas)):
        peoes = casas & ~tab.damas
        avanco = sum(7-CASAS[c][0] if vermelha else CASAS[c][0] for c in indices(peoes))
        protegidas = sum(bool(VIZINHAS[c] & casas) for c in indices(casas))
        ameacadas = 0
        for c in indices(rivais):
            direcoes = range(4) if (1 << c) & tab.damas else (2,3) if vermelha else (0,1)
            for d in direcoes:
                alvo,destino = PASSOS[c][d],SALTOS[c][d]
                if destino >= 0 and casas & (1 << alvo) and not ocupadas & (1 << destino):
                    ameacadas |= 1 << alvo
        valores.append((peoes.bit_count(),(casas & tab.damas).bit_count(),avanco,
                        (casas & CENTRO).bit_count(),(casas & BORDAS).bit_count(),
                        (casas & (15 << 28 if vermelha else 15)).bit_count(),protegidas,ameacadas.bit_count()))
    a,b = valores if tab.vez else valores[::-1]
    return np.asarray(a+b, dtype=float)


def features(estado):
    return features_compactas(compactar(estado))


def avaliacao_professor(estado):
    x = features(estado)
    return float((x[:8]-x[8:]) @ np.array([100, 180, 3, 6, 2, 4, 3, -16]))


class AvaliadorAprendido:
    def __init__(self, caminho=MODELO):
        with np.load(caminho, allow_pickle=False) as a:
            self.media, self.escala = a["media"], a["escala"]
            self.pesos = [a[f"w{i}"] for i in range(int(a["camadas"]))]
            self.bias = [a[f"b{i}"] for i in range(len(self.pesos))]
        if self.media.shape != (len(NOMES),) or self.escala.shape != self.media.shape:
            raise ValueError("Modelo incompatível com as características da partida.")

    def __call__(self, estado):
        return self.prever_features(features(estado))

    def compacto(self, tab):
        return self.prever_features(features_compactas(tab))

    def prever_features(self, vetor):
        x = (vetor-self.media)/self.escala
        for i, (w, b) in enumerate(zip(self.pesos, self.bias)):
            x = x @ w + b
            if i < len(self.pesos)-1:
                x = np.maximum(x, 0)
        return float(np.clip(x.item()*400, -2500, 2500))


@lru_cache(maxsize=1)
def carregar_avaliador():
    return AvaliadorAprendido()
