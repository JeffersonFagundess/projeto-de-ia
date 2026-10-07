"""Treino e teste do classificador de finais de damas."""

import json
from collections import defaultdict
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder

from .dataset import (
    CAMINHO_DADOS,
    CLASSES,
    COLUNAS_MODELO,
    RAIZ,
    carregar_dados,
    estado_da_linha,
    separar_features_target,
)
from .game import CASAS, INDICE, Estado
from projeto_ia.paths import MODELO_FINAIS, RELATORIO_FINAIS


SEMENTE = 42
CAMINHO_MODELO = MODELO_FINAIS
CAMINHO_METRICAS = RELATORIO_FINAIS


def chave_simetria(estado: Estado) -> tuple:
    """Agrupa rotações/reflexões e a troca das cores dos reis."""
    transformacoes = (
        lambda r, c: (r, c),
        lambda r, c: (7 - r, 7 - c),
        lambda r, c: (c, r),
        lambda r, c: (7 - c, 7 - r),
    )
    variantes = []
    for transformar in transformacoes:
        vermelhas = tuple(sorted(INDICE[transformar(*CASAS[casa])] for casa in estado.vermelhas))
        pretas = tuple(sorted(INDICE[transformar(*CASAS[casa])] for casa in estado.pretas))
        variantes.append((vermelhas, pretas, estado.vez))
        variantes.append((pretas, vermelhas, "P" if estado.vez == "V" else "V"))
    return min(variantes)


def dividir_dados(dados):
    """Divide grupos equivalentes em ~64% treino, ~16% validação e ~20% teste."""
    grupos: dict[tuple, list[int]] = defaultdict(list)
    alvos: dict[tuple, str] = {}
    for indice, linha in dados.iterrows():
        chave = chave_simetria(estado_da_linha(linha))
        classe = str(linha["resultado"])
        if chave in alvos and alvos[chave] != classe:
            raise ValueError("Estados simétricos receberam resultados diferentes.")
        alvos[chave] = classe
        grupos[chave].append(indice)

    chaves = list(grupos)
    indices_grupo = np.arange(len(chaves))
    alvos_grupo = [alvos[chave] for chave in chaves]
    grupos_treino_validacao, grupos_teste = train_test_split(
        indices_grupo, test_size=0.20, random_state=SEMENTE, stratify=alvos_grupo
    )
    grupos_treino, grupos_validacao = train_test_split(
        grupos_treino_validacao,
        test_size=0.20,
        random_state=SEMENTE,
        stratify=[alvos_grupo[grupo] for grupo in grupos_treino_validacao],
    )

    def expandir(indices):
        return np.array(sorted(indice for numero in indices for indice in grupos[chaves[numero]]), dtype=int)

    return expandir(grupos_treino), expandir(grupos_validacao), expandir(grupos_teste), len(chaves)


def candidatos():
    codificador = OneHotEncoder(handle_unknown="ignore")
    return {
        "regressao_logistica": make_pipeline(
            clone(codificador), LogisticRegression(max_iter=500)
        ),
        "floresta_aleatoria": make_pipeline(
            clone(codificador),
            RandomForestClassifier(
                n_estimators=80,
                max_depth=18,
                min_samples_leaf=2,
                random_state=SEMENTE,
                n_jobs=-1,
            ),
        ),
        "floresta_balanceada": make_pipeline(
            clone(codificador),
            RandomForestClassifier(
                n_estimators=100,
                max_depth=20,
                min_samples_leaf=2,
                class_weight="balanced_subsample",
                random_state=SEMENTE,
                n_jobs=-1,
            ),
        ),
    }


def _pontuacao(verdadeiro, previsto):
    return {
        "acuracia": round(float(accuracy_score(verdadeiro, previsto)), 4),
        "f1_macro": round(float(f1_score(verdadeiro, previsto, average="macro")), 4),
    }


