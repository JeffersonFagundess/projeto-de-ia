# Modelos entregues

| Arquivo | Uso | Treinamento |
| --- | --- | --- |
| `partidas_completas/assistente_completo.npz` | Avaliação aprendida que complementa a busca da partida completa. | Base de 7.657 posições simuladas: 4.885 de treino, 1.240 de validação e 1.532 de teste, separadas por partida. |
| `finais/damas.joblib` | Classificador da interface de estudo de finais. | 61.504 posições resolvidas; divisão por grupos de simetria. |

O jogo completo consulta diretamente os **rótulos exatos** do CSV de finais quando há até três damas. Ele não usa o classificador `damas.joblib` nessa situação. O classificador continua disponível para reproduzir o experimento anterior.

Os caminhos de dados, modelos e métricas estão em `projeto_ia/paths.py`. Treinamento reproduzível: `python -m scripts.treinar_assistente_completo --reutilizar` e `python -m projeto_ia.damas.train`. Consulte `data/README.md` antes de comparar as bases: seus alvos são diferentes.
