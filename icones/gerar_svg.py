"""Gera os ícones da Suíte Angerô em SVG (paleta e estilo da folha do logo).

Saída: icones/svg/<nome>.svg  — depois `gerar_ico.py` converte para PNG/ICO.
"""
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SAIDA = AQUI / "svg"

# Cores tiradas da folha do logo Grupo Angerô (anil -> azul-céu)
ANIL = "#2b3a8f"
ANIL_MEIO = "#4a64c0"
CEU = "#86d4f5"

DEFS = f"""
<defs>
  <linearGradient id="g" x1="0" y1="1" x2="1" y2="0">
    <stop offset="0" stop-color="{ANIL}"/>
    <stop offset=".55" stop-color="{ANIL_MEIO}"/>
    <stop offset="1" stop-color="{CEU}"/>
  </linearGradient>
</defs>"""

# Fundo: quadrado arredondado em degradê + onda branca suave (eco da onda da folha)
FUNDO = """
<rect x="8" y="8" width="240" height="240" rx="56" fill="url(#g)"/>
<path d="M8 196 C 70 150, 130 222, 248 150 L 248 192 C 248 223, 223 248, 192 248 L 64 248 C 33 248, 8 223, 8 192 Z"
      fill="#ffffff" fill-opacity=".13"/>
"""

def B(w=13):
    return f'fill="none" stroke="#ffffff" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"'

GLIFOS = {
    # Pena de desenho vetorial (Illustrator)
    "vetor": f"""
<path d="M128 44 L176 118 L140 186 L116 186 L80 118 Z" fill="#ffffff"/>
<path d="M128 68 L128 124" stroke="{ANIL_MEIO}" stroke-width="9" stroke-linecap="round"/>
<circle cx="128" cy="132" r="11" fill="{ANIL_MEIO}"/>
<rect x="108" y="194" width="40" height="18" rx="6" fill="#ffffff"/>
""",
    # Moldura com montanha e sol (Photoshop)
    "foto": f"""
<rect x="52" y="62" width="152" height="132" rx="22" {B()}/>
<path d="M66 182 L112 128 L140 160 L160 140 L192 182 Z" fill="#ffffff"/>
<circle cx="160" cy="100" r="15" fill="#ffffff"/>
""",
    # Documento com dobra (leitor/editor de PDF)
    "pdf": f"""
<path d="M76 48 H146 L184 86 V196 C184 204 178 210 170 210 H76 C68 210 62 204 62 196 V62 C62 54 68 48 76 48 Z" {B()}/>
<path d="M144 50 V88 H182" {B()}/>
<path d="M90 130 H158 M90 160 H158 M90 190 H132" {B(11)}/>
""",
    # Tela com play (editor de vídeo)
    "video": f"""
<rect x="44" y="68" width="168" height="120" rx="24" {B()}/>
<path d="M112 102 L160 128 L112 154 Z" fill="#ffffff" stroke="#ffffff" stroke-width="8" stroke-linejoin="round"/>
<path d="M92 212 H164" {B()}/>
""",
    # Grade de miniaturas (galeria / Bridge)
    "galeria": f"""
<rect x="52" y="52" width="66" height="66" rx="16" fill="#ffffff"/>
<rect x="138" y="52" width="66" height="66" rx="16" {B(11)}/>
<rect x="52" y="138" width="66" height="66" rx="16" {B(11)}/>
<rect x="138" y="138" width="66" height="66" rx="16" {B(11)}/>
""",
    # Nuvem com seta (plugin Fluxogama: enviar/baixar do portal)
    "fluxogama": f"""
<path d="M78 178 C 50 178, 38 156, 44 136 C 50 116, 70 108, 86 112 C 92 84, 118 66, 146 70 C 176 74, 194 98, 194 122
         C 214 124, 226 142, 222 160 C 218 172, 208 178, 194 178" {B()}/>
<path d="M128 206 V 128 M 102 152 L 128 126 L 154 152" {B()}/>
""",
    # Brilho de IA (assistente)
    "assistente": """
<path d="M118 52 C 124 100, 136 112, 184 118 C 136 124, 124 136, 118 184 C 112 136, 100 124, 52 118 C 100 112, 112 100, 118 52 Z" fill="#ffffff"/>
<path d="M182 150 C 185 170, 190 175, 210 178 C 190 181, 185 186, 182 206 C 179 186, 174 181, 154 178 C 174 175, 179 170, 182 150 Z" fill="#ffffff"/>
<circle cx="182" cy="74" r="10" fill="#ffffff"/>
""",
}

# Folha do logo redesenhada em vetor (duas metades separadas pela onda branca,
# com os cortes de "pena"); coordenadas na escala da ampliação 600x360 do logo.
FOLHA = """
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

SUITE = f"""
<rect x="8" y="8" width="240" height="240" rx="56" fill="#ffffff" stroke="#e3e7f3" stroke-width="4"/>
{FOLHA}
"""


def svg(conteudo: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">'
        f"{DEFS}{conteudo}</svg>\n"
    )


def main():
    SAIDA.mkdir(exist_ok=True)
    for nome, glifo in GLIFOS.items():
        (SAIDA / f"{nome}.svg").write_text(svg(FUNDO + glifo), encoding="utf-8")
    (SAIDA / "suite.svg").write_text(svg(SUITE), encoding="utf-8")
    print("SVGs em", SAIDA)


if __name__ == "__main__":
    main()
