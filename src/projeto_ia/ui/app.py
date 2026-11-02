"""Duelo local: um participante com ML, outro sem recomendações."""

import json
import random
import tkinter as tk

from projeto_ia.damas.endgame_table import avaliacao_exata
from projeto_ia.damas.full_game import Jogo
from projeto_ia.damas.game import nome_casa
from projeto_ia.damas.match import Configuracao
from projeto_ia.damas.search_board import compactar
from projeto_ia.paths import RELATORIO_COMPLETAS
from projeto_ia.sounds import tocar
from projeto_ia.style import palette as t
from projeto_ia.style.controls import Botao, BotaoIcone, BotaoOlho, Escolha
from projeto_ia.style.fonts import fonte
from projeto_ia.style.icons import desenhar_marca, glifo
from projeto_ia.style.windows import (
    identificar_aplicativo,
    mostrar_informacao,
    preparar,
)
from projeto_ia.ui.analysis_service import ServicoAnalise
from projeto_ia.ui.board import Tabuleiro
from projeto_ia.ui.reasoning import JanelaAnalise

FUNDO, PAPEL, TEXTO, SUAVE = t.FUNDO, t.PAINEL, t.TEXTO, t.SUAVE
AZUL, CORAL, LINHA = t.CIANO, t.CORAL, t.LINHA


def nome(cor):
    return "vermelhas" if cor == "V" else "pretas"


