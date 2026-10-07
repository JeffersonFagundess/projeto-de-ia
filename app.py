"""Compatibilidade com a execução original em terminal."""

from projeto_ia.expert.knowledge import REGRAS
from projeto_ia.expert.inference import encontrar_regra
from projeto_ia.expert.cli import main, perguntar_sim_nao

if __name__ == "__main__":
    main()
