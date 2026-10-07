"""Busca com aprofundamento, transposições e verificação de capturas completas."""

from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from time import monotonic

from .full_game import movimentos
from .game import CASAS
from .search_board import compactar, expandir, gerar, indices

VITORIA = 10000


def avaliar_compacto(tab):
    total = 0
    for casas,vermelha in ((tab.vermelhas,True),(tab.pretas,False)):
        valor = sum(180 if (1 << c) & tab.damas else 100+(7-CASAS[c][0] if vermelha else CASAS[c][0])*3 for c in indices(casas))
        total += valor if vermelha else -valor
    return total if tab.vez else -total


def avaliar(estado):
    return avaliar_compacto(compactar(estado))


@dataclass(frozen=True)
class Analise:
    lance: object
    nota: float
    profundidade: int
    nos: int
    continuacao: tuple
    alternativas: int = 1


@dataclass(frozen=True, slots=True)
class Registro:
    profundidade: int
    nota: float
    limite: str
    linha: tuple


def analisar(estado, segundos=1.5, profundidade_maxima=12, avaliador=avaliar,
             historico=(), sem_progresso=0, cancelado=lambda: False,
             gerador=None, margem=0, usar_transposicoes=True):
    """Só varia entre alternativas verificadas na mesma profundidade.

    `gerador` permite desempates reproduzíveis. `margem` usa a escala em que um
    peão vale 100; nenhuma aleatoriedade é adicionada às notas da avaliação.
    O contexto de repetições integra a chave do cache, inclusive o relógio de
    empate. Entradas de uma linha diferente não podem esconder um empate.
    """
    tab = compactar(estado)
    gerar_lances = lru_cache(maxsize=20000)(gerar)
    funcao = avaliar_compacto if avaliador is avaliar else getattr(avaliador,"compacto",None)
    if funcao is None:
        funcao = lambda t: avaliador(expandir(t))
    estimar = lru_cache(maxsize=24000)(funcao)
    opcoes = list(gerar_lances(tab))
    if not opcoes:
        return Analise(None,-VITORIA,0,0,())
    if gerador is not None:
        gerador.shuffle(opcoes)
    visitas = Counter(compactar(e) for e in historico)
    visitas[tab] += 1
    tabela, historico_ordem, matadoras = {},Counter(),{}
    fim = monotonic()+max(0,segundos)
    nos = 0

    def guardar_nota(nota,ply):
        return nota+ply if nota >= 9000 else nota-ply if nota <= -9000 else nota

    def ler_nota(nota,ply):
        return nota-ply if nota >= 9000 else nota+ply if nota <= -9000 else nota

    def chave(posicao,progresso,repeticoes):
        contexto = frozenset((p,n) for p,n in repeticoes.items() if p != posicao or n > 1)
        return posicao,progresso,contexto

    def descendente(lance,profundidade,alfa,beta,progresso,ply,repeticoes):
        if lance.irreversivel:
            return busca(lance.proximo,profundidade,alfa,beta,0,ply,{lance.proximo:1})
        novo = lance.proximo
        repeticoes[novo] = repeticoes.get(novo,0)+1
        try:
            return busca(novo,profundidade,alfa,beta,progresso+1,ply,repeticoes)
        finally:
            repeticoes[novo] -= 1
            if not repeticoes[novo]:
                del repeticoes[novo]

    def busca(posicao,profundidade,alfa,beta,progresso,ply,repeticoes):
        nonlocal nos
        nos += 1
        if nos % 64 == 1 and (monotonic() >= fim or cancelado()):
            raise TimeoutError
        lances = gerar_lances(posicao)
        if not lances:
            return -VITORIA+ply,()
        if repeticoes.get(posicao,0) >= 3 or progresso >= 80:
            return 0,()
        if profundidade == 0 and not lances[0].capturas:
            return estimar(posicao),()

        k = chave(posicao,progresso,repeticoes) if usar_transposicoes else None
        anterior = tabela.get(k)
        alfa_original,beta_original = alfa,beta
        favorito = anterior.linha[0] if anterior and anterior.linha else None
        if anterior and anterior.profundidade >= profundidade:
            nota = ler_nota(anterior.nota,ply)
            if anterior.limite == "exato":
                return nota,anterior.linha
            if anterior.limite == "inferior":
                alfa = max(alfa,nota)
            else:
                beta = min(beta,nota)
            if alfa >= beta:
                return nota,anterior.linha

        def ordem(lance):
            return (lance == favorito,lance.capturas,
                    bool((1 << lance.destino) & lance.proximo.damas) and not bool((1 << lance.origem) & posicao.damas),
                    lance == matadoras.get(ply),historico_ordem[posicao.vez,lance.origem,lance.destino])

        valor,linha = -float("inf"),()
        for lance in sorted(lances,key=ordem,reverse=True):
            nota,filhos = descendente(lance,max(0,profundidade-1),-beta,-alfa,progresso,ply+1,repeticoes)
            nota = -nota
            if nota > valor:
                valor,linha = nota,(lance,)+filhos
            alfa = max(alfa,valor)
            if alfa >= beta:
                if not lance.capturas:
                    matadoras[ply] = lance
                    historico_ordem[posicao.vez,lance.origem,lance.destino] += profundidade*profundidade
                break
        if usar_transposicoes and (len(tabela) < 60000 or k in tabela):
            tipo = "superior" if valor <= alfa_original else "inferior" if valor >= beta_original else "exato"
            tabela[k] = Registro(profundidade,guardar_nota(valor,ply),tipo,linha)
        return valor,linha

    melhor,nota_melhor,profundidade_feita,linha_melhor,quantidade = opcoes[0],0,0,(opcoes[0],),1
    for profundidade in range(1,profundidade_maxima+1):
        try:
            notas = []
            alfa = -float("inf")
            for lance in opcoes:
                if monotonic() >= fim or cancelado():
                    raise TimeoutError
                # Descarta cedo opções abaixo da faixa. Só notas exatas entram
                # no sorteio; uma poda igual ao melhor valor não é um empate.
                beta_filho = -alfa + max(margem,1e-7) if gerador is not None else -alfa
                nota,linha = descendente(lance,profundidade-1,-float("inf"),beta_filho,
                                         sem_progresso,1,visitas)
                notas.append((-nota,lance,(lance,)+linha,nota < beta_filho))
                alfa = max(alfa,-nota)
            notas.sort(key=lambda n:n[0],reverse=True)
            topo = notas[0][0]
            candidatas = [n for n in notas if n[3] and n[0] >= topo-max(0,margem)] if gerador is not None and abs(topo) < 9000 else [notas[0]]
            nota_melhor,melhor,linha_melhor,_ = gerador.choice(candidatas) if gerador is not None else notas[0]
            quantidade = len(candidatas)
            profundidade_feita = profundidade
            opcoes = [l for _,l,_,_ in notas]
            if abs(topo) >= 9900:
                break
        except TimeoutError:
            break

    # Converte somente a linha escolhida para objetos usados pela interface.
    linha_publica = []
    atual = estado
    for lance in linha_melhor:
        correspondente = next((l for l in movimentos(atual) if l.caminho[0] == lance.origem
                               and l.caminho[-1] == lance.destino and compactar(l.proximo) == lance.proximo),None)
        if correspondente is None:
            break
        linha_publica.append(correspondente)
        atual = correspondente.proximo
    return Analise(linha_publica[0],nota_melhor,profundidade_feita,nos,tuple(linha_publica),quantidade)


def escolher(estado, segundos=1.5, profundidade_maxima=12, **opcoes):
    return analisar(estado,segundos,profundidade_maxima,**opcoes).lance