class JanelaPrincipal:
    def __init__(self, root):
        self.root = root
        preparar(root,"Damas | Duelo com IA","1080x680",(500,640))
        self.config = Configuracao()
        self.gerador = random.Random()
        self.jogo = Jogo()
        self.origem = self.sugestao = self.analise = None
        self.ocupado = False
        self.geracao = 0
        self.analisador = ServicoAnalise()
        self.analise_id = None
        self.dicas_visiveis = True
        self.percentuais_visiveis = True
        self.placar = {"com":0, "sem":0, "empate":0}
        self.resultado_contado = None
        self._animacao_layout = None
        self._montar()
        self.painel = JanelaAnalise(
            root,
            self.detalhar_caminho,
        )
        self._aplicar_layout(animar=False)
        self.atualizar()
        self.responder()
        root.protocol("WM_DELETE_WINDOW", self.fechar)

    @staticmethod
    def texto(pai, text="", tamanho=10, cor=TEXTO, forte=False, **kw):
        return tk.Label(pai, text=text, bg=pai.cget("bg"), fg=cor,
                        font=fonte(tamanho,forte), **kw)

    @staticmethod
    def botao(pai, texto, comando, principal=False, icone=None):
        return Botao(pai, texto, comando, principal, icone=icone)

    def _montar(self):
        topo = tk.Frame(self.root, bg=FUNDO)
        topo.pack(fill="x", padx=20, pady=(12, 10))
        marca = tk.Canvas(topo, width=42, height=42, bg=FUNDO, highlightthickness=0)
        marca.pack(side="left", padx=(0, 12))
        desenhar_marca(marca)
        self.texto(topo, "DAMAS", 24, forte=True).pack(side="left")

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

        corpo = tk.Frame(self.root, bg=FUNDO)
        corpo.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self.corpo = corpo
        esquerda = tk.Frame(corpo, bg=PAPEL, padx=12, pady=12,
                            highlightthickness=1, highlightbackground=LINHA)
        self.painel_tabuleiro = esquerda
        esquerda.pack(side="left", fill="y")
        cabecalho = tk.Frame(esquerda, bg=PAPEL)
        cabecalho.pack(fill="x", pady=(0, 10))
        ferramentas = tk.Frame(cabecalho, bg=PAPEL)
        ferramentas.pack(side="left")
        self.bt_olho=BotaoOlho(ferramentas,self.alternar_dicas,aberto=True)
        self.bt_olho.pack(side="left",padx=(0,4))
        self.bt_jogar=BotaoIcone(
            ferramentas,"lampada",self.aplicar_sugestao,"Usar sugestão",
        )
        self.bt_jogar.pack(side="left",padx=(0,4))
        self.bt_percentuais=BotaoIcone(
            ferramentas,"percentual",self.alternar_percentuais,
            "Mostrar confiança relativa por casa",
        )
        self.bt_percentuais.pack(side="left",padx=(0,4))
        self.bt_dica=BotaoIcone(
            ferramentas,"aprofundar",lambda:self.buscar(aprofundar=True),
            "Aprofundar análise",
        )
        self.bt_dica.pack(side="left",padx=(0,4))
        self.bt_analise=BotaoIcone(
            ferramentas,"analise",self.abrir_analise,"Abrir análise e telemetria",
        )
        self.bt_analise.pack(side="left",padx=(0,4))
        self.bt_voltar=BotaoIcone(
            ferramentas,"desfazer",self.voltar,"Desfazer jogada",
        )
        self.bt_voltar.pack(side="left")
        self.bt_nova=BotaoIcone(
            cabecalho,"adicionar",self.nova,"Nova partida",
        )
        self.bt_nova.pack(side="right")
        self.caption = tk.StringVar()
        moldura = tk.Frame(esquerda, bg="#365369", padx=4, pady=4)
        moldura.pack()
        self.tabuleiro = Tabuleiro(moldura, tamanho=384, ao_clicar=self.clicar)
        self.tabuleiro.pack()
        legenda = tk.Frame(esquerda, bg=PAPEL)
        legenda.pack(fill="x", pady=(12, 5))
        self.texto(legenda, "1  Escolha uma peça", 9, TEXTO).pack(side="left", padx=(4, 15))
        self.texto(legenda, "2  Vá para a casa verde", 9, AZUL).pack(side="left")
        rodape_tabuleiro=tk.Frame(esquerda,bg=PAPEL)
        rodape_tabuleiro.pack(fill="x",pady=(2,0))
        self.texto(
            rodape_tabuleiro,"Coroa = dama  ·  Captura obrigatória",8,SUAVE,
        ).pack(side="left")
        self.texto(
            rodape_tabuleiro, textvariable=self.caption, tamanho=8, cor=SUAVE,
            anchor="e",
        ).pack(side="right")

        direita = tk.Frame(corpo, bg=PAPEL, padx=16, pady=12,
                           highlightthickness=1, highlightbackground=LINHA)
        self.painel_jogo = direita
        direita.pack(side="left", fill="both", expand=True, padx=(14,0))
        jogadores = tk.Frame(direita,bg=PAPEL)
        jogadores.pack(fill="x")
        jogadores.grid_columnconfigure((0, 1), weight=1, uniform="jogadores")
        self.cards = {}
        for indice, cor in enumerate(("V","P")):
            card=tk.Frame(jogadores,bg=t.ELEVADO,padx=10,pady=7,highlightthickness=1,highlightbackground=LINHA)
            card.grid(row=0,column=indice,sticky="nsew",padx=(0,5) if cor == "V" else (5,0))
            nome_jogador=self.texto(card, f"{glifo('ponto')}  Jogador {1 if cor == 'V' else 2}",11,CORAL if cor == "V" else t.PRATA,True)
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
        ajuda_cabecalho=tk.Frame(self.ajuda_frame,bg=t.CIANO_ESCURO)
        ajuda_cabecalho.pack(fill="x")
        self.status_ia=tk.StringVar()
        self.ajuda_titulo=self.texto(ajuda_cabecalho,textvariable=self.status_ia,tamanho=10,cor=AZUL,forte=True)
        self.ajuda_titulo.pack(side="left",anchor="w")
        self.estado_dicas=tk.StringVar(value="DICAS VISÍVEIS")
        self.rotulo_dicas=self.texto(ajuda_cabecalho,textvariable=self.estado_dicas,
                                     tamanho=7,cor=SUAVE,forte=True)
        self.rotulo_dicas.pack(side="right",padx=(0,6))
        self.ajuda_cabecalho=ajuda_cabecalho
        self.motivo=tk.StringVar()
        self.ajuda_texto=self.texto(self.ajuda_frame,textvariable=self.motivo,wraplength=420,justify="left",height=3,anchor="nw")
        self.ajuda_texto.pack(fill="x",pady=(5,0))
        self.relato=tk.StringVar(value="As vermelhas começam. Você pode aceitar a dica ou escolher outra jogada.")
        self.texto(direita,textvariable=self.relato,tamanho=9,cor=SUAVE,wraplength=450,justify="left",height=2,anchor="nw").pack(fill="x",pady=(2,0))
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

    def _aplicar_layout(self, animar=True):
        """Mostra ferramentas do duelo local e anima a largura da janela."""
        expandido = self.config.modo == "dupla"
        if self.painel_tabuleiro.winfo_manager():
            self.painel_tabuleiro.pack_forget()
        if self.painel_jogo.winfo_manager():
            self.painel_jogo.pack_forget()
        if expandido:
            self.painel_tabuleiro.pack(side="left", fill="y")
            self.painel_jogo.pack(
                side="left", fill="both", expand=True, padx=(14, 0),
            )
        else:
            self.painel_tabuleiro.pack(side="top", anchor="n")

        alvo = 1080 if expandido else 520
        if self._animacao_layout is not None:
            self.root.after_cancel(self._animacao_layout)
            self._animacao_layout = None
        self.root.update_idletasks()
        atual = self.root.winfo_width()
        altura = max(640, self.root.winfo_height())
        if not animar or abs(atual-alvo) < 5:
            self.root.geometry(f"{alvo}x{altura}")
            return

        passos = 10

        def redimensionar(passo=1):
            progresso = passo / passos
            suave = 1-(1-progresso)**3
            largura = round(atual+(alvo-atual)*suave)
            self.root.geometry(f"{largura}x{altura}")
            if passo < passos:
                self._animacao_layout = self.root.after(
                    18, redimensionar, passo+1,
                )
            else:
                self._animacao_layout = None

        redimensionar()

    def abrir_analise(self):
        self.painel.abrir()

    def detalhar_caminho(self):
        if self.ocupado or self.jogo.resultado:
            return False
        vez = self.jogo.estado.vez
        somente_analise = (
            not self.config.permite_ajuda(vez) or not self.dicas_visiveis
        )
        self.buscar(
            aprofundar=True,
            detalhar=True,
            somente_analise=somente_analise,
        )
        return True

    def atualizar(self):
        self.origem=self.sugestao=self.analise=None
        e=self.jogo.estado; fim=self.jogo.resultado
        for cor,(card,titulo,role) in self.cards.items():
            assistido=self.config.permite_ajuda(cor)
            quantidade=len(e.vermelhas if cor == "V" else e.pretas)
            estado_ajuda="COM IA" if self.dicas_visiveis else "DICAS OCULTAS"
            role.configure(text=f"{estado_ajuda if assistido else 'SEM DICAS'} · {quantidade} {'peça' if quantidade == 1 else 'peças'}",fg=AZUL if assistido and self.dicas_visiveis else SUAVE)
            titulo.configure(text=f"{glifo('ponto')}  {'Computador' if self.config.usa_computador(cor) else 'Jogador '+('1' if cor == 'V' else '2')}")
            card.configure(highlightbackground=(CORAL if cor == "V" else t.PRATA) if e.vez == cor and not fim else LINHA)
        n = len(self.jogo.historico)
        self.caption.set(f"{n:02d} {'JOGADA' if n == 1 else 'JOGADAS'} · PARTIDA COMPLETA")
        self.titulo.set("Empate" if fim == "empate" else f"{nome(fim).capitalize()} venceram!" if fim else f"Vez do {'computador' if self.config.usa_computador(e.vez) else 'jogador 1' if e.vez == 'V' else 'jogador 2'}")
        self.instrucao.set("A partida terminou. Comece outra para trocar os papéis." if fim else f"Mova uma peça {'vermelha' if e.vez == 'V' else 'preta'} para uma casa verde.")
        self.bt_jogar.configure(state="disabled",active=False)
        self.bt_dica.configure(state="disabled",active=False)
        self.bt_voltar.configure(state="normal" if self.jogo.historico or self.ocupado else "disabled")
        self.bt_olho.definir(self.dicas_visiveis)
        self.bt_olho.configure(state="disabled" if self.ocupado and self.config.usa_computador(e.vez) else "normal")
        self.bt_percentuais.configure(active=self.percentuais_visiveis)
        self.estado_dicas.set("DICAS VISÍVEIS" if self.dicas_visiveis else "DICAS OCULTAS")
        com_ajuda = self.config.permite_ajuda(e.vez) and self.dicas_visiveis and not fim
        fundo_ajuda = t.CIANO_ESCURO if com_ajuda else t.ELEVADO
        self.ajuda_frame.configure(bg=fundo_ajuda,highlightbackground="#2E6862" if com_ajuda else LINHA)
        self.ajuda_cabecalho.configure(bg=fundo_ajuda)
        self.ajuda_titulo.configure(bg=fundo_ajuda,fg=AZUL if com_ajuda else t.PRATA)
        self.rotulo_dicas.configure(bg=fundo_ajuda,fg=AZUL if self.dicas_visiveis else SUAVE)
        self.ajuda_texto.configure(bg=fundo_ajuda)
        if fim:
            self.status_ia.set("Resultado da partida")
            self.motivo.set("Empate por repetição ou falta de progresso." if fim == "empate" else f"As {nome(e.vez)} ficaram sem peças ou sem movimentos.")
            tipo, titulo, mensagem = self._descricao_resultado(fim)
            if self.resultado_contado is None:
                tocar(tipo)
                chave="empate" if fim == "empate" else "com" if fim == self.config.lado_assistido else "sem"
                self.placar[chave]+=1;self.resultado_contado=chave
            self.painel.aguardar("Partida concluída. Inicie outra para uma nova análise.")
        elif self.config.permite_ajuda(e.vez) and self.dicas_visiveis:
            self.status_ia.set("●  Assistente da IA")
            self.motivo.set("Preparando uma sugestão para este jogador…")
        elif self.config.permite_ajuda(e.vez):
            self.status_ia.set("Dicas ocultas")
            self.motivo.set("Clique no olho fechado para analisar esta posição e revelar uma sugestão.")
            self.painel.ocultar()
        elif self.config.usa_computador(e.vez):
            self.status_ia.set("Turno do computador")
            self.motivo.set("O adversário analisará a posição e fará sua própria jogada.")
        else:
            self.status_ia.set("Sua estratégia, sua jogada")
            self.motivo.set("Este jogador está sem ajuda. Escolha uma peça e depois uma casa verde.")
            self.painel.aguardar("Turno sem assistência: nenhuma recomendação é calculada.")
        self.tabuleiro.exibir(e,caminhos=self.jogo.caminhos_recentes())
        if fim:
            self.tabuleiro.mostrar_resultado(
                tipo, titulo, mensagem, self.nova,
            )
        self.serie.set(f"PLACAR    Com IA  {self.placar['com']}    /    Sem ajuda  {self.placar['sem']}    /    Empates  {self.placar['empate']}")

    def _descricao_resultado(self, fim):
        if fim == "empate":
            return (
                "empate", "Empate",
                "A posição se repetiu ou chegou ao limite sem progresso.",
            )
        if self.config.modo == "computador":
            if fim == self.config.lado_assistido:
                return "vitoria", "Vitória!", "Você superou o computador nesta partida."
            return "derrota", "Derrota", "O computador venceu. Tente uma estratégia diferente."
        return (
            "vitoria", f"Vitória das {nome(fim)}!",
            "Comece outra rodada mantendo os mesmos jogadores.",
        )

    def cancelar(self):
        self.geracao+=1
        self.analisador.cancelar();self.analise_id=None
        self.tabuleiro.cancelar();self.ocupado=False
        if hasattr(self,"painel"):
            self.painel.cancelar();self.painel.falha_detalhes()

    def fechar(self):
        self.cancelar();self.analisador.fechar();self.painel.fechar();self.root.destroy()

    def nova(self):
        self.cancelar();self.jogo=Jogo();self.resultado_contado=None
        self.relato.set("Nova partida: 12 peças de cada lado. Só o jogador marcado ‘Com IA’ recebe sugestões.")
        self.atualizar();self.responder()

    def configurar(self,_evento=None):
        self.config=Configuracao("dupla" if self.modo.current() == 0 else "computador","V" if self.lado.current() == 0 else "P")
        self._aplicar_layout();self.nova()

    def alternar_dicas(self):
        if self.ocupado and self.config.usa_computador(self.jogo.estado.vez):
            return
        if self.ocupado:
            self.cancelar()
        self.dicas_visiveis=not self.dicas_visiveis
        self.sugestao=self.analise=None
        self.relato.set(
            "Dicas ativadas. A IA analisará as suas opções nesta vez."
            if self.dicas_visiveis else
            "Dicas ocultadas. Você continua jogando normalmente; a IA do computador permanece ativa."
        )
        self.atualizar();self.responder()

    def alternar_percentuais(self):
        self.percentuais_visiveis=not self.percentuais_visiveis
        self.bt_percentuais.configure(active=self.percentuais_visiveis)
        if self.sugestao:
            self.mostrar_dica()

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
            tocar("erro")
            self.instrucao.set("Há uma captura obrigatória. Escolha a peça que pode capturar." if any(l.capturadas for l in lances) else f"Escolha uma peça das {nome(self.jogo.estado.vez)} que possa se mover.")
            return
        tocar("selecionar")
        self.origem=casa
        percentuais = (
            self._percentuais_por_casa(casa)
            if self.percentuais_visiveis else {}
        )
        self.tabuleiro.exibir(
            self.jogo.estado,selecionada=casa,
            destinos={l.caminho[-1] for l in opcoes},percentuais=percentuais,
            explicacoes=self._explicacoes_por_casa(casa),
        )
        self.instrucao.set("Agora clique em uma das casas verdes.")

    def jogar(self,lance):
        if self.ocupado or lance not in self.jogo.lances:return
        self.ocupado=True;self.bt_jogar.configure(state="disabled");self.bt_dica.configure(state="disabled")
        anterior=self.jogo.estado;self.instrucao.set("Observe o movimento…")
        tocar("mover")
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
        elif self.config.permite_ajuda(vez) and self.dicas_visiveis:self.buscar(False)

    def buscar(self,executar=False,aprofundar=False,detalhar=False,
               somente_analise=False):
        vez=self.jogo.estado.vez
        permitido=(self.config.usa_computador(vez) if executar
                   else self.config.permite_ajuda(vez) or somente_analise)
        if (not permitido or (not executar and not self.dicas_visiveis and
                              not somente_analise) or self.ocupado or
                self.jogo.resultado):return
        if detalhar:self.painel.abrir()
        self.ocupado=True;token=self.geracao;estado=self.jogo.estado
        historico=tuple(e for e,_,_ in self.jogo.historico);sem_progresso=self.jogo.sem_progresso
        self.bt_jogar.configure(state="disabled");self.bt_dica.configure(state="disabled");self.bt_voltar.configure(state="normal")
        self.bt_olho.configure(state="disabled" if executar else "normal")
        self.instrucao.set("O computador está pensando…" if executar else "A IA está comparando jogadas e respostas…")
        if executar:
            self.status_ia.set("●  Computador pensando")
            self.motivo.set("Aguarde o movimento do adversário. A ajuda volta na sua vez.")
        else:
            self.status_ia.set("●  Aprofundando a análise…" if aprofundar else "●  Analisando os dois lados…")
            self.motivo.set("Estou verificando mais jogadas à frente. Aguarde até 8 segundos." if aprofundar else "Comparando seus movimentos e as respostas do adversário. A melhor casa pulsará no tabuleiro.")
        self.painel.iniciar("computador" if executar else "jogador",len(self.jogo.lances),aprofundar)
        identificador = self.analisador.analisar(
            estado,
            com_ajuda=not executar,
            semente=self.gerador.getrandbits(64),
            historico=historico,
            sem_progresso=sem_progresso,
            segundos=8 if aprofundar else None,
            profundidade_maxima=18 if aprofundar else 12,
            variar=not aprofundar,
            detalhar=detalhar,
        )
        self.analise_id = identificador
        def receber():
            if token != self.geracao or identificador != self.analise_id:return
            resposta=erro=None
            for evento_id,tipo,valor in self.analisador.receber():
                if evento_id != identificador:
                    continue
                if tipo == "progresso":self.painel.registrar_progresso(valor)
                elif tipo == "resultado":resposta=valor
                elif tipo == "detalhes":self.painel.detalhes_disponiveis(valor)
                else:erro=valor
            if resposta is None and erro is None:
                if not self.analisador.ativo:
                    erro=("ProcessoEncerrado","O processo de análise foi encerrado inesperadamente.")
                else:
                    self.root.after(25,receber);return
            self.analise_id=None
            self.ocupado=False
            if erro is not None:
                tocar("erro")
                if detalhar:self.painel.falha_detalhes()
                nome_erro,mensagem=erro
                self.atualizar();self.status_ia.set("Análise indisponível")
                self.motivo.set(f"Confira os dados e modelos do projeto. Erro: {nome_erro}: {mensagem}")
                self.painel.erro(RuntimeError(f"{nome_erro}: {mensagem}"))
                self.instrucao.set("Você pode continuar jogando manualmente.");return
            self.painel.concluir(resposta,computador=executar)
            if executar:self.jogar(resposta.lance);return
            if somente_analise:
                self.atualizar();self.painel.concluir(resposta)
                self.instrucao.set("Captura detalhada concluída; explore os nós na janela de análise.")
                return
            tocar("dica")
            self.atualizar();self.analise=resposta;self.sugestao=resposta.lance
            caminho=resposta.lance.caminho
            self.status_ia.set(f"{glifo('brilho')}  Sugestão: {nome_casa(caminho[0]).upper()} {glifo('avancar')} {nome_casa(caminho[-1]).upper()}")
            self.motivo.set(self.explicar(resposta))
            self.bt_jogar.configure(state="normal",active=True)
            self.bt_dica.configure(state="normal")
            self.instrucao.set(
                "Passe o mouse sobre a peça ou uma casa para entender a comparação."
                if self.percentuais_visiveis else
                "Escolha a casa pulsante ou faça seu próprio movimento."
            )
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
            return f"A casa ciano pulsa com a sugestão. Uma resposta prevista é {nome_casa(resposta[0]).upper()} → {nome_casa(resposta[-1]).upper()}, marcada em coral."
        return "A casa ciano pulsa com a sugestão comparada às alternativas e respostas do adversário."

    def mostrar_dica(self):
        if self.dicas_visiveis and self.sugestao and not self.ocupado and self.config.permite_ajuda(self.jogo.estado.vez):
            self.origem=None
            resposta = None
            percentual_resposta = None
            percentuais = {}
            if self.percentuais_visiveis and self.analise is not None:
                percentuais = self._percentuais_por_casa()
                if self.analise.respostas:
                    previsao = max(
                        self.analise.respostas,key=lambda opcao:opcao.confianca,
                    )
                    resposta = previsao.lance
                    percentual_resposta = previsao.confianca
            self.tabuleiro.exibir(
                self.jogo.estado,previa=self.sugestao,
                percentuais=percentuais,resposta=resposta,
                percentual_resposta=percentual_resposta,
                explicacoes=self._explicacoes_por_casa(),
            )

    def _percentuais_por_casa(self, origem=None):
        percentuais = {}
        if self.analise is None:
            return percentuais
        for opcao in self.analise.opcoes:
            caminho = opcao.lance.caminho
            if origem is not None and caminho[0] != origem:
                continue
            destino = caminho[-1]
            percentuais[destino] = max(
                percentuais.get(destino,0),opcao.confianca,
            )
        return percentuais

    def _explicacoes_por_casa(self, origem=None):
        if self.analise is None:
            return {}
        grupos = {}
        for opcao in self.analise.opcoes:
            caminho = opcao.lance.caminho
            if origem is not None and caminho[0] != origem:
                continue
            grupos.setdefault(caminho[-1],[]).append(opcao)
        if not grupos:
            return {}

        todas = [opcao for opcoes in grupos.values() for opcao in opcoes]
        sugerida = next(
            (opcao for opcao in self.analise.opcoes
             if opcao.lance == self.analise.lance),
            max(todas,key=lambda opcao:opcao.confianca),
        )
        maior = sugerida.confianca
        total = len(self.analise.opcoes)
        explicacoes = {}
        for destino,opcoes in grupos.items():
            opcoes.sort(key=lambda opcao:opcao.confianca,reverse=True)
            opcao = opcoes[0]
            caminho = opcao.lance.caminho
            movimento = (
                f"{nome_casa(caminho[0]).upper()} → "
                f"{nome_casa(caminho[-1]).upper()}"
            )
            if opcao.lance == self.analise.lance:
                comparacao = "É a jogada individual mais bem avaliada."
                titulo = f"PEÇA E CASA SUGERIDAS · {movimento}"
            else:
                diferenca = max(0,maior-opcao.confianca)
                comparacao = (
                    "Está empatada com a sugestão na confiança arredondada."
                    if diferenca == 0 else
                    f"Ficou {diferenca} ponto(s) percentual(is) abaixo da sugestão."
                )
                titulo = f"ALTERNATIVA · {movimento}"

            detalhes = []
            capturas = len(opcao.lance.capturadas)
            if capturas:
                detalhes.append(
                    f"captura {capturas} peça"+("" if capturas == 1 else "s")
                )
            if (
                caminho[0] not in self.jogo.estado.damas
                and caminho[-1] in opcao.lance.proximo.damas
            ):
                detalhes.append("promove a peça a dama")
            efeito = (
                " Também "+" e ".join(detalhes)+"."
                if detalhes else ""
            )
            rotas = ""
            if len(opcoes) > 1:
                lista = ", ".join(
                    f"{nome_casa(item.lance.caminho[0]).upper()} → "
                    f"{nome_casa(item.lance.caminho[-1]).upper()} "
                    f"({item.confianca}%)"
                    for item in opcoes
                )
                rotas = (
                    f"\nEsta casa recebe {len(opcoes)} jogadas: {lista}. "
                    "O selo mostra a melhor delas; os valores não são somados."
                )
            texto = (
                f"{titulo}\n{opcao.confianca}% de confiança relativa. "
                f"{comparacao}{efeito}\n"
                f"A busca comparou {total} jogadas até a profundidade "
                f"{self.analise.profundidade}, considerando material, avanço, "
                f"mobilidade e respostas do adversário.{rotas}\n"
                "Os 100% são divididos entre as jogadas; não representam chance de vitória."
            )
            explicacoes[destino] = texto

        origem_sugerida = self.analise.lance.caminho[0]
        destino_sugerido = self.analise.lance.caminho[-1]
        if origem is None or origem == origem_sugerida:
            explicacoes[origem_sugerida] = (
                "PEÇA SUGERIDA\n"
                f"Mova {nome_casa(origem_sugerida).upper()} para "
                f"{nome_casa(destino_sugerido).upper()}. "
                "O contorno ciano marca a peça de origem; a casa de chegada pulsa suavemente."
            )
        return explicacoes

    def aplicar_sugestao(self):
        if self.dicas_visiveis and self.sugestao and self.config.permite_ajuda(self.jogo.estado.vez):self.jogar(self.sugestao)

    def voltar(self):
        self.cancelar()
        if self.resultado_contado:
            self.placar[self.resultado_contado]-=1;self.resultado_contado=None
        self.jogo.voltar()
        if self.config.usa_computador(self.jogo.estado.vez):self.jogo.voltar()
        self.relato.set("Jogada desfeita. O placar da sessão considera apenas partidas concluídas.")
        self.atualizar();self.responder()

    def guia(self):
        mostrar_informacao(self.root, "Como demonstrar em sala", "1. Selecione ‘Outra pessoa’. O jogador marcado ‘Com IA’ pode receber sugestões; o outro joga sem dicas.\n\n2. Use o olho aberto/fechado para mostrar ou ocultar a ajuda do jogador. Isso não desliga a IA do computador.\n\n3. O gráfico abre a telemetria com profundidade, posições avaliadas, nota e sequência prevista.\n\n4. A lâmpada aplica a sugestão, a lupa aprofunda a busca e o ícone + inicia outra partida.\n\n5. A ajuda pode errar; nenhuma vitória está garantida.")

    def regras(self):
        mostrar_informacao(self.root, "Regras · damas inglesas", "Peças comuns andam e capturam para a frente, na diagonal. Ao chegar ao outro lado, viram damas, marcadas com uma coroa. Elas também podem voltar e andam uma casa.\n\nCapturar é obrigatório. Os saltos em sequência são completados; a promoção encerra o turno.\n\nVence quem deixa o outro sem peças ou movimentos. Empate: terceira repetição da posição ou 40 jogadas por lado sem captura nem avanço de peão.\n\nContra o computador, você controla o lado marcado ‘Com IA’.")

    def sobre(self):
        try:
            m=json.loads(RELATORIO_COMPLETAS.read_text(encoding='utf-8'))
            dados=f"Rede neural: {m['registros']:,} posições geradas em {m['partidas']} partidas simuladas.\n".replace(',','.')
            dados+=f"Partidas com {m['pecas_min']} a {m['pecas_max']} peças. Finais resolvidos: 61.504 posições de até três damas."
        except (OSError,KeyError,ValueError):dados="Consulte o relatório em resources/reports/partidas_completas/assistente_completo.json."
        mostrar_informacao(self.root, "Como funciona a ajuda", "A ajuda combina a rede neural com análise de peças, proteção, promoção e respostas do adversário. Em finais de até três damas, consulta resultados resolvidos.\n\n"+dados+"\n\nA busca reaproveita posições já analisadas e verifica sequências de captura até o fim. Na abertura, varia entre opções com avaliações próximas.\n\nA ajuda pensa por 3 segundos na abertura, 4 no meio da partida e 5 no final. ‘Pensar mais’ permite até 8 segundos; o computador usa sempre 1,5 segundo.\n\nJogar não retreina a rede. A ajuda não garante vitória; o placar registra o resultado real.")


def main():
    identificar_aplicativo();root=tk.Tk();JanelaPrincipal(root);root.mainloop()


if __name__ == '__main__':main()
