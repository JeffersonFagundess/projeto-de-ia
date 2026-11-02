# Modelos e tabelas entregues

| Arquivo | Uso | Treinamento |
| --- | --- | --- |
| `partidas_completas/assistente_completo.npz` | Avaliação aprendida que complementa a busca da partida completa. | Base de 7.657 posições simuladas: 4.885 de treino, 1.240 de validação e 1.532 de teste, separadas por partida. |
| `finais/damas.joblib` | Classificador da interface de estudo de finais. | 61.504 posições resolvidas; divisão por grupos de simetria. |
| `finais/finais_compactos.npz` | Resultados e distâncias exatos consultados rapidamente pelo jogo. | Compilado do CSV auditável por `python -m tools.compilar_finais`. |

O jogo completo consulta os mesmos **rótulos exatos** do CSV de finais quando há até três damas, usando o NPZ compacto em tempo de execução. O CSV permanece como fonte auditável e seu hash fica gravado no artefato. O jogo não usa o classificador `damas.joblib` nessa situação; ele continua disponível para reproduzir o experimento anterior.

Os caminhos de dados, modelos e métricas estão em `src/projeto_ia/paths.py`. Treinamento reproduzível: `python -m tools.treinar_assistente_completo --reutilizar` e `python -m projeto_ia.damas.train`. Consulte `resources/data/README.md` antes de comparar as bases: seus alvos são diferentes.
