# Revisão da busca e partidas contra o computador

## Alterações avaliadas

- Busca com tabuleiro compacto, ordenação de jogadas e reaproveitamento de posições, incluindo o contexto de repetição.
- Verificação de sequências de captura até uma posição sem captura obrigatória.
- Avaliação assistida que combina a rede neural treinada, material, posição e mobilidade. A contribuição aprendida é limitada a ±25 pontos; um peão vale 100.
- Consulta aos 61.504 rótulos exatos quando restam no máximo três damas. A rede neural foi treinada na outra base, de 7.657 posições.
- Nos finais resolvidos, deriva a distância até o resultado e escolhe diretamente a vitória mais curta; profundidade 0 no registro indica essa consulta, não ausência de análise.
- Mais tempo automático para a ajuda desde a abertura; o computador mantém seu orçamento próprio e sua avaliação tradicional.

## Protocolo

Mesmo motor para ambos os lados. Posição inicial completa; cores alternadas. Sugestões seguidas em todas as jogadas do lado assistido. A ajuda tem mais tempo nas fases com menos peças; o computador permanece com 1,5 s. --segundos força orçamento igual para uma comparação controlada.

**Tempo da ajuda:** 3 s acima de 16 peças; 4 s entre 9 e 16; 5 s com até 8 peças. **Computador:** 1.5 s por jogada.
**Limites:** profundidade máxima 12; até 180 turnos por partida.

| Partida | Semente | Ajuda para | Resultado | Turnos | Profundidade média da ajuda | Profundidade média do computador |
| ---: | ---: | --- | --- | ---: | ---: | ---: |
| 1 | 20261009 | vermelhas | inacabada | 180 | 8.8 | 8.6 |
| 2 | 20261010 | pretas | vitoria | 70 | 9.8 | 9.9 |

**Resumo:** 1 vitória(s), 0 derrota(s), 0 empate(s), 1 inconclusa(s).

## Interpretação

O resultado pertence a esta amostra e ao computador deste projeto. A busca depende do tempo disponível e do hardware. Partidas sem conclusão no limite permanecem inconclusas; vantagem em peças não é convertida em vitória. As partidas não provam vitória garantida contra pessoas nem isolam o efeito da rede neural do efeito da busca, da tabela de finais ou do tempo adicional.

As jogadas, notas, profundidades, orçamentos e resultados individuais estão em `assistente_vs_computador.json`.

Para repetir a comparação da interface: `python -m scripts.avaliar_assistente --partidas 2 --semente 20261009 --max-turnos 180`. Para testar tempo igual: adicione `--segundos 1.5`.
