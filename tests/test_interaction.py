"""Responsividade, telemetria incremental e integridade dos efeitos sonoros."""

import sqlite3
import wave
from contextlib import closing
from hashlib import sha256

import numpy as np

from projeto_ia.damas.full_game import inicial
from projeto_ia.damas.match import Configuracao
from projeto_ia.damas.opponent import analisar
from projeto_ia.damas.trace_store import GravadorRastro, remover_rastro
from projeto_ia.paths import BASE_FINAIS, TABELA_FINAIS
from projeto_ia.sounds.player import EFEITOS, LICENCA
from projeto_ia.ui.app import JanelaPrincipal


def test_telemetria_publica_pulsos_durante_a_busca():
    eventos = []
    analisar(
        inicial(),
        segundos=.25,
        profundidade_maxima=20,
        progresso=eventos.append,
    )
    assert eventos
    assert any(evento["completo"] for evento in eventos)
    assert any(not evento["completo"] for evento in eventos)
    assert [evento["nos"] for evento in eventos] == sorted(
        evento["nos"] for evento in eventos
    )


def test_rastro_detalhado_e_persistido_para_consulta_paginada():
    gravador = GravadorRastro()
    resultado = analisar(
        inicial(), segundos=.15, profundidade_maxima=8, detalhe=gravador,
    )
    caminho = gravador.concluir(resultado)
    try:
        with closing(sqlite3.connect(caminho)) as conexao:
            total = conexao.execute("SELECT COUNT(*) FROM nos").fetchone()[0]
            colunas = {
                linha[1] for linha in conexao.execute("PRAGMA table_info(nos)")
            }
            assert total == resultado.nos
            assert total > 100
            assert {"id", "pai", "iteracao", "nota", "motivo"} <= colunas
            assert conexao.execute(
                "SELECT COUNT(*) FROM nos WHERE pai=0"
            ).fetchone()[0] > 0
    finally:
        remover_rastro(caminho)
    assert not caminho.exists()


def test_sons_locais_sao_wav_validos_e_tem_licenca():
    assert set(EFEITOS) == {
        "alternar", "clique", "derrota", "dica", "empate", "erro", "mover",
        "selecionar", "vitoria",
    }
    for arquivo in EFEITOS.values():
        assert arquivo.is_file()
        with wave.open(str(arquivo), "rb") as audio:
            assert audio.getnframes() > 0
            assert audio.getframerate() > 0
    assert "Creative Commons Zero" in LICENCA.read_text(encoding="utf-8")


def test_resultado_contra_computador_distingue_vitoria_e_derrota():
    janela = object.__new__(JanelaPrincipal)
    janela.config = Configuracao("computador", "V")
    assert janela._descricao_resultado("V")[0] == "vitoria"
    assert janela._descricao_resultado("P")[0] == "derrota"
    assert janela._descricao_resultado("empate")[0] == "empate"


def test_tabela_compacta_corresponde_ao_csv_auditavel():
    with np.load(TABELA_FINAIS, allow_pickle=False) as tabela:
        assert tabela["versao"].tolist() == [1]
        assert len(tabela["resultado"]) == 61504
        assert int((tabela["distancia"] >= 0).sum()) == 57228
        assert tabela["sha256_csv"].item() == sha256(BASE_FINAIS.read_bytes()).hexdigest()
