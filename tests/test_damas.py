"""Regras do final e fluxo entregue para a demonstração."""

from collections import Counter

from projeto_ia.damas.dataset import carregar_dados, estado_da_linha
from projeto_ia.damas.game import Estado, lances_legais, nome_casa
from projeto_ia.damas.inference import analisar_lances, analisar_respostas, carregar_modelo, mapa_respostas, prever


CASA = {nome_casa(indice): indice for indice in range(32)}


def test_captura_obrigatoria_e_salto_multiplo():
    estado = Estado((CASA["c3"],), tuple(sorted((CASA["d4"], CASA["f6"]))), "V")
    lances = lances_legais(estado)
    assert len(lances) == 1
    assert tuple(nome_casa(casa) for casa in lances[0].caminho) == ("c3", "e5", "g7")
    assert len(lances[0].capturadas) == 2
    assert lances[0].proximo.pretas == ()


def test_base_e_classes_do_final():
    dados, auditoria = carregar_dados()
    assert len(dados) == 61504
    assert auditoria.ausentes == 0
    assert auditoria.duplicados_removidos == 0
    assert Counter(dados["resultado"]) == {"win": 30976, "loss": 26252, "draw": 4276}


def test_palpite_e_todos_os_lances_de_cada_tipo():
    dados, _ = carregar_dados()
    respostas = mapa_respostas(dados)
    artefato = carregar_modelo()
    for esperado in ("win", "loss", "draw"):
        indice = next(i for i in artefato["indices_teste"] if dados.at[i, "resultado"] == esperado)
        estado = estado_da_linha(dados.iloc[indice])
        assert prever(estado, artefato) in {"win", "loss", "draw"}
        analise = analisar_lances(estado, respostas)
        assert len(analise) == len(lances_legais(estado))
        ordem = {"loss": 0, "draw": 1, "win": 2}
        for lance, resultado in analise:
            respostas_rival = analisar_respostas(lance, respostas)
            assert len(respostas_rival) == len(lances_legais(lance.proximo))
            assert resultado == (min((valor for _, valor in respostas_rival), key=ordem.get) if respostas_rival else "win")
        resultados = [resultado for _, resultado in analise]
        if esperado == "win":
            assert "win" in resultados
        elif esperado == "loss":
            assert not resultados or set(resultados) == {"loss"}
        else:
            assert "win" not in resultados and "draw" in resultados
