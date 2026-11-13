"""
Gera os SVGs animados "fixos" do README (nao dependem de dados do GitHub):

    assets/header.svg   -> banner com chuva de codigo, nome com glitch e frases digitadas
    assets/divider.svg  -> divisor com pulso de energia viajando
    assets/footer.svg   -> ondas animadas + assinatura

Uso: python scripts/build_static_assets.py
Tudo e SVG puro (CSS/SMIL): funciona dentro de <img> no GitHub, sem JavaScript.
"""
import html
import random
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"

TOKENS = ["{ }", "</>", "=>", "SELECT", "@Bean", "0x1F", "def", "git push", "JWT", "200 OK", "class", "docker", "GET /api",
          "null", "O(n)", "FROM", "async", "main()", "01", "10", "&&", "#!/", "try{", "@GetMapping", "JOIN", "npm"]
LINES = ["Transformando ideias em software", "Back-End · APIs REST · Banco de Dados", "Aprendendo, construindo e evoluindo sempre",
         "Estudante de Ciência da Computação @ UERJ"]


def header():
    W, H = 1000, 260
    rnd = random.Random(11)
    n = len(LINES)
    T = 5 * n  # duracao total do ciclo de frases
    css = f"""text{{font-family:{FONT}}}
.code{{animation:fall linear infinite both;font-size:12px}}
@keyframes fall{{0%{{transform:translateY(-30px);opacity:0}}10%{{opacity:.55}}90%{{opacity:.55}}100%{{transform:translateY({H+30}px);opacity:0}}}}
.n1{{animation:gl1 6s steps(1) infinite}}
.n2{{animation:gl2 6s steps(1) infinite}}
@keyframes gl1{{0%,88%,92%,100%{{transform:translate(0,0)}}89%{{transform:translate(-5px,1px)}}90%{{transform:translate(4px,-1px)}}91%{{transform:translate(-2px,0)}}}}
@keyframes gl2{{0%,88%,92%,100%{{transform:translate(0,0)}}89%{{transform:translate(5px,-1px)}}90%{{transform:translate(-4px,1px)}}91%{{transform:translate(2px,0)}}}}
.ln{{clip-path:inset(0 100% 0 0);animation:ty {T}s infinite both}}
@keyframes ty{{0%{{clip-path:inset(0 100% 0 0);animation-timing-function:steps(36)}}12%{{clip-path:inset(0 0 0 0)}}{100/n-3:.1f}%{{clip-path:inset(0 0 0 0);opacity:1}}{100/n:.1f}%,100%{{clip-path:inset(0 100% 0 0);opacity:0}}}}
.cur{{animation:bl 1s steps(1) infinite}}
@keyframes bl{{50%{{opacity:0}}}}
.ring{{animation:spin 24s linear infinite;transform-origin:500px 105px}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
.eye{{animation:pu 2.6s ease-in-out infinite}}
@keyframes pu{{0%,100%{{opacity:.35}}50%{{opacity:1}}}}"""
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Luckas Fernandes — Desenvolvedor Back-End e Full Stack em formação">',
         f"<style>{css}</style>",
         '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#03050d"/><stop offset=".55" stop-color="#0b1233"/><stop offset="1" stop-color="#1e1b4b"/></linearGradient>'
         '<linearGradient id="tx" x1="0" x2="1"><stop offset="0" stop-color="#93c5fd"/><stop offset=".5" stop-color="#e0e7ff"/><stop offset="1" stop-color="#a78bfa"/></linearGradient>'
         '<radialGradient id="aura"><stop offset="0" stop-color="#3b82f6" stop-opacity=".35"/><stop offset="1" stop-color="#3b82f6" stop-opacity="0"/></radialGradient>'
         '<filter id="glow" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
         f'<clipPath id="fr"><rect width="{W}" height="{H}" rx="18"/></clipPath></defs>',
         f'<g clip-path="url(#fr)"><rect width="{W}" height="{H}" fill="url(#bg)"/>',
         f'<ellipse cx="500" cy="110" rx="420" ry="120" fill="url(#aura)"/>']
    # chuva de codigo
    for i in range(46):
        x = rnd.uniform(10, W - 60)
        t = rnd.choice(TOKENS)
        col = rnd.choice(["#3b82f6", "#6366f1", "#8b5cf6", "#22d3ee", "#60a5fa"])
        dur, dl = rnd.uniform(7, 15), -rnd.uniform(0, 15)
        s.append(f'<text class="code" x="{x:.0f}" y="0" fill="{col}" style="animation-duration:{dur:.1f}s;animation-delay:{dl:.1f}s">{html.escape(t)}</text>')
    # circulo magico girando atras do nome
    s.append('<g class="ring" opacity=".35" fill="none" stroke="#60a5fa"><circle cx="500" cy="105" r="150" stroke-dasharray="3 9"/>'
             '<circle cx="500" cy="105" r="118" stroke="#a78bfa" stroke-dasharray="40 14 4 14"/></g>')
    # nome com glitch (camadas ciano/magenta)
    name = "LUCKAS FERNANDES"
    base = 'x="500" y="125" text-anchor="middle" font-size="58" font-weight="800" letter-spacing="6"'
    s.append(f'<text class="n1" {base} fill="#22d3ee" opacity=".6">{name}</text>')
    s.append(f'<text class="n2" {base} fill="#f472b6" opacity=".5">{name}</text>')
    s.append(f'<text {base} fill="url(#tx)" filter="url(#glow)">{name}</text>')
    # frases digitadas
    for i, line in enumerate(LINES):
        s.append(f'<g style="animation-delay:{5*i}s"><text class="ln" x="500" y="176" text-anchor="middle" font-size="19" fill="#bfdbfe" style="animation-delay:{5*i}s">'
                 f'<tspan fill="#6366f1">&gt; </tspan>{line}<tspan class="cur" fill="#22d3ee">▌</tspan></text></g>')
    s.append('<text x="24" y="30" font-size="11" fill="#60a5fa" letter-spacing="3">[ SISTEMA ] PERFIL CARREGADO</text>')
    s.append(f'<circle class="eye" cx="{W-28}" cy="26" r="4" fill="#22d3ee"/>')
    s.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="17" fill="none" stroke="#3b82f6" stroke-opacity=".5"/></g></svg>')
    return "".join(s)


