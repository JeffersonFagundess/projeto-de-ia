"""Uma partida explorável, com histórico e desfazer, independente da interface."""

from .game import Estado, Lance, lances_legais


class Partida:
    def __init__(self, inicial: Estado):
        self.inicial = inicial
        self.estado = inicial
        self.historico: list[tuple[Estado, Lance]] = []

    @property
    def lances(self):
        return lances_legais(self.estado)

    @property
    def vencedor(self):
        if self.lances:
            return None
        return "P" if self.estado.vez == "V" else "V"

    def jogar(self, lance: Lance):
        if lance not in self.lances:
            raise ValueError("Essa jogada não está disponível neste tabuleiro.")
        self.historico.append((self.estado, lance))
        self.estado = lance.proximo

    def voltar(self):
        if self.historico:
            self.estado, _ = self.historico.pop()

    def recomecar(self):
        self.estado = self.inicial
        self.historico.clear()

    def caminhos_recentes(self):
        por_cor = {}
        for estado, lance in reversed(self.historico):
            por_cor.setdefault(estado.vez, lance.caminho)
            if len(por_cor) == 2:
                break
        return tuple(por_cor.values())
