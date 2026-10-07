"""Capturas e mudanças de turno precisam poder ser desfeitas na demonstração."""

import pytest

from projeto_ia.damas.game import Estado, nome_casa
from projeto_ia.damas.session import Partida

CASA = {nome_casa(i): i for i in range(32)}


def test_captura_termina_e_voltar_restaura_as_duas_pecas():
    inicial = Estado((CASA["c3"],), tuple(sorted((CASA["d4"], CASA["f6"]))), "V")
    partida = Partida(inicial)
    lance = partida.lances[0]
    partida.jogar(lance)
    assert partida.vencedor == "V" and not partida.estado.pretas
    with pytest.raises(ValueError):
        partida.jogar(lance)
    partida.voltar()
    assert partida.estado == inicial and partida.vencedor is None
    assert partida.lances == (lance,)


def test_dois_turnos_caminhos_e_recomeco():
    inicial = Estado((CASA["c3"],), (CASA["h8"],), "V")
    partida = Partida(inicial)
    primeira = partida.lances[0]
    partida.jogar(primeira)
    assert partida.estado.vez == "P"
    segunda = partida.lances[0]
    partida.jogar(segunda)
    assert partida.estado.vez == "V"
    assert partida.caminhos_recentes() == (segunda.caminho, primeira.caminho)
    partida.voltar()
    assert partida.estado == primeira.proximo
    partida.recomecar()
    assert partida.estado == inicial and not partida.historico
