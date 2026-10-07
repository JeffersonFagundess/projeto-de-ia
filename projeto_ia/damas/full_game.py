"""Partida completa de damas inglesas: peões, damas, capturas e empates."""

from dataclasses import dataclass

from .game import CASAS, DIRECOES, INDICE


@dataclass(frozen=True)
class Posicao:
    vermelhas: tuple[int, ...]
    pretas: tuple[int, ...]
    vez: str = "V"
    damas: frozenset[int] = frozenset()

    def __post_init__(self):
        ocupadas = self.vermelhas + self.pretas
        if self.vez not in ("V", "P") or len(set(ocupadas)) != len(ocupadas):
            raise ValueError("Posição inválida.")
        if any(c not in range(32) for c in ocupadas) or not self.damas <= set(ocupadas):
            raise ValueError("Casas ou damas inválidas.")


@dataclass(frozen=True)
class Movimento:
    caminho: tuple[int, ...]
    capturadas: tuple[int, ...]
    proximo: Posicao


def inicial():
    return Posicao(tuple(range(20, 32)), tuple(range(12)))


def movimentos(estado):
    nossas = estado.vermelhas if estado.vez == "V" else estado.pretas
    rivais = estado.pretas if estado.vez == "V" else estado.vermelhas
    if not nossas or not rivais:
        return ()
    frente = -1 if estado.vez == "V" else 1
    ultima = 0 if estado.vez == "V" else 7
    capturas, simples = [], []

    def vizinha(casa, dr, dc, distancia=1):
        linha, coluna = CASAS[casa]
        return INDICE.get((linha + dr * distancia, coluna + dc * distancia))

    for origem in nossas:
        dama = origem in estado.damas
        direcoes = DIRECOES if dama else ((frente, -1), (frente, 1))
        outras = set(nossas) - {origem}

        def criar(atual, restantes, caminho, removidas):
            promovida = dama or CASAS[atual][0] == ultima
            damas = (estado.damas - {origem} - set(removidas)) | ({atual} if promovida else set())
            a, b = tuple(sorted(outras | {atual})), tuple(sorted(restantes))
            proximo = Posicao(a, b, "P", frozenset(damas)) if estado.vez == "V" else Posicao(b, a, "V", frozenset(damas))
            return Movimento(caminho, removidas, proximo)

        def saltar(atual, restantes, caminho, removidas):
            # Ao coroar um peão, o turno termina mesmo se a nova dama puder saltar.
            if removidas and not dama and CASAS[atual][0] == ultima:
                capturas.append(criar(atual, restantes, caminho, removidas))
                return
            encontrou = False
            for dr, dc in direcoes:
                meio, destino = vizinha(atual, dr, dc), vizinha(atual, dr, dc, 2)
                if meio in restantes and destino is not None and destino not in restantes and destino not in outras:
                    encontrou = True
                    saltar(destino, restantes - {meio}, caminho + (destino,), removidas + (meio,))
            if removidas and not encontrou:
                capturas.append(criar(atual, restantes, caminho, removidas))

        saltar(origem, set(rivais), (origem,), ())
        for dr, dc in direcoes:
            destino = vizinha(origem, dr, dc)
            if destino is not None and destino not in nossas and destino not in rivais:
                simples.append(criar(destino, set(rivais), (origem, destino), ()))
    return tuple(capturas or simples)


class Jogo:
    def __init__(self, estado=None):
        self.estado = estado or inicial()
        self.historico = []
        self.sem_progresso = 0

    @property
    def resultado(self):
        if not movimentos(self.estado):
            return "P" if self.estado.vez == "V" else "V"
        repeticoes = 1 + sum(anterior == self.estado for anterior, _, _ in self.historico)
        if repeticoes >= 3 or self.sem_progresso >= 80:
            return "empate"
        return None

    @property
    def lances(self):
        return () if self.resultado else movimentos(self.estado)

    def jogar(self, lance):
        if lance not in self.lances:
            raise ValueError("Jogada indisponível.")
        self.historico.append((self.estado, lance, self.sem_progresso))
        self.sem_progresso = 0 if lance.capturadas or lance.caminho[0] not in self.estado.damas else self.sem_progresso + 1
        self.estado = lance.proximo

    def voltar(self):
        if self.historico:
            self.estado, _, self.sem_progresso = self.historico.pop()

    def caminhos_recentes(self):
        cores = {}
        for estado, lance, _ in reversed(self.historico):
            cores.setdefault(estado.vez, lance.caminho)
            if len(cores) == 2:
                break
        return tuple(cores.values())
