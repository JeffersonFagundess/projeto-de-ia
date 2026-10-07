# Arquitetura do projeto

## Fluxo da partida

```text
interface (ui/app.py)
    ↓ jogada escolhida
regras e histórico (damas/full_game.py)
    ↓ posição da vez
política de ajuda (damas/assistant.py)
    ├─ finais de até três damas: resultado e distância exatos (damas/endgame_table.py)
    └─ demais posições: busca e respostas (damas/opponent.py)
    ├─ tabuleiro compacto e lances (damas/search_board.py)
    ├─ avaliação tradicional do computador (damas/opponent.py)
    └─ avaliação da ajuda (damas/strategy.py)
         ├─ rede neural treinada (damas/learning.py, models/partidas_completas/)
         └─ consulta aos rótulos de finais durante a busca (damas/endgame_table.py)
```

As regras públicas ficam em `full_game.py`. O tabuleiro compacto da busca deve produzir os mesmos lances; `tests/test_search.py` compara ambos em posições de partidas simuladas e finais variados. A interface usa uma thread de trabalho para não travar a janela durante a análise. Uma geração e um evento de cancelamento descartam resultados antigos após desfazer, iniciar ou trocar o lado assistido.

## Duas fontes de dados

| Fonte | Quantidade | Produção | Papel no jogo |
| --- | ---: | --- | --- |
| `data/raw/partidas_completas/posicoes_completas.csv` | 7.657 | Partidas legais simuladas e notas de uma busca limitada. | 4.885 posições treinam a rede; as demais compõem validação e teste. |
| `data/raw/finais/finais_damas.csv` | 61.504 | Enumeração e solução exata de finais com duas ou três damas. | Fornece o resultado conhecido nesses finais específicos. |

As duas bases somam **69.161 linhas**. Elas têm alvos diferentes e não são misturadas no treinamento de uma única rede. `scripts/auditar_dados.py` valida os CSVs e gera `data/manifesto.json`, incluindo SHA-256, classes e divisão dos conjuntos. `projeto_ia/paths.py` centraliza os caminhos para evitar referências duplicadas.

## Como reproduzir

1. `python -m scripts.auditar_dados` confere os dados entregues.
2. `python -m scripts.treinar_assistente_completo --reutilizar` repete o treino com o CSV atual.
3. `python -m projeto_ia.damas.train` treina separadamente o classificador de finais do estudo anterior.
4. `python -m scripts.avaliar_assistente --partidas 4` testa o assistente da interface contra o computador, alternando as cores. O tempo é variável para a ajuda e fixo para o computador, conforme `assistant.py`.
5. `python -m pytest -q` verifica regras, equivalência do tabuleiro compacto, dados, modelo e controle da ajuda.

O relatório de partidas registra jogadas, tempo, profundidade, resultado real e casos sem fim no limite. O placar do aplicativo usa apenas partidas terminadas; não converte partidas sem conclusão em empates ou vitórias.
