"""Plugin Fluxogama no Illustre - Angerô.

Roda o plugin original da Adobe (CEP, pasta plugins/fluxogama, sem alterações) numa janela própria,
num servidor separado (porta 8792 — outra origem, sem acesso à API do iniciador). Este módulo faz o
papel do Illustrator para o plugin:
- /cep-shim.js imita o motor CEP (window.__adobe_cep__ e window.cep.fs);
- /cep/eval executa os scripts do plugin (getFile, exportJPEG, exportArtBoard, openDocument) no Illustre;
- /fxg/* e /fxg-cdn/* repassam para o Fluxogama (o site deles não deixa o navegador ler o token de login).
"""
import base64
import json
import os
import re
import ssl
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import programas

AQUI = Path(__file__).resolve().parent
PLUGIN = AQUI.parent / "plugins" / "fluxogama"
PORTA = int(os.environ.get("SUITE_PORTA_FXG", "8792"))
HOSTS_OK = {f"127.0.0.1:{PORTA}", f"localhost:{PORTA}"}
ID_EXTENSAO = "br.com.fluxogama.extension"
SITE = "https://angero.fluxogama.com.br"
CDN = "https://cdn.fluxogama.com.br"
SSL = ssl.create_default_context()
TEMP = Path(os.environ["LOCALAPPDATA"]) / "Temp" / ID_EXTENSAO
ESCALA_300DPI = 300 / 72
TIPOS = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
         ".js": "text/javascript; charset=utf-8", ".png": "image/png", ".jpg": "image/jpeg",
         ".svg": "image/svg+xml", ".json": "application/json"}

# ---------------------------------------------------------------- "Illustrator" para o plugin


def _documento_ativo():
    """(caminho, salvo, doc) do documento ativo no Illustre; caminho None se não achar."""
    ui = json.loads(programas.PONTES.chamar("vetor", "inspect_ui", {}))
    docs, ativo = ui.get("documents") or [], ui.get("activeDocument")
    if not docs or ativo is None:
        return None, False, None
    info = docs[ativo]
    doc = json.loads(programas.PONTES.chamar("vetor", "inspect_document", {}))
    caminho = doc.get("path")
    if not caminho:
        # .ai importado (pela parte PDF) não guarda o caminho: acha pelo nome nos arquivos recentes
        for r in (ui.get("ui") or {}).get("recent_files") or []:
            if Path(r).name.lower() == info["title"].lower() and Path(r).exists():
                caminho = str(Path(r))
                break
    return caminho, not info.get("dirty"), doc


def _intersecta(b, a):
    return (b["x"] < a["x"] + a["width"] and b["x"] + b["width"] > a["x"]
            and b["y"] < a["y"] + a["height"] and b["y"] + b["height"] > a["y"])


def _exportar(caminho_jpg, indice):
    programas.PONTES.chamar("vetor", "export", {"path": caminho_jpg, "format": "jpg",
                                                "artboard": indice, "scale": ESCALA_300DPI})


def avaliar(script: str) -> str:
    """Executa um dos scripts ExtendScript que o plugin manda (host/index.jsx)."""
    m = re.fullmatch(r'\s*(\w+)\((?:"(.*)")?\)\s*;?\s*', script, re.S)
    if not m:
        return "EvalScript error."
    funcao, arg = m.group(1), (m.group(2) or "").replace("\\\\", "\\")
    try:
        if funcao == "openDocument":
            programas.abrir("vetor", str(Path(arg)))
            return "undefined"
        if not programas.porta_aberta(programas.PROGRAMAS["vetor"]["porta"]):
            return "-1"
        caminho, salvo, doc = _documento_ativo()
        if doc is None:
            return "-1"
        if not salvo or not caminho:
            return "-2"
        if funcao == "getFile":
            return caminho
        if funcao == "exportJPEG":
            _exportar(arg, 0)
            return "true"
        if funcao == "exportArtBoard":
            objetos = [c["bounds"] for camada in doc.get("layers", []) for c in camada.get("children", [])
                       if c.get("visible", True) and c.get("bounds")]
            ret = []
            for i, ab in enumerate(doc.get("artboards", [])):
                elementos = sum(1 for b in objetos if _intersecta(b, ab))
                if not elementos:
                    ret.append(None)  # como no Illustrator: posição vazia no array
                    continue
                arquivo = f"{arg}-ab-{i + 1}.jpg"
                _exportar(arquivo, i)
                ret.append({"arquivo": arquivo, "indice": i + 1, "nome": ab.get("name", f"Prancheta {i + 1}"),
                            "elementos": elementos})
            return json.dumps(ret, ensure_ascii=False)
        return "EvalScript error."
    except Exception:
        return "-3"


