from .knowledge import REGRAS


def encontrar_regra(fatos):
    """Compara os fatos com as condicoes e devolve a primeira regra compativel."""
    for regra in REGRAS:
        corresponde = all(
            fatos[nome_do_fato] == valor_esperado
            for nome_do_fato, valor_esperado in regra["condicoes"].items()
        )

        if corresponde:
            return regra

    return None
