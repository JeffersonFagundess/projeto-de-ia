"""Gera os sprites antialiasados e o ícone da aplicação, sem rede.

Executar apenas ao editar a identidade visual: python -m tools.gerar_recursos_interface.
O jogo consome os PNGs prontos e não precisa do Pillow em tempo de execução.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from projeto_ia.style import palette as p
from projeto_ia.style.fonts import FONT_AWESOME
from projeto_ia.style.icons import ICONES_FONT_AWESOME
from projeto_ia.style.images import VARIANTES_ICONES

DESTINO = Path(__file__).resolve().parents[1] / "src/projeto_ia/style/assets/images"
DESTINO_ICONES = DESTINO / "icons"
DESTINO_PECAS = DESTINO / "pieces"

CORES_ICONES = {
    "claro": p.TEXTO,
    "escuro": p.FUNDO,
    "ciano": p.CIANO,
    "suave": p.SUAVE,
    "desabilitado": p.DESABILITADO,
}


def interpolar(inicio, fim, fracao):
    return tuple(round(a+(b-a)*fracao) for a, b in zip(inicio, fim))


def peca(tamanho, vermelha, dama=False):
    """Desenha em 6× e reduz com Lanczos para preservar o antialiasing."""
    escala = 6
    imagem = Image.new("RGBA", (tamanho*escala, tamanho*escala))
    desenho = ImageDraw.Draw(imagem)
    centro = tamanho*escala/2
    raio = tamanho*escala*.375

    def circulo(r, cor, dy=0, borda=None, largura=1):
        desenho.ellipse((centro-r, centro-r+dy, centro+r, centro+r+dy),
                        fill=cor, outline=borda, width=largura)

    circulo(raio+escala, (2, 8, 17, 110), escala*2)
    circulo(raio, "#6C263E" if vermelha else "#09121E", escala*1.6)
    circulo(raio, "#FF9FA4" if vermelha else "#B1CDE1")
    externo, interno = ((234, 91, 111), (170, 43, 76)) if vermelha else ((62, 89, 112), (25, 43, 64))
    for r in range(int(raio-escala), 0, -1):
        circulo(r, interpolar(externo, interno, 1-r/raio))
    r = raio*.79
    desenho.arc((centro-r, centro-r, centro+r, centro+r), 195, 345,
                fill="#FFBCC1" if vermelha else "#8AAFC6", width=escala)
    r = raio*.66
    desenho.ellipse((centro-r, centro-r, centro+r, centro+r),
                    outline="#F38696" if vermelha else "#63869F", width=max(2, escala//2))
    if dama:
        pontos = ((-.43,.22),(-.51,-.30),(-.22,-.10),(0,-.45),(.22,-.10),(.51,-.30),(.43,.22))
        desenho.polygon([(centro+x*raio,centro+y*raio) for x,y in pontos], fill="#FFF1B9")
        desenho.line((centro-raio*.36,centro+raio*.36,centro+raio*.36,centro+raio*.36),
                     fill="#FFF1B9",width=escala)
    else:
        circulo(raio*.12, "#FFB0BA" if vermelha else "#96B7CE")
    return imagem.resize((tamanho,tamanho),Image.Resampling.LANCZOS)


def icone_font_awesome(codigo, cor, tamanho=20):
    """Rasteriza um glifo oficial sem exigir instalação da fonte no sistema."""
    escala = 4
    lado = tamanho * escala
    imagem = Image.new("RGBA", (lado, lado))
    desenho = ImageDraw.Draw(imagem)
    fonte = ImageFont.truetype(str(FONT_AWESOME), int(lado * .68))
    caixa = desenho.textbbox((0, 0), codigo, font=fonte)
    largura, altura = caixa[2] - caixa[0], caixa[3] - caixa[1]
    posicao = ((lado-largura)/2-caixa[0], (lado-altura)/2-caixa[1])
    desenho.text(posicao, codigo, font=fonte, fill=cor)
    return imagem.resize((tamanho, tamanho), Image.Resampling.LANCZOS)


def main():
    DESTINO.mkdir(parents=True,exist_ok=True)
    DESTINO_ICONES.mkdir(parents=True, exist_ok=True)
    DESTINO_PECAS.mkdir(parents=True, exist_ok=True)
    for nome, variantes in VARIANTES_ICONES.items():
        for variante in variantes:
            icone_font_awesome(ICONES_FONT_AWESOME[nome], CORES_ICONES[variante]).save(
                DESTINO_ICONES / f"{nome}_{variante}.png"
            )
    for tamanho in (22, 40, 48):
        for cor in ("vermelha", "preta"):
            for dama in (False, True):
                tipo = "dama" if dama else "peca"
                peca(tamanho, cor == "vermelha", dama).save(
                    DESTINO_PECAS / f"{cor}_{tipo}_{tamanho}.png"
                )
    icone = Image.new("RGBA",(1024,1024))
    desenho = ImageDraw.Draw(icone)
    desenho.rounded_rectangle((24,24,1000,1000),radius=232,fill="#0C1A2A",outline="#3D7F83",width=24)
    desenho.ellipse((155,190,869,904),fill="#08131E",outline="#264B57",width=12)
    desenho.ellipse((155,134,869,848),fill="#163A43",outline="#67E8D2",width=32)
    desenho.ellipse((224,203,800,779),outline="#38746F",width=12)
    desenho.polygon(((330,560),(290,354),(424,439),(512,287),(600,439),(734,354),(694,560)),fill="#8BF5DE")
    desenho.rounded_rectangle((341,605,683,649),radius=15,fill="#8BF5DE")
    icone=icone.resize((256,256),Image.Resampling.LANCZOS)
    icone.save(DESTINO/"damas.png")
    icone.save(DESTINO/"damas.ico",sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])


if __name__ == "__main__":
    main()
