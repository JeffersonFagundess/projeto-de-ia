"""Política de ajuda, modelo aprendido, isolamento dos dados e empate na busca."""

import csv
from collections import defaultdict
import numpy as np

from projeto_ia.damas.full_game import inicial, movimentos, Posicao
from projeto_ia.damas.learning import RAIZ, NOMES, features, carregar_avaliador
from projeto_ia.damas.match import Configuracao
from projeto_ia.damas.opponent import analisar
from scripts.treinar_assistente_completo import chave
from projeto_ia.paths import BASE_COMPLETAS


def test_ajuda_apenas_no_lado_designado_em_ambos_os_modos():
    for modo in ('dupla','computador'):
        for lado in ('V','P'):
            config=Configuracao(modo,lado)
            rival='P' if lado == 'V' else 'V'
            assert config.permite_ajuda(lado) and not config.permite_ajuda(rival)
            assert not config.usa_computador(lado)
            assert config.usa_computador(rival) == (modo == 'computador')


def test_busca_usa_avaliador_aprendido_e_devolve_jogada_legal():
    modelo=carregar_avaliador();chamadas=[]
    def registrar(estado):
        chamadas.append(estado)
        return modelo(estado)
    estado=inicial()
    resultado=analisar(estado,segundos=3,profundidade_maxima=2,avaliador=registrar)
    assert resultado.profundidade == 2 and chamadas
    assert resultado.lance in movimentos(estado)
    assert all(np.isfinite(modelo(e)) for e in chamadas)


def test_base_completa_sem_vazamento_de_partidas_ou_posicoes():
    divisao_partidas=defaultdict(set);posicoes=set();contagens=set()
    with BASE_COMPLETAS.open(encoding='utf-8') as arquivo:
        for r in csv.DictReader(arquivo):
            estado=Posicao(tuple(map(int,r['vermelhas'].split())),tuple(map(int,r['pretas'].split())),r['vez'],frozenset(map(int,r['damas'].split())))
            k=chave(estado)
            assert k not in posicoes
            posicoes.add(k);divisao_partidas[r['partida']].add(r['divisao'])
            contagens.add(len(estado.vermelhas)+len(estado.pretas))
            assert np.allclose(features(estado),[float(r[n]) for n in NOMES])
    assert len(posicoes) == 7657 and 24 in contagens and 2 in contagens
    assert all(len(grupos) == 1 for grupos in divisao_partidas.values())


def test_busca_trata_terceira_repeticao_como_empate():
    estado=Posicao((28,),(3,),'V',frozenset((28,3)))
    opcoes=movimentos(estado)
    historico=tuple(l.proximo for l in opcoes for _ in range(2))
    resultado=analisar(estado,segundos=1,profundidade_maxima=2,historico=historico,avaliador=lambda _:999)
    assert resultado.nota == 0
