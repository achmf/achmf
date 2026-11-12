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
.tw{animation:t 2.4s steps(2) infinite}
@keyframes t{50%{opacity:.2}}
@media (prefers-reduced-motion:reduce){.blink,.tw{animation:none}}
text{font-family:'P',monospace}"""
BG = "#0f0f1b"


def font_face_css(ttf_path, text):
    opts = subset.Options(flavor="woff2", layout_features=[], notdef_outline=True)
    f = TTFont(ttf_path)
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


def svg(w, h, body, text):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'shape-rendering="crispEdges" role="img" aria-label="{text}">'
            f'<style>{font_face_css(TTF, TEXT)}{CSS}</style>'
            f'<rect width="{w}" height="{h}" fill="{BG}"/>{body}</svg>')


H_TXT = [("ACHMF", 230, 120, 40, "#39ff14", ""),
         ("MOBILE &amp; WEB DEV", 230, 160, 14, "#00e5ff", ""),
         ("PRESS START", 230, 205, 12, "#ffd23f", ' class="blink"')]
F_TXT = [("GAME OVER", 420, 55, 28, "#ff3e88", ""),
         ("INSERT COIN TO CONTINUE", 420, 95, 12, "#ffd23f", ' class="blink"')]
# subset must cover every glyph used (unescape &amp;)
TEXT = "".join(t for t, *_ in H_TXT + F_TXT).replace("&amp;", "&") + " "


def texts(items, anchor=""):
    return "".join(f'<text x="{x}" y="{y}" font-size="{s}" fill="{c}"{anchor}{cls}>{t}</text>'
                   for t, x, y, s, c, cls in items)


def build_header():
    return svg(840, 240, stars(40, 840, 240, 7) + sprite_rects(CAT, PAL, 60, 56, 8) + texts(H_TXT),
               "ACHMF - Mobile and Web Dev - Press Start")


def build_footer():
    return svg(840, 120, texts(F_TXT, ' text-anchor="middle"'), "Game over - insert coin to continue")


def main():
    for name, fn in (("header", build_header), ("footer", build_footer)):
        with open(f"assets/{name}.svg", "w", encoding="utf-8") as fh:
            fh.write(fn())
        print(f"wrote assets/{name}.svg")
    for f in ("assets/header.svg", "assets/footer.svg"):
        s = open(f, encoding="utf-8").read()
        ET.fromstring(s)
        assert "data:font/woff2;base64," in s
        assert "<script" not in s and "foreignObject" not in s
        assert 'shape-rendering="crispEdges"' in s
        assert len(s.encode()) <= 100_000, f"{f} too big"
    assert all(len(r) == 16 for r in CAT) and len(CAT) == 16


if __name__ == "__main__":
    main()
