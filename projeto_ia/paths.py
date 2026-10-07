"""Localização única dos dados, modelos e relatórios entregues no projeto."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

BASE_FINAIS = RAIZ / "data/raw/finais/finais_damas.csv"
BASE_COMPLETAS = RAIZ / "data/raw/partidas_completas/posicoes_completas.csv"
MANIFESTO_DADOS = RAIZ / "data/manifesto.json"

MODELO_FINAIS = RAIZ / "models/finais/damas.joblib"
MODELO_COMPLETAS = RAIZ / "models/partidas_completas/assistente_completo.npz"

RELATORIO_FINAIS = RAIZ / "reports/finais/metricas.json"
RELATORIO_COMPLETAS = RAIZ / "reports/partidas_completas/assistente_completo.json"
RELATORIO_DUELO = RAIZ / "reports/partidas_completas/assistente_vs_computador.json"
