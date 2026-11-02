"""Predição do modelo e análise exata dos lances legais."""

from pathlib import Path

import joblib
import pandas as pd

from .dataset import COLUNAS_FEATURES, COLUNAS_MODELO, construir_features, linha_do_estado
from .game import Estado, lances_legais
from .modeling import CAMINHO_MODELO
from .solver import DERROTA, EMPATE, VITORIA, resultado_do_lance


def carregar_modelo(caminho: Path = CAMINHO_MODELO) -> dict:
    if not caminho.is_file():
        raise FileNotFoundError(f"Modelo não encontrado: {caminho}. Execute `python -m projeto_ia.damas.train`.")
    artefato = joblib.load(caminho)
    if artefato["colunas"] != list(COLUNAS_MODELO):
        raise ValueError("As colunas do modelo não correspondem ao dataset atual.")
    return artefato


def prever(estado: Estado, artefato: dict) -> str:
    linha = construir_features(pd.DataFrame([linha_do_estado(estado)], columns=COLUNAS_FEATURES))
    return str(artefato["modelo"].predict(linha)[0])


def mapa_respostas(dados: pd.DataFrame) -> dict[Estado, str]:
    respostas = {}
    for valores in dados.itertuples(index=False, name=None):
        casas = valores[:32]
        estado = Estado(
            tuple(indice for indice, valor in enumerate(casas) if valor == "v"),
            tuple(indice for indice, valor in enumerate(casas) if valor == "p"),
            str(valores[32]),
        )
        respostas[estado] = str(valores[33])
    return respostas


def analisar_lances(estado: Estado, respostas: dict[Estado, str]):
    """Lista cada jogada legal e seu resultado exato para a pessoa da vez."""
    resultados = []
    for lance in lances_legais(estado):
        if lance.proximo.vermelhas == () or lance.proximo.pretas == ():
            resposta_rival = DERROTA
        else:
            resposta_rival = respostas[lance.proximo]
        resultado = resultado_do_lance(lance, {lance.proximo: resposta_rival})
        resultados.append((lance, resultado))
    return resultados


def analisar_respostas(lance, respostas: dict[Estado, str]):
    """Todas as respostas legais do rival, vistas pelo jogador inicial."""
    inverter = {VITORIA: DERROTA, DERROTA: VITORIA, EMPATE: EMPATE}
    return [(resposta, inverter[resultado]) for resposta, resultado in analisar_lances(lance.proximo, respostas)]


def explicar(resultado: str, lances: list[tuple]) -> str:
    vencedores = sum(rotulo == VITORIA for _, rotulo in lances)
    empates = sum(rotulo == EMPATE for _, rotulo in lances)
    if resultado == VITORIA:
        return f"Você tem {vencedores} jogada(s) que garantem vitória, mesmo com a melhor resposta do adversário."
    if resultado == DERROTA:
        return "Nenhuma jogada evita a derrota se o adversário responder da melhor forma."
    return f"Não há vitória garantida. {empates} jogada(s) preservam o empate."