def divider():
    W, H = 1000, 28
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="presentation" aria-hidden="true">'
            '<defs><linearGradient id="l" x1="0" x2="1"><stop offset="0" stop-color="#3b82f6" stop-opacity="0"/><stop offset=".5" stop-color="#8b5cf6"/><stop offset="1" stop-color="#3b82f6" stop-opacity="0"/></linearGradient>'
            '<radialGradient id="d"><stop offset="0" stop-color="#e0f2fe"/><stop offset="1" stop-color="#22d3ee" stop-opacity="0"/></radialGradient></defs>'
            f'<line x1="0" y1="14" x2="{W}" y2="14" stroke="url(#l)" stroke-width="2"/>'
            '<circle r="9" cy="14" fill="url(#d)"><animate attributeName="cx" values="0;1000;0" dur="7s" repeatCount="indefinite" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1"/></circle>'
            f'<path d="M500 4 L510 14 L500 24 L490 14Z" fill="#0b1233" stroke="#818cf8"><animateTransform attributeName="transform" type="rotate" values="0 500 14;360 500 14" dur="10s" repeatCount="indefinite"/></path>'
            "</svg>")


def footer():
    W, H = 1000, 150
    css = f"""text{{font-family:{FONT}}}
.w1{{animation:mv 11s linear infinite}}.w2{{animation:mv 16s linear infinite reverse}}.w3{{animation:mv 23s linear infinite}}
@keyframes mv{{to{{transform:translateX(-500px)}}}}
.sig{{animation:pu 3s ease-in-out infinite}}@keyframes pu{{0%,100%{{opacity:.65}}50%{{opacity:1}}}}"""

    def wave(amp, y, off=0):
        pts = f"M{-500 + off} {y}"
        for k in range(-1, 6):
            x = k * 250 + off
            pts += f" Q{x + 62} {y - amp} {x + 125} {y} T{x + 250} {y}"
        return pts + f" V{H} H{-500 + off} Z"

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Rodapé animado: Feito com dedicação, curiosidade e muitos commits">'
            f"<style>{css}</style>"
            '<defs><linearGradient id="g1" x1="0" x2="1"><stop offset="0" stop-color="#2563eb"/><stop offset=".5" stop-color="#4f46e5"/><stop offset="1" stop-color="#7c3aed"/></linearGradient></defs>'
            f'<clipPath id="c"><rect width="{W}" height="{H}" rx="18"/></clipPath><g clip-path="url(#c)"><rect width="{W}" height="{H}" fill="#070b1d"/>'
            f'<g class="w3" opacity=".25"><path d="{wave(22, 78)}" fill="url(#g1)"/></g>'
            f'<g class="w2" opacity=".45"><path d="{wave(18, 98)}" fill="url(#g1)"/></g>'
            f'<g class="w1" opacity=".9"><path d="{wave(14, 118)}" fill="url(#g1)"/></g>'
            f'<text class="sig" x="500" y="52" text-anchor="middle" font-size="15" fill="#c7d2fe">Feito com dedicação, curiosidade e muitos commits 💜</text>'
            "</g></svg>")


if __name__ == "__main__":
    ASSETS.mkdir(exist_ok=True)
    for name, fn in [("header", header), ("divider", divider), ("footer", footer)]:
        (ASSETS / f"{name}.svg").write_text(fn(), encoding="utf-8")
        print("ok", ASSETS / f"{name}.svg")
