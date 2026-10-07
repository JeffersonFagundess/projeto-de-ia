"""Consulta exata aos 61.504 finais já entregues com o projeto."""

import csv
import heapq
from collections import Counter, defaultdict
from functools import lru_cache

from projeto_ia.paths import BASE_FINAIS
from .search_board import TabuleiroBusca, gerar


@lru_cache(maxsize=1)
def carregar_finais():
    tabela = {}
    with BASE_FINAIS.open(encoding="utf-8",newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        colunas = tuple(f"c{i:02d}" for i in range(1,33))
        if tuple(leitor.fieldnames or ()) != (*colunas,"vez","resultado"):
            raise ValueError("Base de finais com colunas inesperadas.")
        for linha in leitor:
            vermelhas = sum(1 << i for i,col in enumerate(colunas) if linha[col] == "v")
            pretas = sum(1 << i for i,col in enumerate(colunas) if linha[col] == "p")
            resultado = linha["resultado"]
            if resultado not in ("win","loss","draw") or linha["vez"] not in ("V","P"):
                raise ValueError("Rótulo inválido na base de finais.")
            tabela[vermelhas,pretas,linha["vez"] == "V"] = resultado
    if len(tabela) != 61504:
        raise ValueError("A base de finais está incompleta ou duplicada.")
    return tabela


@lru_cache(maxsize=1)
def carregar_distancias():
    """Deriva o número de turnos até o desfecho dos rótulos exatos.

    Em uma posição vencedora escolhe o caminho mais curto; em uma perdedora,
    conta a resistência mais longa. Isso evita alternar indefinidamente entre
    posições rotuladas como vitória sem avançar até a captura decisiva.
    """
    rotulos = carregar_finais()
    anteriores = defaultdict(set)
    restantes, maior_filhos, distancias = {}, {}, {}
    pendentes = []

    for chave, rotulo in rotulos.items():
        vermelhas, pretas, vez = chave
        tab = TabuleiroBusca(vermelhas, pretas, vermelhas | pretas, vez)
        lances = gerar(tab)
        destinos = set()
        captura_final = False
        for lance in lances:
            proximo = lance.proximo
            destino = (proximo.vermelhas, proximo.pretas, proximo.vez)
            if destino in rotulos:
                destinos.add(destino)
                anteriores[destino].add(chave)
            elif not proximo.vermelhas or not proximo.pretas:
                captura_final = True
            else:
                raise ValueError("Final saiu da base sem terminar a partida.")
        if not lances:
            if rotulo != "loss":
                raise ValueError("Rótulo terminal contradiz as regras.")
            distancias[chave] = 0
            heapq.heappush(pendentes, (0, chave))
        elif captura_final:
            if rotulo != "win":
                raise ValueError("Captura terminal contradiz o rótulo.")
            distancias[chave] = 1
            heapq.heappush(pendentes, (1, chave))
        elif rotulo == "loss":
            restantes[chave] = len(destinos)
            maior_filhos[chave] = 0

    while pendentes:
        distancia, posicao = heapq.heappop(pendentes)
        for anterior in anteriores[posicao]:
            if anterior in distancias:
                continue
            if rotulos[anterior] == "win" and rotulos[posicao] == "loss":
                distancias[anterior] = distancia + 1
                heapq.heappush(pendentes, (distancia + 1, anterior))
            elif rotulos[anterior] == "loss" and rotulos[posicao] == "win":
                restantes[anterior] -= 1
                maior_filhos[anterior] = max(maior_filhos[anterior], distancia)
                if restantes[anterior] == 0:
                    distancias[anterior] = maior_filhos[anterior] + 1
                    heapq.heappush(pendentes, (distancias[anterior], anterior))

    resolvidos = Counter(rotulos[chave] for chave in distancias)
    esperados = Counter(rotulo for rotulo in rotulos.values() if rotulo != "draw")
    if resolvidos != esperados:
        raise ValueError("Não foi possível determinar a distância de todos os finais decisivos.")
    return distancias


def avaliacao_exata(tab):
    if (tab.vermelhas | tab.pretas).bit_count() > 3:
        return None
    if tab.damas != tab.vermelhas | tab.pretas:
        return None
    chave = (tab.vermelhas,tab.pretas,tab.vez)
    resultado = carregar_finais().get(chave)
    if resultado == "draw":
        return 0
    if resultado is None:
        return None
    distancia = carregar_distancias()[chave]
    return 1800-distancia if resultado == "win" else -1800+distancia
