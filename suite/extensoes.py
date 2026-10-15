"""Extensões do Illustre - Angerô (como Janela > Extensões do Illustrator).

- listar(): extensões instaladas em plugins/<pasta>/CSXS/manifest.xml (formato CEP da Adobe, host ILST).
- Rodando como programa (pythonw extensoes.py): mostra o botão "Extensões ▾" na barra de cima do Illustre;
  ele segue a janela, some quando o Illustre minimiza e fecha junto com ele.
"""
import ctypes
import ctypes.wintypes as w
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

# o Python portátil do instalador não põe a pasta do script no caminho de importação
sys.path.insert(0, str(Path(__file__).resolve().parent))

AQUI = Path(__file__).resolve().parent
PLUGINS = AQUI.parent / "plugins"
PORTA_SUITE = 8790

# extensões que a Suíte já sabe executar (as funções do Illustrator que elas usam foram adaptadas)
SUPORTADAS = {"br.com.fluxogama": {"nome": "Fluxogama - Angerô", "url": "http://127.0.0.1:8792/"}}


def listar() -> list[dict]:
    saida = []
    for manifesto in sorted(PLUGINS.glob("*/CSXS/manifest.xml")):
        try:
            raiz = ET.parse(manifesto).getroot()
        except ET.ParseError:
            continue
        hosts = [h.get("Name") for h in raiz.iter("Host")]
        if "ILST" not in hosts:
            continue
        bundle = raiz.get("ExtensionBundleId", manifesto.parent.parent.name)
        menu = next((m.text for m in raiz.iter("Menu") if m.text), raiz.get("ExtensionBundleName") or bundle)
        sup = SUPORTADAS.get(bundle)
        saida.append({"id": bundle, "pasta": manifesto.parent.parent.name,
                      "nome": sup["nome"] if sup else menu, "suportada": bool(sup),
                      "url": sup["url"] if sup else None})
    return saida


# ---------------------------------------------------------------- botão sobre o Illustre

def _pedir(rota, dados):
    req = urllib.request.Request(f"http://127.0.0.1:{PORTA_SUITE}{rota}", data=json.dumps(dados).encode(),
                                 method="POST", headers={"Content-Type": "application/json", "X-Suite": "1"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def barra():
    import tkinter as tk
    import janelas  # também deixa o processo com DPI real

    u32 = ctypes.windll.user32
    # uma barra só, mesmo que o atalho seja clicado de novo
    ctypes.windll.kernel32.CreateMutexW(None, False, "SuiteAngero.BarraExtensoes")
    if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        return

    alvo = janelas.esperar_janela(exe="illustre.exe", segundos=90)
    if not alvo:
        return
    escala = u32.GetDpiForWindow(alvo) / 96 if hasattr(u32, "GetDpiForWindow") else 1

    raiz = tk.Tk()
    raiz.title("Extensões Angerô")
    raiz.overrideredirect(True)
    raiz.configure(bg="#2b2b2b")
    fonte = ("Segoe UI", 9)
    botao = tk.Label(raiz, text="  🧩 Extensões ▾  ", fg="#ffffff", bg="#3b4fa6", font=fonte, cursor="hand2", pady=2)
    botao.pack(fill="both", expand=True)
    botao.bind("<Enter>", lambda e: botao.configure(bg="#4a64c0"))
    botao.bind("<Leave>", lambda e: botao.configure(bg="#3b4fa6"))

    def abrir_menu(_=None):
        menu = tk.Menu(raiz, tearoff=0, font=fonte, bg="#323232", fg="#ffffff",
                       activebackground="#4a64c0", activeforeground="#ffffff")
        itens = listar()
        if not itens:
            menu.add_command(label="Nenhuma extensão instalada", state="disabled")
        for ext in itens:
            if ext["suportada"]:
                menu.add_command(label=ext["nome"], command=lambda i=ext["id"]: _abrir(i))
            else:
                menu.add_command(label=f"{ext['nome']} (ainda não adaptada)", state="disabled")
        menu.add_separator()
        menu.add_command(label="Abrir pasta de extensões", command=lambda: __import__("os").startfile(PLUGINS))
        menu.tk_popup(botao.winfo_rootx(), botao.winfo_rooty() + botao.winfo_height())

    def _abrir(ext_id):
        try:
            _pedir("/api/extensao", {"id": ext_id})
        except Exception:
            pass

    botao.bind("<Button-1>", abrir_menu)

    raiz.update_idletasks()
    meu = int(raiz.frame(), 16) if raiz.frame() else raiz.winfo_id()
    # "dono" = Illustre: fica sempre sobre ele, some ao minimizar, mas não fica por cima de outros programas
    ctypes.windll.user32.SetWindowLongPtrW(meu, -8, alvo)  # GWLP_HWNDPARENT

    larg, alt = int(118 * escala), int(26 * escala)

    def seguir():
        if not u32.IsWindow(alvo):
            raiz.destroy()
            return
        r = w.RECT()
        u32.GetWindowRect(alvo, ctypes.byref(r))
        if u32.IsIconic(alvo) or not u32.IsWindowVisible(alvo):
            raiz.withdraw()
        else:
            raiz.deiconify()
            # na barra de cima, logo depois do menu "Ajuda"
            x = r.left + int(620 * escala)
            y = r.top + int(7 * escala)
            raiz.geometry(f"{larg}x{alt}+{x}+{y}")
        raiz.after(250, seguir)

    seguir()
    raiz.mainloop()


if __name__ == "__main__":
    if "--listar" in sys.argv:
        print(json.dumps(listar(), ensure_ascii=False, indent=2))
    else:
        barra()
