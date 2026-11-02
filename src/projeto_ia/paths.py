"""Localização única dos dados, modelos e relatórios entregues no projeto."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RECURSOS = RAIZ / "resources"

BASE_FINAIS = RECURSOS / "data/raw/finais/finais_damas.csv"
BASE_COMPLETAS = RECURSOS / "data/raw/partidas_completas/posicoes_completas.csv"
MANIFESTO_DADOS = RECURSOS / "data/manifesto.json"

MODELO_FINAIS = RECURSOS / "models/finais/damas.joblib"
TABELA_FINAIS = RECURSOS / "models/finais/finais_compactos.npz"
MODELO_COMPLETAS = RECURSOS / "models/partidas_completas/assistente_completo.npz"

RELATORIO_FINAIS = RECURSOS / "reports/finais/metricas.json"
RELATORIO_COMPLETAS = RECURSOS / "reports/partidas_completas/assistente_completo.json"
RELATORIO_DUELO = RECURSOS / "reports/partidas_completas/assistente_vs_computador.json"
