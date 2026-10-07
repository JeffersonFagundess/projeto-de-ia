"""Identidade das janelas e agrupamento próprio na barra de tarefas."""

import sys
import tkinter as tk
from pathlib import Path

ICONE = Path(__file__).parent / "assets" / "damas.ico"


def identificar_aplicativo():
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ProjetoIA.Damas.Desktop.1")


def configurar_icone(root):
    if sys.platform == "win32":
        root.iconbitmap(default=str(ICONE))
    imagem = tk.PhotoImage(file=str(ICONE.with_suffix(".png")))
    root.iconphoto(True, imagem)
    root._icone_damas = imagem
