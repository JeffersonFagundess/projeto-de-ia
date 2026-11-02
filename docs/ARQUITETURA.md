# Arquitetura do projeto

## Fluxo da partida

```text
entrada única (main.py)
    ↓
interface (src/projeto_ia/ui/app.py)
    ├─ olho aberto/fechado: política opcional de exibição e cálculo da dica
    ├─ janela separada de telemetria e exploração (ui/reasoning.py)
    ├─ resultado animado sobre o tabuleiro (ui/result_overlay.py)
    ├─ processo persistente da IA (ui/analysis_service.py)
    ├─ efeitos WAV assíncronos (src/projeto_ia/sounds/)
    └─ estilo central (src/projeto_ia/style/)
         ├─ paleta, tipografia e fonte oficial Font Awesome local
         ├─ controles, janelas e sub-janelas
         └─ glifos Font Awesome rasterizados e sprites antialiasados reutilizáveis
    ↓ jogada escolhida
regras e histórico (damas/full_game.py)
    ↓ posição da vez
política de ajuda (damas/assistant.py)
    ├─ finais de até três damas: resultado e distância exatos (damas/endgame_table.py)
    └─ demais posições: busca e respostas (damas/opponent.py)
    ├─ tabuleiro compacto e lances (damas/search_board.py)
    ├─ avaliação tradicional do computador (damas/opponent.py)
    └─ avaliação da ajuda (damas/strategy.py)
         ├─ rede neural treinada (damas/learning.py, resources/models/partidas_completas/)
         └─ consulta aos rótulos de finais durante a busca (damas/endgame_table.py)
```

As regras públicas ficam em `full_game.py`. O tabuleiro compacto da busca deve produzir os mesmos lances; `tests/test_search.py` compara ambos em posições de partidas simuladas e finais variados. A busca roda no processo persistente `IA-Damas`, separado do processo do Tkinter. Isso remove a disputa do GIL com a interface e preserva o modelo e seus caches entre turnos. Um contador compartilhado de geração cancela e descarta resultados antigos após desfazer, iniciar, ocultar a dica ou trocar o lado assistido.

Durante cada profundidade, `opponent.py` publica pulsos limitados a aproximadamente 120 ms com nível e quantidade de posições. Ao concluir o nível, inclui nota e linha principal. O processo envia os eventos por uma fila limitada; somente o Tkinter atualiza o terminal e a animação. Pulsos podem ser descartados se a interface estiver atrasada, mas o resultado nunca é descartado. A telemetria permanece opcional e isolada: uma falha no consumidor não altera a jogada escolhida. O olho suspende apenas a análise destinada ao jogador; a busca automática do computador segue independente.

Ao encerrar a profundidade final, a busca também devolve as notas das jogadas da raiz e das respostas exploradas para a opção escolhida. A interface normaliza essas notas como confiança relativa, preserva o vínculo com cada `Movimento` legal e desenha os percentuais nas casas. Essa normalização é apenas comparativa; não converte a regressão em probabilidade de vitória.

O comando **Detalhar caminho** inicia uma busca explícita instrumentada. Cada nó concluído — inclusive os interrompidos pelo limite de tempo — é gravado em lotes por `damas/trace_store.py` num SQLite temporário. A fila envia à interface somente o caminho do arquivo pronto. `ui/reasoning.py` consulta 250 nós por página e reconstrói sob demanda a cadeia de pais do nó selecionado. Assim, uma captura com 40 mil ou mais interações não cria 40 mil widgets nem transfere todos os registros pela fila do Tkinter. O arquivo anterior é removido ao recapturar ou fechar o aplicativo.

O diagnóstico, as medições e a ordem recomendada para futuras otimizações estão em `docs/DESEMPENHO.md`.

## Duas fontes de dados

| Fonte | Quantidade | Produção | Papel no jogo |
| --- | ---: | --- | --- |
| `resources/data/raw/partidas_completas/posicoes_completas.csv` | 7.657 | Partidas legais simuladas e notas de uma busca limitada. | 4.885 posições treinam a rede; as demais compõem validação e teste. |
| `resources/data/raw/finais/finais_damas.csv` | 61.504 | Enumeração e solução exata de finais com duas ou três damas. | Fornece o resultado conhecido nesses finais específicos. |

As duas bases somam **69.161 linhas**. Elas têm alvos diferentes e não são misturadas no treinamento de uma única rede. `tools/auditar_dados.py` valida os CSVs e gera `resources/data/manifesto.json`, incluindo SHA-256, classes e divisão dos conjuntos. `src/projeto_ia/paths.py` é o único ponto que conhece a localização física dos recursos.

## Como reproduzir

1. `python -m tools.auditar_dados` confere os dados entregues.
2. `python -m tools.treinar_assistente_completo --reutilizar` repete o treino com o CSV atual.
3. `python -m projeto_ia.damas.train` treina separadamente o classificador de finais do estudo anterior.
4. `python -m tools.avaliar_assistente --partidas 4` testa o assistente da interface contra o computador, alternando as cores. O tempo é variável para a ajuda e fixo para o computador, conforme `assistant.py`.
5. `python -m pytest -q` verifica regras, equivalência do tabuleiro compacto, dados, modelo e controle da ajuda.

O relatório de partidas registra jogadas, tempo, profundidade, resultado real e casos sem fim no limite. O placar do aplicativo usa apenas partidas terminadas; não converte partidas sem conclusão em empates ou vitórias.
