import base64, io, random
import xml.etree.ElementTree as ET
from fontTools import subset
from fontTools.ttLib import TTFont

TTF = "scripts/fonts/PressStart2P-Regular.ttf"
PAL = {"W": "#f4f4f4", "Y": "#ffd23f", "O": "#e8a65d", "D": "#b8733a",
       "K": "#0f0f1b", "P": "#ff3e88", "C": "#00e5ff"}
CAT = [
    "......Y..Y......",
    "....WWWWWWWW....",
    "...WWWYYYYWWW...",
    "......Y..Y......",
    "..KOOOOOOOOOOK..",
    ".KODKOOOOOOKDOK.",
    ".KOOKOOOOOOKOOK.",
    ".KOOOOODDOOOOOK.",
    "..KOOOOOOOOOOK..",
    "..KKOOOOOOOOKK..",
    ".KOOOOOOOOOCCOK.",
    ".KOOOOOOOOCCCCK.",
    ".KOODDOOOCPPPPC.",
    "..KODDOOOCPPPPC.",
    "..KKOOOOOOCCCC..",
    "......Y..Y......",
]
CSS = """.blink{animation:b 1s steps(1) infinite}
@keyframes b{50%{opacity:0}}
.seg{animation:f .2s steps(1) both}
@keyframes f{from{opacity:0}}
.tw{animation:t 2.4s steps(2) infinite}
@keyframes t{50%{opacity:.2}}
@media (prefers-reduced-motion:reduce){.blink,.tw,.seg{animation:none}}
text{font-family:'P',monospace}"""
BG = "#0f0f1b"


def font_face_css(ttf_path, text):
    opts = subset.Options(flavor="woff2", layout_features=[], notdef_outline=True)
    f = TTFont(ttf_path, recalcTimestamp=False)
    s = subset.Subsetter(opts)
    s.populate(text=text)
    s.subset(f)
    f.flavor = "woff2"
    buf = io.BytesIO()
    f.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return "@font-face{font-family:'P';src:url(data:font/woff2;base64,%s)}" % b64


def sprite_rects(grid, palette, x, y, px):
    return "".join(
        f'<rect x="{x + c * px}" y="{y + r * px}" width="{px}" height="{px}" fill="{palette[ch]}"/>'
        for r, row in enumerate(grid) for c, ch in enumerate(row) if ch != ".")


def stars(n, w, h, seed):
    rnd = random.Random(seed)
    return "".join(
        f'<rect class="tw" x="{rnd.randrange(w - 2)}" y="{rnd.randrange(h - 2)}" width="2" height="2" '
        f'fill="#f4f4f4" style="animation-delay:{rnd.randrange(24) / 10}s"/>'
        for _ in range(n))


def svg(w, h, body, text, bg=True):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'shape-rendering="crispEdges" role="img" aria-label="{text}">'
            f'<style>{font_face_css(TTF, TEXT)}{CSS}</style>'
            + (f'<rect width="{w}" height="{h}" fill="{BG}"/>' if bg else '') + f'{body}</svg>')


H_TXT = [("ACHMF", 230, 120, 40, "#39ff14", ""),
         ("SOFTWARE DEVELOPER", 230, 160, 14, "#00e5ff", ""),
         ("PRESS START", 230, 205, 12, "#ffd23f", ' class="blink"')]
F_TXT = [("GAME OVER", 420, 55, 28, "#ff3e88", ""),
         ("INSERT COIN TO CONTINUE", 420, 95, 12, "#ffd23f", ' class="blink"')]
STATS = [("FRONTEND", 8), ("BACKEND", 6), ("MOBILE", 7), ("UI/UX", 5)]
PLAYER_LABEL = "Player 1: ACHMF, Software Developer. " + ", ".join(
    f"{l if '/' in l else l.capitalize()} {n}" for l, n in STATS) + " of 10."
TITLES = ["INVENTORY", "SELECT STAGE", "PLAYER STATS", "HIGH SCORE", "CONTINUE?"]
# subset must cover every glyph of every string used by every builder
TEXT = "".join(t for t, *_ in H_TXT + F_TXT)+ "".join(
    ["ACHMF", "SOFTWARE DEVELOPER", "P1 READY"] + [l for l, _ in STATS] + TITLES) + " "


def texts(items, anchor=""):
    return "".join(f'<text x="{x}" y="{y}" font-size="{s}" fill="{c}"{anchor}{cls}>{t}</text>'
                   for t, x, y, s, c, cls in items)


def build_header():
    return svg(840, 240, stars(40, 840, 240, 7) + sprite_rects(CAT, PAL, 60, 56, 8) + texts(H_TXT),
               "ACHMF - Software Developer - Press Start")


