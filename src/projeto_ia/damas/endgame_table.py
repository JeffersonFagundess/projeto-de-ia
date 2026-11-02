"""Consulta exata aos 61.504 finais já entregues com o projeto."""

import csv
import heapq
from collections import Counter, defaultdict
from functools import lru_cache
from hashlib import sha256

import numpy as np

from projeto_ia.paths import BASE_FINAIS, TABELA_FINAIS

from .search_board import TabuleiroBusca, gerar

CODIGO_RESULTADO = {"loss": -1, "draw": 0, "win": 1}
RESULTADO_CODIGO = {codigo: resultado for resultado, codigo in CODIGO_RESULTADO.items()}


def ler_finais_csv():
    """Lê a fonte auditável; usada por validação e compilação do artefato."""
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


def derivar_distancias(rotulos):
    """Deriva o número de turnos até o desfecho dos rótulos exatos.

    Em uma posição vencedora escolhe o caminho mais curto; em uma perdedora,
    conta a resistência mais longa. Isso evita alternar indefinidamente entre
    posições rotuladas como vitória sem avançar até a captura decisiva.
    """
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


def compilar_finais(destino=TABELA_FINAIS):
    """Compila CSV e distâncias em arrays pequenos e rápidos de carregar."""
    rotulos = ler_finais_csv()
    distancias = derivar_distancias(rotulos)
    linhas = sorted(rotulos)
    resultado = np.asarray(
        [CODIGO_RESULTADO[rotulos[chave]] for chave in linhas], dtype=np.int8,
    )
    distancia = np.asarray(
        [distancias.get(chave, -1) for chave in linhas], dtype=np.int16,
    )
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_suffix(".tmp.npz")
    np.savez_compressed(
        temporario,
        versao=np.asarray([1], dtype=np.uint8),
        sha256_csv=np.asarray([sha256(BASE_FINAIS.read_bytes()).hexdigest()]),
        vermelhas=np.asarray([chave[0] for chave in linhas], dtype=np.uint32),
        pretas=np.asarray([chave[1] for chave in linhas], dtype=np.uint32),
        vez=np.asarray([chave[2] for chave in linhas], dtype=np.bool_),
        resultado=resultado,
        distancia=distancia,
    )
    temporario.replace(destino)
    return destino


@lru_cache(maxsize=1)
def carregar_compacto():
    """Carrega uma vez o artefato imutável usado durante as partidas."""
    if not TABELA_FINAIS.is_file():
        return None
    with np.load(TABELA_FINAIS, allow_pickle=False) as arquivo:
        if arquivo["versao"].tolist() != [1]:
            raise ValueError("Versão incompatível da tabela compacta de finais.")
        dados = tuple(
            arquivo[nome].copy()
            for nome in ("vermelhas", "pretas", "vez", "resultado", "distancia")
        )
    if any(len(coluna) != 61504 for coluna in dados):
        raise ValueError("Tabela compacta de finais incompleta.")
    return dados


@lru_cache(maxsize=1)
def carregar_finais():
    compacto = carregar_compacto()
    if compacto is None:
        return ler_finais_csv()
    vermelhas, pretas, vez, resultados, _distancias = compacto
    return {
        (int(v), int(p), bool(turno)): RESULTADO_CODIGO[int(resultado)]
        for v, p, turno, resultado in zip(
            vermelhas, pretas, vez, resultados, strict=True,
        )
    }


@lru_cache(maxsize=1)
def carregar_distancias():
    compacto = carregar_compacto()
    if compacto is None:
        return derivar_distancias(carregar_finais())
    vermelhas, pretas, vez, _resultados, distancias = compacto
    return {
        (int(v), int(p), bool(turno)): int(distancia)
        for v, p, turno, distancia in zip(
            vermelhas, pretas, vez, distancias, strict=True,
        )
        if distancia >= 0
    }


@lru_cache(maxsize=1)
def carregar_avaliacoes():
    """Materializa somente o mapa usado no laço de avaliação do jogo."""
    compacto = carregar_compacto()
    if compacto is None:
        resultados = carregar_finais()
        distancias = carregar_distancias()
        return {
            chave: (
                0 if resultado == "draw"
                else 1800-distancias[chave] if resultado == "win"
                else -1800+distancias[chave]
            )
            for chave, resultado in resultados.items()
        }
    vermelhas, pretas, vez, resultados, distancias = compacto
    notas = np.where(
        resultados == 0,
        0,
        np.where(resultados > 0, 1800-distancias, -1800+distancias),
    )
    return {
        (int(v), int(p), bool(turno)): int(nota)
        for v, p, turno, nota in zip(vermelhas, pretas, vez, notas, strict=True)
    }


def avaliacao_exata(tab):
    if (tab.vermelhas | tab.pretas).bit_count() > 3:
        return None
    if tab.damas != tab.vermelhas | tab.pretas:
        return None
    chave = (tab.vermelhas,tab.pretas,tab.vez)
    return carregar_avaliacoes().get(chave)
