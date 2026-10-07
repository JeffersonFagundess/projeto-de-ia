# Relatórios

## `partidas_completas/`

- `assistente_completo.json` e `.md`: origem da base de 7.657 posições, seleção do modelo neural e métricas de teste.
- `assistente_vs_computador.json`: partidas simuladas com o computador da interface, cores alternadas e detalhes de cada jogada. O número de partidas, o tempo e o limite de turnos estão no próprio arquivo. O orçamento da ajuda varia de 3 a 5 segundos de acordo com o número de peças; o computador usa 1,5 segundo.
- `revisao_busca.md`: resumo das partidas detalhadas e das mudanças no motor, gerado por `python -m scripts.resumir_ensaio`.
- `duelo_simulado.json`: ensaio **anterior** contra programas simples; não mede o desempenho do assistente atual contra o computador da interface.

## `finais/`

- `metricas.json`: validação e teste do classificador de finais com até três damas.
- `resultado.md`: explicação do estudo de finais.
- `figures/`: gráficos desse estudo.

As bases correspondentes estão catalogadas em `data/README.md` e verificadas por `data/manifesto.json`. Não compare diretamente as métricas de regressão das partidas completas com a acurácia de classificação dos finais: são tarefas e conjuntos diferentes.
