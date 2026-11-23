import base64, io, os, re, urllib.request
import xml.etree.ElementTree as ET
from fontTools import subset
from fontTools.ttLib import TTFont

BOLD, MED = "scripts/fonts/Inter-Bold.ttf", "scripts/fonts/Inter-Medium.ttf"
NAME = "achmf"
ROLE = "Software Developer"
W, H = 800, 240
GX = 520  # dot grid starts here
CSS = """text{font-family:'IM',sans-serif;font-weight:500}
.n{font-family:'IB',sans-serif;font-weight:700}
.in{animation:in .6s ease-out both}
@keyframes in{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
.bar{transform-origin:48px 0;animation:bar .5s ease-out .45s both}
@keyframes bar{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@media (prefers-reduced-motion:reduce){.in,.bar{animation:none;opacity:1;transform:none}}"""


def font_b64(ttf_path, text):
    opts = subset.Options(flavor="woff2", layout_features=[], notdef_outline=True)
    f = TTFont(ttf_path, recalcTimestamp=False)
    s = subset.Subsetter(opts)
    s.populate(text=text)
    s.subset(f)
    f.flavor = "woff2"
    buf = io.BytesIO()
    f.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


def font_face_css(ttf_path, text, family, weight):
    b64 = font_b64(ttf_path, text)
    return "@font-face{font-family:'%s';font-weight:%d;src:url(data:font/woff2;base64,%s)}" % (family, weight, b64)


def text_width(ttf_path, text, size):
    f = TTFont(ttf_path)
    cmap, hmtx = f.getBestCmap(), f["hmtx"]
    return sum(hmtx[cmap[ord(c)]][0] for c in text) * size / f["head"].unitsPerEm


def build_banner():
    dots = "".join(f'<circle cx="{x}" cy="{y}" r="1.5"/>'
                   for x in range(GX + 4, W - 8, 24) for y in range(20, H - 8, 24))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="{NAME} - {ROLE}">'
        f'<style>{font_face_css(BOLD, NAME, "IB", 700)}{font_face_css(MED, ROLE, "IM", 500)}{CSS}</style>'
        f'<rect width="{W}" height="{H}" fill="#0d1117"/>'
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" fill="none" stroke="#30363d"/>'
        f'<g fill="#58a6ff" opacity=".12">{dots}</g>'
        f'<text class="n in" x="48" y="110" font-size="64" font-weight="700" fill="#f0f6fc">{NAME}</text>'
        f'<text class="in" x="48" y="172" font-size="26" font-weight="500" fill="#58a6ff" style="animation-delay:.15s">{ROLE}</text>'
        f'<rect class="bar" x="48" y="128" width="96" height="4" fill="#facc15"/>'
        f'</svg>')


SI = "https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/%s.svg"  # CC0, pinned
CONTACTS = (("linkedin", "linkedin", "LinkedIn", "#0A66C2"), ("email", "gmail", "Email", "#EA4335"),
            ("portfolio", "vercel", "Portfolio", "#f0f6fc"), ("instagram", "instagram", "Instagram", "#E4405F"))
BASE = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz %,.:/+-()#"
LABELS = ("Contributions", "Current streak", "Longest streak", "Public repos", "Last 30 days",
          "Top languages", "days", "Stats unavailable", "C++", "C#", "Jupyter Notebook")
FONT_TEXT = "".join(sorted(set(BASE + "".join(LABELS))))


def icon_path(slug):
    with urllib.request.urlopen(SI % slug, timeout=30) as r:
        return re.search(r'<path d="([^"]+)"', r.read().decode()).group(1)


def build_contact(label, path_d, color):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" '
            f'role="img" aria-label="{label}">'
            f'<circle cx="32" cy="32" r="31" fill="#0d1117" stroke="#30363d"/>'
            f'<path transform="translate(18 18) scale(1.1667)" fill="{color}" d="{path_d}"/></svg>')


def write_font_module():
    with open("stats-api/font.js", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(f'export const IB = "{font_b64(BOLD, FONT_TEXT)}";\nexport const IM = "{font_b64(MED, FONT_TEXT)}";\n')


def main():
    os.makedirs("stats-api", exist_ok=True)
    out = build_banner()
    with open("assets/banner.svg", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(out)
    print("wrote assets/banner.svg")
    s = open("assets/banner.svg", encoding="utf-8").read()
    ET.fromstring(s)
    assert s.count("data:font/woff2;base64,") == 2
    assert "<script" not in s and "foreignObject" not in s and "href=" not in s
    assert len(s.encode()) <= 100_000, "banner too big"
    for ttf, txt in ((BOLD, NAME), (MED, ROLE)):
        cmap = TTFont(ttf).getBestCmap()
        assert all(ord(c) in cmap for c in txt), f"glyph missing in {ttf}"
    assert "@media (prefers-reduced-motion:reduce){.in,.bar{" in s
    assert 48 + text_width(BOLD, NAME, 64) <= GX - 24, "name too wide"
    for e in ET.fromstring(s).iter("{http://www.w3.org/2000/svg}text"):
        assert float(e.get("font-size")) * 343 / W >= 7, "text too small on mobile"

    first = {}
    for name, slug, label, color in CONTACTS:
        f = f"assets/contact-{name}.svg"
        with open(f, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(build_contact(label, icon_path(slug), color))
        c = open(f, encoding="utf-8").read()
        ET.fromstring(c)
        assert "<script" not in c and "href" not in c and len(c.encode()) <= 8192, f
        first[f] = c
    write_font_module()
    js = open("stats-api/font.js", encoding="utf-8").read()
    for k in ("IB", "IM"):
        m = re.search(rf'export const {k} = "([A-Za-z0-9+/=]+)";', js)
        assert m and len(base64.b64decode(m.group(1))) > 1000, k
    for f, c in first.items():
        assert open(f, encoding="utf-8").read() == c
    for name, slug, label, color in CONTACTS:
        f = f"assets/contact-{name}.svg"
        with open(f, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(build_contact(label, icon_path(slug), color))
        assert open(f, encoding="utf-8").read() == first[f], "not deterministic"
    write_font_module()
    assert open("stats-api/font.js", encoding="utf-8").read() == js, "font.js not deterministic"
    print("ok")


if __name__ == "__main__":
    main()