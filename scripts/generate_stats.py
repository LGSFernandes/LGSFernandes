"""
Gera os cards animados do perfil (SVG proprio, sem servicos externos):

    profile/status.svg   -> "Janela de Status" estilo Solo Leveling (nível, XP, atributos reais)
    profile/langs.svg    -> linguagens mais usadas (barras animadas)
    profile/contrib.svg  -> mapa de contribuicoes com onda de "sombras"
    profile/leetcode.svg -> problemas resolvidos no LeetCode (API publica)

Uso no GitHub Actions:   python scripts/generate_stats.py   (usa GITHUB_TOKEN)
Sem token / sem rede:    python scripts/generate_stats.py --demo  (cards "aguardando sincronização")

So usa a biblioteca padrao do Python.
"""
import datetime as dt
import json
import math
import os
import sys
import urllib.request
from pathlib import Path

USER = os.environ.get("PROFILE_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "LGSFernandes"
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
OUT = Path(__file__).resolve().parent.parent / "profile"

LANG_COLORS = {"Java": "#f59e0b", "Python": "#60a5fa", "JavaScript": "#facc15", "TypeScript": "#38bdf8",
               "HTML": "#fb7185", "CSS": "#a78bfa", "Dockerfile": "#22d3ee", "Shell": "#4ade80",
               "PLpgSQL": "#818cf8", "SCSS": "#f472b6"}
FALLBACK = ["#818cf8", "#60a5fa", "#a78bfa", "#38bdf8", "#c084fc", "#22d3ee"]

FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"
QUESTS = [  # missao diaria: troca todo dia, de forma deterministica
    "Resolver 1 problema no LeetCode",
    "Fazer 1 commit com teste ou refatoração",
    "Ler 1 artigo sobre arquitetura de APIs",
    "Revisar uma query SQL e criar um índice",
    "Estudar 20 min de estruturas de dados",
    "Melhorar o README de um projeto",
    "Containerizar um serviço com Docker",
]


# ----------------------------------------------------------------- coleta
def gql(query, **variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "User-Agent": "profile-stats"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def fetch():
    q = """query($u:String!){ user(login:$u){
      followers{totalCount}
      pullRequests{totalCount} issues{totalCount}
      repositories(ownerAffiliations:OWNER, isFork:false, first:100, orderBy:{field:PUSHED_AT,direction:DESC}){
        totalCount nodes{ stargazerCount languages(first:8, orderBy:{field:SIZE,direction:DESC}){ edges{ size node{name color} } } } }
      contributionsCollection{ contributionCalendar{ totalContributions weeks{ contributionDays{ contributionCount date } } }
        totalCommitContributions restrictedContributionsCount }
    } }"""
    u = gql(q, u=USER)["user"]
    langs = {}
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            n = e["node"]["name"]
            langs.setdefault(n, [0, e["node"]["color"]])[0] += e["size"]
    cal = u["contributionsCollection"]["contributionCalendar"]
    return {
        "live": True,
        "followers": u["followers"]["totalCount"],
        "prs": u["pullRequests"]["totalCount"],
        "issues": u["issues"]["totalCount"],
        "repos": u["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        "contribs": cal["totalContributions"],
        "commits": u["contributionsCollection"]["totalCommitContributions"],
        "weeks": [[d["contributionCount"] for d in w["contributionDays"]] for w in cal["weeks"]],
        "langs": sorted(((k, v[0], v[1]) for k, v in langs.items()), key=lambda x: -x[1])[:6],
    }


LEETCODE_USER = os.environ.get("LEETCODE_USER", "LGSFernandes")


def fetch_leetcode():
    """API publica do LeetCode (sem login). Se falhar, o card fica em modo 'aguardando'."""
    q = "query($u:String!){matchedUser(username:$u){submitStatsGlobal{acSubmissionNum{difficulty count}}}}"
    req = urllib.request.Request(
        "https://leetcode.com/graphql",
        data=json.dumps({"query": q, "variables": {"u": LEETCODE_USER}}).encode(),
        headers={"Content-Type": "application/json", "Referer": "https://leetcode.com", "User-Agent": "profile-stats"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        rows = json.load(r)["data"]["matchedUser"]["submitStatsGlobal"]["acSubmissionNum"]
    c = {x["difficulty"]: x["count"] for x in rows}
    return {"live": True, "total": c.get("All", 0), "easy": c.get("Easy", 0), "medium": c.get("Medium", 0), "hard": c.get("Hard", 0)}


def demo_leetcode():
    return {"live": False, "total": 0, "easy": 0, "medium": 0, "hard": 0}


def demo():
    return {"live": False, "followers": 0, "prs": 0, "issues": 0, "repos": 0, "stars": 0, "contribs": 0,
            "commits": 0, "weeks": [[0] * 7 for _ in range(53)],
            "langs": [("Java", 1, None), ("Python", 1, None), ("JavaScript", 1, None)]}


# ----------------------------------------------------------------- helpers
def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def level_of(xp):
    """Nivel cresce com sqrt(XP): rapido no comeco, mais dificil depois. Retorna (nivel, progresso 0..1)."""
    lvl = int(math.sqrt(xp / 4)) + 1
    lo, hi = 4 * (lvl - 1) ** 2, 4 * lvl ** 2
    return lvl, (xp - lo) / (hi - lo)


def rank_of(lvl):
    for lim, r in [(60, "S"), (40, "A"), (25, "B"), (15, "C"), (8, "D")]:
        if lvl >= lim:
            return r
    return "E"


STYLE_COMMON = f"""text{{font-family:{FONT}}}
@keyframes blink{{50%{{opacity:0}}}}
@keyframes fadeup{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
@keyframes grow{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
@keyframes pulse{{0%,100%{{opacity:.5}}50%{{opacity:1}}}}
"""
DEFS = """<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#050816"/><stop offset="1" stop-color="#0c1430"/></linearGradient>
<linearGradient id="bar" x1="0" x2="1"><stop offset="0" stop-color="#6366f1"/><stop offset="1" stop-color="#22d3ee"/></linearGradient>
<filter id="glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>"""


def wrap(w, h, label, body, extra_css=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(label)}">'
            f"<style>{STYLE_COMMON}{extra_css}</style>{DEFS}"
            f'<rect width="{w}" height="{h}" rx="14" fill="url(#bg)"/>'
            f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="13" fill="none" stroke="#3b82f6" stroke-opacity=".45"/>'
            f"{body}</svg>")


# ----------------------------------------------------------------- status.svg
def status_svg(d):
    W, H = 552, 620          # mesma proporção do retrato (jinwoo-art.svg: 552 x 620)
    live = d["live"]
    xp = d["commits"] * 2 + d["prs"] * 8 + d["issues"] * 3 + d["repos"] * 10 + d["stars"] * 5 if live else 0
    lvl, prog = level_of(xp)
    rank = rank_of(lvl) if live else "?"
    today = dt.date.today()
    quest = QUESTS[today.toordinal() % len(QUESTS)]
    show = lambda v: v if live else "--"

    css = """
.row{opacity:0;animation:fadeup .6s ease-out forwards}
.xp{transform-box:fill-box;transform-origin:left;animation:grow 1.6s .9s cubic-bezier(.2,.8,.2,1) both}
.sc{animation:sc 6s linear infinite}
@keyframes sc{from{transform:translateY(-6px)}to{transform:translateY(%dpx)}}
.rk{animation:pulse 2.6s ease-in-out infinite}
""".replace("%d", str(H))
    b = []
    b.append(f'<rect class="sc" width="{W}" height="6" fill="#60a5fa" opacity=".07"/>')
    b.append('<text x="28" y="38" font-size="13" fill="#60a5fa" letter-spacing="4" class="rk">[ JANELA DE STATUS ]</text>')
    if not live:
        b.append(f'<text x="{W-28}" y="38" text-anchor="end" font-size="10" fill="#f59e0b" class="rk">aguardando 1ª sincronização</text>')
    b.append(f'<line x1="28" y1="54" x2="{W-28}" y2="54" stroke="#3b82f6" stroke-opacity=".5"/>')
    # rank
    b.append(f'<g class="rk" filter="url(#glow)"><rect x="{W-100}" y="76" width="72" height="72" rx="12" fill="none" stroke="#22d3ee" stroke-width="2"/>'
             f'<text x="{W-64}" y="127" text-anchor="middle" font-size="44" font-weight="800" fill="#e0f2fe">{rank}</text></g>')
    b.append(f'<text x="{W-64}" y="166" text-anchor="middle" font-size="10" fill="#64748b" letter-spacing="2">RANK</text>')
    info = [("NOME", "Luckas Fernandes"), ("CLASSE", "Desenvolvedor Back-End"),
            ("TÍTULO", "Estudante de CC @ UERJ"), ("NÍVEL", f"{lvl if live else '--'}")]
    for i, (k, v) in enumerate(info):
        y = 92 + i * 34
        b.append(f'<g class="row" style="animation-delay:{.15*i:.2f}s"><text x="28" y="{y}" font-size="12" fill="#64748b">{k}</text>'
                 f'<text x="112" y="{y}" font-size="15" fill="#e2e8f0" font-weight="600">{esc(v)}</text></g>')
    # XP
    b.append('<text x="28" y="252" font-size="12" fill="#64748b">XP</text>')
    b.append(f'<rect x="112" y="241" width="{W-140}" height="12" rx="6" fill="#1e293b"/>')
    bw = (W - 140) * (prog if live else 0.0)
    b.append(f'<rect class="xp" x="112" y="241" width="{bw:.1f}" height="12" rx="6" fill="url(#bar)" filter="url(#glow)"/>')
    b.append(f'<text x="{W-28}" y="274" text-anchor="end" font-size="10" fill="#64748b">{xp if live else "--"} XP · atualiza todo dia</text>')
    # atributos: 2 colunas x 3 linhas
    attrs = [("COMMITS", d["commits"], "#60a5fa"), ("PULL REQUESTS", d["prs"], "#a78bfa"), ("REPOSITÓRIOS", d["repos"], "#22d3ee"),
             ("ESTRELAS", d["stars"], "#facc15"), ("SEGUIDORES", d["followers"], "#4ade80"), ("CONTRIB. / ANO", d["contribs"], "#f472b6")]
    tw = (W - 56 - 14) // 2
    for i, (k, v, c) in enumerate(attrs):
        col, row = i % 2, i // 2
        x, y = 28 + col * (tw + 14), 292 + row * 74
        b.append(f'<g class="row" style="animation-delay:{.5+.12*i:.2f}s"><rect x="{x}" y="{y}" width="{tw}" height="64" rx="10" fill="#0f172a" stroke="{c}" stroke-opacity=".35"/>'
                 f'<text x="{x+16}" y="{y+24}" font-size="10" fill="#64748b" letter-spacing="1.5">{k}</text>'
                 f'<text x="{x+16}" y="{y+51}" font-size="28" font-weight="700" fill="{c}">{show(v)}</text></g>')
    # missão diária
    b.append(f'<g transform="translate(28,{H-96})"><rect width="{W-56}" height="68" rx="10" fill="#1e1b4b" fill-opacity=".6" stroke="#818cf8" stroke-opacity=".5"/>'
             f'<text x="16" y="24" font-size="10" fill="#a5b4fc" letter-spacing="2">MISSÃO DIÁRIA · {today.strftime("%d/%m")}</text>'
             f'<text x="16" y="50" font-size="14" fill="#e0e7ff">&gt; {esc(quest)}</text></g>')
    return wrap(W, H, f"Janela de status do perfil: nível {lvl}, rank {rank}", "".join(b), css)


# ----------------------------------------------------------------- langs.svg
def langs_svg(d):
    W = 560
    langs = d["langs"] or [("--", 1, None)]
    tot = sum(x[1] for x in langs) or 1
    H = 70 + len(langs) * 30
    css = ".bar{transform-box:fill-box;transform-origin:left;animation:grow 1.2s cubic-bezier(.2,.8,.2,1) both}"
    b = ['<text x="24" y="32" font-size="12" fill="#60a5fa" letter-spacing="4">[ INVENTÁRIO DE LINGUAGENS ]</text>']
    for i, (name, size, color) in enumerate(langs):
        c = LANG_COLORS.get(name) or color or FALLBACK[i % len(FALLBACK)]
        pct = size / tot * 100 if d["live"] else 0
        y = 62 + i * 30
        bw = (W - 220) * pct / 100
        b.append(f'<text x="24" y="{y+11}" font-size="12" fill="#e2e8f0">{esc(name)}</text>')
        b.append(f'<rect x="130" y="{y}" width="{W-220}" height="12" rx="6" fill="#1e293b"/>')
        b.append(f'<rect class="bar" style="animation-delay:{.12*i:.2f}s" x="130" y="{y}" width="{bw:.1f}" height="12" rx="6" fill="{c}" filter="url(#glow)"/>')
        b.append(f'<text x="{W-24}" y="{y+11}" text-anchor="end" font-size="12" fill="#94a3b8">{pct:.1f}%</text>' if d["live"] else
                 f'<text x="{W-24}" y="{y+11}" text-anchor="end" font-size="12" fill="#475569">--</text>')
    return wrap(W, H, "Linguagens mais usadas nos repositórios", "".join(b), css)


# ----------------------------------------------------------------- contrib.svg
def contrib_svg(d):
    weeks = d["weeks"][-53:]
    cell, gap = 11, 3
    W = 24 * 2 + len(weeks) * (cell + gap)
    H = 70 + 7 * (cell + gap) + 30
    mx = max([max(w) for w in weeks] + [1])
    pal = ["#131c36", "#1e3a8a", "#2563eb", "#7c3aed", "#c4b5fd"]
    css = """.cell{animation:wave 5s ease-in-out infinite}
@keyframes wave{0%,100%{opacity:.55}50%{opacity:1}}
.top{animation:top 1.6s ease-in-out infinite}
@keyframes top{0%,100%{transform:scale(1)}50%{transform:scale(1.35)}}"""
    b = [f'<text x="24" y="32" font-size="12" fill="#60a5fa" letter-spacing="4">[ DIÁRIO DE MASMORRAS · {d["contribs"] if d["live"] else "--"} CONTRIBUIÇÕES / ANO ]</text>']
    best = (0, 0, 0)
    for wi, w in enumerate(weeks):
        for di, n in enumerate(w):
            if n > best[0]:
                best = (n, wi, di)
    for wi, w in enumerate(weeks):
        for di, n in enumerate(w):
            lv = 0 if n == 0 else min(4, 1 + int(3 * n / mx))
            x, y = 24 + wi * (cell + gap), 52 + di * (cell + gap)
            cls = "top" if (n, wi, di) == best and n > 0 else "cell"
            delay = (wi * 0.09) % 5 if cls == "cell" else 0
            st = f"animation-delay:{delay:.2f}s;transform-box:fill-box;transform-origin:center"
            b.append(f'<rect class="{cls}" style="{st}" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{pal[lv]}"/>')
    ly = H - 14
    b.append(f'<text x="24" y="{ly}" font-size="10" fill="#64748b">menos</text>')
    for i, c in enumerate(pal):
        b.append(f'<rect x="{66+i*16}" y="{ly-9}" width="11" height="11" rx="3" fill="{c}"/>')
    b.append(f'<text x="{66+5*16+4}" y="{ly}" font-size="10" fill="#64748b">mais</text>')
    return wrap(W, H, "Mapa de contribuições do último ano", "".join(b), css)


def leetcode_svg(lc):
    W, H = 560, 170
    live = lc["live"]
    tot = max(lc["total"], 1)
    r = 52
    goal = (lc["total"] // 50 + 1) * 50   # meta: proximo multiplo de 50
    circ = 2 * math.pi * r
    css = f""".ring{{stroke-dasharray:{circ:.1f};stroke-dashoffset:{circ:.1f};animation:fill 2s .3s cubic-bezier(.2,.8,.2,1) forwards;transform:rotate(-90deg);transform-origin:80px 95px}}
@keyframes fill{{to{{stroke-dashoffset:{circ*(1-(lc["total"]/goal) if live else 1):.1f}}}}}
.bar{{transform-box:fill-box;transform-origin:left;animation:grow 1.2s cubic-bezier(.2,.8,.2,1) both}}"""
    b = ['<text x="24" y="30" font-size="12" fill="#60a5fa" letter-spacing="4">[ TREINO NO LEETCODE ]</text>',
         f'<circle cx="80" cy="95" r="{r}" fill="none" stroke="#1e293b" stroke-width="10"/>',
         f'<circle class="ring" cx="80" cy="95" r="{r}" fill="none" stroke="url(#bar)" stroke-width="10" stroke-linecap="round" filter="url(#glow)"/>',
         f'<text x="80" y="102" text-anchor="middle" font-size="26" font-weight="800" fill="#e0f2fe">{lc["total"] if live else "--"}</text>',
         '<text x="80" y="118" text-anchor="middle" font-size="9" fill="#64748b" letter-spacing="2">RESOLVIDOS</text>',
         f'<text x="80" y="160" text-anchor="middle" font-size="9" fill="#475569">meta: {goal}</text>']
    for i, (k, key, c) in enumerate([("Fácil", "easy", "#4ade80"), ("Médio", "medium", "#facc15"), ("Difícil", "hard", "#fb7185")]):
        y = 62 + i * 30
        w = (W - 300) * (lc[key] / tot if live else 0)
        b.append(f'<text x="170" y="{y+11}" font-size="12" fill="#e2e8f0">{k}</text>')
        b.append(f'<rect x="240" y="{y}" width="{W-300}" height="12" rx="6" fill="#1e293b"/>')
        b.append(f'<rect class="bar" style="animation-delay:{.15*i:.2f}s" x="240" y="{y}" width="{w:.1f}" height="12" rx="6" fill="{c}" filter="url(#glow)"/>')
        b.append(f'<text x="{W-24}" y="{y+11}" text-anchor="end" font-size="12" fill="#94a3b8">{lc[key] if live else "--"}</text>')
    return wrap(W, H, "Problemas resolvidos no LeetCode", "".join(b), css)


def main():
    OUT.mkdir(exist_ok=True)
    if "--demo" in sys.argv or not TOKEN:
        d = demo()
        print("modo demo (sem token): gerando cards 'aguardando sincronização'")
    else:
        d = fetch()
    try:
        lc = demo_leetcode() if d is not None and not d["live"] else fetch_leetcode()
    except Exception as e:  # LeetCode fora do ar nao pode derrubar o resto
        print("aviso: LeetCode indisponivel:", e)
        lc = demo_leetcode()
    (OUT / "leetcode.svg").write_text(leetcode_svg(lc), encoding="utf-8")
    print("ok", OUT / "leetcode.svg")
    for name, fn in [("status", status_svg), ("langs", langs_svg), ("contrib", contrib_svg)]:
        (OUT / f"{name}.svg").write_text(fn(d), encoding="utf-8")
        print("ok", OUT / f"{name}.svg")


if __name__ == "__main__":
    main()
