"""Extensões do Illustre - Angerô (como Janela > Extensões do Illustrator).

- listar(): extensões instaladas em plugins/<pasta>/CSXS/manifest.xml (formato CEP da Adobe, host ILST).
- "extensoes.py --listar": a lista em JSON, lida pelo botão "Extensões" da barra de cima do Illustre.
"""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# o Python portátil do instalador não põe a pasta do script no caminho de importação
sys.path.insert(0, str(Path(__file__).resolve().parent))

AQUI = Path(__file__).resolve().parent
PLUGINS = AQUI.parent / "plugins"

# extensões que a Suíte já sabe executar (as funções do Illustrator que elas usam foram adaptadas)
SUPORTADAS = {"br.com.fluxogama": {"nome": "Fluxogama - Angerô", "url": "http://127.0.0.1:8792/"}}


def listar() -> list[dict]:
    saida = []
    for manifesto in sorted(PLUGINS.glob("*/CSXS/manifest.xml")):
        try:
            raiz = ET.parse(manifesto).getroot()
        except ET.ParseError:
            continue
        hosts = [h.get("Name") for h in raiz.iter("Host")]
        if "ILST" not in hosts:
            continue
        bundle = raiz.get("ExtensionBundleId", manifesto.parent.parent.name)
        menu = next((m.text for m in raiz.iter("Menu") if m.text), raiz.get("ExtensionBundleName") or bundle)
        sup = SUPORTADAS.get(bundle)
        saida.append({"id": bundle, "pasta": manifesto.parent.parent.name,
                      "nome": sup["nome"] if sup else menu, "suportada": bool(sup),
                      "url": sup["url"] if sup else None})
    return saida


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(listar(), ensure_ascii=False, indent=2))
