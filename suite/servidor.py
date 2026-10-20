"""Servidor local da Suíte Angerô (só nesta máquina, 127.0.0.1).

Serve o iniciador (web/index.html) e a API usada por ele e pelo assistente.
Uso: python servidor.py  (porta pelo env SUITE_PORTA, padrão 8790)
"""
import json
import os
import socket
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# o Python portátil do instalador não põe a pasta do script no caminho de importação
sys.path.insert(0, str(Path(__file__).resolve().parent))

import assistente
import atualizador
import fluxogama
import programas


AQUI = Path(__file__).resolve().parent
WEB = AQUI / "web"
ICONES = AQUI.parent / "icones" / "png"
PORTA = int(os.environ.get("SUITE_PORTA", "8790"))
HOSTS_OK = {f"127.0.0.1:{PORTA}", f"localhost:{PORTA}"}
TIPOS = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
         ".js": "text/javascript; charset=utf-8", ".png": "image/png", ".svg": "image/svg+xml",
         ".ico": "image/x-icon", ".woff2": "font/woff2", ".ttf": "font/ttf"}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        if sys.stderr:  # sem console (pythonw) não há stderr
            sys.stderr.write("[suite] " + (fmt % args) + "\n")

    # ---- respostas
    def _json(self, dados, codigo=200):
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _arquivo(self, caminho: Path):
        if not caminho.is_file():
            return self._json({"erro": "não encontrado"}, 404)
        corpo = caminho.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", TIPOS.get(caminho.suffix.lower(), "application/octet-stream"))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _host_ok(self):
        # bloqueia DNS rebinding: só aceita o próprio endereço local
        return self.headers.get("Host", "") in HOSTS_OK

    def _corpo(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}") if n else {}

    # ---- rotas
    def do_GET(self):
        if not self._host_ok():
            return self._json({"erro": "host"}, 403)
        url = urlparse(self.path)
        if url.path in ("/", "/index.html"):
            return self._arquivo(WEB / "index.html")
        if url.path.startswith("/web/"):
            alvo = (WEB / url.path[5:]).resolve()
            return self._arquivo(alvo) if WEB in alvo.parents else self._json({}, 404)
        if url.path.startswith("/icones/"):
            alvo = (ICONES / Path(url.path).name).resolve()
            return self._arquivo(alvo)
        if url.path == "/api/programas":
            return self._json(programas.situacao())
        if url.path == "/api/config":
            return self._json({"config": assistente.config_publica(),
                               "pastas_busca": [str(p) for p in sum(assistente.pastas_busca(), [])]})
        if url.path == "/api/atualizacoes":
            return self._json(atualizador.estado)
        if url.path == "/api/arquivos":
            termo = parse_qs(url.query).get("termo", [""])[0]
            return self._json(assistente.buscar_arquivos(termo))
        return self._json({"erro": "rota"}, 404)

    def do_POST(self):
        # O cabeçalho X-Suite força pré-verificação CORS, que este servidor não responde:
        # assim nenhum site aberto no navegador consegue mandar comandos para cá.
        if not self._host_ok() or self.headers.get("X-Suite") != "1":
            return self._json({"erro": "proibido"}, 403)
        url = urlparse(self.path)
        try:
            dados = self._corpo()
            if url.path == "/api/abrir":
                return self._json({"mensagem": programas.abrir(dados["programa"], dados.get("arquivo"))})
            if url.path == "/api/escolher":
                caminho = programas.escolher_arquivo()
                if not caminho:
                    return self._json({"caminho": None})
                pid = programas.programa_para(caminho)
                if not pid:
                    return self._json({"caminho": caminho,
                                       "mensagem": f"Nenhum programa da Suíte abre arquivos {Path(caminho).suffix}."})
                return self._json({"caminho": caminho, "mensagem": programas.abrir(pid, caminho)})
            if url.path == "/api/fluxogama":
                abrir_painel_fluxogama()
                return self._json({"mensagem": "Abrindo o Fluxogama…"})
            if url.path == "/api/extensao":
                import extensoes
                ext = next((e for e in extensoes.listar() if e["id"] == dados.get("id")), None)
                if not ext or not ext["suportada"]:
                    return self._json({"erro": "extensão não encontrada ou ainda não adaptada"}, 404)
                abrir_painel_fluxogama()
                return self._json({"mensagem": f"Abrindo {ext['nome']}…"})
            if url.path == "/api/atualizar":
                threading.Thread(target=atualizador.verificar, daemon=True).start()
                return self._json({"mensagem": "Procurando atualizações…"})
            if url.path == "/api/mostrar":
                programas.mostrar_na_pasta(dados["caminho"])
                return self._json({"ok": True})
            if url.path == "/api/chat":
                return self._json(assistente.conversar(dados.get("historico", [])))
            if url.path == "/api/config":
                assistente.salvar_config(dados)
                return self._json({"config": assistente.config_publica()})
            if url.path == "/api/testar":
                return self._json(assistente.testar_chave(dados.get("provedor", "groq")))
        except Exception as e:
            return self._json({"erro": str(e)}, 400)
        return self._json({"erro": "rota"}, 404)


