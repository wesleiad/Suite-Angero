"""Assistente Angerô: IA na nuvem (Groq ou Gemini, plano gratuito) com ferramentas para
abrir programas, achar arquivos e comandar os programas da Suíte via MCP."""
import json
import os
import re
import ssl
import time
import unicodedata
import urllib.error
import urllib.request
import winreg
from pathlib import Path

import programas

PASTA_CONFIG = Path(os.environ["APPDATA"]) / "SuiteAngero"
ARQ_CONFIG = PASTA_CONFIG / "config.json"

PROVEDORES = {
    "groq": {
        "nome": "Groq",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "modelos_url": "https://api.groq.com/openai/v1/models",
        "modelo": "openai/gpt-oss-120b",
    },
    "gemini": {
        "nome": "Google Gemini",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "modelos_url": "https://generativelanguage.googleapis.com/v1beta/openai/models",
        "modelo": "gemini-3.1-flash-lite",  # rápido (~1 s) e com cota grátis maior
    },
}

PADRAO = {
    "provedor": "gemini",
    "chaves": {"groq": "", "gemini": ""},
    "modelos": {"groq": PROVEDORES["groq"]["modelo"], "gemini": PROVEDORES["gemini"]["modelo"]},
    "reserva": False,          # se o provedor principal estourar o limite, tenta o outro
    "pastas_extras": [],       # ex.: ["P:\\", "\\\\servidor\\pasta"]
    "fluxogama_junto_illustre": False,  # abrir o painel do Fluxogama ao lado do Illustre
}

SSL = ssl.create_default_context()  # usa os certificados do Windows (inclui o de proxies corporativos)


# ---------------------------------------------------------------- configuração

REG_CENTRAL = r"Software\Grupo Angero\Suite Angero\Assistente"
ARQ_CENTRAL = Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "SuiteAngero" / "assistente.json"


def config_central() -> dict:
    r"""Chave e modelo definidos pelo TI para o computador (o usuário não altera):
    1) registro HKLM\Software\Grupo Angero\Suite Angero\Assistente (GeminiChave, GeminiModelo) — dá para mandar por GPO;
    2) %ProgramData%\SuiteAngero\assistente.json  {"gemini_chave": "...", "gemini_modelo": "..."}."""
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_CENTRAL) as k:
            chave = winreg.QueryValueEx(k, "GeminiChave")[0]
            try:
                modelo = winreg.QueryValueEx(k, "GeminiModelo")[0]
            except OSError:
                modelo = ""
            if chave:
                return {"chave": chave.strip(), "modelo": (modelo or "").strip(), "origem": "registro do computador"}
    except OSError:
        pass
    try:
        dados = json.loads(ARQ_CENTRAL.read_text(encoding="utf-8-sig"))
        if dados.get("gemini_chave"):
            return {"chave": dados["gemini_chave"].strip(), "modelo": (dados.get("gemini_modelo") or "").strip(),
                    "origem": "arquivo do computador"}
    except (OSError, ValueError):
        pass
    return {}


def ler_config() -> dict:
    cfg = json.loads(json.dumps(PADRAO))
    try:
        salvo = json.loads(ARQ_CONFIG.read_text(encoding="utf-8"))
        for k, v in salvo.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    except (OSError, ValueError):
        pass
    central = config_central()
    if central:
        cfg["chaves"]["gemini"] = central["chave"]
        if central["modelo"]:
            cfg["modelos"]["gemini"] = central["modelo"]
    cfg["provedor"] = "gemini"
    return cfg


def salvar_config(novo: dict) -> dict:
    """Só o que o usuário pode mudar pela tela (a chave da IA é do TI: config_central)."""
    try:
        cfg = json.loads(ARQ_CONFIG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cfg = {}
    for k in ("pastas_extras", "fluxogama_junto_illustre"):
        if k in novo:
            cfg[k] = novo[k]
    for prov, valor in (novo.get("modelos") or {}).items():  # troca automática de modelo aposentado
        if prov in PROVEDORES and valor:
            cfg.setdefault("modelos", {})[prov] = str(valor).strip()
    PASTA_CONFIG.mkdir(parents=True, exist_ok=True)
    tmp = ARQ_CONFIG.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, ARQ_CONFIG)
    return ler_config()


