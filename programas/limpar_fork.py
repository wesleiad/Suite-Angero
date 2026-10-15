"""Transforma um fork do ArtCraft na versão Angerô: tira tudo o que é do projeto antigo e põe o nosso.

Uso: python limpar_fork.py <pasta-do-fork> <id>      (depois de rebrand.py)

- .exe e ferramenta de linha de comando com nome novo (ex.: illustre.exe, illustre-cli.exe);
- pastas de configuração/dados com o nome novo;
- remove documentação, roteiro, automações (CI), empacotamento e logos do projeto antigo;
- logos usados pelo código passam para assets/marca/ com nome Angerô;
- README novo (Grupo Angerô) e NOTICE com o aviso de modificação exigido pela licença Apache-2.0.
  LICENSE-APACHE, LICENSE-MIT e o NOTICE original ficam: a licença exige.
"""
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rebrand import PROGRAMAS, REPO_SUITE, GITHUB, nome_completo  # noqa: E402

PACOTE = {"illustre": "vectorcraft", "fotografe": "photocraft", "pdf": "pdfcraft", "cena": "filmcraft",
          "lightbridge": "lightcraft"}
EXE = {"illustre": "illustre", "fotografe": "fotografe", "pdf": "pdf-angero", "cena": "cena", "lightbridge": "lightbridge"}
PASTA_DADOS = {"illustre": "Illustre-Angero", "fotografe": "Fotografe-Angero", "pdf": "PDF-Angero",
               "cena": "Cena-Angero", "lightbridge": "LightBridge-Angero"}
DESCRICAO = {
    "illustre": "Desenho vetorial: fichas técnicas, estampas e artes — com menus, ferramentas e atalhos no estilo do Illustrator.",
    "fotografe": "Edição de imagens com camadas, máscaras e estilos; abre e salva PSD.",
    "pdf": "Leitura, organização, junção, assinatura e proteção de PDFs.",
    "cena": "Edição de vídeo com linha do tempo, cortes, legendas, efeitos e mixagem de áudio.",
    "lightbridge": "Catálogo de fotos: organizar, etiquetar, revelar e exportar em lote.",
}
APAGAR = ["AGENTS.md", "CLAUDE.md", "ROADMAP.md", "ASSETS.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md",
          "SECURITY.md", "CHANGELOG.md", "contributors", ".github", ".claude", ".config"]
PODAR = ["docs", "packaging", "examples"]  # apaga tudo, menos o que o código embute


def _ler(p):
    return p.read_text(encoding="utf-8")


def _gravar(p, s):
    p.write_text(s, encoding="utf-8", newline="\n")


def arquivos_rs(raiz):
    return [p for p in raiz.rglob("*.rs") if "target" not in p.parts and "vendor" not in p.parts]


def incluidos(raiz):
    """Arquivos fora do src que o código embute (include_bytes!/include_str!) — não podem sumir."""
    usados = set()
    for p in arquivos_rs(raiz):
        for m in re.finditer(r'include_(?:bytes|str)!\(\s*"([^"]+)"\s*\)', _ler(p)):
            alvo = (p.parent / m.group(1)).resolve()
            if alvo.exists():
                usados.add(alvo)
    return usados


def renomear_exes(raiz, pid):
    pac, exe = PACOTE[pid], EXE[pid]
    for app, novo in ((pac, exe), (f"{pac}-cli", f"{exe}-cli")):
        toml = raiz / "apps" / app / "Cargo.toml"
        s = _ler(toml)
        if f'name = "{app}"\npath = "src/main.rs"' in s:  # o -cli já declara [[bin]]
            s = s.replace(f'[[bin]]\nname = "{app}"', f'[[bin]]\nname = "{novo}"')
        elif "[[bin]]" not in s:
            s = s.rstrip("\n") + f'\n\n[[bin]]\nname = "{novo}"\npath = "src/main.rs"\n'
        s = s.replace(f'default-run = "{app}"', f'default-run = "{novo}"')
        _gravar(toml, s)
        build = raiz / "apps" / app / "build.rs"
        if build.exists():
            b = _ler(build)
            b = b.replace(f'"{app}.exe"', f'"{novo}.exe"').replace(f'"InternalName", "{app}"', f'"InternalName", "{novo}"')
            _gravar(build, b)
    # textos de ajuda da linha de comando
    for p in (raiz / "apps" / f"{pac}-cli").rglob("*.rs"):
        s = _ler(p)
        novo = re.sub(rf'(?<![\w_]){pac}-cli(?![\w-])', f"{exe}-cli", s)
        if novo != s:
            _gravar(p, novo)


def renomear_pastas_dados(raiz, pid):
    """Pastas de configuração (%APPDATA%/%LOCALAPPDATA%) com o nome novo, sem acento."""
    orig = PROGRAMAS[pid]["orig"]
    for p in arquivos_rs(raiz / "apps") + arquivos_rs(raiz / "crates"):
        if "tests" in p.parts or p.name.startswith("tests"):
            continue
        s = _ler(p)
        novo = s.replace(f'"{orig}"', f'"{PASTA_DADOS[pid]}"')
        if novo != s:
            _gravar(p, novo)


