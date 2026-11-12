# Character Select Refactor Plan

**Goal:** Remove every emoji from the profile, replace the PLAYER 1 text box with a pixel "Character Select" SVG, replace the `▶` headings with pixel-font title SVGs, and change the role everywhere to "Software Developer".

**Architecture:** Extend the existing generator `scripts/build_svgs.py`, which already does the font subset, cat sprite and SVG wrapper. New SVGs land in `assets/`. README only swaps markup. Bio is edited in GitHub settings.

**Spec:** user choices on 2026-11-12: option A (Character Select) + titles option 1 (pixel SVG titles), no emoji anywhere, role = Software Developer.

## Global Constraints

- Same palette, font (Press Start 2P, embedded woff2 subset), SVG rules (no script/foreignObject/external href, CSS `@keyframes` only, `shape-rendering="crispEdges"`, integer coordinates, each file ≤ 100 KB, `prefers-reduced-motion` stops animation).
- No emoji or pictographic symbol anywhere in README.md or the bio. "Emoji" means any char in U+2190–U+2BFF or U+1F000–U+1FFFF.
- Commits carry no Claude attribution.

## Decisions (rulings, easy to change later)

| Item | Value |
|---|---|
| Role text | `SOFTWARE DEVELOPER` |
| Stat bars (of 10) | FRONTEND 8, BACKEND 6, MOBILE 7, UI/UX 5 |
| Typing lines | `SOFTWARE DEVELOPER`, `BUILDING FOR WEB + MOBILE`, `INFORMATION SYSTEMS STUDENT`, `LEVEL UP EVERY DAY` |
| Section titles | `INVENTORY`, `SELECT STAGE`, `PLAYER STATS`, `HIGH SCORE`, `CONTINUE?`. The `PLAYER 1` heading is dropped, because the card itself says P1. |
| Bio | `Information Systems Student · Software Developer` |

---

### Task 1: Generator — character select card, titles, role text

**Files:** Modify `scripts/build_svgs.py`. Output: `assets/player.svg`, `assets/title-inventory.svg`, `assets/title-select-stage.svg`, `assets/title-player-stats.svg`, `assets/title-high-score.svg`, `assets/title-continue.svg`, plus regenerated `header.svg` and `footer.svg`.

- [ ] **Step 1: Make the subset text cover all strings.** Replace the hand-built `TEXT` with one constant listing every string used by every builder (header, footer, card, titles). Change `TTFont(ttf_path)` to `TTFont(ttf_path, recalcTimestamp=False)` so the output is deterministic.
- [ ] **Step 2: Header role.** `H_TXT` line 2 becomes `SOFTWARE DEVELOPER` (same x/y/size/color). The aria-label becomes `ACHMF - Software Developer - Press Start`.
- [ ] **Step 3: `build_player() -> str`**, viewBox `0 0 840 260`. Layout:
  - Portrait frame: outer rect x=40 y=30 w=200 h=200, fill `#1a1c2c`, 4 px `#39ff14` border made of rects. `CAT` at x=60 y=50 px=10.
  - Selection cursor: four yellow `#ffd23f` L-shaped corner brackets (2 rects each, 4 px thick, 16 px long) just outside the frame, class `blink`.
  - Text: `ACHMF` at x=280 y=70, size 28, `#39ff14`. `SOFTWARE DEVELOPER` at y=100, size 12, `#00e5ff`.
  - Stat rows at y=135, 160, 185, 210. Label at x=280, size 10, `#f4f4f4`, padded to the same width. Bar at x=420: 10 segments of 20×12 with a 4 px gap. Filled segments are `#ff3e88`, empty ones `#1a1c2c` with a `#f4f4f4` 2 px outline (or simply `#2a2c3c`).
  - Fill animation: each filled segment has class `seg` with `animation-delay: {row*0.15 + i*0.08}s`. CSS: `.seg{animation:f .2s steps(1) both}@keyframes f{from{opacity:0}}`. Add `.seg` to the reduced-motion rule.
  - `P1 READY` at x=800 y=240, size 10, `#ffd23f`, `text-anchor="end"`, class `blink`.
  - aria-label: `Player 1: ACHMF, Software Developer. Frontend 8, Backend 6, Mobile 7, UI/UX 5 of 10.`
