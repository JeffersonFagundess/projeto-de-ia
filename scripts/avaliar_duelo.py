"""Ensaio automatizado, sem representar o desempenho contra pessoas."""

import json
import random
from collections import Counter

from projeto_ia.damas.full_game import Jogo
from projeto_ia.damas.learning import RAIZ, carregar_avaliador
from projeto_ia.damas.opponent import analisar, avaliar
from projeto_ia.paths import RAIZ


def executar():
    modelo=carregar_avaliador()
    detalhes=[]
    for politica in ('aleatorio','material'):
        for partida in range(12):
            rng=random.Random(20261004+partida)
            assistido='V' if partida % 2 == 0 else 'P'
            jogo=Jogo()
            # Aberturas variadas, as mesmas sementes para as duas políticas.
            for _ in range(4):jogo.jogar(rng.choice(jogo.lances))
            for _ in range(160):
                if jogo.resultado:break
                if jogo.estado.vez == assistido:
                    lance=analisar(jogo.estado,segundos=.05,profundidade_maxima=4,avaliador=modelo,
                                   historico=tuple(e for e,_,_ in jogo.historico),sem_progresso=jogo.sem_progresso).lance
                elif politica == 'aleatorio':lance=rng.choice(jogo.lances)
                else:
                    notas=[-avaliar(l.proximo)+rng.uniform(-.1,.1) for l in jogo.lances]
                    lance=jogo.lances[max(range(len(notas)),key=notas.__getitem__)]
                jogo.jogar(lance)
            resultado='inacabada' if jogo.resultado is None else 'empate' if jogo.resultado == 'empate' else 'vitoria' if jogo.resultado == assistido else 'derrota'
            detalhes.append({'politica':politica,'partida':partida,'assistido':assistido,'resultado':resultado,'turnos':len(jogo.historico)})
            print(politica,partida,resultado,flush=True)
    resumo={p:dict(Counter(r['resultado'] for r in detalhes if r['politica'] == p)) for p in ('aleatorio','material')}
    registro={'protocolo':'12 partidas por política, cores alternadas, 4 lances iniciais aleatórios, até 160 lances adicionais; ML+busca com 50 ms e profundidade máxima 4',
              'semente':20261004,'limites':'Ensaio pequeno contra programas simples; tempo limitado torna o resultado dependente do hardware. Não estima vitória contra humanos nem isola o efeito do ML da busca.',
              'resumo':resumo,'partidas':detalhes}
    destino=RAIZ/'reports/partidas_completas/duelo_simulado.json'
    destino.parent.mkdir(parents=True,exist_ok=True)
    destino.write_text(json.dumps(registro,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(resumo),flush=True)


if __name__ == '__main__':executar()
