"""Política da demonstração: somente um lado recebe ajuda."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Configuracao:
    modo: str = "dupla"
    lado_assistido: str = "V"

    def __post_init__(self):
        if self.modo not in ("dupla", "computador") or self.lado_assistido not in ("V", "P"):
            raise ValueError("Configuração de partida inválida.")

    def usa_computador(self, vez):
        return self.modo == "computador" and vez != self.lado_assistido

    def permite_ajuda(self, vez):
        return vez == self.lado_assistido