def config_publica() -> dict:
    """Config para a tela: nada de chave."""
    cfg = ler_config()
    central = config_central()
    return {"assistente_configurado": bool(cfg["chaves"].get("gemini")),
            "origem": central.get("origem", "usuário" if cfg["chaves"].get("gemini") else ""),
            "pastas_extras": cfg.get("pastas_extras", []),
            "fluxogama_junto_illustre": bool(cfg.get("fluxogama_junto_illustre"))}


# ---------------------------------------------------------------- busca de arquivos

def _pasta_shell(nome_reg: str, padrao: Path) -> Path:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as k:
            return Path(os.path.expandvars(winreg.QueryValueEx(k, nome_reg)[0]))
    except OSError:
        return padrao


def pastas_busca() -> list[Path]:
    casa = Path.home()
    base = [
        _pasta_shell("Desktop", casa / "Desktop"),
        _pasta_shell("Personal", casa / "Documents"),
        _pasta_shell("{374DE290-123F-4565-9164-39C4925E467B}", casa / "Downloads"),
        _pasta_shell("My Pictures", casa / "Pictures"),
        _pasta_shell("My Video", casa / "Videos"),
    ]
    extras = [Path(p) for p in ler_config().get("pastas_extras", [])]
    vistas, saida = set(), []
    for p in base + extras:
        chave = str(p).lower()
        if chave not in vistas and p.exists():
            vistas.add(chave)
            saida.append(p)
    return saida


