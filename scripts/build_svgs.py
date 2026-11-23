import base64, io
import xml.etree.ElementTree as ET
from fontTools import subset
from fontTools.ttLib import TTFont

BOLD, MED = "scripts/fonts/Inter-Bold.ttf", "scripts/fonts/Inter-Medium.ttf"
NAME = "achmf"
ROLE = "Software Developer"
SUB = "Information Systems · UPN Veteran Jakarta"
W, H = 1200, 280
CSS = """text{font-family:'IM',sans-serif}
.n{font-family:'IB',sans-serif}
.in{opacity:0;animation:in .6s ease-out forwards}
@keyframes in{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
.bar{transform:scaleX(0);transform-origin:72px 0;animation:bar .5s ease-out .45s forwards}
@keyframes bar{to{transform:scaleX(1)}}
@media (prefers-reduced-motion:reduce){.in,.bar{animation:none;opacity:1;transform:none}}"""


def font_face_css(ttf_path, text, family):
    opts = subset.Options(flavor="woff2", layout_features=[], notdef_outline=True)
    f = TTFont(ttf_path, recalcTimestamp=False)
    s = subset.Subsetter(opts)
    s.populate(text=text)
    s.subset(f)
    f.flavor = "woff2"
    buf = io.BytesIO()
    f.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return "@font-face{font-family:'%s';src:url(data:font/woff2;base64,%s)}" % (family, b64)


def text_width(ttf_path, text, size):
    f = TTFont(ttf_path)
    cmap, hmtx = f.getBestCmap(), f["hmtx"]
    return sum(hmtx[cmap[ord(c)]][0] for c in text) * size / f["head"].unitsPerEm


def build_banner():
    dots = "".join(f'<circle cx="{x}" cy="{y}" r="1.5"/>'
                   for x in range(772, W - 8, 24) for y in range(20, H - 8, 24))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="{NAME} - {ROLE}. {SUB}">'
        f'<style>{font_face_css(BOLD, NAME, "IB")}{font_face_css(MED, ROLE + SUB, "IM")}{CSS}</style>'
        f'<rect width="{W}" height="{H}" fill="#0d1117"/>'
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" fill="none" stroke="#30363d"/>'
        f'<g fill="#58a6ff" opacity=".12">{dots}</g>'
        f'<text class="n in" x="72" y="128" font-size="64" font-weight="700" fill="#f0f6fc">{NAME}</text>'
        f'<text class="in" x="72" y="176" font-size="26" fill="#58a6ff" style="animation-delay:.15s">{ROLE}</text>'
        f'<text class="in" x="72" y="214" font-size="16" fill="#8b949e" style="animation-delay:.3s">{SUB}</text>'
        f'<rect class="bar" x="72" y="146" width="96" height="4" fill="#facc15"/>'
        f'</svg>')


def main():
    out = build_banner()
    with open("assets/banner.svg", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(out)
    print("wrote assets/banner.svg")
    s = open("assets/banner.svg", encoding="utf-8").read()
    ET.fromstring(s)
    assert s.count("data:font/woff2;base64,") == 2
    assert "<script" not in s and "foreignObject" not in s and "href=" not in s
    assert len(s.encode()) <= 100_000, "banner too big"
    for ttf, txt in ((BOLD, NAME), (MED, ROLE + SUB)):
        cmap = TTFont(ttf).getBestCmap()
        assert all(ord(c) in cmap for c in txt), f"glyph missing in {ttf}"
    assert "@media (prefers-reduced-motion:reduce){.in,.bar{" in s
    assert text_width(BOLD, NAME, 64) <= 760, "name too wide"
    assert text_width(MED, SUB, 16) <= W - 72 * 2, "subline too wide"


if __name__ == "__main__":
    main()