def build_footer():
    return svg(840, 120, texts(F_TXT, ' text-anchor="middle"'), "Game over - insert coin to continue")


def build_player():
    r = lambda x, y, w, h, c, cls="": f'<rect{cls} x="{x}" y="{y}" width="{w}" height="{h}" fill="{c}"/>'
    b = r(24, 30, 200, 200, "#39ff14") + r(28, 34, 192, 192, "#1a1c2c") + sprite_rects(CAT, PAL, 44, 50, 10)
    cur = "".join(r(x, y, 16, 4, "#ffd23f") + r(x if dx < 0 else x + 12, y if dy < 0 else y - 12, 4, 16, "#ffd23f")
                  for x, y, dx, dy in ((16, 22, -1, -1), (216, 22, 1, -1), (16, 234, -1, 1), (216, 234, 1, 1)))
    b += f'<g class="blink">{cur}</g>'
    b += texts([("ACHMF", 252, 70, 32, "#39ff14", ""), ("SOFTWARE DEVELOPER", 252, 104, 16, "#00e5ff", "")])
    bx = 252 + 8 * 14 + 12  # bars start after the longest label
    for row, (label, n) in enumerate(STATS):
        y = 140 + row * 28
        b += texts([(label, 252, y, 14, "#f4f4f4", "")])
        for i in range(10):
            x = bx + i * 20
            b += (f'<rect class="seg" x="{x}" y="{y - 12}" width="16" height="12" fill="#ff3e88" '
                  f'style="animation-delay:{row * 0.15 + i * 0.08:.2f}s"/>' if i < n
                  else r(x, y - 12, 16, 12, "#2a2c3c"))
    b += texts([("P1 READY", 584, 258, 12, "#ffd23f", ' class="blink"')], ' text-anchor="end"')
    return svg(600, 270, b, PLAYER_LABEL)


def slug(label):
    return "".join(c if c.isalnum() else "-" for c in label.lower()).strip("-")


ARROW = (16, 12, 8, 4)


def build_title(label):
    tri = "".join(f'<rect x="{c * 4}" y="{16 - h // 2}" width="4" height="{h}" fill="#ffd23f"/>'
                  for c, h in enumerate(ARROW))
    t = (f'<text x="28" y="22" font-size="14" fill="#39ff14" stroke="#0f0f1b" stroke-width="4" '
         f'paint-order="stroke">{label}</text>')
    return svg(28 + len(label) * 14 + 8, 32, f'<g class="blink">{tri}</g>{t}', label, bg=False)


def main():
    readme = open("README.md", encoding="utf-8").read()
    out = [("header", build_header()), ("footer", build_footer()), ("player", build_player())]
    out += [("title-" + slug(t), build_title(t)) for t in TITLES]
    for name, content in out:
        with open(f"assets/{name}.svg", "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        print(f"wrote assets/{name}.svg")
    for name, _ in out:
        f = f"assets/{name}.svg"
        s = open(f, encoding="utf-8").read()
        root = ET.fromstring(s)
        assert "data:font/woff2;base64," in s
        assert "<script" not in s and "foreignObject" not in s and "href" not in s
        assert 'shape-rendering="crispEdges"' in s
        assert len(s.encode()) <= 100_000, f"{f} too big"
        vw, vh = map(int, root.get("viewBox").split()[2:])
        ns = "{http://www.w3.org/2000/svg}"
        if name.startswith("title-"):
            assert not any(e.get("width") == str(vw) and e.get("height") == str(vh)
                           for e in root.iter(ns + "rect")), f"{f}: title must be transparent"
        if name == "player":
            assert all(int(e.get("x")) + int(e.get("width")) <= vw - 16
                       for e in root.iter(ns + "rect") if e.get("class") == "seg" or e.get("fill") == "#2a2c3c"), "bar overflows margin"
        for e in root.iter(ns + "text"):
            w = len(e.text) * int(e.get("font-size"))
            x = int(e.get("x"))
            a = e.get("text-anchor")
            lo = x - w if a == "end" else x - w // 2 if a == "middle" else x
            assert 0 <= lo and lo + w <= vw and int(e.get("y")) <= vh, f"{f}: {e.text!r} outside viewBox"
            assert all(ch in TEXT for ch in e.text), f"{f}: glyph missing from subset"
    assert all(a > b for a, b in zip(ARROW, ARROW[1:])), "arrow must be a right-pointing triangle"
    d = dict(out)
    assert f'alt="{PLAYER_LABEL[:-1]}"' in readme, "README player alt drifted from aria-label"
    assert "SOFTWARE DEVELOPER" in d["header"]
    assert d["player"].count('class="seg"') == 8 + 6 + 7 + 5
    assert all(len(r) == 16 for r in CAT) and len(CAT) == 16


if __name__ == "__main__":
    main()
