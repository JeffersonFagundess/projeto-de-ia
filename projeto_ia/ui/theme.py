"""Paleta e tipografia compartilhadas pela interface de jogo."""

FUNDO = "#080F1A"
PAINEL = "#101C2C"
ELEVADO = "#162538"
LINHA = "#283B50"
TEXTO = "#EDF4FC"
SUAVE = "#9FB2C8"
CIANO = "#67E8D2"
CIANO_ESCURO = "#123C3D"
CORAL = "#FF7A86"
PRATA = "#C3D5EA"
DESABILITADO = "#62778E"


def titulo_escuro(janela):
    """Solicita a barra de título escura no Windows; opcional em outros sistemas."""
    import sys

    if sys.platform == "win32":
        import ctypes

        janela.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(janela.winfo_id())
        valor = ctypes.c_int(1)
        try:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(valor), 4)
        except (AttributeError, OSError):
            pass