def mover_logos(raiz):
    """docs/brand/artcraft-* usados pelo código -> assets/marca/angero-*; caminhos no código atualizados."""
    marca = raiz / "assets" / "marca"
    for alvo in sorted(incluidos(raiz)):
        if "docs" not in alvo.parts or "brand" not in alvo.parts:
            continue
        marca.mkdir(parents=True, exist_ok=True)
        novo = marca / alvo.name.replace("artcraft", "angero")
        shutil.copy2(alvo, novo)
        for p in arquivos_rs(raiz):
            s = _ler(p)
            if alvo.name not in s:
                continue
            rel_antigo = re.compile(r'include_(bytes|str)!\(\s*"([^"]*' + re.escape(alvo.name) + r')"\s*\)')

            def troca(m):
                caminho = (p.parent / m.group(2)).resolve()
                if caminho != alvo:
                    return m.group(0)
                rel = Path(*[".."] * (len(p.parent.relative_to(raiz).parts))) / "assets" / "marca" / novo.name
                return f'include_{m.group(1)}!("{rel.as_posix()}")'

            _gravar(p, rel_antigo.sub(troca, s))
            _gravar(p, _ler(p).replace(f'"bytes://{alvo.name}"', f'"bytes://{novo.name}"'))


def apagar_antigos(raiz):
    protegidos = incluidos(raiz)
    for nome in APAGAR:
        alvo = raiz / nome
        if not alvo.exists():
            continue
        if any(alvo == p or alvo in p.parents for p in protegidos):
            print("  mantido (o código usa):", nome)
            continue
        shutil.rmtree(alvo) if alvo.is_dir() else alvo.unlink()
    protegidos = incluidos(raiz)
    for nome in PODAR:
        docs = raiz / nome
        if not docs.exists():
            continue
        for p in sorted(docs.rglob("*"), reverse=True):
            if p.is_file() and p.resolve() not in protegidos:
                p.unlink()
            elif p.is_dir() and not any(p.iterdir()):
                p.rmdir()
        if docs.exists() and not any(docs.iterdir()):
            docs.rmdir()


def readme(raiz, pid):
    cfg = PROGRAMAS[pid]
    nome, exe = nome_completo(cfg), EXE[pid]
    _gravar(raiz / "README.md", f"""# {nome}

Programa da **Suíte Angerô**, o pacote de criação do **Grupo Angerô**.

{DESCRICAO[pid]}

- Ajuda: {REPO_SUITE}/blob/main/docs/ajuda/{pid}.md
- Suíte Angerô (iniciador, assistente de IA, instaladores): {REPO_SUITE}
- Versões compiladas: aba **Releases** deste repositório (a Suíte Angerô se atualiza sozinha a partir delas).

## Compilar

Windows, com Rust (MSVC) e Visual Studio Build Tools (C++):

```
cargo build --release --locked -p {PACOTE[pid]} -p {PACOTE[pid]}-cli
```

Gera `target/release/{exe}.exe` e `target/release/{exe}-cli.exe`.
A cada push no ramo `angero`, o GitHub Actions compila e publica uma versão nova em Releases.

## Código-base e licença

Desenvolvido por Weslei Domingues (TI) para o Grupo Angerô, a partir do código aberto do
**{cfg['orig']}** (projeto ArtCraft, https://github.com/storytold/{PACOTE[pid]}), usado como base.
Licença: MIT OU Apache-2.0, à escolha — veja `LICENSE-MIT`, `LICENSE-APACHE` e `NOTICE`.
""")
    notice = raiz / "NOTICE"
    original = _ler(notice) if notice.exists() else ""
    if "Grupo Angerô" not in original:
        _gravar(notice, f"""{nome} — Grupo Angerô
Modificado por Weslei Domingues (TI) para o Grupo Angerô, {2026}: identidade visual, nomes,
textos, links de ajuda e empacotamento. Arquivos alterados: veja o histórico do git (ramo `angero`).

---- Aviso original ----
{original}""")


def ajustes_especificos(raiz, pid):
    if pid == "lightbridge":  # acha o Fotografe para "editar em outro programa"
        p = raiz / "apps" / "lightcraft" / "src" / "editors.rs"
        s = _ler(p).replace('"photocraft.exe"', '"fotografe.exe"').replace('join("PhotoCraft")', 'join("Fotografe - Angerô")')
        _gravar(p, s)


def main():
    raiz, pid = Path(sys.argv[1]).resolve(), sys.argv[2]
    renomear_exes(raiz, pid)
    renomear_pastas_dados(raiz, pid)
    ajustes_especificos(raiz, pid)
    mover_logos(raiz)
    apagar_antigos(raiz)
    readme(raiz, pid)
    print("ok", pid)


if __name__ == "__main__":
    main()
