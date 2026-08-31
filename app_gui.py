"""Interface grafica do assistente de estrategia para jogos."""

import tkinter as tk
from tkinter import messagebox

from app import encontrar_regra


CORES = {
    "fundo": "#0B1020",
    "painel": "#121A2E",
    "cartao": "#18233B",
    "borda": "#263552",
    "texto": "#F4F7FB",
    "texto_secundario": "#A7B2C7",
    "destaque": "#6C63FF",
    "destaque_hover": "#7C75FF",
    "sim": "#19A974",
    "nao": "#E05A67",
    "botao_neutro": "#24314C",
}


PERGUNTAS = [
    (
        "vida_baixa",
        "A vida do personagem está baixa?",
        "Considere baixa quando há risco de ser derrotado rapidamente.",
    ),
    (
        "muitos_inimigos",
        "Existem muitos inimigos próximos?",
        "Responda sim quando estiver em desvantagem numérica.",
    ),
    (
        "tem_cura",
        "O personagem possui um item de cura?",
        "Pode ser poção, kit médico ou outra forma de recuperação.",
    ),
    (
        "municao_baixa",
        "A munição ou mana está baixa?",
        "Considere se os recursos são suficientes para o próximo combate.",
    ),
    (
        "aliado_perto",
        "Existe um aliado por perto?",
        "O aliado deve estar próximo o suficiente para ajudar.",
    ),
]


class AssistenteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Assistente de Estratégia para Jogos")
        self.root.geometry("800x520")
        self.root.minsize(760, 500)
        self.root.configure(bg=CORES["fundo"])

        self._definir_icone_janela()

        self.respostas = {
            identificador: tk.IntVar(value=-1)
            for identificador, _, _ in PERGUNTAS
        }
        self.botoes_resposta = {}
        self.progresso = tk.StringVar(value="0/5 respondidas")

        self._criar_interface()

    def _definir_icone_janela(self):
        """Cria um pequeno controle pixelado sem depender de arquivo externo."""
        icone = tk.PhotoImage(width=32, height=32)
        destaque = CORES["destaque"]
        claro = CORES["texto"]
        escuro = CORES["fundo"]

        icone.put(destaque, to=(6, 7, 26, 25))
        icone.put(destaque, to=(3, 11, 29, 22))
        icone.put(destaque, to=(1, 15, 31, 20))
        icone.put(escuro, to=(9, 13, 17, 19))
        icone.put(claro, to=(12, 12, 14, 20))
        icone.put(claro, to=(9, 15, 17, 17))
        icone.put(CORES["sim"], to=(22, 13, 25, 16))
        icone.put(CORES["nao"], to=(25, 17, 28, 20))

        self.icone_janela = icone
        self.root.iconphoto(True, self.icone_janela)

    def _criar_interface(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        cabecalho = tk.Frame(self.root, bg=CORES["fundo"])
        cabecalho.grid(row=0, column=0, sticky="ew", padx=24, pady=(15, 12))
        cabecalho.grid_columnconfigure(1, weight=1)

        tk.Label(
            cabecalho,
            image=self.icone_janela,
            bg=CORES["fundo"],
        ).grid(row=0, column=0, rowspan=3, sticky="w", padx=(0, 12))

        tk.Label(
            cabecalho,
            text="SISTEMA ESPECIALISTA",
            bg=CORES["fundo"],
            fg=CORES["destaque_hover"],
            font=("Segoe UI Semibold", 8),
        ).grid(row=0, column=1, sticky="w")

        tk.Label(
            cabecalho,
            text="Assistente de Estratégia para Jogos",
            bg=CORES["fundo"],
            fg=CORES["texto"],
            font=("Segoe UI Semibold", 18),
        ).grid(row=1, column=1, sticky="w", pady=(1, 0))

        tk.Label(
            cabecalho,
            text="Informe a situação atual para receber uma recomendação explicada.",
            bg=CORES["fundo"],
            fg=CORES["texto_secundario"],
            font=("Segoe UI", 9),
        ).grid(row=2, column=1, sticky="w", pady=(2, 0))

        tk.Label(
            cabecalho,
            textvariable=self.progresso,
            bg=CORES["fundo"],
            fg=CORES["texto_secundario"],
            font=("Segoe UI", 9),
        ).grid(row=1, column=2, rowspan=2, sticky="e")

        conteudo = tk.Frame(self.root, bg=CORES["fundo"])
        conteudo.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        conteudo.grid_columnconfigure(0, weight=3)
        conteudo.grid_columnconfigure(1, weight=2)
        conteudo.grid_rowconfigure(0, weight=1)

        painel_perguntas = tk.Frame(
            conteudo,
            bg=CORES["painel"],
            highlightbackground=CORES["borda"],
            highlightthickness=1,
        )
        painel_perguntas.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        painel_perguntas.grid_columnconfigure(0, weight=1)

        tk.Label(
            painel_perguntas,
            text="Situação da partida",
            bg=CORES["painel"],
            fg=CORES["texto"],
            font=("Segoe UI Semibold", 13),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(13, 2))

        tk.Label(
            painel_perguntas,
            text="Selecione Sim ou Não em cada pergunta.",
            bg=CORES["painel"],
            fg=CORES["texto_secundario"],
            font=("Segoe UI", 8),
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 7))

        for indice, (identificador, pergunta, ajuda) in enumerate(PERGUNTAS, start=2):
            self._criar_pergunta(
                painel_perguntas,
                indice,
                identificador,
                pergunta,
                ajuda,
            )

        area_acoes = tk.Frame(painel_perguntas, bg=CORES["painel"])
        area_acoes.grid(row=7, column=0, sticky="ew", padx=16, pady=(9, 13))
        area_acoes.grid_columnconfigure(0, weight=1)

        self.botao_analisar = tk.Button(
            area_acoes,
            text="Analisar situação",
            command=self.analisar,
            state="disabled",
            cursor="hand2",
            bg=CORES["destaque"],
            activebackground=CORES["destaque_hover"],
            disabledforeground="#77829A",
            fg="white",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=18,
            pady=8,
            font=("Segoe UI Semibold", 10),
        )
        self.botao_analisar.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        tk.Button(
            area_acoes,
            text="Limpar",
            command=self.limpar,
            cursor="hand2",
            bg=CORES["botao_neutro"],
            activebackground=CORES["borda"],
            fg=CORES["texto"],
            activeforeground=CORES["texto"],
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            font=("Segoe UI Semibold", 9),
        ).grid(row=0, column=1, sticky="e")

        self._criar_painel_resultado(conteudo)

    def _criar_pergunta(self, pai, linha, identificador, pergunta, _ajuda):
        cartao = tk.Frame(
            pai,
            bg=CORES["cartao"],
            highlightbackground=CORES["borda"],
            highlightthickness=1,
        )
        cartao.grid(row=linha, column=0, sticky="ew", padx=16, pady=3)
        cartao.grid_columnconfigure(0, weight=1)

        tk.Label(
            cartao,
            text=pergunta,
            bg=CORES["cartao"],
            fg=CORES["texto"],
            font=("Segoe UI Semibold", 9),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=(12, 7), pady=9)

        grupo_botoes = tk.Frame(cartao, bg=CORES["cartao"])
        grupo_botoes.grid(row=0, column=1, padx=9, pady=6)

        botao_sim = self._criar_botao_resposta(
            grupo_botoes,
            "Sim",
            lambda nome=identificador: self.selecionar(nome, 1),
        )
        botao_sim.grid(row=0, column=0, padx=(0, 4))

        botao_nao = self._criar_botao_resposta(
            grupo_botoes,
            "Não",
            lambda nome=identificador: self.selecionar(nome, 0),
        )
        botao_nao.grid(row=0, column=1)

        self.botoes_resposta[identificador] = (botao_sim, botao_nao)

    @staticmethod
    def _criar_botao_resposta(pai, texto, comando):
        return tk.Button(
            pai,
            text=texto,
            command=comando,
            cursor="hand2",
            width=6,
            bg=CORES["botao_neutro"],
            activebackground=CORES["borda"],
            fg=CORES["texto"],
            activeforeground=CORES["texto"],
            relief="flat",
            bd=0,
            pady=5,
            font=("Segoe UI Semibold", 8),
        )

    def _criar_painel_resultado(self, pai):
        self.painel_resultado = tk.Frame(
            pai,
            bg=CORES["painel"],
            highlightbackground=CORES["borda"],
            highlightthickness=1,
        )
        self.painel_resultado.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.painel_resultado.grid_columnconfigure(0, weight=1)
        self.painel_resultado.grid_rowconfigure(5, weight=1)

        tk.Label(
            self.painel_resultado,
            text="RESULTADO DA ANÁLISE",
            bg=CORES["painel"],
            fg=CORES["destaque_hover"],
            font=("Segoe UI Semibold", 8),
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(18, 8))

        self.rotulo_regra = tk.Label(
            self.painel_resultado,
            text="AGUARDANDO RESPOSTAS",
            bg=CORES["botao_neutro"],
            fg=CORES["texto_secundario"],
            font=("Segoe UI Semibold", 8),
            padx=8,
            pady=4,
        )
        self.rotulo_regra.grid(row=1, column=0, sticky="w", padx=18)

        self.rotulo_decisao = tk.Label(
            self.painel_resultado,
            text="A recomendação aparecerá aqui.",
            bg=CORES["painel"],
            fg=CORES["texto"],
            font=("Segoe UI Semibold", 15),
            justify="left",
            anchor="nw",
            wraplength=260,
        )
        self.rotulo_decisao.grid(row=2, column=0, sticky="ew", padx=18, pady=(15, 7))

        tk.Label(
            self.painel_resultado,
            text="POR QUE?",
            bg=CORES["painel"],
            fg=CORES["texto_secundario"],
            font=("Segoe UI Semibold", 8),
        ).grid(row=3, column=0, sticky="w", padx=18, pady=(10, 4))

        self.rotulo_explicacao = tk.Label(
            self.painel_resultado,
            text=(
                "Depois de responder às cinco perguntas, o motor de inferência "
                "comparará os fatos com as oito regras da base de conhecimento."
            ),
            bg=CORES["painel"],
            fg=CORES["texto_secundario"],
            font=("Segoe UI", 9),
            justify="left",
            anchor="nw",
            wraplength=260,
        )
        self.rotulo_explicacao.grid(row=4, column=0, sticky="ew", padx=18)

        tk.Label(
            self.painel_resultado,
            text="FATOS → REGRAS → INFERÊNCIA → DECISÃO",
            bg=CORES["painel"],
            fg="#6F7C96",
            font=("Segoe UI Semibold", 7),
        ).grid(row=6, column=0, sticky="sw", padx=18, pady=18)

    def selecionar(self, identificador, valor):
        self.respostas[identificador].set(valor)
        botao_sim, botao_nao = self.botoes_resposta[identificador]

        botao_sim.configure(
            bg=CORES["sim"] if valor == 1 else CORES["botao_neutro"]
        )
        botao_nao.configure(
            bg=CORES["nao"] if valor == 0 else CORES["botao_neutro"]
        )

        quantidade = sum(valor.get() != -1 for valor in self.respostas.values())
        self.progresso.set(f"{quantidade}/5 respondidas")
        self.botao_analisar.configure(
            state="normal" if quantidade == len(PERGUNTAS) else "disabled"
        )

    def analisar(self):
        if any(valor.get() == -1 for valor in self.respostas.values()):
            messagebox.showwarning(
                "Respostas incompletas",
                "Responda às cinco perguntas antes de analisar.",
            )
            return

        fatos = {
            identificador: bool(valor.get())
            for identificador, valor in self.respostas.items()
        }
        regra = encontrar_regra(fatos)

        if regra is None:
            self.rotulo_regra.configure(text="SEM REGRA COMPATÍVEL")
            self.rotulo_decisao.configure(text="Não foi possível decidir.")
            self.rotulo_explicacao.configure(
                text="A base de conhecimento não possui uma regra para esta situação."
            )
            return

        self.rotulo_regra.configure(
            text=f"REGRA {regra['id']} ENCONTRADA",
            bg=CORES["sim"],
            fg="white",
        )
        self.rotulo_decisao.configure(text=regra["decisao"])
        self.rotulo_explicacao.configure(text=regra["explicacao"])

    def limpar(self):
        for identificador, valor in self.respostas.items():
            valor.set(-1)
            botao_sim, botao_nao = self.botoes_resposta[identificador]
            botao_sim.configure(bg=CORES["botao_neutro"])
            botao_nao.configure(bg=CORES["botao_neutro"])

        self.progresso.set("0/5 respondidas")
        self.botao_analisar.configure(state="disabled")
        self.rotulo_regra.configure(
            text="AGUARDANDO RESPOSTAS",
            bg=CORES["botao_neutro"],
            fg=CORES["texto_secundario"],
        )
        self.rotulo_decisao.configure(text="A recomendação aparecerá aqui.")
        self.rotulo_explicacao.configure(
            text=(
                "Depois de responder às cinco perguntas, o motor de inferência "
                "comparará os fatos com as oito regras da base de conhecimento."
            )
        )


def main():
    root = tk.Tk()
    AssistenteApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
