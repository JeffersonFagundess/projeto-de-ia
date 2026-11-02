"""Assistente híbrido: material e estratégia conferem a avaliação da rede.

A rede original é preservada para reproduzir o experimento de regressão.
No jogo, sua contribuição é simetrizada e limitada para que um erro do modelo
não faça algumas características posicionais valerem mais que várias peças.
"""

from functools import lru_cache

import numpy as np

from .game import CASAS
from .learning import carregar_avaliador, features_compactas
from .search_board import compactar, indices, PASSOS
from .endgame_table import avaliacao_exata

PESOS_ESTRUTURA = np.array([0,0,3,5,1,2,4,-12])


class AvaliadorEstrategico:
    def __init__(self, modelo=None):
        self.modelo = modelo or carregar_avaliador()

    def __call__(self, estado):
        return self.compacto(compactar(estado))

    def compacto(self, tab):
        final = avaliacao_exata(tab)
        if final is not None:
            return final
        x = features_compactas(tab)
        n = (tab.vermelhas | tab.pretas).bit_count()
        material = (x[0]-x[8])*100 + (x[1]-x[9])*220
        estrutura = (x[:8]-x[8:]) @ PESOS_ESTRUTURA
        if n > 12:
            estrutura += (x[5]-x[13])*8
        ocupadas = tab.vermelhas | tab.pretas
        mobilidade = 0
        proximidade = 0
        for vermelha,casas,rivais in ((True,tab.vermelhas,tab.pretas),(False,tab.pretas,tab.vermelhas)):
            sinal = 1 if vermelha == tab.vez else -1
            for c in indices(casas):
                dama = (1 << c) & tab.damas
                direcoes = range(4) if dama else (0,1) if vermelha else (2,3)
                mobilidade += sinal*sum(dest >= 0 and not ocupadas & (1 << dest) for dest in (PASSOS[c][d] for d in direcoes))*3
                if not dama:
                    avanco = 7-CASAS[c][0] if vermelha else CASAS[c][0]
                    estrutura += sinal*(0,0,0,0,2,8,24,0)[avanco]
                elif n <= 10 and rivais:
                    distancia = min(max(abs(CASAS[c][0]-CASAS[r][0]),abs(CASAS[c][1]-CASAS[r][1])) for r in indices(rivais))
                    # O lado em vantagem deve aproximar as damas e concluir a partida.
                    if material*sinal > 50:
                        proximidade += sinal*(7-distancia)*6
        tradicional = material*(1+(24-n)/100) + estrutura + mobilidade + proximidade
        # Até 25 pontos de ajuste aprendido (um peão vale 100).
        ajuste = .25*max(-100,min(100,self._aprendida(tuple(x))-material))
        return float(tradicional+ajuste)

    @lru_cache(maxsize=32768)
    def _aprendida(self, valores):
        """Tabuleiros com as mesmas 16 características compartilham a inferência."""
        direta = self.modelo.prever_features(np.asarray(valores))
        inversa = self.modelo.prever_features(np.asarray(valores[8:]+valores[:8]))
        return (direta-inversa)/2


@lru_cache(maxsize=1)
def carregar_assistente():
    return AvaliadorEstrategico()