class ServidorUnico(ThreadingHTTPServer):
    """Porta só deste processo: no Windows o padrão (SO_REUSEADDR) deixava cada abertura da Suíte
    subir mais um servidor na mesma porta, em vez de repassar o pedido ao que já estava aberto."""
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def _ja_rodando(acao, dados):
    """Manda o pedido para o iniciador que já está aberto."""
    import urllib.request
    req = urllib.request.Request(f"http://127.0.0.1:{PORTA}{acao}", data=json.dumps(dados).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "X-Suite": "1"})
    urllib.request.urlopen(req, timeout=30).read()


def main():
    # Atalhos: "--abrir vetor" abre um programa (o Illustre já traz o painel do Fluxogama);
    # "--fluxogama" abre só o painel. Nos dois casos a janela do iniciador não aparece.
    acao = None
    if "--abrir" in sys.argv:
        acao = ("/api/abrir", {"programa": sys.argv[sys.argv.index("--abrir") + 1]})
        if "--arquivo" in sys.argv:  # duplo clique num arquivo associado
            acao[1]["arquivo"] = sys.argv[sys.argv.index("--arquivo") + 1]
    elif "--fluxogama" in sys.argv:
        acao = ("/api/fluxogama", {})
    # reiniciando depois de atualizar: a versão anterior pode levar uns segundos para soltar as portas
    tentativas = 30 if "--reiniciando" in sys.argv else 1
    for i in range(tentativas):
        try:
            srv = ServidorUnico(("127.0.0.1", PORTA), Handler)
            break
        except OSError:
            if i + 1 < tentativas:
                time.sleep(0.5)
    else:
        # já tem um iniciador rodando: só repassa o pedido
        _ja_rodando(*acao) if acao else abrir_janela()
        return
    for i in range(tentativas):
        try:  # plugin Fluxogama em outra porta (outra origem: não enxerga a API do iniciador)
            fxg = ServidorUnico(("127.0.0.1", fluxogama.PORTA), fluxogama.HandlerFluxogama)
            threading.Thread(target=fxg.serve_forever, daemon=True).start()
            break
        except OSError:
            if i + 1 < tentativas:
                time.sleep(0.5)
    programas.GANCHOS_ABRIR.append(_painel_junto_do_illustre)
    atualizador.AO_ATUALIZAR_SUITE.append(_reiniciar_quando_livre)
    atualizador.iniciar_em_segundo_plano()
    print(f"Suíte Angerô em http://127.0.0.1:{PORTA}/")
    if acao:
        threading.Timer(0.3, lambda: _ja_rodando(*acao)).start()
    elif "--sem-janela" not in sys.argv:
        threading.Timer(0.5, abrir_janela).start()
    try:
        srv.serve_forever()
    finally:
        programas.PONTES.fechar_todas()


def _reiniciar_quando_livre():
    """Depois de uma atualização da Suíte, troca este servidor por um novo (com o código novo).
    Espera o painel do Fluxogama ser fechado: o login dele fica na memória deste servidor."""
    def trabalho():
        import subprocess
        import janelas
        while janelas.janelas(titulo="Fluxogama - Angerô"):
            time.sleep(60)
        programas.PONTES.fechar_todas()
        # o novo espera as portas, que se soltam no os._exit (fechá-las antes derrubaria o laço principal)
        subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--sem-janela", "--reiniciando"],
                         cwd=str(Path(__file__).resolve().parent))
        os._exit(0)

    threading.Thread(target=trabalho, daemon=True).start()


def _painel_junto_do_illustre(pid, arquivo):
    if pid != "vetor":
        return
    # o botão "Extensões" agora é do próprio Illustre (lê `extensoes.py --listar` e pede /api/extensao)
    if assistente.ler_config().get("fluxogama_junto_illustre", False):
        abrir_painel_fluxogama()


def abrir_painel_fluxogama():
    """Painel do Fluxogama encaixado à direita, com o Illustre ao lado (como um painel do Illustrator)."""
    import janelas
    existente = janelas.janelas(titulo="Fluxogama - Angerô")
    if not existente:
        ill = janelas.janela_illustre()  # abre já no monitor do Illustre
        x, y, larg, alt = janelas.area_trabalho(ill)
        lp = janelas.largura_painel(ill)
        abrir_janela(f"http://127.0.0.1:{fluxogama.PORTA}/", f"{lp},{alt}", f"{x + larg - lp},{y}")
    threading.Thread(target=janelas.encaixar_illustre_e_painel, daemon=True).start()


def abrir_janela(url=None, tamanho="1280,820", posicao=None):
    url = url or f"http://127.0.0.1:{PORTA}/"
    edge = [Path(os.environ.get(v, "")) / "Microsoft/Edge/Application/msedge.exe"
            for v in ("ProgramFiles(x86)", "ProgramFiles")]
    for e in edge:
        if e.is_file():
            import subprocess
            extra = [f"--window-position={posicao}"] if posicao else []
            subprocess.Popen([str(e), f"--app={url}", f"--window-size={tamanho}"] + extra,
                             creationflags=0x00000008)
            return
    webbrowser.open(url)


if __name__ == "__main__":
    main()
