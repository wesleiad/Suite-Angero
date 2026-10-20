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


class _MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", w.DWORD), ("rcMonitor", w.RECT), ("rcWork", w.RECT), ("dwFlags", w.DWORD)]


def largura_painel(h=None):
    """Largura do painel na escala do monitor da janela h (ou na do sistema, sem janela)."""
    try:
        dpi = (u32.GetDpiForWindow(w.HWND(h)) if h else 0) or u32.GetDpiForSystem()
        return int(LARGURA_PAINEL_96DPI * dpi / 96)
    except (AttributeError, OSError):
        return LARGURA_PAINEL_96DPI


def area_trabalho(h=None):
    """Área útil (sem a barra de tarefas) do monitor onde está a janela h; sem janela, a da tela principal."""
    r = w.RECT()
    mi = _MONITORINFO(cbSize=ctypes.sizeof(_MONITORINFO))
    u32.MonitorFromWindow.restype = w.HMONITOR
    mon = u32.MonitorFromWindow(w.HWND(h), 2) if h else None  # MONITOR_DEFAULTTONEAREST
    if mon and u32.GetMonitorInfoW(mon, ctypes.byref(mi)):
        r = mi.rcWork
    else:
        u32.SystemParametersInfoW(0x0030, 0, ctypes.byref(r), 0)  # SPI_GETWORKAREA
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
    # ao trocar de monitor com escala diferente o programa se redimensiona sozinho (WM_DPICHANGED):
    # posiciona de novo para ficar no tamanho certo
    time.sleep(0.3)
    u32.MoveWindow(h, x, y, larg, alt, True)


def janela_illustre(segundos=0):
    """A janela principal do Illustre (a maior visível do processo), esperando até `segundos`."""
    fim = time.time() + segundos
    while True:
        achadas = janelas(exe="illustre.exe")
        if achadas:
            def area(h):
                r = w.RECT()
                u32.GetWindowRect(h, ctypes.byref(r))
                return (r.right - r.left) * (r.bottom - r.top)
            return max(achadas, key=area)
        if time.time() >= fim:
            return None
        time.sleep(0.5)


def encaixar_illustre_e_painel():
    """Deixa o Illustre ocupando o monitor onde ele está, menos a faixa da direita, onde fica o painel."""
    h = janela_illustre(segundos=60)
    x, y, larg, alt = area_trabalho(h)
    lp = largura_painel(h)
    if h:
        mover(h, x, y, larg - lp, alt)
    p = esperar_janela(titulo="Fluxogama - Angerô", segundos=30)
    if p:
        mover(p, x + larg - lp, y, lp, alt)
