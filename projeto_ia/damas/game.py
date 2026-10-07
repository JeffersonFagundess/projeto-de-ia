"""Regras de um final de damas inglesas com até três reis.

Tabuleiro 8x8, casas escuras, reis de passo curto, captura obrigatória e
saltos múltiplos completos. Não há promoção: todas as peças já são reis.
"""

from dataclasses import dataclass


CASAS = tuple((linha, coluna) for linha in range(8) for coluna in range(8) if (linha + coluna) % 2 == 1)
INDICE = {casa: posicao for posicao, casa in enumerate(CASAS)}
DIRECOES = ((-1, -1), (-1, 1), (1, -1), (1, 1))


@dataclass(frozen=True, order=True)
class Estado:
    vermelhas: tuple[int, ...]
    pretas: tuple[int, ...]
    vez: str  # "V" ou "P"

    def __post_init__(self):
        if self.vez not in {"V", "P"}:
            raise ValueError("A vez precisa ser V ou P.")
        if self.vermelhas != tuple(sorted(self.vermelhas)) or self.pretas != tuple(sorted(self.pretas)):
            raise ValueError("As casas das peças devem estar ordenadas.")
        ocupadas = self.vermelhas + self.pretas
        if len(set(ocupadas)) != len(ocupadas) or any(casa not in range(32) for casa in ocupadas):
            raise ValueError("As peças precisam ocupar casas escuras diferentes.")


@dataclass(frozen=True)
class Lance:
    caminho: tuple[int, ...]
    capturadas: tuple[int, ...]
    proximo: Estado


def nome_casa(indice: int) -> str:
    linha, coluna = CASAS[indice]
    return f"{'abcdefgh'[coluna]}{8 - linha}"


def _vizinha(casa: int, dr: int, dc: int, passos: int = 1) -> int | None:
    linha, coluna = CASAS[casa]
    return INDICE.get((linha + dr * passos, coluna + dc * passos))


def lances_legais(estado: Estado) -> tuple[Lance, ...]:
    """Devolve todos os lances completos; captura tem prioridade obrigatória."""
    nossas = estado.vermelhas if estado.vez == "V" else estado.pretas
    rivais = estado.pretas if estado.vez == "V" else estado.vermelhas
    if not nossas or not rivais:
        return ()
    proxima_vez = "P" if estado.vez == "V" else "V"

    def criar_estado(pecas_nossas, pecas_rivais):
        if estado.vez == "V":
            return Estado(tuple(sorted(pecas_nossas)), tuple(sorted(pecas_rivais)), proxima_vez)
        return Estado(tuple(sorted(pecas_rivais)), tuple(sorted(pecas_nossas)), proxima_vez)

    capturas: list[Lance] = []
    for origem in nossas:
        outras = frozenset(nossas) - {origem}

        def continuar(atual, restantes, caminho, removidas):
            encontrou = False
            for dr, dc in DIRECOES:
                meio = _vizinha(atual, dr, dc)
                destino = _vizinha(atual, dr, dc, 2)
                if meio is None or destino is None:
                    continue
                if meio in restantes and destino not in restantes and destino not in outras:
                    encontrou = True
                    continuar(destino, restantes - {meio}, caminho + (destino,), removidas + (meio,))
            if not encontrou and removidas:
                capturas.append(Lance(caminho, removidas, criar_estado(outras | {atual}, restantes)))

        continuar(origem, frozenset(rivais), (origem,), ())

    if capturas:
        return tuple(capturas)

    movimentos: list[Lance] = []
    ocupadas = frozenset(nossas + rivais)
    for origem in nossas:
        for dr, dc in DIRECOES:
            destino = _vizinha(origem, dr, dc)
            if destino is not None and destino not in ocupadas:
                novas = (frozenset(nossas) - {origem}) | {destino}
                movimentos.append(Lance((origem, destino), (), criar_estado(novas, rivais)))
    return tuple(movimentos)


def rotulo_lance(lance: Lance) -> str:
    separador = " × " if lance.capturadas else " → "
    return separador.join(nome_casa(casa) for casa in lance.caminho)
