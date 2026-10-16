"""Editor Visual da Suíte Angerô (ferramenta do TI).

Mostra as cores de cada programa (crates/ui-egui/src/theme.rs dos repositórios) com seletores de cor.
"Salvar" grava no código e faz o commit; "Publicar" envia ao GitHub — a compilação automática gera a
versão nova e as Suítes instaladas se atualizam sozinhas.

Uso: python editor_visual.py      (abre http://127.0.0.1:8795 numa janela do Edge)
Requer os repositórios em %LOCALAPPDATA%\\SuiteAngero\\src\\<programa>-angero (git clone -b angero ...) e o gh logado.
"""
import json
import os
import re
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SRC = Path(os.environ.get("SUITE_SRC", Path(os.environ["LOCALAPPDATA"]) / "SuiteAngero" / "src"))
PORTA = int(os.environ.get("EDITOR_PORTA", "8795"))
PROGRAMAS = {
    "illustre": "Illustre - Angerô", "fotografe": "Fotografe - Angerô", "pdf": "PDF - Angerô",
    "cena": "Cena - Angerô", "lightbridge": "LightBridge - Angerô",
}
SEM_JANELA = 0x08000000

# "nome: hex(0xRRGGBB)" ou "nome: Color32::from_rgb(r, g, b)" (decimal ou 0x..)
RE_COR = re.compile(
    r"^(?P<pre>\s*(?:pub\s+)?(?:const\s+)?(?P<nome>[A-Za-z_][\w]*)\s*(?::\s*Color32\s*=|:|=)\s*)"
    r"(?P<cor>hex\(\s*0x(?P<hex>[0-9a-fA-F]{6})\s*\)"
    r"|Color32::from_rgb\(\s*(?P<r>0x[0-9a-fA-F]+|\d+)\s*,\s*(?P<g>0x[0-9a-fA-F]+|\d+)\s*,\s*(?P<b>0x[0-9a-fA-F]+|\d+)\s*\))"
)
RE_BLOCO = re.compile(r"^\s*(?:pub\s+)?(?:const\s+)?fn\s+(\w+)|^\s*(?:pub\s+)?const\s+(\w+)\s*:\s*Tokens"
                      r"|^\s*(?:\w+::)*(\w+)\s*(?:\|[^=]*)?=>|^\s*let\s+(\w+)\s*=\s*(?:Tokens|Self)\s*\{")
NOMES = {"dark": "Tema escuro", "darkest": "Tema mais escuro", "light": "Tema claro", "lightest": "Tema mais claro",
         "medium": "Tema médio", "mediumdark": "Tema médio-escuro", "mediumlight": "Tema médio-claro",
         "default": "Padrão", "base": "Tema escuro (padrão)", "high contrast": "Alto contraste"}


def arquivo_tema(pid):
    return SRC / f"{pid}-angero" / "crates" / "ui-egui" / "src" / "theme.rs"


def _n(v):
    return int(v, 16) if v.lower().startswith("0x") else int(v)


BAIXANDO: dict[str, str] = {}  # pid -> situação do download do repositório


def preparar_repositorios():
    """Em outra máquina: baixa (git clone, ramo angero) os repositórios que faltarem, em segundo plano."""
    faltam = [pid for pid in PROGRAMAS if not (SRC / f"{pid}-angero" / ".git").is_dir()]
    for pid in faltam:
        BAIXANDO[pid] = "na fila para baixar o código do programa (primeira vez)…"
    for pid in faltam:
        destino = SRC / f"{pid}-angero"
        BAIXANDO[pid] = "baixando o código do programa (primeira vez, alguns minutos)…"
        try:
            SRC.mkdir(parents=True, exist_ok=True)
            r = subprocess.run(["git", "clone", "-b", "angero", f"https://github.com/wesleiad/{pid}-angero.git", str(destino)],
                               capture_output=True, text=True, encoding="utf-8", creationflags=SEM_JANELA)
            BAIXANDO[pid] = "" if r.returncode == 0 else "não foi possível baixar: " + (r.stderr or r.stdout)[-300:]
        except FileNotFoundError:
            BAIXANDO[pid] = "o Git não está instalado (winget install Git.Git) — necessário para baixar e publicar"
        if not BAIXANDO[pid]:
            del BAIXANDO[pid]


