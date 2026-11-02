# Resultados do projeto P2 — finais de damas

> Estudo anterior, preservado para consulta. A partida completa usa o novo modelo descrito em [assistente_completo.md](../partidas_completas/assistente_completo.md); os números abaixo não avaliam as sugestões do duelo atual. Os rótulos exatos desta base são consultados quando uma partida completa chega a um final de duas ou três damas.

## Problema

Queremos prever vitória, derrota ou empate **para a pessoa da vez** em um final de damas inglesas com até três reis. Um solucionador de grafo calcula o resultado correto; o modelo de Machine Learning aprende a aproximá-lo a partir do tabuleiro. A interface compara os dois e mostra o resultado de cada lance legal disponível agora.

## Base e preparação

Foram geradas **61.504 posições**: 30.976 vitórias (50,36%), 26.252 derrotas (42,68%) e 4.276 empates (6,95%). Não há valores ausentes, duplicados ou casas com categorias inválidas. As entradas do modelo incluem 32 casas, a cor da vez e três contagens de peças derivadas delas, totalizando **36 características**.

Agrupamos estados equivalentes por simetrias do tabuleiro e troca de cores antes da divisão. Assim, posições idênticas sob essas transformações não aparecem ao mesmo tempo no treino e no teste. Com semente 42, ficaram 39.388 posições para treino, 9.852 para validação e 12.264 para teste, em **7.834 grupos**.

## Seleção e avaliação

| Modelo | Acurácia na validação | F1 macro na validação |
| --- | ---: | ---: |
| Regressão logística | 93,02% | 0,7923 |
| Floresta aleatória | 93,21% | 0,8026 |
| Floresta aleatória balanceada | **95,36%** | **0,8956** |

A floresta balanceada foi reentreinada com treino + validação. No conjunto de teste independente ela obteve **94,10% de acurácia** e **0,8499 de F1 macro**. A baseline da classe majoritária obteve **50,36%** e **0,2233**, respectivamente.

| Resultado | Precisão | Revocação | F1 | Posições no teste |
| --- | ---: | ---: | ---: | ---: |
| Vitória | 0,9973 | 0,9598 | 0,9782 | 6.176 |
| Derrota | 0,9368 | 0,9661 | 0,9512 | 5.248 |
| Empate | 0,5969 | 0,6452 | 0,6201 | 840 |

Matriz de confusão, com **linhas exatas** e **colunas previstas**:

| Exato \ previsto | Vitória | Derrota | Empate |
| --- | ---: | ---: | ---: |
| Vitória | 5.928 | 60 | 188 |
| Derrota | 0 | 5.070 | 178 |
| Empate | 16 | 282 | 542 |

Os gráficos estão em `figures/distribuicao_classes.png` e `figures/matriz_confusao.png`. `metricas.json` contém a avaliação completa. O treino pode ser reproduzido com `python -m projeto_ia.damas.train`.

## Interpretação

O modelo supera claramente a baseline, confirmando a hipótese de que peças e posição contêm informação útil. A classe empate continua a mais difícil porque é a menor e porque separa posições em que ninguém consegue forçar vitória. As contagens de peças, obtidas diretamente do tabuleiro, melhoraram muito o desempenho do modelo sem usar a resposta correta como entrada.

Na interface, a explicação de cada lance vem do solucionador **exato**, não de uma justificativa inventada pelo modelo. Para uma vitória, existe ao menos um lance que a força; para uma derrota, todos os lances permitem a vitória adversária; para um empate, há ao menos um lance que mantém empate e nenhum que force vitória. O solucionador foi verificado em todos os **62.560 estados** do grafo, incluindo estados terminais.

## Limites

Este é um final de **damas inglesas com reis de passo curto**, não o jogo brasileiro completo. A base foi gerada por regras, e não coletada de pessoas jogando. Estados com repetição sem vitória forçada são tratados como empate; o contador oficial de jogadas não é modelado. A lista da interface contém todos os **próximos lances legais**, cada um com seu resultado sob jogo correto, mas não desenha todas as sequências completas até o fim.