def _sem_acento(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn")


IGNORAR = {"appdata", "node_modules", "$recycle.bin", "windows", "program files", "program files (x86)", ".git"}


def buscar_arquivos(termo: str, extensoes: list[str] | None = None, limite: int = 25) -> dict:
    palavras = _sem_acento(termo or "").split()
    exts = {("." + e.lower().lstrip(".")) for e in (extensoes or [])}
    achados, fim = [], time.time() + 12
    for raiz in pastas_busca():
        for pasta, subpastas, arquivos in os.walk(raiz):
            subpastas[:] = [s for s in subpastas if s.lower() not in IGNORAR and not s.startswith(".")]
            for a in arquivos:
                if exts and Path(a).suffix.lower() not in exts:
                    continue
                nome = _sem_acento(a)
                if all(p in nome for p in palavras):
                    caminho = Path(pasta) / a
                    try:
                        st = caminho.stat()
                    except OSError:
                        continue
                    achados.append({"caminho": str(caminho), "tamanho_kb": st.st_size // 1024,
                                    "modificado": time.strftime("%d/%m/%Y %H:%M", time.localtime(st.st_mtime))})
            if time.time() > fim or len(achados) >= limite * 3:
                break
        if time.time() > fim:
            break
    achados.sort(key=lambda x: x["modificado"][6:10] + x["modificado"][3:5] + x["modificado"][:2], reverse=True)
    return {"pastas_pesquisadas": [str(p) for p in pastas_busca()], "resultados": achados[:limite],
            "busca_incompleta": time.time() > fim}


# ---------------------------------------------------------------- ferramentas da IA

IDS = list(programas.PROGRAMAS)

FERRAMENTAS = [
    {"type": "function", "function": {
        "name": "listar_programas",
        "description": "Lista os programas da Suíte Angerô, para que servem e se estão abertos.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "abrir_programa",
        "description": "Abre um programa da Suíte (sem arquivo).",
        "parameters": {"type": "object", "properties": {
            "programa": {"type": "string", "enum": IDS}}, "required": ["programa"]}}},
    {"type": "function", "function": {
        "name": "buscar_arquivos",
        "description": "Procura arquivos pelo nome (todas as palavras precisam aparecer, acentos ignorados) "
                       "na Área de Trabalho, Documentos, Downloads, Imagens, Vídeos e pastas extras configuradas.",
        "parameters": {"type": "object", "properties": {
            "termo": {"type": "string", "description": "palavras do nome do arquivo"},
            "extensoes": {"type": "array", "items": {"type": "string"}, "description": "ex.: [\"ai\",\"pdf\"]"}},
            "required": ["termo"]}}},
    {"type": "function", "function": {
        "name": "abrir_arquivo",
        "description": "Abre um arquivo no programa certo da Suíte (escolhido pela extensão, ou o informado).",
        "parameters": {"type": "object", "properties": {
            "caminho": {"type": "string", "description": "caminho completo do arquivo"},
            "programa": {"type": "string", "enum": IDS}}, "required": ["caminho"]}}},
    {"type": "function", "function": {
        "name": "ferramentas_do_programa",
        "description": "Lista os comandos que a IA pode executar dentro de um programa ABERTO (vetor, foto, video, "
                       "galeria). Use 'filtro' com uma palavra em inglês (ex.: export, open, layer, text, color) "
                       "para não receber a lista inteira.",
        "parameters": {"type": "object", "properties": {
            "programa": {"type": "string", "enum": IDS},
            "filtro": {"type": "string"}}, "required": ["programa"]}}},
    {"type": "function", "function": {
        "name": "usar_ferramenta",
        "description": "Executa um comando dentro de um programa aberto (nomes vindos de ferramentas_do_programa). "
                       "Para comandos genéricos use run_command/command_run com o id do comando.",
        "parameters": {"type": "object", "properties": {
            "programa": {"type": "string", "enum": IDS},
            "ferramenta": {"type": "string"},
            "argumentos": {"type": "object"}}, "required": ["programa", "ferramenta"]}}},
]

SISTEMA = """Você é o Assistente Angerô, ajudante dos programas de criação do Grupo Angerô (indústria têxtil e de confecção: moda, pijamas, estampas, fichas técnicas).
Responda sempre em português do Brasil, de forma curta, simples e gentil — os usuários não são técnicos.

Programas da Suíte (todos gratuitos, com menus e atalhos no estilo da Adobe; o id entre parênteses é o usado nas ferramentas):
- Illustre - Angerô (vetor): desenho vetorial como o Illustrator — .ai, .svg, .eps, .pdf vetorial, fichas técnicas e estampas.
- Fotografe - Angerô (foto): edição de imagens como o Photoshop — .psd e imagens.
- PDF - Angerô (pdf): ler, juntar, dividir, assinar PDFs.
- Cena - Angerô (video): edição de vídeo como o Premiere.
- LightBridge - Angerô (galeria): catálogo e revelação de fotos, como o Bridge/Lightroom.
Os usuários chamam os programas pelo nome curto (Illustre, Fotografe, PDF, Cena, LightBridge).

Regras:
- Use as ferramentas para agir de verdade (abrir programas, achar e abrir arquivos, executar comandos). Não diga que fez algo sem ter feito.
- Para achar um arquivo, use buscar_arquivos; se vierem vários, mostre os mais prováveis (nome e pasta) e pergunte qual.
- Para agir dentro de um programa: ele precisa estar aberto; consulte ferramentas_do_programa com um filtro curto e depois usar_ferramenta.
- Antes de apagar, sobrescrever ou fechar sem salvar, peça confirmação.
- Para dúvidas de "como faço…", explique em passos numerados usando os nomes dos menus em português (Arquivo, Editar, Objeto, Texto, Selecionar, Efeito, Exibir, Janela) — eles seguem o Illustrator/Photoshop.
- Se algo falhar, explique o problema em uma frase e sugira o próximo passo."""


def executar(nome: str, args: dict) -> str:
    try:
        if nome == "listar_programas":
            r = programas.situacao()
        elif nome == "abrir_programa":
            r = programas.abrir(args["programa"])
        elif nome == "buscar_arquivos":
            r = buscar_arquivos(args.get("termo", ""), args.get("extensoes"))
        elif nome == "abrir_arquivo":
            caminho = args["caminho"]
            pid = args.get("programa") or programas.programa_para(caminho)
            r = programas.abrir(pid, caminho) if pid else f"Nenhum programa da Suíte abre arquivos {Path(caminho).suffix}."
        elif nome == "ferramentas_do_programa":
            lista = programas.PONTES.ferramentas(args["programa"], args.get("filtro", ""))
            r = {"total": len(lista), "ferramentas": lista[:40],
                 "aviso": "lista cortada, refine o filtro" if len(lista) > 40 else ""}
        elif nome == "usar_ferramenta":
            r = programas.PONTES.chamar(args["programa"], args["ferramenta"], args.get("argumentos") or {})
        else:
            r = f"ferramenta desconhecida: {nome}"
    except Exception as e:  # o erro volta para a IA explicar ao usuário
        r = f"ERRO: {e}"
    texto = r if isinstance(r, str) else json.dumps(r, ensure_ascii=False)
    return texto if len(texto) <= 4000 else texto[:4000] + "\n…(resposta cortada)"


# ---------------------------------------------------------------- chamada à IA

class LimiteAtingido(Exception):
    pass


class Sobrecarga(Exception):
    pass


MODELOS_GEMINI = ["gemini-3.1-flash-lite", "gemini-3.8-flash", "gemini-3-flash-preview"]


def _chamar_com_reserva(provedor: str, cfg: dict, mensagens: list) -> dict:
    """Picos de demanda no Google são comuns: tenta o modelo configurado e os reservas, com pausas curtas."""
    modelos = [cfg["modelos"].get(provedor) or PROVEDORES[provedor]["modelo"]]
    if provedor == "gemini":
        modelos += [m for m in MODELOS_GEMINI if m not in modelos]
    ultimo = None
    for rodada, pausa in enumerate((0, 2, 5)):
        time.sleep(pausa)
        for m in modelos:
            try:
                return _chamar_ia(provedor, dict(cfg, modelos=dict(cfg["modelos"], **{provedor: m})), mensagens)
            except (Sobrecarga, TimeoutError) as e:
                ultimo = e
            except urllib.error.URLError as e:
                if not isinstance(getattr(e, "reason", None), TimeoutError):
                    raise
                ultimo = e
    raise Sobrecarga("a IA do Google está sobrecarregada agora") from ultimo


def _chamar_ia(provedor: str, cfg: dict, mensagens: list) -> dict:
    p = PROVEDORES[provedor]
    chave = cfg["chaves"].get(provedor)
    if not chave:
        raise RuntimeError("o assistente ainda não foi configurado neste computador — fale com o TI")
    corpo = {"model": cfg["modelos"].get(provedor) or p["modelo"], "messages": mensagens,
             "tools": FERRAMENTAS, "tool_choice": "auto", "temperature": 0.3}
    req = urllib.request.Request(p["url"], data=json.dumps(corpo).encode("utf-8"), method="POST",
                                 headers={"Authorization": f"Bearer {chave}", "Content-Type": "application/json",
                                          "User-Agent": "SuiteAngero/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60, context=SSL) as r:
            return json.loads(r.read())["choices"][0]["message"]
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode("utf-8", "replace")[:400]
        sugerido = re.search(r"use models/([\w.\-]+)", detalhe)
        if e.code == 404 and sugerido and not cfg.get("_trocou"):
            # modelo aposentado: o próprio Google indica o substituto; troca e tenta de novo
            salvar_config({"modelos": {provedor: sugerido.group(1)}})
            cfg["modelos"][provedor] = sugerido.group(1)
            cfg["_trocou"] = True
            return _chamar_ia(provedor, cfg, mensagens)
        if e.code in (500, 502, 503, 504):
            raise Sobrecarga(f"{p['nome']} sobrecarregado") from e
        if e.code == 429:
            raise LimiteAtingido(f"{p['nome']}: limite gratuito atingido") from e
        if e.code in (401, 403) or "API key" in detalhe:
            raise RuntimeError("a chave do assistente foi recusada — fale com o TI") from e
        raise RuntimeError(f"{p['nome']} respondeu erro {e.code}: {detalhe}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"sem conexão com o {p['nome']}: {e.reason}") from e


def conversar(historico: list[dict]) -> dict:
    """historico: [{role: user|assistant, content: str}]. Devolve {resposta, acoes, provedor}."""
    cfg = ler_config()
    ordem = [cfg["provedor"]]
    outro = "gemini" if cfg["provedor"] == "groq" else "groq"
    if cfg.get("reserva") and cfg["chaves"].get(outro):
        ordem.append(outro)

    msgs = [{"role": "system", "content": SISTEMA}]
    msgs += [{"role": m["role"], "content": str(m["content"])[:4000]}
             for m in historico[-12:] if m.get("role") in ("user", "assistant")]
    acoes, provedor = [], ordem[0]

    for _ in range(10):
        resposta = None
        for prov in list(ordem):
            try:
                resposta = _chamar_com_reserva(prov, cfg, msgs)
                provedor = prov
                break
            except LimiteAtingido as e:
                ultimo_erro = str(e)
                ordem.remove(prov)
                continue
            except Sobrecarga:
                return {"resposta": "⏳ A IA do Google está sobrecarregada neste momento. Tente de novo em alguns segundos.",
                        "acoes": acoes, "provedor": provedor}
        if resposta is None:
            return {"resposta": f"⏳ {ultimo_erro}. Espere um minuto e tente de novo.", "acoes": acoes,
                    "provedor": provedor}

        chamadas = resposta.get("tool_calls") or []
        if not chamadas:
            return {"resposta": resposta.get("content") or "(sem resposta)", "acoes": acoes, "provedor": provedor}

        msgs.append({"role": "assistant", "content": resposta.get("content") or "", "tool_calls": chamadas})
        for c in chamadas:
            nome = c["function"]["name"]
            try:
                args = json.loads(c["function"].get("arguments") or "{}")
            except ValueError:
                args = {}
            resultado = executar(nome, args)
            acoes.append({"ferramenta": nome, "argumentos": args, "ok": not resultado.startswith("ERRO"),
                          "resumo": resultado[:200]})
            msgs.append({"role": "tool", "tool_call_id": c["id"], "content": resultado})

    return {"resposta": "Fiz várias etapas mas não terminei; pode me dizer o próximo passo?", "acoes": acoes,
            "provedor": provedor}


def escolher_modelo(provedor: str, ids: list[str]) -> str | None:
    """Se o modelo configurado sumiu, pega o Flash mais novo (rápido e com cota grátis maior)."""
    import re
    if provedor != "gemini":
        return None
    candidatos = []
    for i in ids:
        nome = i.split("/")[-1]
        if not nome.startswith("gemini-") or "flash" not in nome:
            continue
        if any(x in nome for x in ("lite", "image", "tts", "live", "audio", "exp", "preview", "thinking", "embedding")):
            continue
        versao = re.match(r"gemini-(\d+(?:\.\d+)?)", nome)
        candidatos.append((float(versao.group(1)) if versao else 0, nome))
    return max(candidatos)[1] if candidatos else None


def testar_chave(provedor: str) -> dict:
    """Confere a chave listando os modelos disponíveis."""
    cfg = ler_config()
    p = PROVEDORES[provedor]
    chave = cfg["chaves"].get(provedor)
    if not chave:
        return {"ok": False, "erro": "sem chave"}
    req = urllib.request.Request(p["modelos_url"], headers={"Authorization": f"Bearer {chave}",
                                                            "User-Agent": "SuiteAngero/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20, context=SSL) as r:
            ids = sorted(m["id"] for m in json.loads(r.read()).get("data", []))
        modelo = cfg["modelos"].get(provedor)
        if not any(i.split("/")[-1] == modelo for i in ids):
            melhor = escolher_modelo(provedor, ids)
            if melhor:
                salvar_config({"modelos": {provedor: melhor}})
                modelo = melhor
        try:  # chamada real curta: confirma que o modelo responde para esta conta
            _chamar_ia(provedor, ler_config(), [{"role": "user", "content": "Responda só: ok"}])
            modelo, responde = ler_config()["modelos"][provedor], True
        except Exception as e:
            return {"ok": False, "erro": str(e)}
        return {"ok": True, "modelos": ids, "modelo_atual": modelo, "modelo_existe": responde}
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode("utf-8", "replace")
        if e.code in (401, 403) or "API key" in detalhe:
            return {"ok": False, "erro": "a chave foi recusada pelo Google — confira se copiou inteira"}
        return {"ok": False, "erro": f"HTTP {e.code}: {detalhe[:200]}"}
    except urllib.error.URLError as e:
        return {"ok": False, "erro": str(e.reason)}
