# Bases de dados do projeto

## Partidas completas — modelo atual

`raw/partidas_completas/posicoes_completas.csv` contém **7.657 posições** de **240 partidas simuladas**, com 2 a 24 peças. É a base usada para treinar a rede neural do duelo atual. Gere novamente com `python -m scripts.treinar_assistente_completo` ou retreine usando o CSV entregue com `python -m scripts.treinar_assistente_completo --reutilizar`.

Cada partida usa uma mistura de escolhas aleatórias e escolhas por avaliação de material e avanço. As amostras são extraídas após os quatro primeiros turnos, com até 32 registros por partida. Uma busca tática de profundidade 2, com extensão de capturas, fornece a nota usada como alvo. Essa nota não é um resultado definitivo nem uma probabilidade de vitória.

| Coluna | Conteúdo |
| --- | --- |
| `partida` | Identificador da partida simulada, usado para separar os conjuntos. |
| `turno` | Número de movimentos individuais realizados antes da posição. |
| `divisao` | Treino, validação ou teste, fixado por partida. |
| `vermelhas`, `pretas` | Índices das casas ocupadas, separados por espaço, de 0 a 31. |
| `damas` | Índices das peças promovidas; vazio quando nenhuma foi promovida. |
| `vez` | `V` ou `P`, a cor que joga agora. |
| `vez_*`, `rival_*` | Oito medidas por lado: peões, damas, avanço, centro, bordas, retaguarda, protegidas e ameaçadas. |
| `nota_professor` | Vantagem estimada para a cor da vez, limitada a −1.600 a +1.600 pontos. |

Os índices seguem as casas escuras, linha a linha. Em cada lado, `protegidas` conta peças com uma peça aliada diagonalmente adjacente; `ameacadas` conta peças que poderiam sofrer um salto inimigo imediato, considerando direções e casas vazias. São descritores aproximados, não garantias de segurança.

Cada partida aparece em uma única divisão. As posições são deduplicadas considerando rotação de 180 graus e troca de cores. A divisão contém **4.885 / 1.240 / 1.532** registros de treino/validação/teste. Os testes verificam ausência de posições equivalentes duplicadas e correspondência das características com o tabuleiro. As métricas estão em `reports/partidas_completas/assistente_completo.json`.

## Finais com até três damas — estudo anterior

`raw/finais/finais_damas.csv` foi gerado neste projeto por `python -m scripts.gerar_dados_damas`.

O script enumera as **61.504 posições** com uma dama de cada cor e, opcionalmente, uma terceira dama. Todas as peças são reis de passo curto no tabuleiro 8×8 de damas inglesas. O solucionador percorre todos os lances legais, respeita capturas obrigatórias e saltos múltiplos, e grava vitória, derrota ou empate **para a cor da vez**. Ciclos sem vitória forçada são rotulados como empate.

As 32 colunas `c01` a `c32` representam as casas escuras em ordem de leitura, com `v` (vermelha), `p` (preta) ou `b` (vazia). `vez` indica `V` ou `P`; `resultado` contém `win`, `loss` ou `draw`. A posição e a vez identificam cada registro. O código que calcula os rótulos está em `projeto_ia/damas/solver.py` e `projeto_ia/damas/game.py`.

Durante a partida completa, o assistente consulta esses rótulos **somente quando restam duas ou três peças e todas são damas**. A partir das relações entre posições, calcula também quantos turnos faltam até o desfecho sob jogo correto. Nesse domínio, escolhe a vitória mais curta ou a defesa mais longa diretamente pela tabela. Fora dele, usa a rede neural, avaliação estratégica e busca. O modelo antigo de floresta aleatória é preservado para o estudo de classificação, mas não fornece as sugestões da partida completa.

Os rótulos de vitória/derrota/empate vêm do solucionador de posições, que não inclui o relógio de 80 meios movimentos nem o histórico anterior. A escolha direta evita uma jogada que cause empate imediatamente por repetição ou falta de progresso. Ainda assim, o rótulo não promete vitória quando esses limites estão próximos.

## Inventário e integridade

As duas bases somam **69.161 linhas de dados**: 61.504 de finais e 7.657 de partidas completas. Essa soma **não** é a quantidade de exemplos usados para treinar uma única rede neural. Cada base atende uma tarefa diferente. O assistente usa ambas, em momentos diferentes do jogo.

`manifesto.json` registra o caminho, quantidade, distribuição, finalidade e SHA-256 de cada CSV. Verifique os arquivos entregues com `python -m scripts.auditar_dados`. A auditoria verifica colunas, peças, rótulos, duplicatas, hashes e a separação das partidas nos conjuntos de treino, validação e teste. Uma divergência interrompe o comando com erro. Depois de regenerar intencionalmente uma base, use `python -m scripts.auditar_dados --atualizar` para revisar e gravar os novos hashes.

Referência de regras: [World Checkers Draughts Federation, Rules of Checkers](https://wcdf.net/rules/rules_of_checkers_english.pdf). Esta base é derivada de regras, não de partidas coletadas.
