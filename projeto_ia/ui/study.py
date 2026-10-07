"""Demonstração guiada: escolher peça, mover, observar e experimentar."""

import queue
import random
import threading
import tkinter as tk
from tkinter import messagebox

from projeto_ia.damas.dataset import carregar_dados, estado_da_linha
from projeto_ia.damas.game import lances_legais
from projeto_ia.damas.inference import analisar_lances, carregar_modelo, mapa_respostas, prever
from projeto_ia.damas.session import Partida
from projeto_ia.ui.board import Tabuleiro
from projeto_ia.ui.options import mostrar_opcoes

FUNDO = "#E7EDF2"
TEXTO = "#192E3D"
SUAVE = "#607787"
VERDE = "#226779"


def cor_nome(cor):
    return "vermelhas" if cor == "V" else "pretas"


def previsao_texto(resultado, vez):
    if resultado == "draw":
        return "O jogo pode terminar empatado"
    vencedor = vez if resultado == "win" else ("P" if vez == "V" else "V")
    return f"As {cor_nome(vencedor)} podem vencer"


class JanelaPrincipal:
    def __init__(self, root, carregar_assincrono=True):
        self.root = root
        self.root.title("Damas — Estudo de finais")
        self.root.geometry("900x610")
        self.root.minsize(900, 610)
        self.root.configure(bg=FUNDO)
        self.partida = None
        self.origem = None
        self.movendo = False
        self.tipo = "win"
        self.gerador = random.Random(42)
        self._montar()
        self.fila = queue.Queue()
        if carregar_assincrono:
            threading.Thread(target=self._ler_recursos, daemon=True).start()
            self.root.after(80, self._aguardar_recursos)
        else:
            self._ler_recursos()
            self._aguardar_recursos()

    def _ler_recursos(self):
        try:
            dados, _ = carregar_dados()
            modelo = carregar_modelo()
            self.fila.put((dados, modelo, mapa_respostas(dados)))
        except Exception as erro:
            self.fila.put(erro)

    def _aguardar_recursos(self):
        try:
            recursos = self.fila.get_nowait()
        except queue.Empty:
            self.root.after(80, self._aguardar_recursos)
            return
        if isinstance(recursos, Exception):
            self.titulo.set("Falha ao abrir os exemplos")
            self.instrucao.set("Confira os arquivos do projeto e tente abrir novamente.")
            self.relato.set(str(recursos))
            return
        self.dados, self.modelo, self.respostas = recursos
        self.candidatos = {tipo: [] for tipo in ("win", "loss", "draw")}
        for indice in self.modelo["indices_teste"]:
            linha = self.dados.iloc[indice]
            if linha["vez"] == "V":
                self.candidatos[str(linha["resultado"])].append(indice)
        self.mostrar_exemplo("win")

    @staticmethod
    def _label(pai, texto="", tamanho=11, cor=TEXTO, forte=False, **kw):
        return tk.Label(pai, text=texto, bg=pai.cget("bg"), fg=cor,
                        font=("Segoe UI Semibold" if forte else "Segoe UI", tamanho), **kw)

    @staticmethod
    def _botao(pai, texto, comando, principal=False):
        return tk.Button(pai, text=texto, command=comando, font=("Segoe UI Semibold", 10),
                         bg=VERDE if principal else "#E3EBF0", fg="white" if principal else TEXTO,
                         activebackground="#D9DFD6", activeforeground=TEXTO, relief="flat",
                         borderwidth=0, padx=13, pady=8, cursor="hand2")

    def _montar(self):
        topo = tk.Frame(self.root, bg=FUNDO)
        topo.pack(fill="x", padx=24, pady=(12, 10))
        marca = tk.Frame(topo, bg=FUNDO)
        marca.pack(fill="x")
        tk.Label(marca, text="Damas", font=("Georgia", 29), bg=FUNDO, fg=TEXTO).pack(side="left")
        self._label(marca, "ESTUDO DE FINAIS", 9, SUAVE).pack(side="left", padx=18, pady=(12, 0))
        self._label(topo, "Escolha uma posição. Experimente os próximos movimentos.", 10, SUAVE).pack(anchor="w", pady=(2, 0))
        exemplos = tk.Frame(self.root, bg=FUNDO)
        exemplos.pack(fill="x", padx=24, pady=(0, 10))
        self._label(exemplos, "Posição", 10, SUAVE).pack(side="left", padx=(0, 12))
        self.botoes_exemplo = {}
        for tipo, texto in (("win", "Vermelhas vencem"), ("loss", "Pretas vencem"), ("draw", "Empate")):
            botao = self._botao(exemplos, texto, lambda t=tipo: self.mostrar_exemplo(t))
            botao.pack(side="left", padx=(0, 6))
            self.botoes_exemplo[tipo] = botao
        self._botao(exemplos, "Trocar posição", lambda: self.mostrar_exemplo(self.tipo)).pack(side="right")
        corpo = tk.Frame(self.root, bg=FUNDO)
        corpo.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        esquerda = tk.Frame(corpo, bg="#FAFCFD", padx=16, pady=14)
        esquerda.pack(side="left", fill="y")
        self.legenda = tk.StringVar(value="Preparando o tabuleiro…")
        self._label(esquerda, textvariable=self.legenda, tamanho=10, cor=SUAVE, wraplength=320).pack(pady=(0, 10))
        self.tabuleiro = Tabuleiro(esquerda, tamanho=320, ao_clicar=self.clicar_casa)
        self.tabuleiro.pack()
        legenda = tk.Frame(esquerda, bg="#FAFCFD")
        legenda.pack(pady=(13, 5))
        for cor, nome in (("#AD4D43", "Vermelhas"), ("#333430", "Pretas")):
            self._label(legenda, "●", 13, cor).pack(side="left", padx=(10, 5))
            self._label(legenda, nome, 9, SUAVE).pack(side="left", padx=(0, 10))
        self._label(esquerda, "Clique numa peça para ver onde ela pode ir.", 9, SUAVE).pack()
        direita = tk.Frame(corpo, bg="#FAFCFD", padx=22, pady=16)
        direita.pack(side="left", fill="both", expand=True, padx=(14, 0))
        self._label(direita, "NO TABULEIRO", 9, SUAVE).pack(anchor="w")
        self.titulo = tk.StringVar(value="Carregando exemplos…")
        self._label(direita, textvariable=self.titulo, tamanho=19, forte=True).pack(anchor="w", pady=(7, 9))
        self.instrucao = tk.StringVar(value="Estamos preparando a IA para você.")
        self._label(direita, textvariable=self.instrucao, tamanho=12, wraplength=410, justify="left", height=2, anchor="nw").pack(fill="x")
        self.botao_mostrar = self._botao(direita, "Mostrar uma jogada  →", self.mostrar_jogada, True)
        self.botao_mostrar.pack(fill="x", pady=(5, 7))
        linha = tk.Frame(direita, bg="#FAFCFD")
        linha.pack(fill="x")
        self.botao_voltar = self._botao(linha, "Desfazer", self.voltar)
        self.botao_voltar.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._botao(linha, "Recomeçar", self.recomecar).pack(side="left", fill="x", expand=True, padx=(4, 0))
        tk.Frame(direita, bg="#D9E3EA", height=1).pack(fill="x", pady=12)
        self.relato = tk.StringVar(value="")
        self._label(direita, textvariable=self.relato, tamanho=10, wraplength=410, justify="left", height=3, anchor="nw").pack(fill="x")
        self._botao(direita, "Consultar previsão", self.ver_palpite).pack(fill="x", pady=(5, 6))
        alternativas = self._label(direita, "Explorar outras jogadas  ↗", 10, VERDE, cursor="hand2")
        alternativas.pack(anchor="w", pady=(9, 0))
        alternativas.bind("<Button-1>", lambda _e: self.ver_opcoes())
        regras = self._label(direita, "Como jogar?", 10, VERDE, cursor="hand2")
        regras.pack(side="bottom", pady=(7, 0))
        regras.bind("<Button-1>", lambda _e: messagebox.showinfo(
            "Como jogar neste exemplo",
            "Você controla as duas cores.\n\nTodas as peças já são damas: andam uma casa na diagonal, para frente ou para trás.\n\nPara capturar, a peça pula sobre uma adversária e chega a uma casa vazia. Se puder capturar, precisa fazer isso.\n\nClique na peça e depois numa casa verde. O programa cuida das regras.\n\nUsamos finais pequenos de damas inglesas para explicar cada jogada.", parent=self.root))

    def mostrar_exemplo(self, tipo, simples=True):
        if not hasattr(self, "candidatos"):
            return
        self.tabuleiro.cancelar()
        self.movendo = False
        self.tipo = tipo
        candidatos = self.candidatos[tipo].copy()
        self.gerador.shuffle(candidatos)
        estado = None
        for indice in candidatos[:1500] if simples else candidatos[:1]:
            estado = estado_da_linha(self.dados.iloc[indice])
            lances = lances_legais(estado)
            if tipo == "win" and any(not lances_legais(l.proximo) for l in lances):
                break
            if tipo == "loss" and lances and all(any(not lances_legais(r.proximo) for r in lances_legais(l.proximo)) for l in lances):
                break
            if tipo == "draw" and len(estado.vermelhas) == len(estado.pretas) == 1:
                break
        self.partida = Partida(estado)
        for chave, botao in self.botoes_exemplo.items():
            botao.configure(bg=VERDE if chave == tipo else "#E3EBF0", fg="white" if chave == tipo else TEXTO)
        self.relato.set("Capture as peças adversárias ou deixe o outro lado sem movimentos. Você controla as duas cores.")
        if tipo == "draw":
            self.relato.set("Se os dois jogarem bem, ninguém consegue vencer. Uma jogada ruim pode dar a vitória ao outro. Teste as duas cores.")
        self._atualizar()

    def _atualizar(self):
        self.origem = None
        estado = self.partida.estado
        vencedor = self.partida.vencedor
        if vencedor:
            self.titulo.set(f"{cor_nome(vencedor).capitalize()} venceram!")
            restantes = estado.vermelhas if estado.vez == "V" else estado.pretas
            self.instrucao.set(f"As {cor_nome(estado.vez)} ficaram sem " + ("movimento." if restantes else "peças.") + "\nVolte para testar outro caminho.")
        else:
            self.titulo.set(f"Vez das {cor_nome(estado.vez)}")
            self.instrucao.set(f"Escolha uma peça {('vermelha' if estado.vez == 'V' else 'preta')} e clique\nnuma das casas verdes.")
        self.legenda.set("Últimos movimentos em verde" if self.partida.historico else "Posição inicial · vermelhas começam")
        self.tabuleiro.exibir(estado, caminhos=self.partida.caminhos_recentes())
        self.botao_mostrar.configure(state="disabled" if vencedor else "normal")
        self.botao_voltar.configure(state="normal" if self.partida.historico else "disabled")

    def clicar_casa(self, casa):
        if not self.partida or self.movendo or self.partida.vencedor:
            return
        lances = self.partida.lances
        escolhas = [l for l in lances if l.caminho[0] == self.origem and l.caminho[-1] == casa]
        if escolhas:
            if len(escolhas) == 1:
                self.jogar(escolhas[0])
            else:
                self.ver_opcoes(escolhas)
            return
        opcoes = [l for l in lances if l.caminho[0] == casa]
        if not opcoes:
            cor = "vermelha" if self.partida.estado.vez == "V" else "preta"
            self.instrucao.set(f"Clique numa peça {cor} que possa jogar." + ("\nUma captura disponível é obrigatória." if any(l.capturadas for l in lances) else ""))
            return
        self.origem = casa
        self.instrucao.set("Agora clique em uma casa verde." + ("\nEsta peça precisa capturar." if opcoes[0].capturadas else ""))
        self.legenda.set("● Verde = lugar onde esta peça pode chegar.")
        self.tabuleiro.exibir(self.partida.estado, selecionada=casa, destinos={l.caminho[-1] for l in opcoes})

    def mostrar_jogada(self):
        if not self.partida or self.movendo or self.partida.vencedor:
            return
        analise = analisar_lances(self.partida.estado, self.respostas)
        ordem = {"loss": 0, "draw": 1, "win": 2}
        lance, _ = max(analise, key=lambda item: (ordem[item[1]], len(item[0].capturadas)))
        self.jogar(lance)

    def jogar(self, lance):
        if self.movendo or lance not in self.partida.lances:
            return
        self.movendo = True
        self.instrucao.set("Observe a peça se mover…")
        cor = cor_nome(self.partida.estado.vez)

        def terminar():
            self.partida.jogar(lance)
            self.movendo = False
            quantidade = len(lance.capturadas)
            acao = (f"capturaram {quantidade} " + ("peça." if quantidade == 1 else "peças.")) if quantidade else "moveram uma peça."
            self.relato.set(f"As {cor} {acao}" + (f" Agora é a vez das {cor_nome(self.partida.estado.vez)}." if not self.partida.vencedor else " A partida terminou."))
            self._atualizar()

        self.tabuleiro.animar(self.partida.estado, lance, terminar)

    def voltar(self):
        if not self.partida:
            return
        self.tabuleiro.cancelar()
        self.movendo = False
        self.partida.voltar()
        self.relato.set("A última jogada foi desfeita. Você pode experimentar outro movimento.")
        self._atualizar()

    def recomecar(self):
        if not self.partida:
            return
        self.tabuleiro.cancelar()
        self.movendo = False
        self.partida.recomecar()
        self.relato.set("Voltamos ao início deste exemplo. As vermelhas começam.")
        self._atualizar()

    def ver_opcoes(self, escolhas=None):
        if not self.partida or self.movendo:
            return
        analise = analisar_lances(self.partida.estado, self.respostas)
        if escolhas is not None:
            analise = [(l, r) for l, r in analise if l in escolhas]
        if not analise:
            messagebox.showinfo("A partida terminou", self.titulo.get(), parent=self.root)
            return
        mostrar_opcoes(self.root, self.partida.estado, analise, self.jogar, previsao_texto)

    def ver_palpite(self):
        if not self.partida or self.movendo:
            return
        if self.partida.vencedor:
            messagebox.showinfo("A partida terminou", self.titulo.get(), parent=self.root)
            return
        estado = self.partida.estado
        palpite = prever(estado, self.modelo)
        correto = self.respostas[estado]
        janela = tk.Toplevel(self.root)
        janela.title("O palpite da IA")
        janela.configure(bg="white", padx=24, pady=22)
        janela.resizable(False, False)
        self._label(janela, "O que pode acontecer daqui?", 18, forte=True).pack(anchor="w")
        self._label(janela, "A IA observa a posição das peças e dá um palpite.", 11, SUAVE).pack(anchor="w", pady=(6, 18))
        self._label(janela, "PALPITE DA IA", 9, VERDE, True).pack(anchor="w")
        self._label(janela, previsao_texto(palpite, estado.vez), 15, forte=True).pack(anchor="w", pady=(3, 15))
        self._label(janela, "CONFERINDO PELAS REGRAS", 9, SUAVE, True).pack(anchor="w")
        self._label(janela, previsao_texto(correto, estado.vez), 13, forte=True).pack(anchor="w", pady=(3, 8))
        texto = "A IA acertou este caso." if correto == palpite else "Neste caso, a IA errou."
        texto += "\nO resultado considera boas jogadas dos dois lados.\nUma escolha ruim pode mudar a partida."
        if correto == "draw":
            texto += "\nNo empate, nenhum lado consegue obrigar o outro a perder."
        self._label(janela, texto, 11, SUAVE, justify="left").pack(anchor="w", pady=(4, 17))
        self._botao(janela, "Entendi, quero testar", janela.destroy, True).pack(fill="x")
        janela.transient(self.root)
        janela.grab_set()


def main():
    root = tk.Tk()
    JanelaPrincipal(root)
    root.mainloop()


if __name__ == "__main__":
    main()
