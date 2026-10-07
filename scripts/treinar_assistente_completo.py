"""Gera posições por partidas legais e treina um avaliador por imitação de busca.

Treino/validação/teste separados por partida; posições equivalentes por troca
de cores e rotação são deduplicadas antes da divisão. Não são partidas humanas.
"""

import argparse
import csv
import json
import random
from pathlib import Path

import numpy as np
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

from projeto_ia.damas.full_game import Jogo, Posicao, movimentos
from projeto_ia.damas.game import CASAS, INDICE
from projeto_ia.damas.learning import RAIZ, NOMES, features, avaliacao_professor, MODELO
from projeto_ia.damas.opponent import analisar, avaliar
from projeto_ia.paths import BASE_COMPLETAS, RELATORIO_COMPLETAS


def chave(estado):
    a = (estado.vermelhas, estado.pretas, estado.vez, tuple(sorted(estado.damas)))
    b = (tuple(sorted(31-c for c in estado.pretas)), tuple(sorted(31-c for c in estado.vermelhas)),
         "P" if estado.vez == "V" else "V", tuple(sorted(31-c for c in estado.damas)))
    return min(a, b)


def gerar(partidas, max_amostras):
    rng = random.Random(2026)
    vistas, linhas = set(), []
    ids = list(range(partidas)); rng.shuffle(ids)
    treino, validacao = set(ids[:int(.64*partidas)]), set(ids[int(.64*partidas):int(.8*partidas)])
    for numero in range(partidas):
        jogo = Jogo()
        grupo = "treino" if numero in treino else "validacao" if numero in validacao else "teste"
        coletadas = []
        for turno in range(150):
            if jogo.resultado:
                break
            estado = jogo.estado
            if turno >= 4 and chave(estado) not in vistas:
                vistas.add(chave(estado))
                coletadas.append((numero, turno, grupo, estado))
            lances = jogo.lances
            if rng.random() < (.35 if numero % 3 else .8):
                lance = rng.choice(lances)
            else:
                notas = [-avaliar(l.proximo)+rng.uniform(-28,28) for l in lances]
                lance = lances[max(range(len(lances)),key=lambda i:notas[i])]
            jogo.jogar(lance)
        if len(coletadas) > max_amostras:
            coletadas = rng.sample(coletadas, max_amostras)
        linhas.extend(coletadas)
    return linhas


def executar(partidas=240, amostras=32, reutilizar=False):
    destino = BASE_COMPLETAS
    registros = None
    if reutilizar:
        with destino.open(encoding='utf-8') as arquivo:
            registros = list(csv.DictReader(arquivo))
        linhas = [(int(r['partida']),int(r['turno']),r['divisao'],
                   Posicao(tuple(map(int,r['vermelhas'].split())),tuple(map(int,r['pretas'].split())),r['vez'],frozenset(map(int,r['damas'].split())))) for r in registros]
    else:
        linhas = gerar(partidas, amostras)
    destino.parent.mkdir(parents=True, exist_ok=True)
    X, y, grupos = [], [], []
    with destino.open('w',newline='',encoding='utf-8') as arq:
        escritor = csv.writer(arq)
        escritor.writerow(['partida','turno','divisao','vermelhas','pretas','damas','vez',*NOMES,'nota_professor'])
        for i,(partida,turno,grupo,estado) in enumerate(linhas):
            if registros is not None:
                nota = float(registros[i]['nota_professor'])
            else:
                analise = analisar(estado, segundos=60, profundidade_maxima=2, avaliador=avaliacao_professor)
                if analise.profundidade < 2 and abs(analise.nota) < 9900:
                    raise RuntimeError('O professor não concluiu a profundidade fixa.')
                nota = float(np.clip(analise.nota,-1600,1600))
            vetor = features(estado)
            X.append(vetor); y.append(nota/400); grupos.append(grupo)
            escritor.writerow([partida,turno,grupo,' '.join(map(str,estado.vermelhas)), ' '.join(map(str,estado.pretas)),
                               ' '.join(map(str,sorted(estado.damas))),estado.vez,*vetor,nota])
            if i % 500 == 0:
                print(f'Rotuladas {i}/{len(linhas)} posições',flush=True)
    X, y, grupos = np.asarray(X), np.asarray(y), np.asarray(grupos)
    masks = {g:grupos == g for g in ('treino','validacao','teste')}
    scaler = StandardScaler().fit(X[masks['treino']])
    dados = scaler.transform(X)
    candidatos = {'ridge':Ridge(alpha=10), 'rede_32':MLPRegressor(hidden_layer_sizes=(32,), max_iter=350,random_state=42,alpha=.1),
                  'rede_48_24':MLPRegressor(hidden_layer_sizes=(48,24),max_iter=350,random_state=42,alpha=.1)}
    validacao = {}
    for nome,modelo in candidatos.items():
        modelo.fit(dados[masks['treino']], y[masks['treino']])
        validacao[nome] = float(mean_absolute_error(y[masks['validacao']]*400,modelo.predict(dados[masks['validacao']])*400))
        print(nome,validacao[nome],flush=True)
    vencedor = min(validacao,key=validacao.get)
    # Artefato é exatamente o modelo escolhido na validação, sem ajuste no teste.
    modelo = candidatos[vencedor]
    predito = modelo.predict(dados[masks['teste']])*400
    verdadeiro = y[masks['teste']]*400
    baseline = DummyRegressor().fit(dados[masks['treino']],y[masks['treino']]*400)
    campos = {'media':scaler.mean_, 'escala':scaler.scale_}
    if isinstance(modelo,Ridge):
        pesos,bias = [modelo.coef_.reshape(-1,1)],[np.array([modelo.intercept_])]
    else:
        pesos,bias = modelo.coefs_,modelo.intercepts_
    campos['camadas'] = len(pesos)
    for i,(w,b) in enumerate(zip(pesos,bias)):campos[f'w{i}']=w;campos[f'b{i}']=b
    MODELO.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(MODELO,**campos)
    metricas = {'origem':'Partidas legais simuladas; rótulos de busca de profundidade 2 com extensão de capturas',
                'registros':len(X),'partidas':partidas,'semente_dados':2026,'semente_modelo':42,'features':list(NOMES),
                'pecas_min':min(len(e.vermelhas)+len(e.pretas) for *_,e in linhas),
                'pecas_max':max(len(e.vermelhas)+len(e.pretas) for *_,e in linhas),
                'divisao':{g:int(m.sum()) for g,m in masks.items()},'validacao_mae':validacao,'modelo_escolhido':vencedor,
                'teste':{'mae':float(mean_absolute_error(verdadeiro,predito)), 'r2':float(r2_score(verdadeiro,predito)),
                         'baseline_mae':float(mean_absolute_error(verdadeiro,baseline.predict(dados[masks['teste']]))),
                         'sinal_correto':float(np.mean(np.sign(predito)==np.sign(verdadeiro)))},
                'limitacao':'Imita uma busca limitada. Nota de vantagem, não probabilidade de vitória nem solução exata.'}
    RELATORIO_COMPLETAS.parent.mkdir(parents=True,exist_ok=True)
    RELATORIO_COMPLETAS.write_text(json.dumps(metricas,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(metricas,ensure_ascii=True),flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--partidas',type=int,default=240)
    parser.add_argument('--amostras',type=int,default=32)
    parser.add_argument('--reutilizar',action='store_true')
    args=parser.parse_args();executar(args.partidas,args.amostras,args.reutilizar)
