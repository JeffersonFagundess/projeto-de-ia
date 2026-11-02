# Desempenho e evolução do motor

## O que causava a sensação de travamento

A busca era executada em uma `threading.Thread`. Embora isso evitasse chamar o
Tkinter diretamente na tarefa de fundo, o motor continuava executando Python
CPU-bound no mesmo processo e disputava o GIL com a interface. Além disso, a
telemetria era emitida somente ao terminar uma profundidade inteira.

Agora a interface e a busca têm responsabilidades separadas:

```text
processo Tkinter                  processo IA-Damas
cliques/animações  ── trabalho ─→ busca + modelo + caches
telemetria/terminal ←─ eventos ── pulsos a cada ~120 ms
```

`src/projeto_ia/ui/analysis_service.py` mantém o processo da IA vivo durante a
sessão. O modelo e caches são carregados uma vez. A fila tem limite para evitar
acúmulo de telemetria e um contador compartilhado cancela buscas obsoletas.

## Medição de referência

Medição local em 2 de novembro de 2026; os números variam conforme o hardware:

| Operação | Resultado observado |
| --- | ---: |
| Busca inicial com orçamento de 0,5 s | 9.409 nós, profundidade 7 |
| Carregar 61.504 finais do CSV | 0,47 s |
| Derivar 57.228 distâncias decisivas | 1,51 s |
| Materializar o mapa operacional de 61.504 notas do NPZ | 0,065 s |
| Materializar 57.228 distâncias pela API de auditoria | 0,031 s |
| Telemetria na análise aprofundada | 374 → 86.529 posições em cerca de 700 ms, sem bloquear a janela |

O tempo de 3 a 8 segundos da sugestão é hoje um orçamento intencional de busca,
não um congelamento da janela. O usuário pode continuar interagindo e cancelar.

A telemetria fica numa janela própria e a interface principal não cria gráficos
ou métricas. A captura completa só é ativada por **Detalhar caminho**. Os nós são
gravados em lotes num SQLite temporário, enquanto o explorador consulta 250 por
página; portanto, uma busca de dezenas de milhares de posições não materializa
dezenas de milhares de widgets nem ocupa a fila de eventos da interface.

Um perfil de 1 segundo registrou aproximadamente 1,67 milhão de chamadas. O
custo acumulado ficou concentrado na avaliação estratégica/atributos (cerca de
56%) e geração de lances (cerca de 34%); a inferência isolada da rede ficou em
aproximadamente 10%. Reproduza a medição com:

```powershell
python -m tools.perfilar_busca --segundos 1
```

## Armazenamento aplicado

`resources/models/finais/finais_compactos.npz` ocupa aproximadamente 32,4 KiB
e contém resultados e distâncias em arrays NumPy tipados. O CSV permanece como
fonte humana e auditável; o SHA-256 dele fica gravado no artefato e é conferido
pelos testes. Durante a partida é materializado somente um mapa de notas exatas;
os mapas separados de rótulos e distâncias ficam reservados às APIs de auditoria.
Para reconstruir:

```powershell
python -m tools.compilar_finais
```

## Próximas otimizações, em ordem de retorno

| Prioridade | Onde | Mudança recomendada | Motivo |
| --- | --- | --- | --- |
| 1 | `damas/opponent.py` e `damas/search_board.py` | Perfilar geração de lances, ordenação e avaliação; reduzir alocações e chamadas Python no laço interno. | É onde quase todo o tempo da busca é gasto. A interface e o carregamento já estão isolados. |
| 2 | `native/damas_engine/` | Se o perfil ainda justificar, portar somente tabuleiro compacto, geração de lances e alfa-beta para Rust com PyO3. | Mantém UI, regras públicas e ML em Python, mas move o núcleo CPU-bound para código nativo. É a fronteira com melhor custo/benefício. |
| 3 | motor nativo | Paralelizar jogadas da raiz em 2–4 workers/Rayon, com limite baseado em `cpu_count - 1`. | Usa múltiplos núcleos sem competir com o Tkinter. Paralelizar alfa-beta ingenuamente em threads Python perde cache e sofre com o GIL. |
| 4 | cache de sessão no processo da IA | Reaproveitar uma tabela de transposição limitada entre posições consecutivas, incluindo repetição e relógio de empate na chave. | Pode acelerar respostas seguintes, mas exige cuidado para não reutilizar uma avaliação em contexto diferente. |

Não é recomendado mover a interface, o carregamento do modelo ou os 16 atributos
da rede para outra linguagem. O ganho relevante está no laço de busca. Antes da
porta nativa, devem ser registrados nós por segundo, taxa de acerto da tabela de
transposição e tempo por avaliação para que a migração tenha meta mensurável.

## Áudio

`src/projeto_ia/sounds/` contém apenas sete WAVs curtos. No Windows eles usam
`winsound` com `SND_ASYNC`, sem thread Python adicional e sem dependência nova.
Em outros sistemas o reprodutor é um no-op seguro; uma versão multiplataforma
pode usar `miniaudio` como dependência opcional, caso isso se torne requisito.
