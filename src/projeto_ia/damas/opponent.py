"""Busca com aprofundamento, transposições e verificação de capturas completas."""

from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from math import exp
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
    opcoes: tuple = ()
    respostas: tuple = ()


@dataclass(frozen=True)
class OpcaoAnalise:
    lance: object
    nota: float
    confianca: int
    exata: bool = True


@dataclass(frozen=True, slots=True)
class Registro:
    profundidade: int
    nota: float
    limite: str
    linha: tuple


def analisar(estado, segundos=1.5, profundidade_maxima=12, avaliador=avaliar,
             historico=(), sem_progresso=0, cancelado=lambda: False,
             gerador=None, margem=0, usar_transposicoes=True, progresso=None,
             detalhe=None):
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
    profundidade_atual = 0
    ultima_nota = 0
    ultima_linha = ()
    ultimo_pulso = monotonic()
    ultimas_notas = []
    respostas_por_posicao = {}

    def informar(profundidade, nota, linha, alternativas):
        """Publica telemetria sem permitir que a interface afete a busca."""
        if progresso is None:
            return
        dados = {
            "profundidade": profundidade,
            "nota": nota,
            "nos": nos,
            "alternativas": alternativas,
            "linha": tuple((lance.origem, lance.destino) for lance in linha),
            "completo": True,
        }
        try:
            progresso(dados)
        except Exception:  # noqa: BLE001 - callback opcional e externo à busca
            # Telemetria é opcional; falhas de apresentação não mudam a jogada.
            return

    def pulsar():
        """Expõe atividade durante uma profundidade longa sem inundar a UI."""
        nonlocal ultimo_pulso
        if progresso is None:
            return
        agora = monotonic()
        if agora - ultimo_pulso < .12:
            return
        ultimo_pulso = agora
        dados = {
            "profundidade": profundidade_atual,
            "nota": ultima_nota,
            "nos": nos,
            "alternativas": quantidade,
            "linha": tuple((lance.origem, lance.destino) for lance in ultima_linha),
            "completo": False,
        }
        try:
            progresso(dados)
        except Exception:  # noqa: BLE001 - callback opcional e externo à busca
            return

    def guardar_nota(nota,ply):
        return nota+ply if nota >= 9000 else nota-ply if nota <= -9000 else nota

    def ler_nota(nota,ply):
        return nota-ply if nota >= 9000 else nota+ply if nota <= -9000 else nota

    def chave(posicao,progresso,repeticoes):
        contexto = frozenset((p,n) for p,n in repeticoes.items() if p != posicao or n > 1)
        return posicao,progresso,contexto

    def descendente(lance,profundidade,alfa,beta,progresso,ply,repeticoes,pai=0):
        if lance.irreversivel:
            return busca(
                lance.proximo, profundidade, alfa, beta, 0, ply,
                {lance.proximo:1}, pai, lance.origem, lance.destino,
            )
        novo = lance.proximo
        repeticoes[novo] = repeticoes.get(novo,0)+1
        try:
            return busca(
                novo, profundidade, alfa, beta, progresso+1, ply,
                repeticoes, pai, lance.origem, lance.destino,
            )
        finally:
            repeticoes[novo] -= 1
            if not repeticoes[novo]:
                del repeticoes[novo]

    def busca(posicao,profundidade,alfa,beta,progresso,ply,repeticoes,
              pai=0,origem=-1,destino=-1):
        nonlocal nos
        nos += 1
        id_no = nos
        alfa_entrada, beta_entrada = alfa, beta

        def concluir(nota, linha, motivo):
            if detalhe is not None:
                dados = {
                    "id": id_no, "pai": pai, "iteracao": profundidade_atual,
                    "ply": ply, "restante": profundidade,
                    "origem": origem, "destino": destino,
                    "vermelhas": posicao.vermelhas, "pretas": posicao.pretas,
                    "damas": posicao.damas, "vez": posicao.vez,
                    "alfa": alfa_entrada, "beta": beta_entrada,
                    "nota": nota, "motivo": motivo,
                }
                try:
                    detalhe(dados)
                except Exception:  # noqa: BLE001 - observabilidade opcional
                    return nota, linha
            return nota, linha

        if nos % 64 == 1 and (monotonic() >= fim or cancelado()):
            concluir(0, (), "interrompido")
            raise TimeoutError
        if nos % 128 == 1:
            pulsar()
        lances = gerar_lances(posicao)
        if not lances:
            return concluir(-VITORIA+ply,(),"terminal")
        if repeticoes.get(posicao,0) >= 3 or progresso >= 80:
            return concluir(0,(),"empate")
        if profundidade == 0 and not lances[0].capturas:
            return concluir(estimar(posicao),(),"avaliacao")

        k = chave(posicao,progresso,repeticoes) if usar_transposicoes else None
        anterior = tabela.get(k)
        alfa_original,beta_original = alfa,beta
        favorito = anterior.linha[0] if anterior and anterior.linha else None
        if anterior and anterior.profundidade >= profundidade:
            nota = ler_nota(anterior.nota,ply)
            if anterior.limite == "exato":
                return concluir(nota,anterior.linha,"cache")
            if anterior.limite == "inferior":
                alfa = max(alfa,nota)
            else:
                beta = min(beta,nota)
            if alfa >= beta:
                return concluir(nota,anterior.linha,"cache-corte")

        def ordem(lance):
            return (lance == favorito,lance.capturas,
                    bool((1 << lance.destino) & lance.proximo.damas) and not bool((1 << lance.origem) & posicao.damas),
                    lance == matadoras.get(ply),historico_ordem[posicao.vez,lance.origem,lance.destino])

        valor,linha = -float("inf"),()
        respostas_no = [] if ply == 1 else None
        for lance in sorted(lances,key=ordem,reverse=True):
            try:
                nota,filhos = descendente(
                    lance, max(0,profundidade-1), -beta, -alfa,
                    progresso, ply+1, repeticoes, id_no,
                )
            except TimeoutError:
                concluir(
                    0 if valor == -float("inf") else valor,
                    linha,
                    "interrompido",
                )
                raise
            nota = -nota
            if respostas_no is not None:
                respostas_no.append((nota,lance))
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
        if respostas_no is not None:
            # A mesma posição pode reaparecer depois com uma janela estreita e
            # sofrer corte logo na primeira resposta. Preserve a amostra mais
            # completa de cada profundidade para a previsão mostrada na UI. A
            # busca seguinte pode ser interrompida sem apagar o nível pronto.
            chave_respostas = (posicao,profundidade_atual)
            anterior_respostas = respostas_por_posicao.get(chave_respostas)
            if (
                anterior_respostas is None
                or len(respostas_no) > len(anterior_respostas)
            ):
                respostas_por_posicao[chave_respostas] = tuple(respostas_no)
        return concluir(valor,linha,"corte" if alfa >= beta else "expandido")

    _melhor,nota_melhor,profundidade_feita,linha_melhor,quantidade = opcoes[0],0,0,(opcoes[0],),1
    for profundidade in range(1,profundidade_maxima+1):
        profundidade_atual = profundidade
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
            nota_melhor,_melhor,linha_melhor,_ = gerador.choice(candidatas) if gerador is not None else notas[0]
            quantidade = len(candidatas)
            profundidade_feita = profundidade
            ultimas_notas = notas
            opcoes = [l for _,l,_,_ in notas]
            ultima_nota, ultima_linha = nota_melhor, linha_melhor
            informar(profundidade_feita, nota_melhor, linha_melhor, quantidade)
            if abs(topo) >= 9900:
                break
        except TimeoutError:
            break

    def converter(posicao,lance_busca):
        return next((
            lance for lance in movimentos(posicao)
            if lance.caminho[0] == lance_busca.origem
            and lance.caminho[-1] == lance_busca.destino
            and compactar(lance.proximo) == lance_busca.proximo
        ),None)

    def confiancas(valores):
        """Normaliza preferência relativa; não representa chance de vitória."""
        if not valores:
            return ()
        melhor = max(valores)
        pior = min(valores)
        # A avaliação estratégica pode usar escalas diferentes (heurística ou
        # modelo aprendido). Uma temperatura adaptativa mantém a comparação
        # legível sem converter a nota em uma falsa probabilidade de vitória.
        temperatura = max(1.0,min(60.0,(melhor-pior)/2.5))
        pesos = [
            exp(max(-20,min(0,(valor-melhor)/temperatura)))
            for valor in valores
        ]
        total = sum(pesos)
        brutos = [peso*100/total for peso in pesos]
        inteiros = [int(valor) for valor in brutos]
        restantes = 100-sum(inteiros)
        ordem = sorted(
            range(len(brutos)),key=lambda i:brutos[i]-inteiros[i],reverse=True,
        )
        for indice in ordem[:restantes]:
            inteiros[indice] += 1
        return tuple(inteiros)

    # Converte a linha e as alternativas somente depois que a busca termina.
    linha_publica = []
    atual = estado
    for lance in linha_melhor:
        correspondente = converter(atual,lance)
        if correspondente is None:
            break
        linha_publica.append(correspondente)
        atual = correspondente.proximo

    opcoes_convertidas = []
    for nota,lance,_linha,exata in ultimas_notas:
        correspondente = converter(estado,lance)
        if correspondente is not None:
            opcoes_convertidas.append((correspondente,nota,exata))
    if not opcoes_convertidas and linha_publica:
        opcoes_convertidas.append((linha_publica[0],nota_melhor,True))
    percentuais = confiancas([nota for _,nota,_ in opcoes_convertidas])
    opcoes_publicas = tuple(
        OpcaoAnalise(lance,nota,percentual,exata)
        for (lance,nota,exata),percentual in zip(
            opcoes_convertidas,percentuais,strict=True,
        )
    )

    respostas_publicas = ()
    if linha_publica:
        registro = respostas_por_posicao.get((
            compactar(linha_publica[0].proximo),profundidade_feita,
        ))
        if registro is not None:
            convertidas = []
            for nota,lance in registro:
                correspondente = converter(linha_publica[0].proximo,lance)
                if correspondente is not None:
                    convertidas.append((correspondente,nota))
            percentuais = confiancas([nota for _,nota in convertidas])
            respostas_publicas = tuple(
                OpcaoAnalise(lance,nota,percentual)
                for (lance,nota),percentual in zip(
                    convertidas,percentuais,strict=True,
                )
            )
        if not respostas_publicas and len(linha_publica) > 1:
            respostas_publicas = (
                OpcaoAnalise(linha_publica[1],-nota_melhor,100),
            )
    return Analise(
        linha_publica[0],nota_melhor,profundidade_feita,nos,
        tuple(linha_publica),quantidade,opcoes_publicas,respostas_publicas,
    )


def escolher(estado, segundos=1.5, profundidade_maxima=12, **opcoes):
    return analisar(estado,segundos,profundidade_maxima,**opcoes).lance
