"""Aplica a identidade Angerô no código-fonte de um dos programas (forks do ArtCraft).

Uso: python rebrand.py <pasta-do-fork> <id>        ids: illustre, fotografe, pdf, cena, lightbridge

O que faz (só o que o usuário vê; nomes internos, formatos de arquivo e testes ficam como estão):
- ícones de assets/app-icon (barra do app, janela, .exe) -> ícones da Suíte Angerô;
- textos traduzidos (i18n *.tsv / *.json): nome do programa, "ArtCraft" e site -> Angerô;
- nome do programa no título da janela, Sobre e recursos do .exe;
- links de Ajuda -> GitHub da Suíte Angerô; o Discord sai dos menus e da barra (feito à parte, por programa).
"""
import json
import os
import re
import struct
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ICONES = AQUI.parent / "icones"
GITHUB = "https://github.com/wesleiad"
REPO_SUITE = f"{GITHUB}/Suite-Angero"

PROGRAMAS = {
    "illustre": {"orig": "VectorCraft", "curto": "Illustre", "icone": "vetor", "fork": "illustre-angero"},
    "fotografe": {"orig": "PhotoCraft", "curto": "Fotografe", "icone": "foto", "fork": "fotografe-angero"},
    "pdf": {"orig": "PdfCraft", "curto": "PDF Angerô", "icone": "pdf", "fork": "pdf-angero"},
    "cena": {"orig": "FilmCraft", "curto": "Cena", "icone": "video", "fork": "cena-angero"},
    "lightbridge": {"orig": "LightCraft", "curto": "LightBridge", "icone": "galeria", "fork": "lightbridge-angero"},
}


def nome_completo(cfg):
    return f"{cfg['curto'].replace(' Angerô', '')} - Angerô"


def links(pid, cfg):
    return {
        "site": REPO_SUITE,
        "ajuda": f"{REPO_SUITE}/blob/main/docs/ajuda/{pid}.md",
        "codigo": f"{GITHUB}/{cfg['fork']}",
    }


# ---------------------------------------------------------------- ícones

def tamanho_png(p: Path):
    with open(p, "rb") as f:
        cab = f.read(24)
    return struct.unpack(">II", cab[16:24]) if cab[:8] == b"\x89PNG\r\n\x1a\n" else None


def cli_vetor():
    """illustre-cli.exe (instalado ou compilado); na primeira vez, o vectorcraft-cli original serve."""
    local = Path(os.environ["LOCALAPPDATA"])
    for c in (local / "Programs" / "Suite Angero" / "Illustre - Angerô" / "illustre-cli.exe",
              local / "SuiteAngero" / "src" / "illustre-angero" / "target" / "release" / "illustre-cli.exe",
              *sorted((local / "SuiteAngero" / "apps").glob("vectorcraft-*/vectorcraft-cli.exe"))):
        if c.is_file():
            return c
    raise SystemExit("illustre-cli.exe não encontrado")


def trocar_icones(raiz: Path, cfg):
    svg = ICONES / "svg" / f"{cfg['icone']}.svg"
    ico = ICONES / "ico" / f"{cfg['icone']}.ico"
    cli = cli_vetor()
    n = 0
    for p in (raiz / "assets" / "app-icon").rglob("*"):
        if p.suffix.lower() == ".png":
            tam = tamanho_png(p)
            if not tam:
                continue
            lado = max(tam)
            subprocess.run([str(cli), "convert", str(svg), str(p), "--scale", str(lado / 256)],
                           check=True, capture_output=True)
            n += 1
        elif p.suffix.lower() == ".ico":
            p.write_bytes(ico.read_bytes())
            n += 1
        elif p.suffix.lower() == ".svg":
            p.write_bytes(svg.read_bytes())
            n += 1
    return n


def trocar_marcas(raiz: Path):
    """Logos do ArtCraft (docs/brand, usados na tela inicial/Sobre) -> folha da Suíte Angerô."""
    svg = ICONES / "svg" / "suite.svg"
    cli = cli_vetor()
    n = 0
    for p in (raiz / "docs" / "brand").glob("artcraft-*"):
        if p.suffix.lower() == ".svg":
            p.write_bytes(svg.read_bytes())
        elif p.suffix.lower() == ".png" and (tam := tamanho_png(p)):
            subprocess.run([str(cli), "convert", str(svg), str(p), "--scale", str(max(tam) / 256)],
                           check=True, capture_output=True)
        else:
            continue
        n += 1
    return n


# ---------------------------------------------------------------- textos

def trocas_texto(pid, cfg):
    o, c, l = cfg["orig"], cfg["curto"], links(pid, cfg)
    return [
        # frases inteiras primeiro (menus de Ajuda)
        (f"{o} em getartcraft.com", f"Ajuda do {c}"),
        (f"{o} on getartcraft.com", f"{c} Help"),
        (f"{o} no GitHub", f"Código-fonte do {c} (GitHub)"),
        (f"{o} on GitHub", f"{c} source code (GitHub)"),
        ("Site do ArtCraft", "Site da Suíte Angerô"),
        ("ArtCraft Website", "Suíte Angerô Website"),
        ("ArtCraft website", "Suíte Angerô website"),
        ("discord.gg/artcraft", l["site"].replace("https://", "")),
        ("getartcraft.com", l["site"].replace("https://", "")),
        ("ArtCraft", "Grupo Angerô"),
        (o, c),
    ]


def aplicar(texto, trocas):
    for a, b in trocas:
        texto = texto.replace(a, b)
    return texto


