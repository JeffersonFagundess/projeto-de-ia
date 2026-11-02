"""Painel visual com telemetria real da busca da IA."""

import math
import tkinter as tk

from projeto_ia.damas.game import nome_casa
from projeto_ia.style import palette as t
from projeto_ia.style.fonts import fonte, mono
from projeto_ia.style.images import carregar_icone_fa


class PainelRaciocinio(tk.Frame):
    """Anima a exploração e registra somente eventos observáveis da busca."""

    def __init__(self, pai, largura=322):
        super().__init__(pai, width=largura, bg=t.PAINEL, padx=13, pady=12,
                         highlightthickness=1, highlightbackground=t.LINHA)
        self.pack_propagate(False)
        self._fase = 0.0
        self._pulso = 0
        self._ativo = False
        self._linhas = 0

        cabecalho = tk.Frame(self, bg=t.PAINEL)
        cabecalho.pack(fill="x")
        self.icone_terminal = carregar_icone_fa(self, "terminal", "suave")
        tk.Label(cabecalho, text="  TELEMETRIA DA BUSCA", image=self.icone_terminal,
                 compound="left", bg=t.PAINEL, fg=t.SUAVE,
                 font=fonte(8,True)).pack(side="left")
        self.estado = tk.Label(cabecalho, text="EM ESPERA", bg=t.CIANO_ESCURO,
                               fg=t.CIANO, padx=7, pady=3,
                               font=fonte(7,True))
        self.estado.pack(side="right")

        self.canvas = tk.Canvas(self, height=205, bg=t.GRAFO,
                                highlightthickness=1, highlightbackground=t.LINHA)
        self.canvas.pack(fill="x", pady=(10, 9))
        self.canvas.bind("<Configure>", lambda _e: self._desenhar())

        metricas = tk.Frame(self, bg=t.PAINEL)
        metricas.pack(fill="x", pady=(0, 10))
        metricas.grid_columnconfigure((0, 1, 2), weight=1, uniform="metricas")
        self.profundidade = tk.StringVar(value="—")
        self.posicoes = tk.StringVar(value="—")
        self.avaliacao = tk.StringVar(value="—")
        for coluna, (rotulo, variavel) in enumerate((
            ("NÍVEL", self.profundidade),
            ("POSIÇÕES", self.posicoes),
            ("AVALIAÇÃO", self.avaliacao),
        )):
            caixa = tk.Frame(metricas, bg=t.ELEVADO, padx=5, pady=6,
                             highlightthickness=1, highlightbackground=t.LINHA)
            caixa.grid(row=0, column=coluna, sticky="nsew",
                       padx=(0, 4) if coluna < 2 else 0)
            tk.Label(caixa, text=rotulo, bg=t.ELEVADO, fg=t.SUAVE,
                     font=fonte(7,True)).pack()
            tk.Label(caixa, textvariable=variavel, bg=t.ELEVADO, fg=t.TEXTO,
                     font=mono(10,True)).pack(pady=(2, 0))

        tk.Label(self, text="EVENTOS DO ALGORITMO", bg=t.PAINEL, fg=t.SUAVE,
                 font=fonte(8,True)).pack(anchor="w", pady=(0, 6))
        terminal_frame = tk.Frame(self, bg=t.TERMINAL, highlightthickness=1,
                                  highlightbackground=t.LINHA)
        terminal_frame.pack(fill="both", expand=True)
        self.terminal = tk.Text(
            terminal_frame, bg=t.TERMINAL, fg="#B8CBE0", insertbackground=t.CIANO,
            selectbackground="#245A60", relief="flat", bd=0, padx=9, pady=8,
            wrap="word", state="disabled", font=mono(8),
            spacing1=2, spacing3=2, cursor="arrow",
        )
        rolagem = tk.Scrollbar(terminal_frame, command=self.terminal.yview,
                               bg=t.ELEVADO, troughcolor=t.TERMINAL, width=10)
        self.terminal.configure(yscrollcommand=rolagem.set)
        self.terminal.pack(side="left", fill="both", expand=True)
        rolagem.pack(side="right", fill="y")
        self.terminal.tag_configure("destaque", foreground=t.CIANO)
        self.terminal.tag_configure("sucesso", foreground="#A5FFCF")
        self.terminal.tag_configure("atencao", foreground="#FFD38A")
        self.terminal.tag_configure("suave", foreground=t.SUAVE)
        self.aguardar("Aguardando uma análise para exibir a exploração.")
        self.after(45, self._animar)

    @staticmethod
    def _nota(valor):
        if valor >= 9900:
            return "VITÓRIA"
        if valor <= -9900:
            return "DERROTA"
        return f"{valor / 100:+.2f}"

    @staticmethod
    def _jogada(origem, destino):
        return f"{nome_casa(origem).upper()}→{nome_casa(destino).upper()}"

    def _limpar(self):
        self.terminal.configure(state="normal")
        self.terminal.delete("1.0", "end")
        self.terminal.configure(state="disabled")
        self._linhas = 0

    def _registrar(self, texto, tag=""):
        self._linhas += 1
        self.terminal.configure(state="normal")
        self.terminal.insert("end", f"[{self._linhas:02d}] ", "suave")
        self.terminal.insert("end", texto + "\n", tag)
        # Limita o histórico para partidas longas sem perder os eventos recentes.
        if int(self.terminal.index("end-1c").split(".")[0]) > 120:
            self.terminal.delete("1.0", "21.0")
        self.terminal.configure(state="disabled")
        self.terminal.see("end")

    def _mudar_estado(self, texto, ativo=False, cor=None):
        self._ativo = ativo
        self.estado.configure(text=texto, fg=cor or (t.CIANO if ativo else t.SUAVE),
                              bg=t.CIANO_ESCURO if ativo else t.ELEVADO)

    def iniciar(self, alvo, opcoes, aprofundar=False):
        self._limpar()
        self.profundidade.set("0")
        self.posicoes.set("0")
        self.avaliacao.set("…")
        self._mudar_estado("ANALISANDO", True)
        self._registrar(f"Leitura da posição: {opcoes} jogadas legais.", "destaque")
        if aprofundar:
            self._registrar("Modo aprofundado: limite ampliado para 8 s.", "atencao")
        self._registrar(
            "Rede híbrida + busca de respostas." if alvo == "jogador"
            else "Busca tática do computador iniciada.",
            "suave",
        )

    def registrar_progresso(self, dados):
        profundidade = dados.get("profundidade", 0)
        nos = dados.get("nos", 0)
        nota = dados.get("nota", 0)
        linha = dados.get("linha", ())
        self._pulso = profundidade
        self.profundidade.set(str(profundidade))
        self.posicoes.set(f"{nos:,}".replace(",", "."))
        self.avaliacao.set(self._nota(nota))
        if not dados.get("completo", True):
            self._mudar_estado("ANALISANDO", True)
            return
        previsao = " · ".join(self._jogada(a, b) for a, b in linha[:3])
        mensagem = f"Nível {profundidade}: {nos:,} posições; nota {self._nota(nota)}."
        self._registrar(mensagem.replace(",", "."), "destaque")
        if previsao:
            self._registrar(f"Linha prevista: {previsao}", "suave")

    def concluir(self, analise, computador=False):
        self._mudar_estado("DECISÃO", False, "#A5FFCF")
        self.profundidade.set(str(analise.profundidade))
        self.posicoes.set(f"{analise.nos:,}".replace(",", "."))
        self.avaliacao.set(self._nota(analise.nota))
        if analise.lance is not None:
            caminho = analise.lance.caminho
            jogada = self._jogada(caminho[0], caminho[-1])
            prefixo = "Computador escolheu" if computador else "Sugestão escolhida"
            self._registrar(f"{prefixo}: {jogada}.", "sucesso")
        self._registrar(
            f"Busca encerrada no nível {analise.profundidade}; "
            f"{analise.nos:,} posições avaliadas.".replace(",", "."),
            "sucesso",
        )

    def ocultar(self):
        self._mudar_estado("OCULTO")
        self.profundidade.set("—")
        self.posicoes.set("—")
        self.avaliacao.set("—")
        self._limpar()
        self._registrar("Dicas do jogador desativadas pelo botão de olho.", "atencao")
        self._registrar("A IA do computador continua funcionando normalmente.", "suave")

    def aguardar(self, mensagem):
        self._mudar_estado("EM ESPERA")
        self.profundidade.set("—")
        self.posicoes.set("—")
        self.avaliacao.set("—")
        self._limpar()
        self._registrar(mensagem, "suave")

    def cancelar(self):
        if self._ativo:
            self._mudar_estado("CANCELADO")
            self._registrar("Análise cancelada; resultado descartado.", "atencao")

    def erro(self, erro):
        self._mudar_estado("ERRO", False, t.CORAL)
        self._registrar(f"Falha na análise: {type(erro).__name__}.", "atencao")

    def _animar(self):
        self._fase = (self._fase + (0.075 if self._ativo else 0.022)) % 1000
        self._desenhar()
        self.after(45, self._animar)

    def _desenhar(self):
        c = self.canvas
        c.delete("all")
        largura = max(280, c.winfo_width())
        altura = max(180, c.winfo_height())
        xs = (0.10, 0.36, 0.64, 0.90)
        nos = (
            (xs[0], .38), (xs[0], .68),
            (xs[1], .27), (xs[1], .52), (xs[1], .77),
            (xs[2], .27), (xs[2], .52), (xs[2], .77),
            (xs[3], .52),
        )
        pontos = [(x * largura, y * altura) for x, y in nos]
        arestas = (
            (0, 2), (0, 3), (0, 4), (1, 2), (1, 3), (1, 4),
            (2, 5), (2, 6), (3, 5), (3, 6), (3, 7), (4, 6), (4, 7),
            (5, 8), (6, 8), (7, 8),
        )
        caminho_ativo = (self._pulso + int(self._fase / 1.8)) % 3
        destaques = ({(0, 2), (2, 5), (5, 8)},
                     {(0, 3), (3, 6), (6, 8)},
                     {(1, 4), (4, 7), (7, 8)})[caminho_ativo]
        for a, b in arestas:
            x1, y1 = pontos[a]
            x2, y2 = pontos[b]
            destaque = (a, b) in destaques
            c.create_line(x1, y1, x2, y2,
                          fill="#2D6A70" if destaque and self._ativo else "#203449",
                          width=2 if destaque and self._ativo else 1)
            if destaque and self._ativo:
                progresso = (self._fase * .72 + a * .17) % 1
                px = x1 + (x2 - x1) * progresso
                py = y1 + (y2 - y1) * progresso
                raio = 3 + math.sin(self._fase * 3) * .7
                c.create_oval(px-raio, py-raio, px+raio, py+raio,
                              fill="#A5FFCF", outline="")
        for indice, (x, y) in enumerate(pontos):
            ativo = self._ativo and any(indice in aresta for aresta in destaques)
            pulso = (1.6 + 1.4 * math.sin(self._fase * 2.5 + indice)) if ativo else 0
            raio = 7 + pulso
            if ativo:
                c.create_oval(x-raio-5, y-raio-5, x+raio+5, y+raio+5,
                              outline="#275A5E", width=2)
            c.create_oval(x-raio, y-raio, x+raio, y+raio,
                          fill=t.CIANO if ativo else "#294158",
                          outline="#B8FFF2" if ativo else "#46617A", width=1)
        for texto, x in zip(("POSIÇÃO", "JOGADAS", "RESPOSTAS", "ESCOLHA"), xs):
            c.create_text(x * largura, 13, text=texto, fill=t.SUAVE,
                          font=fonte(6,True))

