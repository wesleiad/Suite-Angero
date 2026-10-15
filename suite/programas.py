"""Programas da Suíte: localizar, abrir, saber se estão rodando e conversar com eles via MCP."""
import json
import os
import queue
import socket
import subprocess
import threading
import winreg
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DADOS = Path(os.environ["LOCALAPPDATA"]) / "SuiteAngero"
CHAVE_REG = r"Software\Grupo Angero\Suite Angero\Programas"
PASTA_PADRAO = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "Suite Angero"
SEM_JANELA = 0x08000000  # CREATE_NO_WINDOW
DESTACADO = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP


def _expandir(texto: str) -> str:
    return texto.replace("{DADOS}", str(DADOS))


def pasta_instalada(p: dict) -> Path | None:
    """Onde o instalador pôs o programa (registro do usuário; senão a pasta padrão)."""
    for raiz in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(raiz, CHAVE_REG + "\\" + p["pacote"]) as k:
                pasta = Path(winreg.QueryValueEx(k, "Pasta")[0])
                if (pasta / p["exe"]).is_file():
                    return pasta
        except OSError:
            pass
    padrao = PASTA_PADRAO / p["nome"]
    return padrao if (padrao / p["exe"]).is_file() else None


def _achar(p: dict, campo: str = "exe") -> str | None:
    pasta = pasta_instalada(p)
    return str(pasta / p[campo]) if pasta and (pasta / p[campo]).is_file() else None


def carregar() -> list[dict]:
    dados = json.loads((AQUI / "apps.json").read_text(encoding="utf-8"))
    return dados["programas"]


PROGRAMAS = {p["id"]: p for p in carregar()}
GANCHOS_ABRIR = []  # funções (pid, arquivo) chamadas quando um programa é aberto numa janela nova


def porta_aberta(porta: int | None) -> bool:
    if not porta:
        return False
    try:
        with socket.create_connection(("127.0.0.1", porta), timeout=0.3):
            return True
    except OSError:
        return False


def rodando(pid: str) -> bool:
    p = PROGRAMAS[pid]
    if porta_aberta(p.get("porta")):
        return True
    exe = _achar(p)
    if not exe:
        return False
    nome = Path(exe).name
    r = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {nome}", "/NH"],
                       capture_output=True, text=True, creationflags=SEM_JANELA)
    return nome.lower() in r.stdout.lower()


def situacao() -> list[dict]:
    lista = []
    for p in PROGRAMAS.values():
        lista.append({
            "id": p["id"], "nome": p["nome"], "descricao": p["descricao"],
            "instalado": bool(_achar(p)), "aberto": rodando(p["id"]),
            "extensoes": p["extensoes"],
        })
    return lista


def programa_para(caminho: str) -> str | None:
    ext = Path(caminho).suffix.lower()
    for p in PROGRAMAS.values():
        if ext in p["extensoes"]:
            return p["id"]
    return None


