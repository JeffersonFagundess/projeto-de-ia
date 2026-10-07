# Avaliação do assistente para partidas completas

## O que foi treinado

Uma rede neural MLP de regressão, com camadas ocultas de 48 e 24 unidades, aprende a aproximar notas geradas por uma busca tática. O artefato entregue é `models/partidas_completas/assistente_completo.npz`. O alvo é uma nota de vantagem; não é vitória/derrota/empate nem probabilidade calibrada de vitória.

O professor usa busca de profundidade 2 com extensão de capturas e uma avaliação fixa de peças, avanço e posicionamento. Notas terminais e extremas são limitadas ao intervalo −1.600 a +1.600 para treinamento. O alvo é dividido por 400 durante o ajuste e reconvertido na inferência.

## Dados e separação

São **7.657 posições**, extraídas de **240 partidas simuladas**, com **2 a 24 peças**. As partidas usam uma mistura de escolhas aleatórias e escolhas por material/avanço; não são partidas de especialistas humanos. São coletadas até 32 amostras por partida, após quatro turnos iniciais. Nem todas as combinações possíveis de peças estão representadas.

Cada partida pertence a uma única divisão. Posições equivalentes por rotação de 180 graus acompanhada de troca de cores são deduplicadas. Os testes verificam essa propriedade e a correspondência entre as características salvas e o tabuleiro original.

| Divisão | Posições |
| --- | ---: |
| Treino | 4.885 |
| Validação | 1.240 |
| Teste | 1.532 |

As 16 características medem peões, damas, avanço, centro, bordas, retaguarda, proteção e ameaças de cada lado. O escalonamento é ajustado somente no treino.

## Seleção e teste

| Candidato | Erro absoluto médio na validação |
| --- | ---: |
| Regressão Ridge | 105,14 |
| Rede de 32 unidades | 94,73 |
| Rede de 48 e 24 unidades | **93,33** |

O menor erro de validação definiu o modelo entregue. Ele foi avaliado no teste sem ajustar parâmetros usando o teste.

| Medida no teste | Valor |
| --- | ---: |
| Erro absoluto médio do modelo | **96,00 pontos** |
| Erro da referência que prevê a média do treino | 322,59 pontos |
| R² | 0,8546 |
| Concordância do sinal da nota | 88,58% |

O erro representa a distância para o professor limitado. R² e concordância de sinal não são taxas de vitória em partidas. O professor atribui aproximadamente 100 pontos a uma peça comum, portanto o erro médio ainda é relevante para decisões táticas. Na aplicação, a busca explícita de movimentos complementa a avaliação aprendida.

## Uso no jogo

Na versão atual, a rede complementa uma avaliação estratégica nas posições examinadas por minimax com poda alfa-beta e aprofundamento progressivo. O orçamento da ajuda é de 3 segundos com mais de 16 peças, 4 segundos com 9 a 16 e 5 segundos com até 8, até 12 turnos mais sequências de captura completas. O computador continua com 1,5 segundo. A busca compacta usa transposições com contexto de repetição e relógio de empate. Nenhum movimento legal é alterado para favorecer um participante. O tempo maior da ajuda é parte da assistência e deve ser considerado ao interpretar os resultados de partidas.

Em finais de duas ou três damas, o assistente consulta os rótulos exatos de `data/raw/finais/finais_damas.csv` e a distância até o resultado derivada desses rótulos. Escolhe diretamente a vitória mais curta, a defesa que prolonga a derrota ou um caminho que mantém o empate. A base tem 61.504 registros. Ela não foi misturada com as 7.657 linhas de regressão, pois os alvos são de natureza distinta.

A rede é consultada com as características dos dois lados invertidas e sua nota é simetrizada. O ajuste aprendido corresponde a 25% da diferença entre essa nota e o material, limitada a ±100 antes do peso: no máximo ±25 pontos de contribuição aprendida, com um peão valendo 100. A base estratégica considera também mobilidade, proteção, avanço, promoção e aproximação das damas em vantagem. Essa alteração não retreina o modelo nem modifica os resultados de regressão apresentados acima; o desempenho do sistema híbrido deve ser medido em partidas.

Nos oito primeiros turnos, o assistente varia entre opções verificadas na mesma profundidade, com margem de 6 pontos. A pesquisa individual de cada candidata evita sortear lances que apenas empataram num limite de poda. Vitórias forçadas encontradas têm prioridade sobre variedade.

No modo local, o outro jogador não recebe recomendações. No modo contra o computador, o adversário usa avaliação tradicional e a mesma profundidade máxima de 12 turnos, mas dispõe de 1,5 segundo por jogada. A ajuda dispõe de 3 a 5 segundos conforme o número de peças. Essa diferença faz parte do modo assistido e deve ser considerada na comparação.

## Ensaio anterior contra políticas simples

O protocolo e cada resultado estão em `duelo_simulado.json`. Foram realizados 12 jogos contra escolhas aleatórias e 12 contra uma política que escolhe pela avaliação de material imediata. O lado assistido alternou entre vermelhas e pretas, após quatro movimentos iniciais aleatórios. O limite foi de 160 movimentos adicionais. Partidas sem fim no limite seriam registradas como inacabadas, não como empate.

Esse ensaio foi realizado com o avaliador neural original e o motor anterior; não é uma medida da versão híbrida atual. O ensaio atual usa o computador real da interface e está em `assistente_vs_computador.json`, com resumo em `revisao_busca.md`.

| Adversário simples | Vitórias | Derrotas | Empates | Inacabadas |
| --- | ---: | ---: | ---: | ---: |
| Aleatório | 12 | 0 | 0 | 0 |
| Material imediato | 12 | 0 | 0 | 0 |

Nesse ensaio, o assistente usou 50 ms e profundidade máxima 4 por jogada para permitir execução rápida. Esses são adversários mais simples que a opção Computador da interface. O resultado depende do hardware, é uma amostra pequena e não é uma estimativa da taxa de vitória contra seres humanos. Não foi realizado um ensaio de ablação para atribuir o ganho isoladamente ao ML; os resultados pertencem ao conjunto ML mais busca.

## Limitações e próximas melhorias

- O professor e o aluno são aproximados. Damas não permite garantir vitória a partir de qualquer posição.
- O conjunto é sintético e limitado a políticas simples; não cobre todas as estratégias humanas.
- A rede comprime a posição em 16 medidas e pode atribuir notas parecidas a tabuleiros taticamente diferentes.
- O modelo não é atualizado pelas partidas da sala.
- Para avaliar a vantagem entre pessoas, seria necessário um estudo com mais partidas, troca de papéis e registro das escolhas aceitas ou ignoradas.

Os resultados do estudo anterior de finais com até três damas estão em `reports/finais/resultado.md` e `reports/finais/metricas.json`; suas métricas não devem ser atribuídas a este modelo.
