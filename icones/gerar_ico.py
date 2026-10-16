"""Converte icones/svg/*.svg em PNG (vários tamanhos) e .ico, usando o illustre-cli (do Illustre - Angerô).

Também gera icones/previa.png com todos lado a lado, para conferir o visual.
Uso: python gerar_ico.py
"""
import os
import re
import struct
import subprocess
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SVG = AQUI / "svg"
PNG = AQUI / "png"
ICO = AQUI / "ico"
TAMANHOS = [256, 128, 64, 48, 32, 24, 16]

def _cli_illustre():
    """illustre-cli.exe: o instalado, senão o compilado em src/illustre-angero."""
    import os
    local = Path(os.environ["LOCALAPPDATA"])
    for c in (local / "Programs" / "Suite Angero" / "Illustre - Angerô" / "illustre-cli.exe",
              local / "SuiteAngero" / "src" / "illustre-angero" / "target" / "release" / "illustre-cli.exe"):
        if c.is_file():
            return c
    raise SystemExit("illustre-cli.exe não encontrado (instale o Illustre - Angerô ou compile-o)")


CLI = _cli_illustre()


def renderizar(svg: Path, png: Path, tamanho: int):
    r = subprocess.run(
        [str(CLI), "convert", str(svg), str(png), "--scale", str(tamanho / 256)],
        capture_output=True, text=True,
    )
    if r.returncode != 0 or not png.exists():
        raise SystemExit(f"falhou {svg.name} {tamanho}: {r.stdout}{r.stderr}")


def montar_ico(pngs: list[tuple[int, bytes]], destino: Path):
    """ICO com PNGs embutidos (aceito pelo Windows Vista+)."""
    cab = struct.pack("<HHH", 0, 1, len(pngs))
    entradas, dados = b"", b""
    deslocamento = 6 + 16 * len(pngs)
    for tam, conteudo in pngs:
        lado = 0 if tam >= 256 else tam
        entradas += struct.pack("<BBBBHHII", lado, lado, 0, 0, 1, 32, len(conteudo), deslocamento + len(dados))
        dados += conteudo
    destino.write_bytes(cab + entradas + dados)


def previa(nomes: list[str]):
    """Junta todos os SVGs numa faixa só e renderiza."""
    partes = []
    for i, nome in enumerate(nomes):
        corpo = (SVG / f"{nome}.svg").read_text(encoding="utf-8")
        # ids de gradiente únicos por ícone, senão um ícone usa o degradê do outro
        corpo = re.sub(r'id="(\w+)"', rf'id="\1_{i}"', corpo)
        corpo = re.sub(r"url\(#(\w+)\)", rf"url(#\1_{i})", corpo)
        corpo = corpo.replace('<svg ', f'<svg x="{20 + i * 276}" y="20" ', 1)
        partes.append(corpo)
    largura = 20 + len(nomes) * 276
    folha = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="296" viewBox="0 0 {largura} 296">'
             f'<rect width="{largura}" height="296" fill="#f4f5f8"/>{"".join(partes)}</svg>')
    tmp = AQUI / "previa.svg"
    tmp.write_text(folha, encoding="utf-8")
    r = subprocess.run([str(CLI), "convert", str(tmp), str(AQUI / "previa.png")], capture_output=True, text=True)
    tmp.unlink()
    if r.returncode != 0:
        raise SystemExit(f"prévia falhou: {r.stdout}{r.stderr}")


def main():
    PNG.mkdir(exist_ok=True)
    ICO.mkdir(exist_ok=True)
    nomes = []
    for svg in sorted(SVG.glob("*.svg")):
        nome = svg.stem
        nomes.append(nome)
        pngs = []
        for t in TAMANHOS:
            destino = PNG / f"{nome}-{t}.png"
            renderizar(svg, destino, t)
            pngs.append((t, destino.read_bytes()))
        montar_ico(pngs, ICO / f"{nome}.ico")
        print("ok", nome)
    previa(nomes)
    print("prévia:", AQUI / "previa.png")


if __name__ == "__main__":
    main()
