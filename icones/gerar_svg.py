"""Gera os ícones da Suíte Angerô em SVG, na identidade "Lua Nova" com as cores da Angerô.

Programas: fundo bege com manchas nebulosas (pêssego, verde-claro, azul, lilás), o desenho em
traço fino anil e, por baixo dele, uma mancha de cor pastel levemente deslocada (como as
ilustrações do modelo). Suíte: a folha da Angerô no fundo branco (o ícone de antes).
Sem filtros, que nem todo leitor de SVG desenha.

Saída: icones/svg/<nome>.svg  — depois `gerar_ico.py` converte para PNG/ICO.
"""
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SAIDA = AQUI / "svg"

# Angerô (folha do logo) + paleta "Lua Nova"
ANIL = "#2b3a8f"
BEGE = "#eeecde"
PESSEGO = "#ffd3c2"
LILAS = "#f0cdff"
AZUL = "#b2dcfa"
VERDE = "#e0fe9c"

# Cor da mancha de cada programa
COR = {
    "vetor": "#ffb79c",      # Illustre: pêssego forte
    "foto": "#9fd2fa",       # Fotografe: azul
    "pdf": "#f7a8c9",        # PDF: rosa
    "video": "#dcb3f5",      # Cena: lilás
    "galeria": "#c9ec6e",    # LightBridge: verde-limão
    "fluxogama": "#a9c6e0",  # Fluxogama: azul-acinzentado
    "assistente": "#ffd27a", # Assistente IA: amarelo
    "editor": "#f5b3e0",     # Editor Visual: rosa-lilás
}

DEFS = f"""
<defs>
  <radialGradient id="m1" cx=".15" cy=".85" r=".7"><stop offset="0" stop-color="{PESSEGO}"/><stop offset="1" stop-color="{PESSEGO}" stop-opacity="0"/></radialGradient>
  <radialGradient id="m2" cx=".55" cy=".05" r=".55"><stop offset="0" stop-color="{VERDE}" stop-opacity=".75"/><stop offset="1" stop-color="{VERDE}" stop-opacity="0"/></radialGradient>
  <radialGradient id="m3" cx=".95" cy=".45" r=".6"><stop offset="0" stop-color="{AZUL}"/><stop offset="1" stop-color="{AZUL}" stop-opacity="0"/></radialGradient>
  <radialGradient id="m4" cx=".85" cy=".95" r=".5"><stop offset="0" stop-color="{LILAS}"/><stop offset="1" stop-color="{LILAS}" stop-opacity="0"/></radialGradient>
</defs>"""

FUNDO = f"""
<rect x="8" y="8" width="240" height="240" rx="58" fill="{BEGE}"/>
<rect x="8" y="8" width="240" height="240" rx="58" fill="url(#m1)"/>
<rect x="8" y="8" width="240" height="240" rx="58" fill="url(#m2)"/>
<rect x="8" y="8" width="240" height="240" rx="58" fill="url(#m3)"/>
<rect x="8" y="8" width="240" height="240" rx="58" fill="url(#m4)"/>
<rect x="9" y="9" width="238" height="238" rx="57" fill="none" stroke="{ANIL}" stroke-opacity=".14" stroke-width="2"/>
"""

L = f'fill="none" stroke="{ANIL}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"'


def mancha(nome: str, forma: str) -> str:
    """A mancha pastel, deslocada do traço."""
    return f'<g transform="translate(9 8)" fill="{COR[nome]}">{forma}</g>'


