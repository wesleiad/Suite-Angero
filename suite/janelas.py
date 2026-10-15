"""Arruma janelas no Windows: Illustre à esquerda e o painel do Fluxogama encaixado à direita."""
import ctypes
import ctypes.wintypes as w
import time
from pathlib import Path

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
try:  # coordenadas em pixels reais (sem isso, com escala de 125%/150% o Windows distorce as posições)
    u32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))  # PER_MONITOR_AWARE_V2
except (AttributeError, OSError):
    pass
LARGURA_PAINEL_96DPI = 440


def largura_painel():
    try:
        return int(LARGURA_PAINEL_96DPI * u32.GetDpiForSystem() / 96)
    except (AttributeError, OSError):
        return LARGURA_PAINEL_96DPI


def area_trabalho():
    r = w.RECT()
    u32.SystemParametersInfoW(0x0030, 0, ctypes.byref(r), 0)  # SPI_GETWORKAREA (sem a barra de tarefas)
    return r.left, r.top, r.right - r.left, r.bottom - r.top


def _exe_do_processo(pid):
    h = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(520)
        n = w.DWORD(520)
        return Path(buf.value).name.lower() if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)) else ""
    finally:
        k32.CloseHandle(h)


def janelas(exe=None, titulo=None):
    achadas = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, w.HWND, w.LPARAM)
    def cb(h, _):
        if not u32.IsWindowVisible(h):
            return True
        n = u32.GetWindowTextLengthW(h)
        if not n:
            return True
        buf = ctypes.create_unicode_buffer(n + 1)
        u32.GetWindowTextW(h, buf, n + 1)
        pid = w.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        if exe and _exe_do_processo(pid.value) != exe.lower():
            return True
        if titulo and titulo.lower() not in buf.value.lower():
            return True
        achadas.append(h)
        return True

    u32.EnumWindows(cb, 0)
    return achadas


def esperar_janela(exe=None, titulo=None, segundos=60):
    fim = time.time() + segundos
    while time.time() < fim:
        achadas = janelas(exe, titulo)
        if achadas:
            return achadas[0]
        time.sleep(0.5)
    return None


def mover(h, x, y, larg, alt):
    u32.ShowWindow(h, 9)  # SW_RESTORE (sai do maximizado para poder posicionar)
    u32.MoveWindow(h, x, y, larg, alt, True)


def encaixar_illustre_e_painel():
    """Deixa o Illustre ocupando a tela menos a faixa da direita, onde fica o painel."""
    x, y, larg, alt = area_trabalho()
    lp = largura_painel()
    h = esperar_janela(exe="illustre.exe")
    if h:
        mover(h, x, y, larg - lp, alt)
    p = esperar_janela(titulo="Fluxogama - Angerô", segundos=30)
    if p:
        mover(p, x + larg - lp, y, lp, alt)
