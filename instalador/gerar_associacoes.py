"""Gera as associações de arquivo da Suíte Angerô.

- instalador/assoc/<id>.iss  — registros incluídos pelos instaladores (programa.iss e suite.iss)
- docs/ti/AssociacoesPadrao.xml — para a GPO "Definir um arquivo de configuração de associações padrão"

"padrao": o programa vira o padrão da extensão (opção "Usar como programa padrão" do instalador);
"abrir_com": só aparece em "Abrir com" (fotos e vídeos continuam no visualizador/player do Windows).
Uso: python gerar_associacoes.py
"""
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
BARRA = "\\"

PROGRAMAS = {
    "illustre": {"nome": "Illustre - Angerô", "exe": "illustre.exe", "args": "--control 7979",
                 "padrao": {".ai": "Arte do Illustrator", ".ait": "Modelo do Illustrator", ".eps": "Arte EPS",
                            ".svg": "Desenho SVG", ".svgz": "Desenho SVG compactado", ".vectorcraft": "Documento do Illustre"},
                 "abrir_com": [".pdf", ".dxf", ".emf", ".wmf"]},
    "fotografe": {"nome": "Fotografe - Angerô", "exe": "fotografe.exe",
                  "args": "--control 7981 --control-token-file {localappdata}" + BARRA + "SuiteAngero" + BARRA + "fotografe.token",
                  "padrao": {".psd": "Imagem do Photoshop", ".psb": "Imagem grande do Photoshop", ".pcraft": "Documento do Fotografe"},
                  "abrir_com": [".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".bmp", ".gif", ".tga"]},
    "pdf": {"nome": "PDF - Angerô", "exe": "pdf-angero.exe", "args": "",
            "padrao": {".pdf": "Documento PDF"}, "abrir_com": []},
    "cena": {"nome": "Cena - Angerô", "exe": "cena.exe", "args": "--control 7982",
             "padrao": {".fcproj": "Projeto do Cena"},
             "abrir_com": [".mp4", ".mov", ".mkv", ".avi", ".wav", ".mp3", ".flac", ".aiff", ".ogg"]},
    "lightbridge": {"nome": "LightBridge - Angerô", "exe": "lightbridge.exe", "args": "--control 7980",
                    "padrao": {e: "Foto RAW" for e in (".cr2", ".cr3", ".nef", ".arw", ".dng", ".raf", ".orf", ".rw2")},
                    "abrir_com": [".jpg", ".jpeg", ".png", ".tif", ".tiff"]},
}


def progid(pid, ext):
    return f"SuiteAngero.{pid}{ext}"


def chave(*partes):
    return BARRA.join(("Software", "Classes") + partes)


def iss(pid, p):
    """Registros do Inno Setup. {#AppPasta_<id>} = pasta do programa (definida por quem inclui o arquivo).
    Se o instalador definir Cmd_<id> antes, ele substitui o comando de abertura (ex.: Illustre pela Suíte)."""
    pasta = "{#AppPasta_" + pid + "}"
    # o arquivo vem antes das opções: os programas só abrem o arquivo quando ele é o primeiro argumento
    resto = BARRA + p["exe"] + '"" ""%1""' + ((" " + p["args"]) if p["args"] else "")
    linhas = [f"; gerado por gerar_associacoes.py: {p['nome']}",
              f"#ifndef Cmd_{pid}", f"  #define Cmd_{pid} '\"\"' + AppPasta_{pid} + '{resto}'", "#endif"]
    for ext in list(p["padrao"]) + p["abrir_com"]:
        pg = progid(pid, ext)
        desc = p["padrao"].get(ext, f"Arquivo {ext[1:].upper()}")
        linhas += [
            f'Root: HKCU; Subkey: "{chave(pg)}"; ValueType: string; ValueName: ""; ValueData: "{desc}"; Flags: uninsdeletekey',
            f'Root: HKCU; Subkey: "{chave(pg, "DefaultIcon")}"; ValueType: string; ValueName: ""; ValueData: "{pasta}{BARRA}icone.ico"',
            f'Root: HKCU; Subkey: "{chave(pg, "shell", "open", "command")}"; ValueType: string; ValueName: ""; ValueData: "{{#Cmd_{pid}}}"',
            f'Root: HKCU; Subkey: "{chave(ext, "OpenWithProgids")}"; ValueType: string; ValueName: "{pg}"; ValueData: ""; Flags: uninsdeletevalue',
        ]
        if ext in p["padrao"]:
            linhas.append(f'Root: HKCU; Subkey: "{chave(ext)}"; ValueType: string; ValueName: ""; '
                          f'ValueData: "{pg}"; Flags: uninsdeletevalue; Tasks: associar')
    return "\n".join(linhas) + "\n"


def xml_gpo():
    linhas = ['<?xml version="1.0" encoding="UTF-8"?>',
              "<!-- Suíte Angerô: associações padrão para a GPO (Configuração do Computador > Modelos Administrativos >",
              "     Componentes do Windows > Explorador de Arquivos > Definir um arquivo de configuração de associações padrão).",
              "     Os ProgIds são registrados pelos instaladores da Suíte. Gerado por instalador/gerar_associacoes.py. -->",
              "<DefaultAssociations>"]
    for pid, p in PROGRAMAS.items():
        for ext in p["padrao"]:
            linhas.append(f'  <Association Identifier="{ext}" ProgId="{progid(pid, ext)}" ApplicationName="{p["nome"]}" />')
    linhas.append("</DefaultAssociations>")
    return "\n".join(linhas) + "\n"


def main():
    pasta = AQUI / "assoc"
    pasta.mkdir(exist_ok=True)
    for pid, p in PROGRAMAS.items():
        (pasta / f"{pid}.iss").write_text(iss(pid, p), encoding="utf-8-sig", newline="\r\n")
    ti = RAIZ / "docs" / "ti"
    ti.mkdir(parents=True, exist_ok=True)
    (ti / "AssociacoesPadrao.xml").write_text(xml_gpo(), encoding="utf-8", newline="\r\n")
    print("ok:", ", ".join(PROGRAMAS))


if __name__ == "__main__":
    main()
