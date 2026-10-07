"""Representação compacta para a busca; regras públicas continuam em full_game.

Cada inteiro usa 32 bits, um por casa jogável. As tabelas geométricas evitam
construir conjuntos e objetos de apresentação em cada ramo da análise.
"""

from typing import NamedTuple

from .full_game import Posicao
from .game import CASAS, INDICE

DIRECOES = ((-1,-1),(-1,1),(1,-1),(1,1))
PASSOS = tuple(tuple(INDICE.get((r+dr,c+dc),-1) for dr,dc in DIRECOES) for r,c in CASAS)
SALTOS = tuple(tuple(INDICE.get((r+2*dr,c+2*dc),-1) for dr,dc in DIRECOES) for r,c in CASAS)
TOPO, BASE = 15, 15 << 28


class TabuleiroBusca(NamedTuple):
    vermelhas: int
    pretas: int
    damas: int
    vez: bool


class LanceBusca(NamedTuple):
    proximo: TabuleiroBusca
    origem: int
    destino: int
    capturas: int
    irreversivel: bool


def indices(bits):
    while bits:
        bit = bits & -bits
        yield bit.bit_length()-1
        bits ^= bit


def compactar(estado):
    return TabuleiroBusca(sum(1 << c for c in estado.vermelhas),
                          sum(1 << c for c in estado.pretas),
                          sum(1 << c for c in estado.damas),estado.vez == "V")


def expandir(tab):
    return Posicao(tuple(indices(tab.vermelhas)),tuple(indices(tab.pretas)),
                   "V" if tab.vez else "P",frozenset(indices(tab.damas)))


def gerar(tab):
    nossas,rivais = (tab.vermelhas,tab.pretas) if tab.vez else (tab.pretas,tab.vermelhas)
    if not nossas or not rivais:
        return ()
    finais = TOPO if tab.vez else BASE
    capturas,simples = [],[]
    ocupadas = nossas | rivais
    for origem in indices(nossas):
        bit_origem = 1 << origem
        dama = bool(tab.damas & bit_origem)
        direcoes = range(4) if dama else (0,1) if tab.vez else (2,3)
        outras = nossas ^ bit_origem

        def criar(destino,restantes,quantidade):
            bit_destino = 1 << destino
            removidas = rivais ^ restantes
            reis = (tab.damas & ~(bit_origem | removidas))
            if dama or bit_destino & finais:
                reis |= bit_destino
            a = outras | bit_destino
            novo = TabuleiroBusca(a,restantes,reis,False) if tab.vez else TabuleiroBusca(restantes,a,reis,True)
            return LanceBusca(novo,origem,destino,quantidade,bool(quantidade) or not dama)

        def capturar(atual,restantes,quantidade):
            if quantidade and not dama and (1 << atual) & finais:
                capturas.append(criar(atual,restantes,quantidade))
                return
            encontrou = False
            for d in direcoes:
                meio,destino = PASSOS[atual][d],SALTOS[atual][d]
                if destino < 0 or not restantes & (1 << meio):
                    continue
                bit_destino = 1 << destino
                if (restantes | outras) & bit_destino:
                    continue
                encontrou = True
                capturar(destino,restantes ^ (1 << meio),quantidade+1)
            if quantidade and not encontrou:
                capturas.append(criar(atual,restantes,quantidade))

        capturar(origem,rivais,0)
        if not capturas:
            for d in direcoes:
                destino = PASSOS[origem][d]
                if destino >= 0 and not ocupadas & (1 << destino):
                    simples.append(criar(destino,rivais,0))
    return tuple(capturas or simples)
