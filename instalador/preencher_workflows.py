"""Grava .github/workflows/angero.yml em cada fork, a partir de workflow-programa.yml.

Uso: python preencher_workflows.py [pasta dos forks]   (padrão: %LOCALAPPDATA%\\SuiteAngero\\src)
"""
import os
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(os.environ["LOCALAPPDATA"]) / "SuiteAngero" / "src"

PROGRAMAS = [
    # id, pacote cargo, exe, nome, ícone, argumentos do atalho (porta de comando da IA)
    ("illustre", "vectorcraft", "illustre", "Illustre - Angerô", "vetor", "--control 7979"),
    ("fotografe", "photocraft", "fotografe", "Fotografe - Angerô", "foto",
     r"--control 7981 --control-token-file {localappdata}\SuiteAngero\fotografe.token"),
    ("pdf", "pdfcraft", "pdf-angero", "PDF - Angerô", "pdf", ""),
    ("cena", "filmcraft", "cena", "Cena - Angerô", "video", "--control 7982"),
    ("lightbridge", "lightcraft", "lightbridge", "LightBridge - Angerô", "galeria", "--control 7980"),
]


def main():
    modelo = (AQUI / "workflow-programa.yml").read_text(encoding="utf-8")
    for pid, pacote, exe, nome, icone, args in PROGRAMAS:
        texto = (modelo.replace("@PACOTE@", pacote).replace("@EXE@", exe).replace("@ID@", pid)
                 .replace("@NOME@", nome).replace("@ICONE@", icone).replace("@ARGS@", args))
        destino = SRC / f"{pid}-angero" / ".github" / "workflows" / "angero.yml"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(texto, encoding="utf-8")
        print("ok", destino)


if __name__ == "__main__":
    main()
