"""Garantias da organização src, recursos e sistema visual centralizado."""

from projeto_ia.paths import (
    BASE_COMPLETAS,
    BASE_FINAIS,
    MODELO_COMPLETAS,
    MODELO_FINAIS,
    RAIZ,
    RECURSOS,
    TABELA_FINAIS,
)
from projeto_ia.style.fonts import FONT_AWESOME, LICENCA_FONT_AWESOME
from projeto_ia.style.images import (
    ICONE_ICO,
    ICONE_PNG,
    PASTA_ICONES,
    PASTA_PECAS,
    TAMANHOS_PECAS,
    VARIANTES_ICONES,
    caminho_icone,
    caminho_peca,
)


def test_layout_src_e_recursos_centralizados():
    assert (RAIZ / "src/projeto_ia").is_dir()
    assert (RAIZ / "tools").is_dir()
    assert RECURSOS == RAIZ / "resources"
    assert all(caminho.is_file() for caminho in (
        BASE_COMPLETAS, BASE_FINAIS, MODELO_COMPLETAS, MODELO_FINAIS,
        TABELA_FINAIS,
    ))


def test_estilo_centraliza_imagens_em_uso():
    imagens = {arquivo.name for arquivo in ICONE_PNG.parent.iterdir() if arquivo.is_file()}
    assert imagens == {ICONE_ICO.name, ICONE_PNG.name}
    esperadas = {
        caminho_peca(cor, tipo, tamanho).name
        for cor in ("vermelha", "preta")
        for tipo in ("peca", "dama")
        for tamanho in TAMANHOS_PECAS
    }
    assert {arquivo.name for arquivo in PASTA_PECAS.iterdir()} == esperadas
    icones = {
        caminho_icone(nome, variante).name
        for nome, variantes in VARIANTES_ICONES.items()
        for variante in variantes
    }
    assert {arquivo.name for arquivo in PASTA_ICONES.iterdir()} == icones
    assert not (RAIZ / "src/projeto_ia/ui/assets").exists()


def test_font_awesome_local_tem_licenca():
    assert FONT_AWESOME.is_file() and FONT_AWESOME.stat().st_size > 400_000
    assert LICENCA_FONT_AWESOME.is_file()
    assert "SIL OFL 1.1" in LICENCA_FONT_AWESOME.read_text(encoding="utf-8")
