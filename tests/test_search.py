"""Regressões táticas, equivalência de regras e diversidade com qualidade."""

import random

import pytest

from projeto_ia.damas.full_game import Jogo, Posicao, inicial, movimentos
from projeto_ia.damas.game import nome_casa
from projeto_ia.damas.opponent import analisar, avaliar
from projeto_ia.damas.search_board import compactar, expandir, gerar
from projeto_ia.damas.strategy import carregar_assistente

C = {nome_casa(i):i for i in range(32)}


def test_busca_compacta_preserva_movimentos_capturas_e_promocoes():
    rng=random.Random(32)
    posicoes=[]
    for _ in range(16):
        jogo=Jogo()
        for _ in range(100):
            if jogo.resultado:break
            posicoes.append(jogo.estado)
            jogo.jogar(rng.choice(jogo.lances))
    # Inclui finais de damas e capturas em todas as direções.
    for _ in range(200):
        casas=rng.sample(range(32),6)
        posicoes.append(Posicao(tuple(sorted(casas[:3])),tuple(sorted(casas[3:])),
                                rng.choice(('V','P')),frozenset(casas)))
    for estado in posicoes:
        assert expandir(compactar(estado)) == estado
        publico={(l.caminho[0],l.caminho[-1],len(l.capturadas),l.proximo) for l in movimentos(estado)}
        compacto={(l.origem,l.destino,l.capturas,expandir(l.proximo)) for l in gerar(compactar(estado))}
        assert compacto == publico


def test_transposicoes_nao_alteram_resultado_da_busca():
    rng=random.Random(71)
    jogo=Jogo()
    for turno in range(40):
        if jogo.resultado:break
        if turno % 5 == 0:
            parametros=dict(segundos=10,profundidade_maxima=3,
                            historico=tuple(e for e,_,_ in jogo.historico),sem_progresso=jogo.sem_progresso)
            com=analisar(jogo.estado,**parametros)
            sem=analisar(jogo.estado,usar_transposicoes=False,**parametros)
            assert com.profundidade == sem.profundidade == 3
            assert com.nota == sem.nota
        jogo.jogar(rng.choice(jogo.lances))


def test_modelo_hibrido_respeita_troca_de_turno():
    avaliador=carregar_assistente()
    estado=inicial()
    inverso=Posicao(estado.vermelhas,estado.pretas,'P',estado.damas)
    assert avaliador(estado) == pytest.approx(-avaliador(inverso))


def test_varia_apenas_entre_jogadas_avaliadas_na_mesma_faixa():
    avaliador=carregar_assistente()
    escolhas=set()
    melhor=analisar(inicial(),segundos=10,profundidade_maxima=3,avaliador=avaliador)
    for semente in range(8):
        resultado=analisar(inicial(),segundos=10,profundidade_maxima=3,avaliador=avaliador,
                           gerador=random.Random(semente),margem=6)
        assert resultado.profundidade == melhor.profundidade == 3
        assert melhor.nota-6 <= resultado.nota <= melhor.nota+1e-8
        escolhas.add(resultado.lance.caminho)
    assert len(escolhas) > 1


def test_variedade_nunca_troca_vitoria_forcada_por_outra_jogada():
    # B2 pode coroar depois; C3 elimina a última peça imediatamente.
    estado=Posicao(tuple(sorted((C['b2'],C['c3']))),(C['d4'],))
    for seed in range(5):
        resultado=analisar(estado,segundos=2,profundidade_maxima=4,
                           avaliador=carregar_assistente(),gerador=random.Random(seed),margem=6)
        assert resultado.lance.capturadas == (C['d4'],)
        assert resultado.nota >= 9900


def test_cancelamento_mantem_jogada_legal_sem_inventar_analise():
    a=analisar(inicial(),cancelado=lambda:True)
    assert a.lance in movimentos(inicial())
    assert a.profundidade == 0 and a.nos == 0


def test_nao_cai_na_captura_que_perde_todas_as_pecas_na_resposta():
    estado=Posicao(tuple(sorted((C['c3'],C['g5']))),
                   tuple(sorted((C['b4'],C['d4'],C['f6'],C['h8']))),
                   damas=frozenset((C['h8'],)))
    armadilha=next(l for l in movimentos(estado) if l.caminho == (C['c3'],C['e5'],C['g7']))
    # Embora capture duas peças agora, o adversário elimina as duas vermelhas.
    resposta=next(l for l in movimentos(armadilha.proximo) if not l.proximo.vermelhas)
    assert len(resposta.capturadas) == 2
    sugestao=analisar(estado,segundos=5,profundidade_maxima=4,avaliador=carregar_assistente())
    assert sugestao.profundidade == 4 or abs(sugestao.nota) >= 9900
    assert sugestao.lance != armadilha


