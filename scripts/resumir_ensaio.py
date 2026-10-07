"""Cria resumo curto e verificável a partir das partidas detalhadas em JSON."""

import json

from projeto_ia.paths import RELATORIO_DUELO

DESTINO=RELATORIO_DUELO.with_name('revisao_busca.md')


def executar():
    dados=json.loads(RELATORIO_DUELO.read_text(encoding='utf-8'))
    jogos=dados['partidas']
    if not jogos:
        raise ValueError('O relatório não contém partidas.')
    resumo=dados['resumo']
    linhas=[
        '# Revisão da busca e partidas contra o computador',
        '',
        '## Alterações avaliadas',
        '',
        '- Busca com tabuleiro compacto, ordenação de jogadas e reaproveitamento de posições, incluindo o contexto de repetição.',
        '- Verificação de sequências de captura até uma posição sem captura obrigatória.',
        '- Avaliação assistida que combina a rede neural treinada, material, posição e mobilidade. A contribuição aprendida é limitada a ±25 pontos; um peão vale 100.',
        '- Consulta aos 61.504 rótulos exatos quando restam no máximo três damas. A rede neural foi treinada na outra base, de 7.657 posições.',
        '- Nos finais resolvidos, deriva a distância até o resultado e escolhe diretamente a vitória mais curta; profundidade 0 no registro indica essa consulta, não ausência de análise.',
        '- Mais tempo automático para a ajuda desde a abertura; o computador mantém seu orçamento próprio e sua avaliação tradicional.',
        '',
        '## Protocolo',
        '',
        dados['protocolo'],
        '',
        f"**Tempo da ajuda:** {dados['tempo_automatico_ajuda'] or str(dados['segundos_por_jogada_iguais_se_forcado'])+' s para os dois lados'}. **Computador:** {dados['tempo_computador']} s por jogada.",
        f"**Limites:** profundidade máxima {dados['profundidade_maxima']}; até {dados['max_turnos']} turnos por partida.",
        '',
        '| Partida | Semente | Ajuda para | Resultado | Turnos | Profundidade média da ajuda | Profundidade média do computador |',
        '| ---: | ---: | --- | --- | ---: | ---: | ---: |',
    ]
    for jogo in jogos:
        linhas.append(f"| {jogo['numero']} | {jogo['semente']} | {'vermelhas' if jogo['assistido']=='V' else 'pretas'} | {jogo['resultado']} | {jogo['turnos']} | {jogo['profundidade_media_ia']:.1f} | {jogo['profundidade_media_computador']:.1f} |")
    linhas += [
        '',
        f"**Resumo:** {resumo.get('vitoria',0)} vitória(s), {resumo.get('derrota',0)} derrota(s), {resumo.get('empate',0)} empate(s), {resumo.get('inacabada',0)} inconclusa(s).",
        '',
        '## Interpretação',
        '',
        'O resultado pertence a esta amostra e ao computador deste projeto. A busca depende do tempo disponível e do hardware. Partidas sem conclusão no limite permanecem inconclusas; vantagem em peças não é convertida em vitória. As partidas não provam vitória garantida contra pessoas nem isolam o efeito da rede neural do efeito da busca, da tabela de finais ou do tempo adicional.',
        '',
        'As jogadas, notas, profundidades, orçamentos e resultados individuais estão em `assistente_vs_computador.json`.',
        '',
        'Para repetir a comparação da interface: `python -m scripts.avaliar_assistente --partidas 2 --semente 20261009 --max-turnos 180`. Para testar tempo igual: adicione `--segundos 1.5`.',
        '',
    ]
    DESTINO.write_text('\n'.join(linhas),encoding='utf-8')
    print(f'{len(jogos)} partidas resumidas em {DESTINO}')


if __name__ == '__main__':executar()