def ler_cores(pid):
    arq = arquivo_tema(pid)
    if not arq.is_file():
        if BAIXANDO.get(pid):
            return {"erro": BAIXANDO[pid]}
        return {"erro": f"não encontrei {arq} (clone o repositório {pid}-angero)"}
    grupo, cores = "Geral", []
    for i, linha in enumerate(arq.read_bytes().decode("utf-8").replace("\r\n", "\n").split("\n")):
        if linha.strip().startswith("#[cfg(test)]"):
            break  # dali para baixo são testes
        b = RE_BLOCO.match(linha)
        if b and any(b.groups()):
            bruto = next(g for g in b.groups() if g).replace("_", " ")
            if bruto.lower() not in ("some", "none", "ok", "err", "true", "false", "_"):
                grupo = NOMES.get(bruto.lower().replace(" ", ""), NOMES.get(bruto.lower(), bruto))
        m = RE_COR.match(linha)
        if not m:
            continue
        if m.group("hex"):
            cor = "#" + m.group("hex").lower()
        else:
            cor = "#{:02x}{:02x}{:02x}".format(_n(m.group("r")), _n(m.group("g")), _n(m.group("b")))
        cores.append({"linha": i, "nome": m.group("nome").replace("_", " "), "grupo": grupo, "cor": cor})
    return {"programa": PROGRAMAS[pid], "arquivo": str(arq), "cores": cores}


def gravar_cores(pid, alteracoes):
    arq = arquivo_tema(pid)
    texto = arq.read_bytes().decode("utf-8")
    fim = "\r\n" if "\r\n" in texto else "\n"  # mantém as quebras de linha do arquivo
    linhas = texto.split(fim)
    n = 0
    for alt in alteracoes:
        i, cor = int(alt["linha"]), alt["cor"].lstrip("#")
        if not re.fullmatch(r"[0-9a-fA-F]{6}", cor):
            continue
        m = RE_COR.match(linhas[i])
        if not m:
            continue
        if m.group("hex"):
            novo = f"hex(0x{cor})"
        else:
            novo = "Color32::from_rgb(0x{}, 0x{}, 0x{})".format(cor[0:2], cor[2:4], cor[4:6])
        linhas[i] = linhas[i][:m.start("cor")] + novo + linhas[i][m.end("cor"):]
        n += 1
    arq.write_bytes(fim.join(linhas).encode("utf-8"))
    return n


def git(pid, *args):
    r = subprocess.run(["git", "-C", str(SRC / f"{pid}-angero"), *args], capture_output=True, text=True,
                       encoding="utf-8", creationflags=SEM_JANELA)
    return r.returncode, (r.stdout + r.stderr).strip()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, dados, codigo=200):
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        if self.headers.get("Host") not in (f"127.0.0.1:{PORTA}", f"localhost:{PORTA}"):
            return self._json({"erro": "host"}, 403)
        if self.path in ("/", "/index.html"):
            corpo = (AQUI / "editor_visual.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            return self.wfile.write(corpo)
        if self.path == "/api/programas":
            return self._json({pid: ler_cores(pid) for pid in PROGRAMAS})
        return self._json({"erro": "rota"}, 404)

    def do_POST(self):
        if self.headers.get("Host") not in (f"127.0.0.1:{PORTA}", f"localhost:{PORTA}") or self.headers.get("X-Editor") != "1":
            return self._json({"erro": "proibido"}, 403)
        dados = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        pid = dados.get("programa")
        if pid not in PROGRAMAS:
            return self._json({"erro": "programa"}, 400)
        if self.path == "/api/salvar":
            n = gravar_cores(pid, dados.get("alteracoes", []))
            git(pid, "add", "crates/ui-egui/src/theme.rs")
            c, saida = git(pid, "commit", "-m", dados.get("mensagem") or f"visual: {n} cores ajustadas no Editor Visual")
            return self._json({"alteradas": n, "commit": c == 0, "saida": saida[-300:]})
        if self.path == "/api/publicar":
            c, saida = git(pid, "push")
            return self._json({"ok": c == 0, "saida": saida[-400:],
                               "acompanhar": f"https://github.com/wesleiad/{pid}-angero/actions"})
        if self.path == "/api/desfazer":
            c, saida = git(pid, "checkout", "--", "crates/ui-egui/src/theme.rs")
            return self._json({"ok": c == 0})
        return self._json({"erro": "rota"}, 404)


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", PORTA), Handler)
    url = f"http://127.0.0.1:{PORTA}/"
    print("Editor Visual em", url)
    threading.Thread(target=preparar_repositorios, daemon=True).start()
    edge = Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft/Edge/Application/msedge.exe"
    if "--sem-janela" not in sys.argv and edge.is_file():
        threading.Timer(0.5, lambda: subprocess.Popen([str(edge), f"--app={url}", "--window-size=1200,860"])).start()
    srv.serve_forever()


if __name__ == "__main__":
    main()