GLIFOS = {
    # Pena vetorial com curva e alças
    "vetor": lambda n: mancha(n, '<path d="M128 64 L166 120 L146 166 L110 166 L90 120 Z"/>') + f"""
<path d="M128 64 L166 120 L146 166 L110 166 L90 120 Z" {L}/>
<path d="M128 90 V126" {L}/><circle cx="128" cy="134" r="8" {L}/>
<path d="M108 184 H148" {L}/>
<path d="M52 112 H86 M170 112 H204" {L}/>
<rect x="40" y="102" width="20" height="20" rx="5" {L}/><rect x="196" y="102" width="20" height="20" rx="5" {L}/>
""",
    # Câmera com lente
    "foto": lambda n: mancha(n, '<rect x="58" y="88" width="140" height="100" rx="20"/>') + f"""
<rect x="58" y="88" width="140" height="100" rx="20" {L}/>
<path d="M98 88 L108 70 H148 L158 88" {L}/>
<circle cx="128" cy="138" r="30" {L}/><circle cx="128" cy="138" r="13" {L}/>
<circle cx="176" cy="108" r="5" fill="{ANIL}"/>
""",
    # Documento com dobra e selo PDF
    "pdf": lambda n: mancha(n, '<path d="M84 56 H146 L176 86 V196 H84 Z"/>') + f"""
<path d="M92 56 H146 L176 86 V188 C176 193 172 197 167 197 H92 C87 197 83 193 83 188 V65 C83 60 87 56 92 56 Z" {L}/>
<path d="M144 56 V88 H176" {L}/>
<path d="M102 116 H156 M102 136 H156" {L}/>
<rect x="98" y="152" width="62" height="30" rx="8" fill="{ANIL}"/>
<text x="129" y="174" text-anchor="middle" font-family="Montserrat, Arial, Helvetica, sans-serif" font-weight="800" font-size="20" fill="#ffffff">PDF</text>
""",
    # Claquete com play
    "video": lambda n: mancha(n, '<rect x="58" y="100" width="140" height="92" rx="14"/>') + f"""
<rect x="58" y="100" width="140" height="92" rx="14" {L}/>
<path d="M58 100 L52 76 L190 50 L196 74" {L}/>
<path d="M86 70 L100 94 M126 62 L140 88 M164 56 L178 81" {L}/>
<path d="M116 126 L148 146 L116 166 Z" {L}/>
""",
    # Grade de fotos, uma com montanha e sol
    "galeria": lambda n: mancha(n, '<rect x="58" y="58" width="62" height="62" rx="14"/><rect x="136" y="136" width="62" height="62" rx="14"/>') + f"""
<rect x="58" y="58" width="62" height="62" rx="14" {L}/><rect x="136" y="58" width="62" height="62" rx="14" {L}/>
<rect x="58" y="136" width="62" height="62" rx="14" {L}/><rect x="136" y="136" width="62" height="62" rx="14" {L}/>
<path d="M66 110 L82 92 L94 104 L102 96 L112 110" {L}/><circle cx="102" cy="76" r="6" {L}/>
""",
    # Nuvem com seta
    "fluxogama": lambda n: mancha(n, '<path d="M84 172 C60 172 50 154 56 138 C62 122 78 116 92 120 C96 96 116 82 138 85 C162 88 176 108 176 126 C192 127 202 142 198 157 C195 166 186 172 174 172 Z"/>') + f"""
<path d="M84 172 C60 172 50 154 56 138 C62 122 78 116 92 120 C96 96 116 82 138 85 C162 88 176 108 176 126 C192 127 202 142 198 157 C195 166 186 172 174 172" {L}/>
<path d="M128 196 V134 M106 156 L128 134 L150 156" {L}/>
""",
    # Paleta de pintor (Editor Visual: cores dos programas)
    "editor": lambda n: mancha(n, '<path d="M128 60 C170 60 200 88 200 122 C200 146 182 150 168 146 C152 142 142 152 148 168 C154 186 140 196 124 196 C86 196 56 166 56 128 C56 90 88 60 128 60 Z"/>') + f"""
<path d="M128 60 C170 60 200 88 200 122 C200 146 182 150 168 146 C152 142 142 152 148 168 C154 186 140 196 124 196 C86 196 56 166 56 128 C56 90 88 60 128 60 Z" {L}/>
<circle cx="98" cy="104" r="11" fill="#ff8a5c" stroke="{ANIL}" stroke-width="6"/>
<circle cx="134" cy="90" r="11" fill="#38b6f0" stroke="{ANIL}" stroke-width="6"/>
<circle cx="168" cy="110" r="11" fill="#3fbf8a" stroke="{ANIL}" stroke-width="6"/>
<circle cx="92" cy="146" r="11" fill="#9b6cf0" stroke="{ANIL}" stroke-width="6"/>
""",
    # Brilhos de IA
    "assistente": lambda n: mancha(n, '<path d="M118 62 C123 102 134 113 174 118 C134 123 123 134 118 174 C113 134 102 123 62 118 C102 113 113 102 118 62 Z"/>') + f"""
<path d="M118 62 C123 102 134 113 174 118 C134 123 123 134 118 174 C113 134 102 123 62 118 C102 113 113 102 118 62 Z" {L}/>
<path d="M174 148 C176 162 180 166 194 168 C180 170 176 174 174 188 C172 174 168 170 154 168 C168 166 172 162 174 148 Z" {L}/>
<circle cx="178" cy="78" r="7" fill="{ANIL}"/>
""",
}

# Suíte: a folha do logo da Angerô no fundo branco (o ícone de antes)
SUITE = """
<rect x="8" y="8" width="240" height="240" rx="56" fill="#ffffff" stroke="#e3e7f3" stroke-width="4"/>
<linearGradient id="gf" gradientUnits="userSpaceOnUse" x1="40" y1="230" x2="585" y2="110">
  <stop offset="0" stop-color="#34479f"/><stop offset=".5" stop-color="#5f82cc"/><stop offset="1" stop-color="#90d9f5"/>
</linearGradient>
<g transform="translate(14 68) scale(0.38)">
  <path d="M100 82 C160 40, 240 22, 300 30 C360 38, 400 45, 430 40 C500 45, 560 90, 585 140
           C590 160, 570 170, 540 185 C500 205, 450 215, 410 210 C350 200, 300 150, 250 115
           C200 85, 150 78, 100 82 Z" fill="url(#gf)"/>
  <path d="M40 165 C70 120, 140 100, 190 108 C240 115, 280 160, 330 200 C380 238, 450 248, 505 243
           C460 265, 400 290, 330 292 C250 295, 160 290, 120 255 C90 235, 60 200, 40 165 Z" fill="url(#gf)"/>
  <g fill="none" stroke="#ffffff" stroke-width="11" stroke-linecap="round">
    <path d="M300 30 C330 50, 355 75, 368 100"/>
    <path d="M420 40 C435 60, 442 80, 445 95"/>
    <path d="M178 298 C176 272, 180 252, 186 234"/>
    <path d="M305 295 C284 272, 264 248, 252 228"/>
  </g>
</g>
"""


def svg(cabeca: str, conteudo: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">'
        f"{cabeca}{conteudo}</svg>\n"
    )


def main():
    SAIDA.mkdir(exist_ok=True)
    for nome, glifo in GLIFOS.items():
        (SAIDA / f"{nome}.svg").write_text(svg(DEFS, FUNDO + glifo(nome)), encoding="utf-8")
    (SAIDA / "suite.svg").write_text(svg("", SUITE), encoding="utf-8")
    print("SVGs em", SAIDA)


if __name__ == "__main__":
    main()
