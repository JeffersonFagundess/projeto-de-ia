"""Configuração uniforme de janelas principais e modais."""

import sys
import tkinter as tk

from . import palette as p
from .controls import Botao
from .fonts import fonte
from .images import ICONE_ICO, carregar_icone


def identificar_aplicativo():
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ProjetoIA.Damas.Desktop.1")


def titulo_escuro(janela):
    """Solicita a barra de título escura no Windows; é opcional nos demais."""
    if sys.platform == "win32":
        import ctypes
        janela.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(janela.winfo_id())
        valor = ctypes.c_int(1)
        try:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(valor), 4)
        except (AttributeError, OSError):
            pass


def configurar_icone(janela):
    if sys.platform == "win32":
        janela.iconbitmap(default=str(ICONE_ICO))
    imagem = carregar_icone(janela)
    janela.iconphoto(True, imagem)
    janela._icone_damas = imagem


def preparar(janela, titulo, geometria=None, minimo=None, fundo=p.FUNDO):
    """Aplica identidade e dimensões com uma única chamada."""
    janela.title(titulo)
    janela.configure(bg=fundo)
    if geometria:
        janela.geometry(geometria)
    if minimo:
        janela.minsize(*minimo)
    configurar_icone(janela)
    titulo_escuro(janela)


def mostrar_informacao(root, titulo, texto):
    janela = tk.Toplevel(root)
    janela.withdraw()
    janela.resizable(False, False)
    janela.transient(root)
    preparar(janela, titulo, fundo=p.PAINEL)
    tk.Label(janela, text=titulo, bg=p.PAINEL, fg=p.TEXTO,
             font=fonte(19, True)).pack(anchor="w", padx=26, pady=(24, 16))
    tk.Frame(janela, height=2, bg=p.CIANO).pack(fill="x", padx=26)
    tk.Label(janela, text=texto, bg=p.PAINEL, fg=p.SUAVE, font=fonte(11),
             wraplength=490, justify="left").pack(anchor="w", padx=26, pady=20)
    fechar = Botao(janela, "Entendi", janela.destroy, principal=True)
    fechar.pack(fill="x", padx=26, pady=(0, 24))
    janela.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width()-janela.winfo_reqwidth())//2
    y = root.winfo_rooty() + max(0, (root.winfo_height()-janela.winfo_reqheight())//2)
    janela.geometry(f"+{max(0,x)}+{max(0,y)}")
    janela.deiconify()
    janela.grab_set()
    fechar.focus_set()
    janela.bind("<Escape>", lambda _e: janela.destroy())
    return janela
