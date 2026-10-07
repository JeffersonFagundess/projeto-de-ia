"""Valida as duas bases e grava um inventário legível e reproduzível."""

import csv
from collections import Counter, defaultdict
from hashlib import sha256
import json

from projeto_ia.paths import BASE_COMPLETAS, BASE_FINAIS, MANIFESTO_DADOS, RAIZ


def contar_arquivo(caminho):
    digest=sha256()
    with caminho.open('rb') as arquivo:
        for bloco in iter(lambda:arquivo.read(1024*1024),b''):
            digest.update(bloco)
    return digest.hexdigest()


def auditar_finais():
    classes=Counter();chaves=set();colunas=tuple(f'c{i:02d}' for i in range(1,33))
    with BASE_FINAIS.open(encoding='utf-8',newline='') as arquivo:
        leitor=csv.DictReader(arquivo)
        if tuple(leitor.fieldnames or ()) != (*colunas,'vez','resultado'):
            raise ValueError('Colunas da base de finais fora do padrão')
        for numero,linha in enumerate(leitor,2):
            casas=[linha[c] for c in colunas]
            if any(c not in ('v','p','b') for c in casas) or linha['vez'] not in ('V','P') or linha['resultado'] not in ('win','loss','draw'):
                raise ValueError(f'Final inválido na linha {numero}')
            vermelhas,pretas=casas.count('v'),casas.count('p')
            if vermelhas < 1 or pretas < 1 or vermelhas+pretas > 3:
                raise ValueError(f'Número de peças inválido na linha {numero}')
            chave=tuple(casas)+(linha['vez'],)
            if chave in chaves:raise ValueError(f'Final duplicado na linha {numero}')
            chaves.add(chave);classes[linha['resultado']]+=1
    if len(chaves) != 61504:raise ValueError('Base de finais incompleta')
    return {'arquivo':BASE_FINAIS.relative_to(RAIZ).as_posix(),'linhas':len(chaves),
            'sha256':contar_arquivo(BASE_FINAIS),'tarefa':'Classificação exata de finais de até três damas',
            'uso_atual':'Consulta pelo assistente somente quando restam até três damas',
            'classes':dict(sorted(classes.items()))}


def auditar_completas():
    grupos=defaultdict(set);divisao=Counter();chaves=set()
    with BASE_COMPLETAS.open(encoding='utf-8',newline='') as arquivo:
        leitor=csv.DictReader(arquivo)
        obrigatorias={'partida','turno','divisao','vermelhas','pretas','damas','vez','nota_professor'}
        if not obrigatorias <= set(leitor.fieldnames or ()):
            raise ValueError('Faltam colunas da base de partidas completas')
        for numero,linha in enumerate(leitor,2):
            if any(valor is None for valor in linha.values()):raise ValueError(f'Valor ausente na linha {numero}')
            vermelhas=tuple(map(int,linha['vermelhas'].split()))
            pretas=tuple(map(int,linha['pretas'].split()))
            damas=tuple(map(int,linha['damas'].split()))
            casas=vermelhas+pretas
            if len(casas)!=len(set(casas)) or any(c not in range(32) for c in casas) or not set(damas)<=set(casas) or linha['vez'] not in ('V','P'):
                raise ValueError(f'Posição inválida na linha {numero}')
            if linha['divisao'] not in ('treino','validacao','teste') or abs(float(linha['nota_professor'])) > 1600:
                raise ValueError(f'Metadados inválidos na linha {numero}')
            a=(vermelhas,pretas,linha['vez'],damas)
            b=(tuple(sorted(31-c for c in pretas)),tuple(sorted(31-c for c in vermelhas)),
               'P' if linha['vez']=='V' else 'V',tuple(sorted(31-c for c in damas)))
            chave=min(a,b)
            if chave in chaves:raise ValueError(f'Posição equivalente duplicada na linha {numero}')
            chaves.add(chave)
            divisao[linha['divisao']]+=1
            grupos[linha['partida']].add(linha['divisao'])
    if len(chaves) != 7657 or len(grupos) != 240 or any(len(g)!=1 for g in grupos.values()):
        raise ValueError('Divisão das partidas incompleta ou com vazamento')
    return {'arquivo':BASE_COMPLETAS.relative_to(RAIZ).as_posix(),'linhas':len(chaves),
            'sha256':contar_arquivo(BASE_COMPLETAS),'tarefa':'Regressão de vantagem em partidas de 2 a 24 peças',
            'uso_atual':'Treino da rede neural do assistente','partidas':len(grupos),
            'divisao':dict(sorted(divisao.items()))}


def executar(atualizar=False):
    finais=auditar_finais();completas=auditar_completas()
    manifesto={'versao':1,'total_linhas':finais['linhas']+completas['linhas'],
               'observacao':'Bases de tarefas distintas: a soma não é o número de exemplos usados para treinar uma única rede.',
               'bases':{'finais':finais,'partidas_completas':completas}}
    if MANIFESTO_DADOS.exists() and not atualizar:
        anterior=json.loads(MANIFESTO_DADOS.read_text(encoding='utf-8'))
        if anterior != manifesto:
            raise ValueError('As bases não correspondem ao manifesto. Verifique os CSVs ou use --atualizar após uma regeneração intencional.')
    else:
        MANIFESTO_DADOS.write_text(json.dumps(manifesto,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'total_linhas':manifesto['total_linhas'],'finais':finais['linhas'],'partidas_completas':completas['linhas']},ensure_ascii=False))
    return manifesto


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--atualizar',action='store_true',help='Regrava hashes após regenerar intencionalmente as bases')
    executar(parser.parse_args().atualizar)
