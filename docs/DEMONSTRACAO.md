# Roteiro de apresentação — Damas com ajuda de IA

## Preparação

Abra `iniciar_interface.bat` antes da aula para instalar as dependências. Depois dessa preparação, não é necessário usar internet. Deixe selecionados **Outra pessoa** em Jogar contra e **Jogador 1** em Quem recebe ajuda. O jogador 1 controla as vermelhas; o jogador 2 controla as pretas.

## Apresentação em três minutos

**1. Explique a proposta — 30 segundos**

“Duas pessoas jogam damas. Uma recebe sugestões de uma IA treinada com exemplos; a outra decide sozinha. Vamos observar se a ajuda faz diferença, sem alterar as regras do jogo.”

Mostre os cartões **Com IA** e **Sem dicas**. A borda indica a vez de jogar.

**2. Mostre como funciona — 30 segundos**

Clique em **Exemplo rápido** e depois em **Jogar com a sugestão**. A peça faz uma sequência de capturas, e a tela explica o resultado. Diga que é um tabuleiro preparado para demonstrar o movimento, e que ele não conta no placar.

**3. Comece uma partida real — 1 minuto**

Clique em **Nova partida**. Há 12 peças de cada lado. O jogador 1 aceita a sugestão ou clica na peça e numa casa verde. Ao passar a vez, a dica desaparece e o jogador 2 faz sua própria escolha. As casas verdes indicam movimentos permitidos para ambos; não são recomendações para o lado sem ajuda.

O botão **Pensar mais** aprofunda a análise por até 8 segundos. A sugestão automática usa de 3 a 5 segundos conforme o número de peças; o computador usa 1,5 segundo. Para uma comparação técnica com tempo igual, execute `python -m scripts.avaliar_assistente --partidas 4 --segundos 1.5`.

**4. Explique o aprendizado — 1 minuto**

“Geramos 7.657 posições a partir de 240 partidas simuladas. Uma busca calculou notas táticas para esses exemplos. A rede neural aprendeu a aproximar essas notas. Durante a partida, o assistente combina a rede com avaliação de peças e estratégia e compara as respostas do adversário. É um sistema híbrido, não apenas a rede neural.”

Abra **Sobre a IA**. Explique que os exemplos de treino foram gerados por regras e busca, não por partidas humanas, e que a nota não representa chance exata de vitória.

## Comparação em sala

- Joguem uma partida completa e registrem o vencedor real.
- Troquem quem recebe a ajuda e iniciem outra partida.
- O placar da sessão conta vitórias com ajuda, sem ajuda e empates.
- Fechar o aplicativo zera o placar. Desfazer uma jogada que encerrou a partida retira esse resultado do placar.
- Como as duas pessoas usam a mesma tela, ambas veem o que foi exibido no turno anterior. A restrição é não oferecer recomendações no turno sem assistência.

## Perguntas esperadas

**“Quem tem IA sempre ganha?”** A ajuda pode errar. O resultado depende da posição, das escolhas e da força do adversário. O programa aceita vitórias do lado sem ajuda e empates.

**“O que foi testado?”** A rede foi avaliada em 1.532 posições de partidas separadas do treino. O sistema atual também é testado contra o computador da própria interface, com cores alternadas; consulte `reports/partidas_completas/assistente_vs_computador.json`. O ensaio anterior de 24 vitórias usava programas mais simples. Nenhum deles mede desempenho contra pessoas nem demonstra sozinho que o ML é responsável pelas vitórias.

**“Por que a abertura muda?”** Nos primeiros oito turnos, o assistente pode escolher entre opções com avaliações próximas, depois de verificar as respostas. Ele não escolhe qualquer lance aleatório para parecer diferente.

**“Por que existem duas bases, somando 69.161 linhas?”** A rede neural usa 7.657 posições de partidas completas. As outras 61.504 são finais resolvidos de até três damas. Quando esse tipo de final aparece no jogo, a ajuda consulta diretamente o resultado exato. São duas fontes de conhecimento, com finalidades diferentes.

**“A IA aprende enquanto jogamos?”** Não. O modelo entregue já está treinado. O placar mostra os resultados desta sessão, mas não retreina o modelo.
