"""
draw.py - transforma uma imagem em arte ASCII colorida

Uso:
    python draw.py                          # desenha no terminal (ANSI true-color)
    python draw.py --svg assets/jinwoo-art.svg   # gera o SVG animado do README
    python draw.py outra.png --cols 90      # outra imagem / outra resolucao

Dependencias: Pillow, numpy (e scipy opcional, nao e necessario).
"""
import argparse
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageSequence

RAMP = " .:-=+*#%@"
ROOT = Path(__file__).resolve().parent

src = "assets/coding-workspace.gif"
im = Image.open(src); w = 360; h = round(im.height * w / im.width)
durs = [f.info.get("duration", 100) for f in ImageSequence.Iterator(Image.open(src))]
frames = [f.convert("RGBA").resize((w, h), Image.LANCZOS) for f in ImageSequence.Iterator(im)]
frames[0].save("assets/coding-workspace.gif", save_all=True, append_images=frames[1:], duration=durs, loop=0, disposal=2)


# --------------------------------------------------------------------------
# imagem -> grade de intensidades (0..255)
# --------------------------------------------------------------------------
def load_grid(path, cols, rows):
    img = Image.open(path).convert("RGB")
    lum = img.convert("L")
    # realca bordas (nariz, labios, sombra do rosto) antes de reduzir para a grade
    lum = lum.filter(ImageFilter.UnsharpMask(radius=3, percent=260, threshold=1))
    small = np.asarray(lum.resize((cols, rows), Image.BOX), dtype=float) / 255
    lo, hi = np.percentile(small, 1), np.percentile(small, 99.8)
    small = np.clip((small - lo) / max(hi - lo, 1e-6), 0, 1) ** 0.95
    return (np.clip(small, 0, 0.99) * 256).astype(int), img


