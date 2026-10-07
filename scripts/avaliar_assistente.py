"""Partidas contra o computador real da interface, com tempos configuráveis.

python -m scripts.avaliar_assistente --partidas 4
Reproduz a distribuição de tempo da interface. --segundos 1.5 força tempo
igual para comparar os avaliadores; o adversário não tem sua busca reduzida.
"""

import argparse
from collections import Counter
import json
import random
from statistics import mean
from time import monotonic

from projeto_ia.damas.assistant import analisar_turno, tempo_analise, PROFUNDIDADE_MAXIMA
from projeto_ia.damas.full_game import Jogo
from projeto_ia.damas.learning import RAIZ
from projeto_ia.damas.game import nome_casa
from projeto_ia.paths import RELATORIO_DUELO


def executar(partidas=4,segundos=None,semente=20261006,destino=None,max_turnos=240,inicio=0):
    registros=[]
    instante_inicial=monotonic()
    for numero in range(inicio,inicio+partidas):
        lado="V" if numero % 2 == 0 else "P"
        rng=random.Random(semente+numero)
        jogo=Jogo();detalhes=[]
        for turno in range(max_turnos):
            if jogo.resultado:break
            vez=jogo.estado.vez
            orcamento=tempo_analise(jogo.estado,vez == lado) if segundos is None else segundos
            resposta=analisar_turno(jogo.estado,vez == lado,
                                    historico=tuple(e for e,_,_ in jogo.historico),
                                    sem_progresso=jogo.sem_progresso,gerador=rng,segundos=orcamento)
            detalhes.append({"vez":vez,"caminho":[nome_casa(c) for c in resposta.lance.caminho],
                             "nota":resposta.nota,"profundidade":resposta.profundidade,"nos":resposta.nos,
                             "alternativas":resposta.alternativas,"tempo_limite_s":orcamento})
            jogo.jogar(resposta.lance)
            if turno % 20 == 0:
                print(f"Partida {numero-inicio+1}/{partidas} · IA {lado} · turno {turno} · peças {len(jogo.estado.vermelhas)}:{len(jogo.estado.pretas)}",flush=True)
        resultado="inacabada" if jogo.resultado is None else "empate" if jogo.resultado == "empate" else "vitoria" if jogo.resultado == lado else "derrota"
        registros.append({"numero":numero+1,"semente":semente+numero,"assistido":lado,"resultado":resultado,
                          "turnos":len(detalhes),"profundidade_media_ia":mean(d['profundidade'] for d in detalhes if d['vez']==lado),
                          "profundidade_media_computador":mean(d['profundidade'] for d in detalhes if d['vez']!=lado),"jogadas":detalhes})
        print(f"RESULTADO {numero-inicio+1}: {resultado}, {len(detalhes)} turnos",flush=True)
        relatorio={"protocolo":"Mesmo motor para ambos os lados. Posição inicial completa; cores alternadas. Sugestões seguidas em todas as jogadas do lado assistido. A ajuda tem mais tempo nas fases com menos peças; o computador permanece com 1,5 s. --segundos força orçamento igual para uma comparação controlada.",
                   "segundos_por_jogada_iguais_se_forcado":segundos,
                   "tempo_automatico_ajuda":"3 s acima de 16 peças; 4 s entre 9 e 16; 5 s com até 8 peças" if segundos is None else None,
                   "tempo_computador":1.5 if segundos is None else segundos,
                   "profundidade_maxima":PROFUNDIDADE_MAXIMA,"max_turnos":max_turnos,
                   "avaliador_assistido":"Avaliação estratégica + ajuste limitado da rede neural",
                   "adversario":"Computador real da interface; avaliação tradicional de material e avanço",
                   "limites":"Amostra pequena, dependente do tempo e hardware. Não garante vitória; inacabadas são contadas separadamente de empates.",
                   "resumo":dict(Counter(r['resultado'] for r in registros)),"tempo_total_s":round(monotonic()-instante_inicial,2),"partidas":registros}
        arquivo=destino or RELATORIO_DUELO
        arquivo.parent.mkdir(parents=True,exist_ok=True)
        arquivo.write_text(json.dumps(relatorio,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(relatorio['resumo']),flush=True)


if __name__ == '__main__':
    from pathlib import Path
    parser=argparse.ArgumentParser()
    parser.add_argument('--partidas',type=int,default=4)
    parser.add_argument('--segundos',type=float,default=None,help='Força o mesmo tempo por jogada em ambos os lados; omita para reproduzir a interface')
    parser.add_argument('--semente',type=int,default=20261006)
    parser.add_argument('--max-turnos',type=int,default=240)
    parser.add_argument('--inicio',type=int,default=0,help='Índice inicial das partidas; ímpares começam com a ajuda nas pretas')
    parser.add_argument('--destino',type=Path)
    a=parser.parse_args()
    executar(a.partidas,a.segundos,a.semente,a.destino,a.max_turnos,a.inicio)
