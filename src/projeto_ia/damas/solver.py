"""Resolve exaustivamente finais com até três reis, dos dois lados.

Vitória/derrota são relativas a quem joga. Estados que não permitem forçar
um término são classificados como empate (jogo perfeito com repetição).
"""

from collections import defaultdict, deque
from itertools import combinations

from .game import Estado, lances_legais


VITORIA = "win"
DERROTA = "loss"
EMPATE = "draw"


def enumerar_estados() -> set[Estado]:
    """Todas as posições 1V×1P, 2V×1P e 1V×2P, com ambas as vezes."""
    estados: set[Estado] = set()
    for quantidade_vermelhas, quantidade_pretas in ((1, 1), (2, 1), (1, 2)):
        for vermelhas in combinations(range(32), quantidade_vermelhas):
            livres = [casa for casa in range(32) if casa not in vermelhas]
            for pretas in combinations(livres, quantidade_pretas):
                for vez in ("V", "P"):
                    estados.add(Estado(vermelhas, pretas, vez))
    return estados


def resolver() -> dict[Estado, str]:
    """Propaga posições ganhas/perdidas; ciclos restantes são empates."""
    estados = enumerar_estados()
    sucessores: dict[Estado, tuple[Estado, ...]] = {}
    predecessores: dict[Estado, list[Estado]] = defaultdict(list)

    for estado in tuple(estados):
        proximos = tuple(lance.proximo for lance in lances_legais(estado))
        sucessores[estado] = proximos
        for proximo in proximos:
            predecessores[proximo].append(estado)
            if proximo not in estados:
                estados.add(proximo)

    restantes = {estado: len(sucessores.get(estado, ())) for estado in estados}
    valores: dict[Estado, str] = {}
    fila = deque()
    for estado in estados:
        if not restantes[estado]:
            valores[estado] = DERROTA
            fila.append(estado)

    while fila:
        estado = fila.popleft()
        for anterior in predecessores[estado]:
            if anterior in valores:
                continue
            if valores[estado] == DERROTA:
                valores[anterior] = VITORIA
                fila.append(anterior)
            else:
                restantes[anterior] -= 1
                if restantes[anterior] == 0:
                    valores[anterior] = DERROTA
                    fila.append(anterior)

    for estado in estados:
        valores.setdefault(estado, EMPATE)
    return valores


def resultado_do_lance(lance, valores: dict[Estado, str]) -> str:
    """Converte o valor do próximo jogador para o jogador atual."""
    resposta_rival = valores[lance.proximo]
    return {VITORIA: DERROTA, DERROTA: VITORIA, EMPATE: EMPATE}[resposta_rival]
