"""Duelo local: um participante com ML, outro sem recomendações."""

import json
import queue
import random
import threading
import tkinter as tk

from projeto_ia.damas.full_game import Jogo, Posicao
from projeto_ia.damas.game import nome_casa
from projeto_ia.damas.learning import RAIZ
from projeto_ia.damas.match import Configuracao
from projeto_ia.damas.assistant import analisar_turno
from projeto_ia.ui.board import Tabuleiro
from projeto_ia.ui.identity import configurar_icone, identificar_aplicativo
from projeto_ia.ui import theme as t
from projeto_ia.ui.widgets import Botao, Escolha, mostrar_informacao
from projeto_ia.paths import RELATORIO_COMPLETAS
from projeto_ia.damas.endgame_table import avaliacao_exata
from projeto_ia.damas.search_board import compactar

FUNDO, PAPEL, TEXTO, SUAVE = t.FUNDO, t.PAINEL, t.TEXTO, t.SUAVE
AZUL, CORAL, LINHA = t.CIANO, t.CORAL, t.LINHA


def nome(cor):
    return "vermelhas" if cor == "V" else "pretas"


class JanelaPrincipal:
    def __init__(self, root):
        self.root = root
        configurar_icone(root)
        root.title("Damas | Duelo com IA")
        root.geometry("980x660")
        root.minsize(980, 660)
        root.configure(bg=FUNDO)
        self.config = Configuracao()
        self.gerador = random.Random()
        self.jogo = Jogo()
        self.origem = self.sugestao = self.analise = None
        self.ocupado = False
        self.geracao = 0
        self.cancelamento = threading.Event()
        self.demonstracao = False
        self.placar = {"com":0, "sem":0, "empate":0}
        self.resultado_contado = None
        self._montar()
        self.atualizar()
        self.responder()
        root.protocol("WM_DELETE_WINDOW", self.fechar)
        t.titulo_escuro(root)

    @staticmethod
    def texto(pai, text="", tamanho=10, cor=TEXTO, forte=False, **kw):
        return tk.Label(pai, text=text, bg=pai.cget("bg"), fg=cor,
                        font=("Segoe UI Semibold" if forte else "Segoe UI", tamanho), **kw)

    @staticmethod
    def botao(pai, texto, comando, principal=False):
        return Botao(pai, texto, comando, principal)

    def _montar(self):
        topo = tk.Frame(self.root, bg=FUNDO)
        topo.pack(fill="x", padx=20, pady=(12, 10))
        marca = tk.Canvas(topo, width=42, height=42, bg=FUNDO, highlightthickness=0)
        marca.pack(side="left", padx=(0, 12))
        marca.create_oval(2, 2, 40, 40, outline="#255753", width=2)
        marca.create_oval(8, 8, 34, 34, fill=t.CIANO_ESCURO, outline=AZUL, width=2)
        marca.create_polygon(14, 24, 12, 16, 18, 20, 21, 13, 24, 20, 30, 16, 28, 24, fill=AZUL)
        marca.create_line(15, 28, 27, 28, fill=AZUL, width=2)
        self.texto(topo, "DAMAS", 24, forte=True).pack(side="left")
        tk.Frame(topo, width=1, height=25, bg=LINHA).pack(side="left", padx=18)
        assinatura = tk.Frame(topo, bg=FUNDO)
        assinatura.pack(side="left")
        self.texto(assinatura, "DUELO COM IA", 10, AZUL, True).pack(anchor="w")
        self.texto(assinatura, "Dois lados. Um jogador com ajuda.", 9, SUAVE).pack(anchor="w")
        self.botao(topo, "+  Nova partida", self.nova).pack(side="right")

        barra = tk.Frame(self.root, bg=FUNDO)
        barra.pack(fill="x", padx=20, pady=(0, 12))
        adversario = tk.Frame(barra, bg=FUNDO)
        adversario.pack(side="left", padx=(0, 20))
        self.texto(adversario, "JOGAR CONTRA", 8, SUAVE, True).pack(anchor="w", pady=(0, 4))
        self.modo = Escolha(adversario, ("Outra pessoa", "Computador"), largura=111)
        self.modo.pack()
        self.modo.bind("<<ComboboxSelected>>", self.configurar)
        assistencia = tk.Frame(barra, bg=FUNDO)
        assistencia.pack(side="left")
        self.texto(assistencia, "QUEM RECEBE AJUDA", 8, SUAVE, True).pack(anchor="w", pady=(0, 4))
        self.lado = Escolha(assistencia, ("Jogador 1", "Jogador 2"), largura=103)
        self.lado.pack()
        self.lado.bind("<<ComboboxSelected>>", self.configurar)
        self.botao(barra, "▷  Exemplo rápido", self.exemplo).pack(side="right", anchor="s")

        corpo = tk.Frame(self.root, bg=FUNDO)
        corpo.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        esquerda = tk.Frame(corpo, bg=PAPEL, padx=12, pady=12,
                            highlightthickness=1, highlightbackground=LINHA)
        esquerda.pack(side="left", fill="y")
        cabecalho = tk.Frame(esquerda, bg=PAPEL)
        cabecalho.pack(fill="x", pady=(0, 10))
        self.texto(cabecalho, "TABULEIRO", 8, SUAVE, True).pack(side="left")
        self.caption = tk.StringVar()
        self.texto(cabecalho, textvariable=self.caption, tamanho=8, cor=SUAVE).pack(side="right")
        moldura = tk.Frame(esquerda, bg="#365369", padx=4, pady=4)
        moldura.pack()
        self.tabuleiro = Tabuleiro(moldura, tamanho=384, ao_clicar=self.clicar)
        self.tabuleiro.pack()
        legenda = tk.Frame(esquerda, bg=PAPEL)
        legenda.pack(fill="x", pady=(12, 5))
        self.texto(legenda, "1  Escolha uma peça", 9, TEXTO).pack(side="left", padx=(4, 15))
        self.texto(legenda, "2  Vá para a casa verde", 9, AZUL).pack(side="left")
        self.texto(esquerda, "Coroa = dama  ·  Capturar é obrigatório", 9, SUAVE).pack()

        direita = tk.Frame(corpo, bg=PAPEL, padx=16, pady=12,
                           highlightthickness=1, highlightbackground=LINHA)
        direita.pack(side="left", fill="both", expand=True, padx=(14,0))
        jogadores = tk.Frame(direita,bg=PAPEL)
        jogadores.pack(fill="x")
        jogadores.grid_columnconfigure((0, 1), weight=1, uniform="jogadores")
        self.cards = {}
        for indice, cor in enumerate(("V","P")):
            card=tk.Frame(jogadores,bg=t.ELEVADO,padx=10,pady=7,highlightthickness=1,highlightbackground=LINHA)
            card.grid(row=0,column=indice,sticky="nsew",padx=(0,5) if cor == "V" else (5,0))
            nome_jogador=self.texto(card, f"●  Jogador {1 if cor == 'V' else 2}",11,CORAL if cor == "V" else t.PRATA,True)
            nome_jogador.pack(anchor="w")
            role=self.texto(card, tamanho=9,cor=SUAVE);role.pack(anchor="w",pady=(2,0))
            self.cards[cor]=(card,nome_jogador,role)
        self.titulo=tk.StringVar()
        self.texto(direita,textvariable=self.titulo,tamanho=21,forte=True).pack(anchor="w",pady=(12,3))
        self.instrucao=tk.StringVar()
        self.texto(direita,textvariable=self.instrucao,tamanho=10,cor=SUAVE,wraplength=450,justify="left",height=2,anchor="nw").pack(fill="x")

        self.ajuda_frame=tk.Frame(direita,bg=t.CIANO_ESCURO,padx=12,pady=10,
                                  highlightthickness=1,highlightbackground="#2E6862")
        self.ajuda_frame.pack(fill="x",pady=(6,8))
        self.status_ia=tk.StringVar()
        self.ajuda_titulo=self.texto(self.ajuda_frame,textvariable=self.status_ia,tamanho=10,cor=AZUL,forte=True)
        self.ajuda_titulo.pack(anchor="w")
        self.motivo=tk.StringVar()
        self.ajuda_texto=self.texto(self.ajuda_frame,textvariable=self.motivo,wraplength=420,justify="left",height=3,anchor="nw")
        self.ajuda_texto.pack(fill="x",pady=(5,0))
        self.bt_jogar=self.botao(direita,"Jogar com a sugestão  →",self.aplicar_sugestao,True)
        self.bt_jogar.pack(fill="x")
        acoes=tk.Frame(direita,bg=PAPEL);acoes.pack(fill="x",pady=(7,10))
        self.bt_dica=self.botao(acoes,"Pensar mais",lambda:self.buscar(aprofundar=True))
        self.bt_dica.pack(side="left",expand=True,fill="x",padx=(0,4))
        self.bt_voltar=self.botao(acoes,"↶  Desfazer",self.voltar)
        self.bt_voltar.pack(side="left",expand=True,fill="x",padx=(4,0))
        self.relato=tk.StringVar(value="As vermelhas começam. Você pode aceitar a dica ou escolher outra jogada.")
        self.texto(direita,textvariable=self.relato,tamanho=9,cor=SUAVE,wraplength=450,justify="left",height=2,anchor="nw").pack(fill="x")
        rodape=tk.Frame(direita,bg=PAPEL);rodape.pack(side="bottom",fill="x")
        tk.Frame(rodape,height=1,bg=LINHA).pack(fill="x",pady=(4,8))
        self.serie=tk.StringVar()
        self.texto(rodape,textvariable=self.serie,tamanho=9,cor=SUAVE).pack(anchor="w",pady=(0,8))
        links=tk.Frame(rodape,bg=PAPEL);links.pack(fill="x")
        for texto,comando in (("Como demonstrar",self.guia),("Regras",self.regras),("Sobre a IA",self.sobre)):
            link=self.texto(links,texto,9,AZUL,cursor="hand2",takefocus=1);link.pack(side="left",padx=(0,18))
            link.bind("<Button-1>",lambda _e,c=comando:c())
            link.bind("<Return>",lambda _e,c=comando:c())
            link.bind("<space>",lambda _e,c=comando:c())
            link.bind("<FocusIn>",lambda e:e.widget.configure(fg=TEXTO))
            link.bind("<FocusOut>",lambda e:e.widget.configure(fg=AZUL))

    def atualizar(self):
        self.origem=self.sugestao=self.analise=None
        e=self.jogo.estado; fim=self.jogo.resultado
        for cor,(card,titulo,role) in self.cards.items():
            assistido=self.config.permite_ajuda(cor)
            quantidade=len(e.vermelhas if cor == "V" else e.pretas)
            role.configure(text=f"{'COM IA' if assistido else 'SEM DICAS'} · {quantidade} {'peça' if quantidade == 1 else 'peças'}",fg=AZUL if assistido else SUAVE)
            titulo.configure(text=f"●  {'Computador' if self.config.usa_computador(cor) else 'Jogador '+('1' if cor == 'V' else '2')}")
            card.configure(highlightbackground=(CORAL if cor == "V" else t.PRATA) if e.vez == cor and not fim else LINHA)
        n = len(self.jogo.historico)
        self.caption.set("EXEMPLO PREPARADO" if self.demonstracao else f"{n:02d} {'JOGADA' if n == 1 else 'JOGADAS'} · PARTIDA COMPLETA")
        self.titulo.set("Empate" if fim == "empate" else f"{nome(fim).capitalize()} venceram!" if fim else f"Vez do {'computador' if self.config.usa_computador(e.vez) else 'jogador 1' if e.vez == 'V' else 'jogador 2'}")
        self.instrucao.set("A partida terminou. Comece outra para trocar os papéis." if fim else f"Mova uma peça {'vermelha' if e.vez == 'V' else 'preta'} para uma casa verde.")
        self.bt_jogar.configure(state="disabled",text="Jogar com a sugestão  →")
        self.bt_dica.configure(state="disabled")
        self.bt_voltar.configure(state="normal" if self.jogo.historico or self.ocupado else "disabled")
        com_ajuda = self.config.permite_ajuda(e.vez) and not fim
        fundo_ajuda = t.CIANO_ESCURO if com_ajuda else t.ELEVADO
        self.ajuda_frame.configure(bg=fundo_ajuda,highlightbackground="#2E6862" if com_ajuda else LINHA)
        self.ajuda_titulo.configure(bg=fundo_ajuda,fg=AZUL if com_ajuda else t.PRATA)
        self.ajuda_texto.configure(bg=fundo_ajuda)
        if fim:
            self.status_ia.set("Resultado da partida")
            self.motivo.set("Empate por repetição ou falta de progresso." if fim == "empate" else f"As {nome(e.vez)} ficaram sem peças ou sem movimentos.")
            if not self.demonstracao and self.resultado_contado is None:
                chave="empate" if fim == "empate" else "com" if fim == self.config.lado_assistido else "sem"
                self.placar[chave]+=1;self.resultado_contado=chave
        elif self.config.permite_ajuda(e.vez):
            self.status_ia.set("●  Assistente da IA")
            self.motivo.set("Preparando uma sugestão para este jogador…")
        else:
            self.status_ia.set("Sua estratégia, sua jogada")
            self.motivo.set("Este jogador está sem ajuda. Escolha uma peça e depois uma casa verde.")
            self.bt_jogar.configure(text="Sem dicas nesta vez")
        self.tabuleiro.exibir(e,caminhos=self.jogo.caminhos_recentes())
        self.serie.set(f"PLACAR    Com IA  {self.placar['com']}    /    Sem ajuda  {self.placar['sem']}    /    Empates  {self.placar['empate']}")

    def cancelar(self):
        self.geracao+=1
        self.cancelamento.set();self.cancelamento=threading.Event()
        self.tabuleiro.cancelar();self.ocupado=False

    def fechar(self):
        self.cancelar();self.root.destroy()

    def nova(self):
        self.cancelar();self.demonstracao=False;self.jogo=Jogo();self.resultado_contado=None
        self.relato.set("Nova partida: 12 peças de cada lado. Só o jogador marcado ‘Com IA’ recebe sugestões.")
        self.atualizar();self.responder()

    def configurar(self,_evento=None):
        self.config=Configuracao("dupla" if self.modo.current() == 0 else "computador","V" if self.lado.current() == 0 else "P")
        self.nova()

    def exemplo(self):
        self.cancelar();self.demonstracao=True;self.resultado_contado=None
        casa={nome_casa(i):i for i in range(32)}
        estado=Posicao(tuple(sorted(casa[c] for c in ('a1','c1','h2'))),tuple(sorted(casa[c] for c in ('d2','f4','f6'))))
        self.config=Configuracao();self.modo.current(0);self.lado.current(0)
        self.jogo=Jogo(estado)
        self.relato.set("Exemplo preparado para a apresentação. A sequência mostra uma captura múltipla; não conta no placar.")
        self.atualizar();self.responder()

    def clicar(self,casa):
        if self.ocupado or self.jogo.resultado or self.config.usa_computador(self.jogo.estado.vez):return
        lances=self.jogo.lances
        destinos=[l for l in lances if l.caminho[0] == self.origem and l.caminho[-1] == casa]
        if destinos:
            if len(destinos) == 1:self.jogar(destinos[0])
            else:
                from .options import mostrar_opcoes
                mostrar_opcoes(self.root,self.jogo.estado,[(l,"") for l in destinos],self.jogar,lambda *_:"Caminho permitido",rodape="Escolha por onde fazer a captura.")
            return
        opcoes=[l for l in lances if l.caminho[0] == casa]
        if not opcoes:
            self.instrucao.set("Há uma captura obrigatória. Escolha a peça que pode capturar." if any(l.capturadas for l in lances) else f"Escolha uma peça das {nome(self.jogo.estado.vez)} que possa se mover.")
            return
        self.origem=casa
        self.tabuleiro.exibir(self.jogo.estado,selecionada=casa,destinos={l.caminho[-1] for l in opcoes})
        self.instrucao.set("Agora clique em uma das casas verdes.")

    def jogar(self,lance):
        if self.ocupado or lance not in self.jogo.lances:return
        self.ocupado=True;self.bt_jogar.configure(state="disabled");self.bt_dica.configure(state="disabled")
        anterior=self.jogo.estado;self.instrucao.set("Observe o movimento…")
        def terminou():
            self.jogo.jogar(lance);self.ocupado=False
            n=len(lance.capturadas)
            acao=(f"capturaram {n} "+("peça." if n == 1 else "peças.")) if n else "moveram uma peça."
            relato=f"As {nome(anterior.vez)} {acao}"
            if lance.caminho[0] not in anterior.damas and lance.caminho[-1] in lance.proximo.damas:relato+=" A peça virou dama."
            self.relato.set(relato);self.atualizar();self.responder()
        self.tabuleiro.animar(anterior,lance,terminou)

    def responder(self):
        if self.jogo.resultado:return
        vez=self.jogo.estado.vez
        if self.config.usa_computador(vez):self.buscar(True)
        elif self.config.permite_ajuda(vez):self.buscar(False)

    def buscar(self,executar=False,aprofundar=False):
        vez=self.jogo.estado.vez
        permitido=self.config.usa_computador(vez) if executar else self.config.permite_ajuda(vez)
        if not permitido or self.ocupado or self.jogo.resultado:return
        self.ocupado=True;token=self.geracao;estado=self.jogo.estado;evento=self.cancelamento
        historico=tuple(e for e,_,_ in self.jogo.historico);sem_progresso=self.jogo.sem_progresso
        self.bt_jogar.configure(state="disabled");self.bt_dica.configure(state="disabled");self.bt_voltar.configure(state="normal")
        self.instrucao.set("O computador está pensando…" if executar else "A IA está comparando jogadas e respostas…")
        if executar:
            self.status_ia.set("●  Computador pensando")
            self.motivo.set("Aguarde o movimento do adversário. A ajuda volta na sua vez.")
            self.bt_jogar.configure(text="Aguarde o adversário…")
        else:
            self.status_ia.set("●  Aprofundando a análise…" if aprofundar else "●  Analisando os dois lados…")
            self.motivo.set("Estou verificando mais jogadas à frente. Aguarde até 8 segundos." if aprofundar else "Comparando seus movimentos e as respostas do adversário. A seta mostrará a sugestão.")
            self.bt_jogar.configure(text="Analisando a posição…")
        fila=queue.Queue()
        def calcular():
            try:
                fila.put(analisar_turno(estado,com_ajuda=not executar,gerador=self.gerador,
                                       historico=historico,sem_progresso=sem_progresso,cancelado=evento.is_set,
                                       **({"segundos":8,"profundidade_maxima":18,"variar":False} if aprofundar else {})))
            except Exception as erro:fila.put(erro)
        threading.Thread(target=calcular,daemon=True).start()
        def receber():
            if token != self.geracao:return
            try:resposta=fila.get_nowait()
            except queue.Empty:self.root.after(40,receber);return
            self.ocupado=False
            if isinstance(resposta,Exception):
                self.atualizar();self.status_ia.set("Análise indisponível")
                self.motivo.set(f"Confira os dados e modelos do projeto. Erro: {type(resposta).__name__}: {resposta}")
                self.instrucao.set("Você pode continuar jogando manualmente.");return
            if executar:self.jogar(resposta.lance);return
            self.atualizar();self.analise=resposta;self.sugestao=resposta.lance
            caminho=resposta.lance.caminho
            self.status_ia.set(f"✦  Sugestão: {nome_casa(caminho[0]).upper()} → {nome_casa(caminho[-1]).upper()}")
            self.motivo.set(self.explicar(resposta))
            self.bt_jogar.configure(state="normal");self.bt_dica.configure(state="normal")
            self.instrucao.set("Siga a seta ou escolha seu próprio movimento.")
            self.mostrar_dica()
        self.root.after(40,receber)

    def explicar(self,analise):
        lance=analise.lance;n=len(lance.capturadas)
        if not lance.proximo.vermelhas or not lance.proximo.pretas:return "Esta sequência captura as últimas peças do adversário e encerra a partida."
        if avaliacao_exata(compactar(self.jogo.estado)) is not None:
            return "Este final está entre as 61.504 posições resolvidas. A IA usa o resultado conhecido e verifica as respostas do adversário."
        if analise.nota < -130:
            return "A posição está difícil. Esta é a melhor defesa encontrada após analisar as respostas do adversário."
        if n:return f"Esta jogada captura {n} "+("peça." if n == 1 else "peças.")+" A análise inclui possíveis recapturas do adversário."
        if lance.caminho[0] not in self.jogo.estado.damas and lance.caminho[-1] in lance.proximo.damas:return "A peça chega ao outro lado e vira dama, podendo se mover também para trás."
        if len(analise.continuacao) > 1:
            resposta=analise.continuacao[1].caminho
            return f"Siga a seta verde. Uma resposta prevista é {nome_casa(resposta[0]).upper()} → {nome_casa(resposta[-1]).upper()}. A IA recalcula a estratégia depois de cada jogada."
        return "Siga a seta verde. A IA comparou esta jogada com as alternativas e considerou as respostas do adversário."

    def mostrar_dica(self):
        if self.sugestao and not self.ocupado and self.config.permite_ajuda(self.jogo.estado.vez):
            self.origem=None;self.tabuleiro.exibir(self.jogo.estado,previa=self.sugestao)

    def aplicar_sugestao(self):
        if self.sugestao and self.config.permite_ajuda(self.jogo.estado.vez):self.jogar(self.sugestao)

    def voltar(self):
        self.cancelar()
        if self.resultado_contado:
            self.placar[self.resultado_contado]-=1;self.resultado_contado=None
        self.jogo.voltar()
        if self.config.usa_computador(self.jogo.estado.vez):self.jogo.voltar()
        self.relato.set("Jogada desfeita. O placar da sessão considera apenas partidas concluídas.")
        self.atualizar();self.responder()

    def guia(self):
        mostrar_informacao(self.root, "Como demonstrar em sala", "1. Selecione ‘Outra pessoa’. O jogador marcado ‘Com IA’ recebe sugestões; o outro joga sem dicas.\n\n2. Clique em ‘Exemplo rápido’ para mostrar uma captura em sequência. É um tabuleiro preparado para explicar o funcionamento.\n\n3. Clique em ‘Nova partida’ para começar com 12 peças de cada lado.\n\n4. Na vez com IA, aceite a sugestão ou faça sua escolha. Na outra vez, escolha uma peça e uma casa verde.\n\n5. Depois, troquem quem recebe a ajuda e comparem o placar. A IA pode errar; nenhuma vitória está garantida.")

    def regras(self):
        mostrar_informacao(self.root, "Regras · damas inglesas", "Peças comuns andam e capturam para a frente, na diagonal. Ao chegar ao outro lado, viram damas, marcadas com uma coroa. Elas também podem voltar e andam uma casa.\n\nCapturar é obrigatório. Os saltos em sequência são completados; a promoção encerra o turno.\n\nVence quem deixa o outro sem peças ou movimentos. Empate: terceira repetição da posição ou 40 jogadas por lado sem captura nem avanço de peão.\n\nContra o computador, você controla o lado marcado ‘Com IA’.")

    def sobre(self):
        try:
            m=json.loads(RELATORIO_COMPLETAS.read_text(encoding='utf-8'))
            dados=f"Rede neural: {m['registros']:,} posições geradas em {m['partidas']} partidas simuladas.\n".replace(',','.')
            dados+=f"Partidas com {m['pecas_min']} a {m['pecas_max']} peças. Finais resolvidos: 61.504 posições de até três damas."
        except (OSError,KeyError,ValueError):dados="Consulte o relatório em reports/partidas_completas/assistente_completo.json."
        mostrar_informacao(self.root, "Como funciona a ajuda", "A ajuda combina a rede neural com análise de peças, proteção, promoção e respostas do adversário. Em finais de até três damas, consulta resultados resolvidos.\n\n"+dados+"\n\nA busca reaproveita posições já analisadas e verifica sequências de captura até o fim. Na abertura, varia entre opções com avaliações próximas.\n\nA ajuda pensa por 3 segundos na abertura, 4 no meio da partida e 5 no final. ‘Pensar mais’ permite até 8 segundos; o computador usa sempre 1,5 segundo.\n\nJogar não retreina a rede. A ajuda não garante vitória; o placar registra o resultado real.")


def main():
    identificar_aplicativo();root=tk.Tk();JanelaPrincipal(root);root.mainloop()


if __name__ == '__main__':main()