def find_eyes(img):
    """Acha os dois olhos brilhantes (azul-ciano forte). Retorna [(x, y) 0..1]."""
    a = np.asarray(img, dtype=int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mask = (b > 200) & (g > 170) & (b - r > 35)
    ys, xs = np.nonzero(mask)
    if len(xs) < 4:
        return []
    h, w = mask.shape
    mid = np.median(xs)
    eyes = []
    for sel in (xs <= mid, xs > mid):
        if sel.sum():
            eyes.append((xs[sel].mean() / w, ys[sel].mean() / h))
    return eyes


# --------------------------------------------------------------------------
# saida 1: terminal
# --------------------------------------------------------------------------
def print_terminal(grid):
    for row in grid:
        out = ""
        for q in row:
            i = q * 10 // 256
            out += f"\033[38;2;{q*45//100};{q*75//100};{q}m" + RAMP[i]
        print(out + "\033[0m")


# --------------------------------------------------------------------------
# saida 2: SVG animado (roda no README: so <img>, sem JavaScript)
# --------------------------------------------------------------------------
CW, CH = 6, 12          # tamanho de cada "caractere" no SVG
PAD_TOP, PAD_BOT = 40, 52
LEVELS = 16


def level_color(l):
    q = 40 + (255 - 40) * l / (LEVELS - 1)
    return f"#{int(q*.45):02x}{int(q*.75):02x}{int(q):02x}"


def build_svg(grid, eyes, out):
    rows, cols = grid.shape
    W, H = cols * CW, rows * CH
    TW, TH = W + 24, H + PAD_TOP + PAD_BOT
    ox = 12
    rnd = random.Random(7)

    css = ["".join(f".c{l}{{fill:{level_color(l)}}}" for l in range(LEVELS))]
    css.append("""
text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace}
.art text{font-size:10px;white-space:pre}
.r{opacity:0;animation:rev 15s linear infinite both}
@keyframes rev{0%{opacity:0}3%{opacity:1}90%{opacity:1}97%,100%{opacity:0}}
.scan{animation:scan 15s linear infinite both}
@keyframes scan{0%{transform:translateY(-20px);opacity:0}2%{opacity:1}22%{transform:translateY(__H__px);opacity:1}24%,100%{transform:translateY(__H__px);opacity:0}}
.eye{animation:pulse 2.4s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:.55;transform:scale(.85)}50%{opacity:1;transform:scale(1.25)}}
.eyes{opacity:0;animation:eyeson 15s linear infinite both}
@keyframes eyeson{0%,20%{opacity:0}26%,90%{opacity:1}97%,100%{opacity:0}}
.p{animation:rise linear infinite both}
@keyframes rise{0%{transform:translateY(0);opacity:0}15%{opacity:.9}100%{transform:translateY(-__R__px);opacity:0}}
.gl{animation:glitch 15s steps(1) infinite}
@keyframes glitch{0%,52%,54.5%,70%,72.5%,100%{transform:translateX(0)}53%{transform:translateX(6px)}53.8%{transform:translateX(-5px)}71%{transform:translateX(-7px)}71.8%{transform:translateX(4px)}}
.cur{animation:blink 1s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
.typ{clip-path:inset(0 100% 0 0);animation:type 15s steps(12) infinite both}
@keyframes type{0%,30%{clip-path:inset(0 100% 0 0)}38%,92%{clip-path:inset(0 0 0 0)}98%,100%{clip-path:inset(0 100% 0 0)}}
.tag{animation:tag 4s ease-in-out infinite}
@keyframes tag{0%,100%{opacity:.45}50%{opacity:1}}
""".replace("__H__", str(H + 8)).replace("__R__", str(H + 60)))

    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {TW} {TH}" width="{TW}" height="{TH}" role="img" aria-label="Retrato em arte ASCII animada do Sung Jin Woo, o Monarca das Sombras, com olhos azuis brilhando">')
    s.append(f"<style>{''.join(css)}</style>")
    s.append(f"""<defs>
<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#04060c"/><stop offset="1" stop-color="#0a1022"/></linearGradient>
<linearGradient id="sc" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#60a5fa" stop-opacity="0"/><stop offset="1" stop-color="#93c5fd" stop-opacity=".55"/></linearGradient>
<radialGradient id="eg"><stop offset="0" stop-color="#ffffff"/><stop offset=".35" stop-color="#7dd3fc"/><stop offset="1" stop-color="#2563eb" stop-opacity="0"/></radialGradient>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<clipPath id="frame"><rect x="0" y="0" width="{TW}" height="{TH}" rx="14"/></clipPath>
</defs>""")
    s.append(f'<g clip-path="url(#frame)"><rect width="{TW}" height="{TH}" fill="url(#bg)"/>')

    # arte (linhas reveladas de cima para baixo)
    s.append(f'<g class="art" transform="translate({ox},{PAD_TOP})">')
    for y in range(rows):
        row = grid[y]
        idx = [RAMP[q * 10 // 256] for q in row]
        first = next((i for i, c in enumerate(idx) if c != " "), None)
        if first is None:
            continue
        last = max(i for i, c in enumerate(idx) if c != " ")
        runs, cur, cls = [], "", None
        for i in range(first, last + 1):
            l = int(row[i] * LEVELS // 256)
            if cls is None:
                cls = l
            if l != cls and idx[i] != " ":
                runs.append((cls, cur)); cur, cls = "", l
            cur += idx[i].replace("&", "&amp;").replace("<", "&lt;")
        runs.append((cls, cur))
        tsp = "".join(f'<tspan class="c{c}">{t}</tspan>' for c, t in runs)
        glitch = rnd.random() < 0.18
        t = (f'<text class="r" x="{first*CW}" y="{(y+1)*CH-3}" textLength="{(last-first+1)*CW}" '
             f'lengthAdjust="spacing" xml:space="preserve" style="animation-delay:{y*0.075:.2f}s">{tsp}</text>')
        s.append(f'<g class="gl">{t}</g>' if glitch else t)
    s.append("</g>")

    # linha de varredura
    s.append(f'<g transform="translate({ox},{PAD_TOP})"><rect class="scan" width="{W}" height="20" fill="url(#sc)"/></g>')

    # olhos brilhando
    s.append(f'<g class="eyes" transform="translate({ox},{PAD_TOP})" filter="url(#glow)">')
    for ex, ey in eyes:
        cx, cy = ex * W, ey * H
        s.append(f'<g transform="translate({cx:.1f},{cy:.1f})"><circle class="eye" r="9" fill="url(#eg)" style="transform-box:fill-box;transform-origin:center"/><circle r="2" fill="#fff"/></g>')
    s.append("</g>")

    # particulas de sombra subindo (extracao de sombras)
    s.append(f'<g transform="translate(0,{TH-PAD_BOT})">')
    for _ in range(34):
        x = rnd.uniform(14, TW - 14)
        r = rnd.choice([1, 1.3, 1.6, 2.1])
        col = rnd.choice(["#818cf8", "#60a5fa", "#a78bfa", "#38bdf8"])
        dur, dl = rnd.uniform(5, 11), -rnd.uniform(0, 11)
        s.append(f'<circle class="p" cx="{x:.0f}" cy="0" r="{r}" fill="{col}" style="animation-duration:{dur:.1f}s;animation-delay:{dl:.1f}s"/>')
    s.append("</g>")

    # moldura HUD
    s.append(f'<rect x="1" y="1" width="{TW-2}" height="{TH-2}" rx="13" fill="none" stroke="#3b82f6" stroke-opacity=".45"/>')
    for (x, y, dx, dy) in [(8, 8, 1, 1), (TW-8, 8, -1, 1), (8, TH-8, 1, -1), (TW-8, TH-8, -1, -1)]:
        s.append(f'<path d="M{x} {y+dy*16}V{y}H{x+dx*16}" fill="none" stroke="#60a5fa" stroke-width="2" filter="url(#glow)"/>')

    s.append(f'<text x="20" y="25" font-size="11" fill="#60a5fa" class="tag">[ SISTEMA ] JOGADOR DETECTADO</text>')
    s.append(f'<circle cx="{TW-24}" cy="21" r="3.5" fill="#22d3ee" class="tag"/>')
    s.append(f'<text x="20" y="{TH-20}" font-size="14" font-weight="700" fill="#e0f2fe" letter-spacing="3" filter="url(#glow)"><tspan fill="#60a5fa">&gt; </tspan><tspan class="typ">ARISE.</tspan><tspan class="cur" fill="#93c5fd">_</tspan></text>')
    s.append(f'<text x="{TW-20}" y="{TH-20}" font-size="10" fill="#6366f1" text-anchor="end" class="tag">SHADOW MONARCH</text>')
    s.append("</g></svg>")

    Path(out).write_text("\n".join(s), encoding="utf-8")
    print(f"SVG gerado: {out} ({Path(out).stat().st_size/1024:.0f} KB)")


def main():
    ap = argparse.ArgumentParser(description="Imagem -> arte ASCII (terminal ou SVG animado)")
    ap.add_argument("image", nargs="?", default=str(ROOT / "assets" / "jinwoo.png"))
    ap.add_argument("--cols", type=int, default=88)
    ap.add_argument("--svg", metavar="SAIDA.svg", help="gera o SVG animado em vez de imprimir")
    a = ap.parse_args()

    img0 = Image.open(a.image)
    rows = round(a.cols * img0.height / img0.width * (CW / CH))   # corrige proporcao do caractere
    grid, img = load_grid(a.image, a.cols, rows)
    if a.svg:
        build_svg(grid, find_eyes(img), a.svg)
    else:
        print_terminal(grid)


if __name__ == "__main__":
    main()
