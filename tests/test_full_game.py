"""Regras da partida inteira e recomendação de movimentos."""

from projeto_ia.damas.full_game import Jogo, Posicao, inicial, movimentos
from projeto_ia.damas.game import nome_casa
from projeto_ia.damas.opponent import escolher

C = {nome_casa(i): i for i in range(32)}


def test_abertura_tem_24_pecas_e_sete_movimentos():
    estado = inicial()
    assert len(estado.vermelhas) == len(estado.pretas) == 12
    assert not estado.damas and len(movimentos(estado)) == 7
    jogo = Jogo()
    for _ in range(12):
        if jogo.resultado:
            break
        jogo.jogar(jogo.lances[0])
    while jogo.historico:
        jogo.voltar()
    assert jogo.estado == estado and jogo.sem_progresso == 0


def test_peao_coroa_e_para_a_captura():
    estado = Posicao((C['b6'],), tuple(sorted((C['c7'], C['e7']))))
    lance, = movimentos(estado)
    assert lance.caminho == (C['b6'], C['d8'])
    assert lance.proximo.damas == {C['d8']}
    assert lance.proximo.pretas == (C['e7'],)


def test_captura_obrigatoria_multipla_e_vitoria():
    estado = Posicao((C['c3'],), tuple(sorted((C['d4'], C['f6']))))
    lance, = movimentos(estado)
    assert lance.caminho == (C['c3'], C['e5'], C['g7'])
    jogo = Jogo(estado)
    jogo.jogar(lance)
    assert jogo.resultado == 'V'
    jogo.voltar()
    assert jogo.estado == estado


def test_peao_nao_captura_para_tras_mas_dama_sim():
    estado = Posicao((C['e5'],), (C['d4'],))
    assert all(not l.capturadas for l in movimentos(estado))
    dama = Posicao(estado.vermelhas, estado.pretas, 'V', frozenset(estado.vermelhas))
    lance, = movimentos(dama)
    assert lance.caminho == (C['e5'], C['c3'])


def test_empate_repeticao_e_desfazer():
    estado = Posicao((C['a1'],), (C['h8'],), 'V', frozenset((C['a1'],C['h8'])))
    jogo = Jogo(estado)
    for _ in range(2):
        for destino in ('b2','g7','a1','h8'):
            jogo.jogar(next(l for l in jogo.lances if l.caminho[-1] == C[destino]))
    assert jogo.resultado == 'empate'
    jogo.voltar()
    assert jogo.resultado is None


def test_sugestao_legal_e_captura_vencedora():
    assert escolher(inicial(), segundos=.1) in movimentos(inicial())
    estado = Posicao((C['c3'],), (C['d4'],))
    lance = escolher(estado, segundos=.1)
    assert lance.capturadas == (C['d4'],) and not lance.proximo.pretas


def test_empate_sem_progresso_e_reset_por_peao():
    estado = Posicao((C['a1'],), (C['h8'],), 'V', frozenset((C['a1'],C['h8'])))
    jogo = Jogo(estado)
    jogo.sem_progresso = 79
    jogo.jogar(jogo.lances[0])
    assert jogo.resultado == 'empate'
    jogo.voltar()
    assert jogo.sem_progresso == 79
    jogo = Jogo()
    jogo.sem_progresso = 79
    jogo.jogar(jogo.lances[0])
    assert jogo.sem_progresso == 0 and jogo.resultado is None
