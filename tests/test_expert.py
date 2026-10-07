"""Verifica que o sistema especialista original continua funcional."""

from itertools import product

from projeto_ia.expert.inference import encontrar_regra


def test_todas_as_combinacoes_recebem_uma_regra():
    nomes = ("vida_baixa", "muitos_inimigos", "tem_cura", "municao_baixa", "aliado_perto")
    encontrados = set()
    for valores in product((False, True), repeat=len(nomes)):
        regra = encontrar_regra(dict(zip(nomes, valores)))
        assert regra is not None
        encontrados.add(regra["id"])
    assert encontrados == set(range(1, 9))


def test_vida_baixa_com_cura_prioriza_curar():
    fatos = {
        "vida_baixa": True,
        "muitos_inimigos": True,
        "tem_cura": True,
        "municao_baixa": True,
        "aliado_perto": False,
    }
    assert encontrar_regra(fatos)["id"] == 1

\n