- [ ] **Step 4: `build_title(label: str) -> str`**, viewBox `0 0 420 32`, transparent background (no bg rect, so it sits on either GitHub theme). Contents: a yellow pixel right-pointing triangle at x=0 (4 stacked rects: 4/8/12/8/4 px tall, column width 4), class `blink`, and the label at x=28 y=22, size 14, `#39ff14`. Because the background is transparent, add a 2 px `#0f0f1b` text stroke (`paint-order="stroke"`, `stroke-width="4"`) so the green stays readable on the white light theme. File name: `title-<slug>.svg`.
  - `svg()` currently always paints the bg rect. Add a `bg=True` parameter; titles pass `bg=False`.
- [ ] **Step 5: Self-checks in `main()`.** Run the existing asserts over every file written (loop over the list of outputs instead of the hard-coded two). Add: `assert 'SOFTWARE DEVELOPER' in header`, and stat segment count `== 8+6+7+5` filled.
- [ ] **Step 6: Run** `py scripts/build_svgs.py`. Expected: 8 files written, no AssertionError.
- [ ] **Step 7: Visual check.** Render `player.svg` and one title in the browser. The cat must be framed, the bars fill row by row, and the corners blink.
- [ ] **Step 8: Commit** `feat: character select card and pixel section titles`.

### Task 2: README swap

**Files:** Modify `README.md`.

- [ ] **Step 1:** Delete the `### ▶ PLAYER 1` heading and the ```` ```text ```` box (lines 9–19). Put `<div align="center"><img src="assets/player.svg" alt="Player 1: ACHMF, Software Developer. Frontend 8, Backend 6, Mobile 7, UI/UX 5 of 10" width="100%"></div>` in their place.
- [ ] **Step 2:** Replace each `### ▶ X` with `<h3><img src="assets/title-<slug>.svg" alt="X" height="32"></h3>`. The `h3` keeps the document structure and alt keeps it readable for screen readers.
- [ ] **Step 3:** Typing URL `lines=` becomes `SOFTWARE+DEVELOPER;BUILDING+FOR+WEB+%2B+MOBILE;INFORMATION+SYSTEMS+STUDENT;LEVEL+UP+EVERY+DAY`. Update its alt to match.
- [ ] **Step 4: Checks:**
  - `PYTHONIOENCODING=utf-8 py -c "import re;s=open('README.md',encoding='utf-8').read();assert not re.search('[←-⯿\U0001F000-\U0001FFFF]',s)"` passes.
  - The `<img` count equals the `alt="` count.
  - The typing URL returns 200.
- [ ] **Step 5: Commit** `refactor: emoji-free readme with character select card`.

### Task 3: Publish and verify

- [ ] **Step 1:** `git push origin main`.
- [ ] **Step 2:** Edit the bio in GitHub settings via the browser to `Information Systems Student · Software Developer`. Verify with `curl https://api.github.com/users/achmf | grep bio`.
- [ ] **Step 3:** Check github.com/achmf at desktop dark, mobile 375 px light. Expected: no broken images, no horizontal scroll, the titles are readable on both themes, and the card bars animate.

## Review Focus

1. Title SVG legibility on the light theme. The transparent bg plus the dark stroke must keep it readable. Covered by Task 3 Step 3.
2. Title size on mobile. 420 px wide at height 32 scales down cleanly, and the text should stay ≥ 7 px. Checked in Task 3.
3. Font subset missing a glyph (e.g. `/` in UI/UX, `?` in CONTINUE?). Covered by the single TEXT constant in Task 1 Step 1.
4. Card readable without animation (reduced motion). `.seg` is in the reduced-motion rule, so it shows filled.
