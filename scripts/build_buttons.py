"""Gera botões SVG animados, todos com o MESMO tamanho (190x46): assets/btn-*.svg
Cada arquivo é uma "tela" mais larga com o botão CENTRALIZADO dentro dela: assim o centro
funciona em qualquer visualizador, sem depender de align="center".
Uso: python scripts/build_buttons.py"""
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
W, H = 190, 46          # tamanho do botão
PAD_Y = 6               # folga vertical
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"

ICONS = {  # desenhados à mão, 22x22
    "mail": '<rect x="1" y="4" width="20" height="14" rx="2.5" fill="none" stroke="#fff" stroke-width="2"/><path d="M2 6l9 7 9-7" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/>',
    "in": '<rect x="1" y="1" width="20" height="20" rx="4" fill="#fff"/><text x="11" y="16.5" text-anchor="middle" font-size="14" font-weight="800" fill="COLOR">in</text>',
    "code": '<path d="M8 5L2 11l6 6M14 5l6 6-6 6" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',
    "git": '<circle cx="6" cy="4.5" r="2.6" fill="none" stroke="#fff" stroke-width="2"/><circle cx="6" cy="17.5" r="2.6" fill="none" stroke="#fff" stroke-width="2"/><circle cx="16" cy="9" r="2.6" fill="none" stroke="#fff" stroke-width="2"/><path d="M6 7v8M16 11.6c0 3-4 3-9 4.4" fill="none" stroke="#fff" stroke-width="2"/>',
}

BUTTONS = [  # arquivo, texto, ícone, cor 1, cor 2
    ("btn-email", "Email", "mail", "#ea4335", "#b3261e"),
    ("btn-linkedin", "LinkedIn", "in", "#0a66c2", "#084c91"),
    ("btn-leetcode", "LeetCode", "code", "#ffa116", "#e07b00"),
    ("btn-github", "GitHub", "git", "#30363d", "#161b22"),
    ("btn-contact-email", "Enviar e-mail", "mail", "#ea4335", "#b3261e"),
    ("btn-contact-linkedin", "Conectar", "in", "#0a66c2", "#084c91"),
]
CANVAS = {  # largura da "tela": 250 = 4 botões por linha, 500 = 2 botões por linha
    "btn-contact-email": 500, "btn-contact-linkedin": 500,
}
DEFAULT_CANVAS = 250


def button(label, icon, c1, c2, cw=DEFAULT_CANVAS):
    ic = ICONS[icon].replace("COLOR", c1)
    ox, oy, CH = (cw - W) / 2, PAD_Y, H + 2 * PAD_Y
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cw} {CH}" width="{cw}" height="{CH}" role="img" aria-label="{label}">
<style>text{{font-family:{FONT}}}.shine{{animation:s 4.5s ease-in-out infinite}}@keyframes s{{0%,55%{{transform:translateX(-80px)}}100%{{transform:translateX({W+60}px)}}}}</style>
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>
<clipPath id="c"><rect width="{W}" height="{H}" rx="12"/></clipPath></defs>
<g transform="translate({ox},{oy})"><g clip-path="url(#c)"><rect width="{W}" height="{H}" fill="url(#g)"/>
<rect class="shine" x="0" y="-10" width="26" height="{H+20}" fill="#fff" opacity=".22" transform="skewX(-20)"/></g>
<rect x=".75" y=".75" width="{W-1.5}" height="{H-1.5}" rx="11.5" fill="none" stroke="#fff" stroke-opacity=".28" stroke-width="1.5"/>
<g transform="translate(22,12)">{ic}</g>
<text x="58" y="29.5" font-size="15" font-weight="700" letter-spacing="1" fill="#fff">{label}</text></g>
</svg>"""


if __name__ == "__main__":
    for name, label, icon, c1, c2 in BUTTONS:
        (ASSETS / f"{name}.svg").write_text(button(label, icon, c1, c2, CANVAS.get(name, DEFAULT_CANVAS)), encoding="utf-8")
        print("ok", ASSETS / f"{name}.svg")
