from .inference import encontrar_regra


def perguntar_sim_nao(pergunta):
    """Faz uma pergunta ate o usuario responder sim ou nao."""
    while True:
        resposta = input(f"{pergunta} (sim/nao): ").strip().lower()

        if resposta in {"sim", "s"}:
            return True
        if resposta in {"nao", "não", "n"}:
            return False

        print("Resposta invalida. Digite sim ou nao.")


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