def trocar_traducoes(raiz: Path, pid, cfg):
    trocas = trocas_texto(pid, cfg)
    n = 0
    for p in raiz.rglob("*.tsv"):
        if "i18n" not in p.parts and "locales" not in p.parts:
            continue
        linhas = p.read_text(encoding="utf-8").split("\n")
        for i, linha in enumerate(linhas):
            if linha.startswith("#"):
                continue
            col = linha.split("\t")
            if len(col) >= 3 and any(a in col[2] for a, _ in trocas):
                col[2] = aplicar(col[2], trocas)  # só a tradução; a coluna "source" é a chave do código
                linhas[i] = "\t".join(col)
                n += 1
        p.write_text("\n".join(linhas), encoding="utf-8", newline="\n")
    for p in raiz.rglob("*.json"):
        if "locales" not in p.parts or "target" in p.parts:
            continue
        dados = json.loads(p.read_text(encoding="utf-8"))

        def andar(v):
            nonlocal n
            if isinstance(v, str) and any(a in v for a, _ in trocas):
                n += 1
                return aplicar(v, trocas)
            if isinstance(v, dict):
                return {k: andar(x) for k, x in v.items()}  # chaves ficam (são ids)
            if isinstance(v, list):
                return [andar(x) for x in v]
            return v

        p.write_text(json.dumps(andar(dados), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return n


def completar_traducoes(raiz: Path, pid, cfg):
    """Textos de interface (tl!("...")) com a marca antiga e sem tradução pt-br: cria a tradução já trocada."""
    trocas = trocas_texto(pid, cfg)
    alvos = [a for a, _ in trocas] + ["Discord"]
    tsv = next(iter(raiz.rglob("i18n/pt-br.tsv")), None)
    if not tsv:
        return 0
    conteudo = tsv.read_text(encoding="utf-8")
    existentes = {l.split("\t")[1] for l in conteudo.split("\n") if l.count("\t") >= 2 and not l.startswith("#")}
    novos = []
    for p in (raiz / "crates").rglob("*.rs"):
        if "tests" in p.parts or p.name.startswith("tests"):
            continue
        for m in re.finditer(r'tl!\(\s*"((?:[^"\\]|\\.)*)"', p.read_text(encoding="utf-8")):
            fonte = m.group(1)
            if "\\" in fonte or fonte in existentes or not any(a in fonte for a in alvos):
                continue
            existentes.add(fonte)
            novos.append(f"\t{fonte}\t{aplicar(fonte, trocas)}")
    if novos:
        tsv.write_text(conteudo.rstrip("\n") + "\n" + "\n".join(novos) + "\n", encoding="utf-8", newline="\n")
    return len(novos)


def trocar_recursos_exe(raiz: Path, cfg):
    """VERSIONINFO do .exe (build.rs com winresource)."""
    n = 0
    for p in raiz.glob("apps/*/build.rs"):
        s = p.read_text(encoding="utf-8")
        novo = re.sub(r'\.set\("ProductName",\s*"[^"]*"\)', f'.set("ProductName", "{nome_completo(cfg)}")', s)
        novo = re.sub(r'\.set\("FileDescription",\s*"[^"]*"\)', f'.set("FileDescription", "{nome_completo(cfg)}")', novo)
        novo = re.sub(r'\.set\("CompanyName",\s*"[^"]*"\)', '.set("CompanyName", "Grupo Angerô")', novo)
        novo = re.sub(r'\.set\("LegalCopyright",\s*"[^"]*"\)',
                      '.set("LegalCopyright", "Grupo Angerô. MIT OR Apache-2.0 (ver NOTICE).")', novo)
        if novo != s:
            p.write_text(novo, encoding="utf-8", newline="\n")
            n += 1
    return n


def trocar_literais(raiz: Path, pid, cfg):
    """Literal "<Orig>" (título da janela, Sobre) e URLs de Ajuda no código de interface."""
    o, l = cfg["orig"], links(pid, cfg)
    n = 0
    pastas = [raiz / "crates" / "ui-egui" / "src", raiz / "crates" / "engine" / "src"] + list((raiz / "apps").glob("*/src"))
    for pasta in pastas:
        for p in pasta.rglob("*.rs"):
            if p.name.startswith("tests") or "tests" in p.parts:
                continue
            s = p.read_text(encoding="utf-8")
            novo = s
            if "ui-egui" in p.parts or "apps" in p.parts:
                novo = novo.replace(f'"{o}"', f'"{nome_completo(cfg)}"')
            novo = re.sub(r'"https://getartcraft\.com/apps/[^"]*"', f'"{l["ajuda"]}"', novo)
            novo = novo.replace('"https://getartcraft.com"', f'"{l["site"]}"')
            novo = re.sub(r'"https://github\.com/storytold/[^"{]*"', f'"{l["codigo"]}"', novo)
            novo = novo.replace('format!("https://github.com/storytold/{APP_ID}")', f'"{l["codigo"]}".to_string()')
            novo = re.sub(r'format!\("https://getartcraft\.com/apps/\{[A-Z_]+\}"\)', f'"{l["ajuda"]}".to_string()', novo)
            if novo != s:
                p.write_text(novo, encoding="utf-8", newline="\n")
                n += 1
    return n


def main():
    raiz, pid = Path(sys.argv[1]), sys.argv[2]
    cfg = PROGRAMAS[pid]
    print("ícones:", trocar_icones(raiz, cfg))
    print("logos:", trocar_marcas(raiz))
    print("traduções:", trocar_traducoes(raiz, pid, cfg))
    print("traduções criadas:", completar_traducoes(raiz, pid, cfg))
    print("recursos .exe:", trocar_recursos_exe(raiz, cfg))
    print("código:", trocar_literais(raiz, pid, cfg))


if __name__ == "__main__":
    main()
