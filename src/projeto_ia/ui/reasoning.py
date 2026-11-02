"""Painel visual com telemetria real da busca da IA."""

import math
import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from projeto_ia.damas.game import nome_casa
from projeto_ia.damas.search_board import TabuleiroBusca, expandir
from projeto_ia.damas.trace_store import remover_rastro
from projeto_ia.style import palette as t
from projeto_ia.style.controls import Botao
from projeto_ia.style.fonts import fonte, mono
from projeto_ia.style.images import carregar_icone_fa
from projeto_ia.style.windows import preparar
from projeto_ia.ui.board import Tabuleiro


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
        if self.winfo_ismapped():
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


class VisualizadorRastro(tk.Frame):
    """Consulta paginada do rastro completo sem materializar milhares de widgets."""

    TAMANHO_PAGINA = 250

    def __init__(self, pai, ao_detalhar):
        super().__init__(pai, bg=t.PAINEL, padx=13, pady=12,
                         highlightthickness=1, highlightbackground=t.LINHA)
        self.ao_detalhar = ao_detalhar
        self.conexao = None
        self.caminho = None
        self.pagina = self.total = 0

        cabecalho = tk.Frame(self, bg=t.PAINEL)
        cabecalho.pack(fill="x")
        tk.Label(cabecalho, text="CAMINHO COMPLETO", bg=t.PAINEL, fg=t.SUAVE,
                 font=fonte(8, True)).pack(side="left")
        self.bt_detalhar = Botao(
            cabecalho, "Detalhar caminho", self._solicitar,
            largura=150, altura=32, icone="analise",
        )
        self.bt_detalhar.pack(side="right")

        self.resumo = tk.StringVar(value="Solicite uma captura para registrar cada nó visitado.")
        tk.Label(self, textvariable=self.resumo, bg=t.PAINEL, fg=t.SUAVE,
                 font=fonte(9), justify="left", anchor="w", wraplength=560).pack(
                     fill="x", pady=(9, 8),
                 )

        selecao = tk.Frame(self, bg=t.PAINEL)
        selecao.pack(fill="x", pady=(0, 8))
        self.tabuleiro = Tabuleiro(selecao, tamanho=176)
        self.tabuleiro.pack(side="left")
        detalhes = tk.Frame(selecao, bg=t.ELEVADO, padx=10, pady=9)
        detalhes.pack(side="left", fill="both", expand=True, padx=(10, 0))
        tk.Label(detalhes, text="NÓ SELECIONADO", bg=t.ELEVADO, fg=t.SUAVE,
                 font=fonte(7, True)).pack(anchor="w")
        self.caminho_texto = tk.StringVar(value="Selecione uma linha da exploração.")
        tk.Label(detalhes, textvariable=self.caminho_texto, bg=t.ELEVADO,
                 fg=t.TEXTO, font=mono(8), wraplength=340, justify="left",
                 anchor="nw").pack(fill="both", expand=True, pady=(8, 0))

        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure(
            "Rastro.Treeview", background=t.TERMINAL, fieldbackground=t.TERMINAL,
            foreground="#B8CBE0", rowheight=24, borderwidth=0, font=mono(8),
        )
        estilo.configure(
            "Rastro.Treeview.Heading", background=t.ELEVADO, foreground=t.TEXTO,
            relief="flat", font=fonte(8, True),
        )
        estilo.map("Rastro.Treeview", background=[("selected", "#245A60")])
        tabela_frame = tk.Frame(self, bg=t.TERMINAL)
        tabela_frame.pack(fill="both", expand=True)
        colunas = ("id", "iteracao", "ply", "jogada", "nota", "motivo")
        self.tabela = ttk.Treeview(
            tabela_frame, columns=colunas, show="headings", style="Rastro.Treeview",
            selectmode="browse",
        )
        titulos = ("NÓ", "NÍVEL", "PASSO", "JOGADA", "NOTA", "RESULTADO")
        larguras = (70, 55, 55, 90, 75, 105)
        for coluna, titulo, largura in zip(colunas, titulos, larguras, strict=True):
            self.tabela.heading(coluna, text=titulo)
            self.tabela.column(coluna, width=largura, stretch=coluna == "motivo")
        rolagem = tk.Scrollbar(tabela_frame, command=self.tabela.yview, width=10)
        self.tabela.configure(yscrollcommand=rolagem.set)
        self.tabela.pack(side="left", fill="both", expand=True)
        rolagem.pack(side="right", fill="y")
        self.tabela.bind("<<TreeviewSelect>>", self._selecionar)

        navegacao = tk.Frame(self, bg=t.PAINEL)
        navegacao.pack(fill="x", pady=(8, 0))
        self.bt_anterior = Botao(navegacao, "Anterior", lambda: self._mudar(-1),
                                 largura=100, altura=32)
        self.bt_anterior.pack(side="left")
        self.paginacao = tk.StringVar(value="Página —")
        tk.Label(navegacao, textvariable=self.paginacao, bg=t.PAINEL, fg=t.SUAVE,
                 font=mono(8)).pack(side="left", expand=True)
        self.bt_proxima = Botao(navegacao, "Próxima", lambda: self._mudar(1),
                                largura=100, altura=32)
        self.bt_proxima.pack(side="right")
        self._estados_navegacao()

    def _solicitar(self):
        self.bt_detalhar.configure(state="disabled", text="Capturando…")
        self.resumo.set("Capturando cada posição visitada. A análise detalhada é mais lenta.")
        if self.ao_detalhar() is False:
            self.bt_detalhar.configure(state="normal", text="Detalhar caminho")
            self.resumo.set("Aguarde a análise atual terminar e tente novamente.")

    def falha(self):
        self.bt_detalhar.configure(state="normal", text="Detalhar caminho")

    def abrir(self, caminho):
        self.fechar(remover=True)
        self.caminho = Path(caminho)
        self.conexao = sqlite3.connect(f"file:{self.caminho.as_posix()}?mode=ro", uri=True)
        self.total = self.conexao.execute("SELECT COUNT(*) FROM nos").fetchone()[0]
        meta = dict(self.conexao.execute("SELECT chave,valor FROM meta"))
        iteracoes = self.conexao.execute("SELECT COUNT(DISTINCT iteracao) FROM nos").fetchone()[0]
        cortes = self.conexao.execute(
            "SELECT COUNT(*) FROM nos WHERE motivo IN ('corte','cache-corte')"
        ).fetchone()[0]
        self.resumo.set(
            f"{self.total:,} nós registrados · {iteracoes} níveis · "
            f"{cortes:,} cortes · decisão no nível {meta.get('profundidade','—')}."
            .replace(",", ".")
        )
        self.bt_detalhar.configure(state="normal", text="Capturar novamente")
        self.pagina = 0
        self._carregar_pagina()

    def _carregar_pagina(self):
        self.tabela.delete(*self.tabela.get_children())
        if self.conexao is None:
            self._estados_navegacao()
            return
        deslocamento = self.pagina * self.TAMANHO_PAGINA
        linhas = self.conexao.execute(
            """SELECT id,iteracao,ply,origem,destino,nota,motivo
               FROM nos ORDER BY id LIMIT ? OFFSET ?""",
            (self.TAMANHO_PAGINA, deslocamento),
        )
        for no, iteracao, ply, origem, destino, nota, motivo in linhas:
            jogada = "—" if origem < 0 else f"{nome_casa(origem).upper()}→{nome_casa(destino).upper()}"
            self.tabela.insert(
                "", "end", iid=str(no),
                values=(no, iteracao, ply, jogada, f"{nota/100:+.2f}", motivo),
            )
        paginas = max(1, (self.total+self.TAMANHO_PAGINA-1)//self.TAMANHO_PAGINA)
        self.paginacao.set(f"Página {self.pagina+1} de {paginas} · até 250 nós por página")
        self._estados_navegacao()

    def _estados_navegacao(self):
        paginas = max(1, (self.total+self.TAMANHO_PAGINA-1)//self.TAMANHO_PAGINA)
        self.bt_anterior.configure(state="normal" if self.pagina > 0 else "disabled")
        self.bt_proxima.configure(
            state="normal" if self.conexao is not None and self.pagina+1 < paginas else "disabled",
        )

    def _mudar(self, passo):
        self.pagina += passo
        self._carregar_pagina()

    def _selecionar(self, _evento=None):
        selecao = self.tabela.selection()
        if not selecao or self.conexao is None:
            return
        no = int(selecao[0])
        linha = self.conexao.execute(
            "SELECT vermelhas,pretas,damas,vez,nota,motivo FROM nos WHERE id=?",
            (no,),
        ).fetchone()
        vermelhas, pretas, damas, vez, nota, motivo = linha
        self.tabuleiro.exibir(expandir(TabuleiroBusca(vermelhas, pretas, damas, bool(vez))))
        caminho = self.conexao.execute(
            """WITH RECURSIVE rota(id,pai,origem,destino,ordem) AS (
                   SELECT id,pai,origem,destino,0 FROM nos WHERE id=?
                   UNION ALL
                   SELECT n.id,n.pai,n.origem,n.destino,r.ordem+1
                   FROM nos n JOIN rota r ON n.id=r.pai
               ) SELECT origem,destino FROM rota WHERE origem>=0 ORDER BY ordem DESC""",
            (no,),
        ).fetchall()
        jogadas = " · ".join(
            f"{nome_casa(origem).upper()}→{nome_casa(destino).upper()}"
            for origem, destino in caminho
        ) or "posição inicial"
        self.caminho_texto.set(
            f"{jogadas}\n\nNota do nó: {nota/100:+.2f}\nEncerramento: {motivo}"
        )

    def fechar(self, remover=False):
        if self.conexao is not None:
            self.conexao.close()
            self.conexao = None
        if remover and self.caminho is not None:
            remover_rastro(self.caminho)
            self.caminho = None


class JanelaAnalise:
    """Telemetria e exploração completa fora da interface principal."""

    def __init__(self, root, ao_detalhar):
        self.root = root
        self.janela = tk.Toplevel(root)
        self.janela.withdraw()
        preparar(self.janela, "Análise da busca", "1040x720", (920, 620))
        self.janela.protocol("WM_DELETE_WINDOW", self.janela.withdraw)
        corpo = tk.Frame(self.janela, bg=t.FUNDO, padx=14, pady=14)
        corpo.pack(fill="both", expand=True)
        self.painel = PainelRaciocinio(corpo, largura=340)
        self.painel.pack(side="left", fill="y")
        self.rastro = VisualizadorRastro(corpo, ao_detalhar)
        self.rastro.pack(side="left", fill="both", expand=True, padx=(12, 0))

    def abrir(self):
        self.janela.deiconify()
        self.janela.lift()
        self.janela.focus_force()

    def detalhes_disponiveis(self, caminho):
        self.rastro.abrir(caminho)
        self.abrir()

    def falha_detalhes(self):
        self.rastro.falha()

    def fechar(self):
        self.rastro.fechar(remover=True)
        self.janela.destroy()

    def __getattr__(self, nome):
        return getattr(self.painel, nome)

