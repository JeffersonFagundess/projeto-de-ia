"""Armazenamento temporário e paginado de buscas detalhadas."""

import sqlite3
import tempfile
import uuid
from pathlib import Path

PASTA_RASTROS = Path(tempfile.gettempdir()) / "projeto-ia-damas"


class GravadorRastro:
    """Grava dezenas de milhares de nós em lotes, sem trafegar pela fila da UI."""

    COLUNAS = (
        "id", "pai", "iteracao", "ply", "restante", "origem", "destino",
        "vermelhas", "pretas", "damas", "vez", "alfa", "beta", "nota", "motivo",
    )

    def __init__(self):
        PASTA_RASTROS.mkdir(parents=True, exist_ok=True)
        self.caminho = PASTA_RASTROS / f"busca-{uuid.uuid4().hex}.sqlite3"
        self.conexao = sqlite3.connect(self.caminho)
        self.conexao.execute("PRAGMA journal_mode=OFF")
        self.conexao.execute("PRAGMA synchronous=OFF")
        self.conexao.execute("PRAGMA temp_store=MEMORY")
        self.conexao.execute(
            """CREATE TABLE nos (
                id INTEGER PRIMARY KEY, pai INTEGER NOT NULL,
                iteracao INTEGER NOT NULL, ply INTEGER NOT NULL,
                restante INTEGER NOT NULL, origem INTEGER NOT NULL,
                destino INTEGER NOT NULL, vermelhas INTEGER NOT NULL,
                pretas INTEGER NOT NULL, damas INTEGER NOT NULL,
                vez INTEGER NOT NULL, alfa REAL, beta REAL,
                nota REAL NOT NULL, motivo TEXT NOT NULL
            )"""
        )
        self.conexao.execute("CREATE TABLE meta (chave TEXT PRIMARY KEY, valor TEXT NOT NULL)")
        self.buffer = []

    def __call__(self, dados):
        self.buffer.append(tuple(dados[coluna] for coluna in self.COLUNAS))
        if len(self.buffer) >= 500:
            self._despejar()

    def _despejar(self):
        if not self.buffer:
            return
        marcadores = ",".join("?" for _ in self.COLUNAS)
        self.conexao.executemany(
            f"INSERT INTO nos ({','.join(self.COLUNAS)}) VALUES ({marcadores})",
            self.buffer,
        )
        self.buffer.clear()

    def concluir(self, analise):
        self._despejar()
        metadados = {
            "nos": analise.nos,
            "profundidade": analise.profundidade,
            "nota": analise.nota,
            "alternativas": analise.alternativas,
        }
        self.conexao.executemany(
            "INSERT INTO meta (chave,valor) VALUES (?,?)",
            ((chave, str(valor)) for chave, valor in metadados.items()),
        )
        self.conexao.execute("CREATE INDEX idx_nos_iteracao ON nos(iteracao,id)")
        self.conexao.execute("CREATE INDEX idx_nos_pai ON nos(pai)")
        self.conexao.commit()
        self.conexao.close()
        return self.caminho

    def descartar(self):
        try:
            self.conexao.close()
        finally:
            self.caminho.unlink(missing_ok=True)


def remover_rastro(caminho):
    if caminho:
        Path(caminho).unlink(missing_ok=True)
