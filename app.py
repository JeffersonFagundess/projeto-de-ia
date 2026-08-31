"""Sistema especialista simples para recomendar uma acao em um jogo."""


REGRAS = [
    {
        "id": 1,
        "condicoes": {"vida_baixa": True, "tem_cura": True},
        "decisao": "Use o item de cura antes de continuar.",
        "explicacao": (
            "Sua vida esta baixa e voce possui um item de cura. "
            "Recuperar vida reduz o risco de ser derrotado."
        ),
    },
    {
        "id": 2,
        "condicoes": {
            "vida_baixa": True,
            "tem_cura": False,
            "aliado_perto": True,
        },
        "decisao": "Recue e fique perto do aliado.",
        "explicacao": (
            "Sua vida esta baixa, voce nao possui cura e existe um aliado por perto. "
            "O aliado pode ajudar a proteger sua retirada."
        ),
    },
    {
        "id": 3,
        "condicoes": {
            "vida_baixa": True,
            "tem_cura": False,
            "aliado_perto": False,
        },
        "decisao": "Fuja do combate e procure um local seguro.",
        "explicacao": (
            "Sua vida esta baixa, voce nao possui cura e nao ha um aliado por perto. "
            "Continuar lutando seria muito arriscado."
        ),
    },
    {
        "id": 4,
        "condicoes": {"vida_baixa": False, "municao_baixa": True},
        "decisao": "Procure municao ou recursos antes de lutar.",
        "explicacao": (
            "Sua vida esta em boas condicoes, mas sua municao esta baixa. "
            "Reabastecer evita ficar sem recursos durante o combate."
        ),
    },
    {
        "id": 5,
        "condicoes": {
            "vida_baixa": False,
            "municao_baixa": False,
            "muitos_inimigos": True,
            "aliado_perto": True,
        },
        "decisao": "Ataque em equipe com o aliado.",
        "explicacao": (
            "Sua vida e sua municao estao boas. Existem muitos inimigos, "
            "mas um aliado esta por perto para ajudar no combate."
        ),
    },
    {
        "id": 6,
        "condicoes": {
            "vida_baixa": False,
            "municao_baixa": False,
            "muitos_inimigos": True,
            "aliado_perto": False,
        },
        "decisao": "Evite o confronto e procure cobertura.",
        "explicacao": (
            "Embora sua vida e sua municao estejam boas, existem muitos inimigos "
            "e nenhum aliado esta por perto. Lutar sozinho seria arriscado."
        ),
    },
    {
        "id": 7,
        "condicoes": {
            "vida_baixa": False,
            "municao_baixa": False,
            "muitos_inimigos": False,
            "aliado_perto": True,
        },
        "decisao": "Avance com o aliado.",
        "explicacao": (
            "Sua vida e sua municao estao boas, nao existem muitos inimigos "
            "e ha um aliado por perto. A situacao e favoravel para avancar."
        ),
    },
    {
        "id": 8,
        "condicoes": {
            "vida_baixa": False,
            "municao_baixa": False,
            "muitos_inimigos": False,
            "aliado_perto": False,
        },
        "decisao": "Explore a area com cuidado.",
        "explicacao": (
            "Sua vida e sua municao estao boas e nao existem muitos inimigos. "
            "Como voce esta sozinho, o melhor e explorar com cautela."
        ),
    },
]


def perguntar_sim_nao(pergunta):
    """Faz uma pergunta ate o usuario responder sim ou nao."""
    while True:
        resposta = input(f"{pergunta} (sim/nao): ").strip().lower()

        if resposta in {"sim", "s"}:
            return True
        if resposta in {"nao", "não", "n"}:
            return False

        print("Resposta invalida. Digite sim ou nao.")


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


def main():
    print("=" * 55)
    print("       ASSISTENTE DE ESTRATEGIA PARA JOGOS")
    print("=" * 55)
    print("Responda as perguntas para receber uma recomendacao.\n")

    fatos = {
        "vida_baixa": perguntar_sim_nao("A vida do personagem esta baixa?"),
        "muitos_inimigos": perguntar_sim_nao(
            "Existem muitos inimigos proximos?"
        ),
        "tem_cura": perguntar_sim_nao("O personagem possui um item de cura?"),
        "municao_baixa": perguntar_sim_nao("A municao ou mana esta baixa?"),
        "aliado_perto": perguntar_sim_nao("Existe um aliado por perto?"),
    }

    regra = encontrar_regra(fatos)

    print("\n" + "-" * 55)
    if regra is None:
        print("Nao foi possivel encontrar uma recomendacao.")
        return

    print(f"REGRA UTILIZADA: {regra['id']}")
    print(f"RECOMENDACAO: {regra['decisao']}")
    print(f"MOTIVO: {regra['explicacao']}")
    print("-" * 55)


if __name__ == "__main__":
    main()
