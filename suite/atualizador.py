"""Atualização automática pela aba Releases do GitHub.

Cada repositório publica, a cada push, uma versão com dois arquivos de nome fixo:
  versao.txt                       ex.: 1.0.0.42 (versão + número da compilação)
  <exe>-windows-x64.zip            os programas (ou suite-angero.zip, para o iniciador)
Os links "releases/latest/download/..." não usam a API do GitHub (sem limite de consultas por IP,
que seria dividido por todos os computadores da empresa).

Programas: só atualiza o que está instalado e fechado (aberto, tenta de novo na próxima rodada).
Iniciador: só se atualiza quando foi instalado pelo instalador (arquivo instalado.txt na pasta).
"""
import io
import os
import ssl
import threading
import time
import urllib.error
import urllib.request
import winreg
import zipfile
from pathlib import Path

import programas

GITHUB = "https://github.com/wesleiad"
REPO_SUITE = "Suite-Angero"
RAIZ_SUITE = Path(__file__).resolve().parent.parent
INTERVALO = 6 * 3600
SSL = ssl.create_default_context()

estado = {"ultima_verificacao": None, "verificando": False, "itens": {}, "mensagem": ""}
_trava = threading.Lock()


def _baixar(url: str, limite_mb=600) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "SuiteAngero-Atualizador/1.0"})
    with urllib.request.urlopen(req, timeout=120, context=SSL) as r:
        dados = r.read(limite_mb * 1024 * 1024 + 1)
    if len(dados) > limite_mb * 1024 * 1024:
        raise ValueError("arquivo grande demais")
    return dados


def _versao(texto: str | None) -> tuple:
    try:
        return tuple(int(x) for x in (texto or "").strip().lstrip("v").split("."))
    except ValueError:
        return ()


def versao_remota(repo: str) -> str | None:
    try:
        return _baixar(f"{GITHUB}/{repo}/releases/latest/download/versao.txt", 1).decode().strip()
    except (urllib.error.URLError, OSError, ValueError):
        return None


def _versao_local_programa(p: dict, pasta: Path) -> str:
    arq = pasta / "versao.txt"
    if arq.is_file():
        return arq.read_text(encoding="utf-8").strip()
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, programas.CHAVE_REG + "\\" + p["pacote"]) as k:
            return winreg.QueryValueEx(k, "Versao")[0]
    except OSError:
        return ""


def _extrair(dados: bytes, destino: Path, ignorar_prefixo=""):
    with zipfile.ZipFile(io.BytesIO(dados)) as z:
        nomes = z.namelist()
        # zip com uma pasta raiz única: extrai o conteúdo dela
        raiz = nomes[0].split("/")[0] + "/" if nomes and all(n.startswith(nomes[0].split("/")[0] + "/") for n in nomes) else ""
        for info in z.infolist():
            nome = info.filename[len(raiz):]
            if not nome or info.is_dir() or (ignorar_prefixo and nome.startswith(ignorar_prefixo)):
                continue
            alvo = (destino / nome).resolve()
            if destino.resolve() not in alvo.parents:  # proteção contra caminhos "../"
                continue
            alvo.parent.mkdir(parents=True, exist_ok=True)
            tmp = alvo.with_name(alvo.name + ".novo")
            tmp.write_bytes(z.read(info))
            os.replace(tmp, alvo)


def atualizar_programa(p: dict) -> dict:
    pasta = programas.pasta_instalada(p)
    if not pasta:
        return {"nome": p["nome"], "situacao": "não instalado"}
    local = _versao_local_programa(p, pasta)
    remota = versao_remota(p["repo"])
    info = {"nome": p["nome"], "instalada": local, "disponivel": remota}
    if not remota:
        return {**info, "situacao": "sem conexão com o GitHub"}
    if _versao(remota) <= _versao(local):
        return {**info, "situacao": "atualizado"}
    if programas.rodando(p["id"]):
        return {**info, "situacao": "versão nova disponível — será instalada quando o programa for fechado"}
    zipname = p["exe"].replace(".exe", "-windows-x64.zip")
    _extrair(_baixar(f"{GITHUB}/{p['repo']}/releases/latest/download/{zipname}"), pasta)
    (pasta / "versao.txt").write_text(remota, encoding="utf-8")
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, programas.CHAVE_REG + "\\" + p["pacote"]) as k:
            winreg.SetValueEx(k, "Versao", 0, winreg.REG_SZ, remota)
    except OSError:
        pass
    return {**info, "instalada": remota, "situacao": f"atualizado para {remota}"}


def atualizar_suite() -> dict:
    marca = RAIZ_SUITE / "instalado.txt"
    local_arq = RAIZ_SUITE / "versao.txt"
    local = local_arq.read_text(encoding="utf-8").strip() if local_arq.is_file() else ""
    info = {"nome": "Suíte Angerô (iniciador e assistente)", "instalada": local}
    if not marca.is_file():
        return {**info, "situacao": "cópia de desenvolvimento — não se atualiza sozinha"}
    remota = versao_remota(REPO_SUITE)
    info["disponivel"] = remota
    if not remota:
        return {**info, "situacao": "sem conexão com o GitHub"}
    if _versao(remota) <= _versao(local):
        return {**info, "situacao": "atualizado"}
    # plugins/ e python/ ficam como estão (extensões instaladas pela empresa e o Python do pacote)
    _extrair(_baixar(f"{GITHUB}/{REPO_SUITE}/releases/latest/download/suite-angero.zip"), RAIZ_SUITE)
    local_arq.write_text(remota, encoding="utf-8")
    return {**info, "instalada": remota, "situacao": f"atualizado para {remota} — vale ao reabrir a Suíte"}


def verificar():
    if not _trava.acquire(blocking=False):
        return
    try:
        estado["verificando"] = True
        itens = {}
        try:
            itens["suite"] = atualizar_suite()
        except Exception as e:
            itens["suite"] = {"nome": "Suíte Angerô", "situacao": f"erro: {e}"}
        for p in programas.PROGRAMAS.values():
            try:
                itens[p["id"]] = atualizar_programa(p)
            except Exception as e:
                itens[p["id"]] = {"nome": p["nome"], "situacao": f"erro: {e}"}
        estado["itens"] = itens
        estado["ultima_verificacao"] = time.strftime("%d/%m/%Y %H:%M")
    finally:
        estado["verificando"] = False
        _trava.release()


def iniciar_em_segundo_plano(espera_inicial=20):
    def laco():
        time.sleep(espera_inicial)
        while True:
            verificar()
            time.sleep(INTERVALO)

    threading.Thread(target=laco, daemon=True).start()
