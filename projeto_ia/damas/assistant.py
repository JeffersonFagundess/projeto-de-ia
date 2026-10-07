"""Configuração única usada pelo jogo e pelo ensaio contra o computador."""

import random
from collections import Counter

from .opponent import Analise, analisar, avaliar
from .strategy import carregar_assistente
from .endgame_table import avaliacao_exata, carregar_finais, carregar_distancias
from .full_game import movimentos
from .search_board import compactar

TEMPO_COMPUTADOR = 1.5
PROFUNDIDADE_MAXIMA = 12


def analisar_final_exato(estado, historico=(), sem_progresso=0):
    """Segue a vitória mais curta ou prolonga a derrota na tabela de finais."""
    atual = compactar(estado)
    if avaliacao_exata(atual) is None:
        return None
    carregar_distancias()
    visitas = Counter(compactar(anterior) for anterior in historico)
    visitas[atual] += 1

    def nota(lance, relogio, anteriores):
        proximo = lance.proximo
        if not movimentos(proximo):
            return 10000
        tab = compactar(proximo)
        novo_relogio = 0 if lance.capturadas else relogio + 1
        if novo_relogio >= 80 or anteriores[tab] >= 2:
            return 0
        valor = avaliacao_exata(tab)
        if valor is None:
            raise ValueError("A jogada saiu da base de finais resolvidos.")
        return -valor

    opcoes = movimentos(estado)
    if not opcoes:
        return Analise(None,-10000,0,0,())
    lance = max(opcoes,key=lambda opcao:nota(opcao,sem_progresso,visitas))
    valor = nota(lance,sem_progresso,visitas)
    linha = [lance]
    if valor != 10000 and valor != 0:
        visitas[compactar(lance.proximo)] += 1
        relogio = 0 if lance.capturadas else sem_progresso + 1
        respostas = movimentos(lance.proximo)
        if respostas:
            linha.append(max(respostas,key=lambda opcao:nota(opcao,relogio,visitas)))
    return Analise(lance,valor,0,len(opcoes),tuple(linha))


def tempo_analise(estado,com_ajuda):
    """Amplia a análise nos trechos em que cada erro custa mais peças."""
    if not com_ajuda:
        return TEMPO_COMPUTADOR
    pecas=len(estado.vermelhas)+len(estado.pretas)
    return 3.0 if pecas > 16 else 4.0 if pecas > 8 else 5.0


def analisar_turno(estado, com_ajuda, historico=(), sem_progresso=0,
                   cancelado=lambda:False, gerador=None,
                   segundos=None, profundidade_maxima=PROFUNDIDADE_MAXIMA,
                   variar=True):
    abertura = variar and len(historico) < 8
    if com_ajuda and (len(estado.vermelhas)+len(estado.pretas) <= 7):
        carregar_finais()
    if com_ajuda and len(estado.vermelhas)+len(estado.pretas) <= 3 and len(estado.damas) == len(estado.vermelhas)+len(estado.pretas):
        final = analisar_final_exato(estado,historico,sem_progresso)
        if final is not None:
            return final
    return analisar(estado,segundos=tempo_analise(estado,com_ajuda) if segundos is None else segundos,
                    profundidade_maxima=profundidade_maxima,
                    avaliador=carregar_assistente() if com_ajuda else avaliar,
                    historico=historico,sem_progresso=sem_progresso,cancelado=cancelado,
                    gerador=(gerador or random.Random()) if abertura else None,
                    margem=6 if abertura and com_ajuda else 0)