def abrir(pid: str, arquivo: str | None = None) -> str:
    p = PROGRAMAS.get(pid)
    if not p:
        raise ValueError(f"programa desconhecido: {pid}")
    exe = _achar(p)
    if not exe:
        raise FileNotFoundError(f"{p['nome']} não está instalado")
    if arquivo and not Path(arquivo).exists():
        raise FileNotFoundError(f"arquivo não encontrado: {arquivo}")

    if arquivo and rodando(pid) and p.get("abrir_mcp") and porta_aberta(p.get("porta")):
        a = p["abrir_mcp"]
        valor = [arquivo] if a["lista"] else arquivo
        try:
            PONTES.chamar(pid, a["ferramenta"], {a["campo"]: valor})
            _confirmar_importacao(pid, arquivo)
            return f"{Path(arquivo).name} aberto no {p['nome']} (que já estava aberto)."
        except Exception:
            pass  # cai para abrir uma janela nova

    if rodando(pid) and not arquivo:
        return f"{p['nome']} já está aberto."
    args = [exe] + ([arquivo] if arquivo else []) + [_expandir(x) for x in p["controle"]]
    subprocess.Popen(args, cwd=str(Path(exe).parent), creationflags=DESTACADO,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    _confirmar_importacao(pid, arquivo)
    for gancho in GANCHOS_ABRIR:
        try:
            gancho(pid, arquivo)
        except Exception:
            pass
    return f"Abrindo o {p['nome']}" + (f" com {Path(arquivo).name}." if arquivo else ".")


def _confirmar_importacao(pid, arquivo):
    """O Vetor pergunta "Importar PDF" ao abrir .ai/.pdf; confirma com Enter em segundo plano."""
    if pid != "vetor" or not arquivo or Path(arquivo).suffix.lower() not in (".ai", ".ait", ".pdf"):
        return

    def trabalho():
        import time
        fim = time.time() + 90
        while time.time() < fim:
            time.sleep(1.5)
            if not porta_aberta(PROGRAMAS[pid]["porta"]):
                continue
            try:
                ui = json.loads(PONTES.chamar(pid, "inspect_ui", {}))
            except Exception:
                continue
            if (ui.get("ui") or {}).get("dialog"):
                PONTES.chamar(pid, "press_key", {"key": "Enter"})
                return
            if ui.get("documents"):
                return

    threading.Thread(target=trabalho, daemon=True).start()


def escolher_arquivo() -> str | None:
    """Abre a janela padrão do Windows "Abrir arquivo" (na frente de tudo) e devolve o caminho escolhido."""
    filtros = []
    for p in PROGRAMAS.values():
        exts = ";".join("*" + e for e in p["extensoes"])
        filtros.append(f"{p['nome']} ({exts})|{exts}")
    todos = ";".join("*" + e for p in PROGRAMAS.values() for e in p["extensoes"])
    filtro = "|".join([f"Arquivos da Suíte|{todos}"] + filtros + ["Todos os arquivos (*.*)|*.*"])
    script = (
        "Add-Type -AssemblyName System.Windows.Forms;"
        "$f=New-Object System.Windows.Forms.Form -Property @{TopMost=$true;ShowInTaskbar=$false;"
        "WindowState='Minimized'};$f.Show();$f.Hide();"
        "$d=New-Object System.Windows.Forms.OpenFileDialog;"
        "$d.Title='Abrir arquivo - Suíte Angerô';"
        f"$d.Filter='{filtro.replace(chr(39), '')}';"
        "$d.InitialDirectory=[Environment]::GetFolderPath('Desktop');"
        "if($d.ShowDialog($f) -eq 'OK'){[Console]::OutputEncoding=[Text.Encoding]::UTF8;$d.FileName}"
    )
    r = subprocess.run(["powershell", "-NoProfile", "-STA", "-Command", script],
                       capture_output=True, text=True, encoding="utf-8", creationflags=SEM_JANELA)
    caminho = r.stdout.strip()
    return caminho or None


def mostrar_na_pasta(caminho: str):
    if not Path(caminho).exists():
        raise FileNotFoundError(f"arquivo não encontrado: {caminho}")
    subprocess.Popen(["explorer", "/select,", caminho])


class Ponte:
    """Um servidor MCP (stdio) ligado a um programa aberto."""

    def __init__(self, pid: str):
        p = PROGRAMAS[pid]
        cli = _achar(p, "cli")
        if not cli or not p.get("mcp"):
            raise RuntimeError(f"{p['nome']} não aceita comandos da IA")
        self.proc = subprocess.Popen([cli] + [_expandir(x) for x in p["mcp"]],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                     text=True, encoding="utf-8", creationflags=SEM_JANELA)
        self.fila: queue.Queue = queue.Queue()
        self.n = 0
        self.trava = threading.Lock()
        threading.Thread(target=self._ler, daemon=True).start()
        self._pedir("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                   "clientInfo": {"name": "suite-angero", "version": "1"}})
        self._enviar({"jsonrpc": "2.0", "method": "notifications/initialized"})
        self.ferramentas = self._pedir("tools/list", {}).get("tools", [])

    def _ler(self):
        for linha in self.proc.stdout:
            try:
                self.fila.put(json.loads(linha))
            except ValueError:
                pass
        self.fila.put(None)

    def _enviar(self, msg):
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

    def _pedir(self, metodo, params, espera=120):
        with self.trava:
            self.n += 1
            meu = self.n
            self._enviar({"jsonrpc": "2.0", "id": meu, "method": metodo, "params": params})
            while True:
                m = self.fila.get(timeout=espera)
                if m is None:
                    raise RuntimeError("o programa fechou a conexão")
                if m.get("id") == meu:
                    if "error" in m:
                        raise RuntimeError(m["error"].get("message", str(m["error"])))
                    return m.get("result", {})

    def vivo(self):
        return self.proc.poll() is None

    def chamar(self, ferramenta, argumentos):
        r = self._pedir("tools/call", {"name": ferramenta, "arguments": argumentos or {}})
        partes = []
        for c in r.get("content", []):
            if c.get("type") == "text":
                partes.append(c["text"])
            else:
                partes.append(f"[{c.get('type')} omitido]")
        texto = "\n".join(partes)
        if r.get("isError"):
            raise RuntimeError(texto or "erro no programa")
        return texto

    def fechar(self):
        try:
            self.proc.kill()
        except OSError:
            pass


class Pontes:
    def __init__(self):
        self.ativas: dict[str, Ponte] = {}
        self.trava = threading.Lock()

    def obter(self, pid) -> Ponte:
        with self.trava:
            pt = self.ativas.get(pid)
            if pt and pt.vivo():
                return pt
            if pt:
                pt.fechar()
            if not porta_aberta(PROGRAMAS[pid].get("porta")):
                raise RuntimeError(f"{PROGRAMAS[pid]['nome']} não está aberto; abra o programa primeiro")
            pt = self.ativas[pid] = Ponte(pid)
            return pt

    def chamar(self, pid, ferramenta, argumentos):
        try:
            return self.obter(pid).chamar(ferramenta, argumentos)
        except (RuntimeError, OSError, queue.Empty) as e:
            # conexão velha (programa reiniciado): tenta uma vez com uma ponte nova
            with self.trava:
                velha = self.ativas.pop(pid, None)
            if velha:
                velha.fechar()
            if "não está aberto" in str(e) or "não aceita" in str(e):
                raise
            return self.obter(pid).chamar(ferramenta, argumentos)

    def ferramentas(self, pid, filtro=""):
        filtro = (filtro or "").lower()
        saida = []
        for t in self.obter(pid).ferramentas:
            desc = (t.get("description") or "").replace("\n", " ")
            if filtro and filtro not in t["name"].lower() and filtro not in desc.lower():
                continue
            saida.append({"nome": t["name"], "descricao": desc[:160],
                          "parametros": list((t.get("inputSchema") or {}).get("properties", {}).keys())})
        return saida

    def fechar_todas(self):
        for pt in self.ativas.values():
            pt.fechar()


PONTES = Pontes()
