"""Dataset próprio de finais de damas, derivado do solucionador exato."""

from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from .game import Estado
from projeto_ia.paths import BASE_FINAIS, RAIZ


COLUNAS_CASAS = tuple(f"c{indice:02d}" for indice in range(1, 33))
COLUNAS_FEATURES = (*COLUNAS_CASAS, "vez")
COLUNAS_DERIVADAS = ("quantidade_vermelhas", "quantidade_pretas", "vantagem_de_pecas")
COLUNAS_MODELO = (*COLUNAS_FEATURES, *COLUNAS_DERIVADAS)
COLUNA_ALVO = "resultado"
CLASSES = ("win", "loss", "draw")
CAMINHO_DADOS = BASE_FINAIS


@dataclass(frozen=True)
class Auditoria:
    registros_originais: int
    registros_utilizados: int
    duplicados_removidos: int
    ausentes: int

    def como_dict(self) -> dict:
        return asdict(self)


def linha_do_estado(estado: Estado) -> dict[str, str]:
    casas = ["v" if indice in estado.vermelhas else "p" if indice in estado.pretas else "b" for indice in range(32)]
    return {**dict(zip(COLUNAS_CASAS, casas)), "vez": estado.vez}


def estado_da_linha(linha) -> Estado:
    vermelhas = tuple(indice for indice, coluna in enumerate(COLUNAS_CASAS) if linha[coluna] == "v")
    pretas = tuple(indice for indice, coluna in enumerate(COLUNAS_CASAS) if linha[coluna] == "p")
    return Estado(vermelhas, pretas, str(linha["vez"]))


def carregar_dados(caminho: Path = CAMINHO_DADOS) -> tuple[pd.DataFrame, Auditoria]:
    if not caminho.is_file():
        raise FileNotFoundError(f"Dataset não encontrado: {caminho}")
    dados = pd.read_csv(caminho, dtype="string")
    if list(dados.columns) != [*COLUNAS_FEATURES, COLUNA_ALVO]:
        raise ValueError("Colunas do CSV de damas fora do padrão esperado.")
    ausentes = int(dados.isna().sum().sum())
    if ausentes:
        raise ValueError(f"O dataset contém {ausentes} valores ausentes.")
    if not all(dados[coluna].isin(["v", "p", "b"]).all() for coluna in COLUNAS_CASAS):
        raise ValueError("As casas devem conter v, p ou b.")
    if not dados["vez"].isin(["V", "P"]).all() or not dados[COLUNA_ALVO].isin(CLASSES).all():
        raise ValueError("Vez ou resultado fora das categorias aceitas.")
    vermelhas = dados[list(COLUNAS_CASAS)].eq("v").sum(axis=1)
    pretas = dados[list(COLUNAS_CASAS)].eq("p").sum(axis=1)
    if not vermelhas.isin([1, 2]).all() or not pretas.isin([1, 2]).all() or not (vermelhas + pretas).le(3).all():
        raise ValueError("Cada posição deve conter uma dama de cada cor e, no máximo, três peças.")
    originais = len(dados)
    dados = dados.drop_duplicates().reset_index(drop=True)
    auditoria = Auditoria(originais, len(dados), originais - len(dados), ausentes)
    return dados, auditoria


def construir_features(dados: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta a contagem de peças, informação visível no tabuleiro."""
    X = dados.loc[:, list(COLUNAS_FEATURES)].copy()
    vermelhas = X[list(COLUNAS_CASAS)].eq("v").sum(axis=1)
    pretas = X[list(COLUNAS_CASAS)].eq("p").sum(axis=1)
    X["quantidade_vermelhas"] = vermelhas.astype(str)
    X["quantidade_pretas"] = pretas.astype(str)
    vantagem = (vermelhas - pretas).where(X["vez"] == "V", pretas - vermelhas)
    X["vantagem_de_pecas"] = vantagem.astype(str)
    return X


def separar_features_target(dados: pd.DataFrame):
    return construir_features(dados), dados[COLUNA_ALVO]