# ---------------------------------------------------------------- cep.fs (arquivos locais)

def _dentro_temp(p: Path) -> bool:
    try:
        return p.resolve().is_relative_to(TEMP.resolve())
    except OSError:
        return False


def fs(op: str, caminho: str, dados=None, codificacao="UTF-8") -> dict:
    """Mesmos códigos de erro do CEP: 0 ok, 3 não encontrado, 4 sem leitura, 6 sem escrita..."""
    p = Path(caminho)
    try:
        if op == "stat":
            if not p.exists():
                return {"err": 3}
            st = p.stat()
            return {"err": 0, "data": {"mtime": st.st_mtime * 1000, "isFile": p.is_file(), "isDirectory": p.is_dir()}}
        if op == "readFile":
            if not p.is_file():
                return {"err": 3}
            bruto = p.read_bytes()
            texto = base64.b64encode(bruto).decode() if codificacao == "Base64" else bruto.decode("utf-8", "replace")
            return {"err": 0, "data": texto}
        # escrita só na pasta temporária do plugin (o plugin só escreve lá)
        if not _dentro_temp(p):
            return {"err": 6}
        if op == "makedir":
            p.mkdir(parents=True, exist_ok=True)
            return {"err": 0}
        if op == "writeFile":
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(base64.b64decode(dados) if codificacao == "Base64" else str(dados).encode("utf-8"))
            return {"err": 0}
        if op == "deleteFile":
            if p.is_file():
                p.unlink()
            return {"err": 0}
    except OSError:
        return {"err": 1}
    return {"err": 2}


# ---------------------------------------------------------------- servidor HTTP


