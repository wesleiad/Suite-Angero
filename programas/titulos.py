"""Troca os nomes antigos que aparecem na tela sem passar pela tradução (títulos de janela com arquivo
aberto, nomes padrão de biblioteca/conjuntos, textos fixos). Complementa rebrand.py e limpar_fork.py.

Uso: python titulos.py [pasta dos forks]
"""
import os
import sys
from pathlib import Path

SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(os.environ["LOCALAPPDATA"]) / "SuiteAngero" / "src"
TRAVESSAO = "\\u{2014}"

TROCAS = {
    "illustre-angero": {
        "crates/ui-egui/src/chrome.rs": [
            (f' {TRAVESSAO} VectorCraft"', f' {TRAVESSAO} Illustre - Angerô"'),
        ],
    },
    "fotografe-angero": {
        "crates/ui-egui/src/panels.rs": [
            (f'{TRAVESSAO} PhotoCraft"', f'{TRAVESSAO} Fotografe - Angerô"'),
        ],
        "crates/ui-egui/src/gpu_status.rs": [
            ('format!("PhotoCraft {}"', 'format!("Fotografe - Angerô {}"'),
        ],
        "crates/engine/src/atn_cmds.rs": [
            ('pub const DEFAULT_SET: &str = "PhotoCraft Actions";', 'pub const DEFAULT_SET: &str = "Ações do Fotografe";'),
        ],
    },
    "pdf-angero": {
        "crates/ui-egui/src/lib.rs": [
            ('format!("{name} — PdfCraft")', 'format!("{name} — PDF - Angerô")'),
        ],
        "crates/ui-egui/src/web_print.rs": [
            ("<title>PdfCraft</title>", "<title>PDF - Angerô</title>"),
        ],
    },
    "cena-angero": {
        "crates/ui-egui/src/panels/sequence_settings.rs": [
            ('"Not supported in FilmCraft yet"', '"Ainda não disponível no Cena"'),
            ('"FilmCraft always composites in linear light"', '"O Cena sempre compõe em luz linear"'),
        ],
        # Nome do projeto de exemplo que abre ao iniciar (aparece no título da janela)
        "crates/engine/src/demo.rs": [
            ('Project::new("FilmCraft Demo")', 'Project::new("Projeto de exemplo")'),
            ('p.new_sequence("Main Edit",', 'p.new_sequence("Edição principal",'),
        ],
        "crates/engine/src/project_tools_tests.rs": [
            ('i.name == "Main Edit"', 'i.name == "Edição principal"'),
        ],
        "crates/ui-egui/tests/sequence_ui.rs": [
            ('("sequenceSettings.name", "Main Edit")', '("sequenceSettings.name", "Edição principal")'),
        ],
        "crates/engine/src/commands.rs": [
            ('unwrap_or("Untitled").to_string()', 'unwrap_or("Sem título").to_string()'),
        ],
        "crates/engine/src/clip_ops.rs": [
            ('Project::new("Untitled")', 'Project::new("Sem título")'),
        ],
    },
    "lightbridge-angero": {
        "crates/ui-egui/src/lib.rs": [
            ('format!("LightCraft — {name}")', 'format!("LightBridge - Angerô — {name}")'),
            ('/// "LightCraft — <library name>"', '/// "LightBridge - Angerô — <nome da biblioteca>"'),
        ],
        "crates/ui-egui/src/panels/second.rs": [
            ('"LightCraft — Second Window"', '"LightBridge - Angerô — Segunda janela"'),
        ],
        "crates/engine/src/library.rs": [
            ('pub const DEFAULT_NAME: &str = "LightCraft Library";', 'pub const DEFAULT_NAME: &str = "Biblioteca LightBridge";'),
        ],
        "crates/ui-egui/src/control.rs": [
            ('join("LightCraft Exports")', 'join("LightBridge Exportações")'),
        ],
        "crates/ui-egui/src/menus.rs": [
            ('unwrap_or("LightCraft Presets")', 'unwrap_or("Predefinições LightBridge")'),
        ],
        "crates/ui-egui/src/panels/faces.rs": [
            ('"LightCraft does not know this model, so it assumed:"', '"O LightBridge não conhece este modelo; por isso considerou:"'),
        ],
        "apps/lightcraft/src/main.rs": [
            ("~/Pictures/LightCraft Library", "~/Pictures/Biblioteca LightBridge"),
        ],
    },
}


def main():
    for fork, arquivos in TROCAS.items():
        for rel, trocas in arquivos.items():
            p = SRC / fork / rel
            texto = p.read_bytes().decode("utf-8")
            for antes, depois in trocas:
                if antes in texto:
                    texto = texto.replace(antes, depois)
                    print(f"ok  {fork}/{rel}: {antes[:50]}")
                elif depois not in texto:
                    print(f"!!  {fork}/{rel}: não achei {antes[:50]}")
            p.write_bytes(texto.encode("utf-8"))


if __name__ == "__main__":
    main()