def test_ajuste_aprendido_e_usado_mas_nao_supera_o_limite():
    from projeto_ia.damas.strategy import AvaliadorEstrategico

    class RedeExagerada:
        def __init__(self):self.chamadas=0
        def prever_features(self,x):
            self.chamadas+=1
            return (x[0]-x[8])*100000

    class RedeNeutra:
        def prever_features(self,x):
            return (x[0]-x[8])*100+(x[1]-x[9])*220

    estado=Posicao((C['a1'],C['c3']),(C['h8'],))
    rede=RedeExagerada()
    alterado=AvaliadorEstrategico(rede)(estado)
    referencia=AvaliadorEstrategico(RedeNeutra())(estado)
    assert rede.chamadas == 2
    assert alterado-referencia == pytest.approx(25)


def test_finais_resolvidos_usam_a_base_exata_sem_consultar_a_rede():
    import csv
    from projeto_ia.paths import BASE_FINAIS
    from projeto_ia.damas.endgame_table import avaliacao_exata, carregar_distancias, carregar_finais
    from projeto_ia.damas.search_board import compactar
    from projeto_ia.damas.strategy import AvaliadorEstrategico

    exemplos={}
    with BASE_FINAIS.open(encoding='utf-8',newline='') as arq:
        for linha in csv.DictReader(arq):
            exemplos.setdefault(linha['resultado'],linha)
            if len(exemplos)==3:break
    assert len(carregar_finais()) == 61504
    distancias=carregar_distancias()
    assert len(distancias) == 30976+26252

    class RedeNaoDeveSerUsada:
        def prever_features(self,_):raise AssertionError('Rede consultada em final resolvido')

    assistente=AvaliadorEstrategico(RedeNaoDeveSerUsada())
    for rotulo,linha in exemplos.items():
        vermelhas=tuple(i for i in range(32) if linha[f'c{i+1:02d}']=='v')
        pretas=tuple(i for i in range(32) if linha[f'c{i+1:02d}']=='p')
        estado=Posicao(vermelhas,pretas,linha['vez'],frozenset(vermelhas+pretas))
        chave=(compactar(estado).vermelhas,compactar(estado).pretas,estado.vez=='V')
        esperado=0 if rotulo=='draw' else (1800-distancias[chave] if rotulo=='win' else -1800+distancias[chave])
        assert avaliacao_exata(compactar(estado)) == esperado
        assert assistente(estado) == esperado


def test_final_vencedor_avanca_ate_capturar_em_vez_de_repetir():
    from projeto_ia.damas.assistant import analisar_final_exato
    from projeto_ia.damas.endgame_table import avaliacao_exata

    # Final da partida de regressão que antes ficou repetindo com duas damas
    # vermelhas contra uma preta. Ambos os lados escolhem a melhor resistência.
    jogo=Jogo(Posicao((C['d8'],C['b2']),(C['b8'],),'V',
                    frozenset((C['d8'],C['b2'],C['b8']))))
    notas=[]
    for _ in range(24):
        if jogo.resultado:break
        posicao=compactar(jogo.estado)
        notas.append(abs(avaliacao_exata(posicao)))
        analise=analisar_final_exato(jogo.estado,
                                    tuple(e for e,_,_ in jogo.historico),jogo.sem_progresso)
        assert analise.lance in jogo.lances
        jogo.jogar(analise.lance)
    assert jogo.resultado=='V'
    assert len(jogo.historico) <= 21
    assert notas == sorted(notas)


def test_orcamento_da_ajuda_cresce_sem_reduzir_o_do_computador():
    from projeto_ia.damas.assistant import tempo_analise

    fases=(
        (inicial(),3.0),
        (Posicao(tuple(range(6)),tuple(range(6,12))),4.0),
        (Posicao(tuple(range(4)),tuple(range(4,8))),5.0),
    )
    for estado,esperado in fases:
        assert tempo_analise(estado,True) == esperado
        assert tempo_analise(estado,False) == 1.5