class HandlerFluxogama(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _enviar(self, corpo: bytes, tipo="application/json; charset=utf-8", codigo=200, extras=None):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Cache-Control", "no-store")
        for k, v in (extras or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _json(self, dados, codigo=200):
        self._enviar(json.dumps(dados, ensure_ascii=False).encode("utf-8"), codigo=codigo)

    def _host_ok(self):
        return self.headers.get("Host", "") in HOSTS_OK

    def do_GET(self):
        self._rota("GET")

    def do_POST(self):
        self._rota("POST")

    def do_PUT(self):
        self._rota("PUT")

    def do_DELETE(self):
        self._rota("DELETE")

    def _rota(self, metodo):
        if not self._host_ok():
            return self._json({"erro": "host"}, 403)
        url = urlparse(self.path)
        if url.path.startswith("/fxg-cdn/"):
            return self._proxy(metodo, CDN + self.path[len("/fxg-cdn"):])
        if url.path.startswith("/fxg/"):
            return self._proxy(metodo, SITE + self.path[len("/fxg"):])
        if metodo == "POST" and url.path.startswith("/cep/"):
            if self.headers.get("X-Cep") != "1":
                return self._json({"erro": "proibido"}, 403)
            n = int(self.headers.get("Content-Length") or 0)
            dados = json.loads(self.rfile.read(n) or b"{}")
            if url.path == "/cep/eval":
                return self._json({"resultado": avaliar(dados.get("script", ""))})
            if url.path == "/cep/fs":
                return self._json(fs(dados.get("op"), dados.get("caminho", ""), dados.get("dados"),
                                     dados.get("codificacao", "UTF-8")))
            if url.path == "/cep/abrir-url":
                if str(dados.get("url", "")).startswith(("https://", "http://")):
                    os.startfile(dados["url"])
                return self._json({"ok": True})
            return self._json({"erro": "rota"}, 404)
        if metodo != "GET":
            return self._json({"erro": "rota"}, 404)
        if url.path == "/cep/caminho":
            tipo = parse_qs(url.query).get("tipo", ["userData"])[0]
            caminhos = {"userData": os.environ["APPDATA"], "extension": str(PLUGIN),
                        "myDocuments": str(Path.home() / "Documents")}
            return self._enviar(("file:///" + caminhos.get(tipo, os.environ["APPDATA"]).replace("\\", "/")).encode(),
                                "text/plain; charset=utf-8")
        if url.path == "/cep-shim.js":
            return self._enviar((AQUI / "web" / "cep-shim.js").read_bytes(), TIPOS[".js"])
        if url.path == "/plugin-illustrator.js":
            return self._bootstrap()
        if url.path in ("/", "/index.html"):
            html = (PLUGIN / "index.html").read_text(encoding="utf-8")
            html = html.replace(f"'{SITE}/plugin-illustrator.js?v='", "'/plugin-illustrator.js?v='")
            html = html.replace("<head>", '<head>\n<script src="/cep-shim.js"></script>', 1)
            html = html.replace("<title>Fluxogama Angero</title>", "<title>Fluxogama - Angerô</title>")
            return self._enviar(html.encode("utf-8"), TIPOS[".html"])
        alvo = (PLUGIN / url.path.lstrip("/")).resolve()
        if PLUGIN.resolve() in alvo.parents and alvo.is_file():
            return self._enviar(alvo.read_bytes(), TIPOS.get(alvo.suffix.lower(), "application/octet-stream"))
        return self._json({"erro": "não encontrado"}, 404)

    def _bootstrap(self):
        """Script do Fluxogama que define os endereços; troca os do site/CDN do cliente pelo intermediário."""
        try:
            with urllib.request.urlopen(f"{SITE}/plugin-illustrator.js", timeout=30, context=SSL) as r:
                js = r.read().decode("utf-8")
        except (urllib.error.URLError, OSError):
            js = (f"var Fluxogama = {{'cdn': '{CDN}', 'cdnPortalCliente': '{CDN}/upload/portal/angero',"
                  f" 'urlCliente': '{SITE}'}};")
        base = f"http://127.0.0.1:{PORTA}"
        js = re.sub(r"('urlCliente'\s*:\s*')https://[^']+'", rf"\1{base}/fxg'", js)
        js = re.sub(r"('cdnPortalCliente'\s*:\s*')https://cdn\.fluxogama\.com\.br", rf"\1{base}/fxg-cdn", js)
        self._enviar(js.encode("utf-8"), TIPOS[".js"])

    def _proxy(self, metodo, destino):
        n = int(self.headers.get("Content-Length") or 0)
        corpo = self.rfile.read(n) if n else None
        cab = {k: v for k, v in self.headers.items()
               if k.lower() in ("content-type", "authorization", "accept", "x-requested-with")}
        cab["User-Agent"] = "SuiteAngero-Fluxogama/1.0"
        req = urllib.request.Request(destino, data=corpo, method=metodo, headers=cab)
        try:
            r = urllib.request.urlopen(req, timeout=600, context=SSL)
            codigo = r.status
        except urllib.error.HTTPError as e:
            r, codigo = e, e.code
        except urllib.error.URLError as e:
            return self._json({"erro": f"sem conexão com o Fluxogama: {e.reason}"}, 502)
        with r:
            dados = r.read()
            extras = {k: v for k, v in r.headers.items()
                      if k.lower() in ("authorization", "content-disposition")}
            self._enviar(dados, r.headers.get("Content-Type", "application/octet-stream"), codigo, extras)