def _salvar_graficos(dados, y_teste, previsoes, pasta: Path):
    pasta.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 11})
    contagens = dados["resultado"].value_counts().reindex(CLASSES)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(["Vitória", "Derrota", "Empate"], contagens.values, color=["#DB5261", "#303749", "#DBAF53"])
    ax.set_title("Resultados dos finais de damas")
    ax.set_ylabel("Posições")
    fig.tight_layout()
    fig.savefig(pasta / "distribuicao_classes.png", dpi=160)
    plt.close(fig)

    matriz = confusion_matrix(y_teste, previsoes, labels=CLASSES)
    fig, ax = plt.subplots(figsize=(6, 5))
    imagem = ax.imshow(matriz, cmap="Purples")
    ax.set_xticks(range(3), ["Vitória", "Derrota", "Empate"])
    ax.set_yticks(range(3), ["Vitória", "Derrota", "Empate"])
    ax.set_xlabel("Previsto")
    ax.set_ylabel("Exato")
    ax.set_title("Matriz de confusão no teste")
    for linha in range(3):
        for coluna in range(3):
            ax.text(coluna, linha, f"{matriz[linha, coluna]:,}".replace(",", "."), ha="center", va="center")
    fig.colorbar(imagem, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(pasta / "matriz_confusao.png", dpi=160)
    plt.close(fig)
    return matriz.tolist()


def treinar(
    caminho_dados: Path = CAMINHO_DADOS,
    caminho_modelo: Path = CAMINHO_MODELO,
    caminho_metricas: Path = CAMINHO_METRICAS,
) -> dict:
    dados, auditoria = carregar_dados(caminho_dados)
    X, y = separar_features_target(dados)
    treino, validacao, teste, quantidade_grupos = dividir_dados(dados)

    avaliacoes = {}
    opcoes = candidatos()
    for nome, modelo in opcoes.items():
        modelo.fit(X.iloc[treino], y.iloc[treino])
        avaliacoes[nome] = _pontuacao(y.iloc[validacao], modelo.predict(X.iloc[validacao]))

    escolhido = max(avaliacoes, key=lambda nome: avaliacoes[nome]["f1_macro"])
    treino_validacao = np.concatenate([treino, validacao])
    modelo = clone(opcoes[escolhido])
    modelo.fit(X.iloc[treino_validacao], y.iloc[treino_validacao])
    previsoes = modelo.predict(X.iloc[teste])

    baseline = DummyClassifier(strategy="most_frequent")
    baseline.fit(X.iloc[treino_validacao], y.iloc[treino_validacao])
    pontuacao_baseline = _pontuacao(y.iloc[teste], baseline.predict(X.iloc[teste]))
    pontuacao_teste = _pontuacao(y.iloc[teste], previsoes)

    caminho_modelo.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "modelo": modelo,
            "colunas": list(COLUNAS_MODELO),
            "classes": list(CLASSES),
            "indices_teste": teste.tolist(),
        },
        caminho_modelo,
        compress=3,
    )
    matriz = _salvar_graficos(dados, y.iloc[teste], previsoes, caminho_metricas.parent / "figures")
    metricas = {
        "dataset": "Finais próprios de damas inglesas com até três reis",
        "registros": len(dados),
        "auditoria": auditoria.como_dict(),
        "features": len(COLUNAS_MODELO),
        "target": "resultado da pessoa que joga agora",
        "classes": {classe: int((y == classe).sum()) for classe in CLASSES},
        "grupos_de_simetria": quantidade_grupos,
        "divisao": {"treino": len(treino), "validacao": len(validacao), "teste": len(teste)},
        "semente": SEMENTE,
        "avaliacao_validacao": avaliacoes,
        "modelo_escolhido": escolhido,
        "baseline_teste": pontuacao_baseline,
        "modelo_teste": pontuacao_teste,
        "matriz_confusao": matriz,
        "ordem_matriz": list(CLASSES),
        "relatorio_classes": classification_report(
            y.iloc[teste], previsoes, labels=CLASSES, output_dict=True, zero_division=0
        ),
    }
    caminho_metricas.parent.mkdir(parents=True, exist_ok=True)
    caminho_metricas.write_text(json.dumps(metricas, ensure_ascii=False, indent=2), encoding="utf-8")
    return metricas
