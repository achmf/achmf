# Professional Profile Plan

**Goal:** Replace the retro pixel theme with a clean, professional profile (concept B, "Clean Card Layout") that keeps one subtle animation.

**Architecture:** `scripts/build_svgs.py` is rewritten to produce a single `assets/banner.svg`. It reuses the existing `font_face_css` subset approach, now with Inter instead of Press Start 2P. Everything else is plain Markdown plus hosted cards (github-stats-extended, streak-stats, skillicons, shields). All pixel assets and game wording are removed.

**Spec (user choices, 2026-11-23):** concept B. Name shown is `achmf`. Animation: a subtle banner entrance only. Colors: black, blue, yellow. The "Currently" section is drafted by me and reviewed by the user. The typing line and Pac-Man were not chosen, so both are dropped. No emoji, no Claude attribution in commits.

## Global Constraints

- Palette: bg `#0d1117` (near-black, matches GitHub dark), border `#30363d`, text `#c9d1d9`, muted `#8b949e`, white `#f0f6fc`, blue `#58a6ff`, yellow `#facc15`.
- Banner SVG rules:
  - no script, foreignObject, or external href;
  - CSS `@keyframes` only;
  - every animation runs **once** (`forwards`) and ends static;
  - `prefers-reduced-motion` shows the final state with no motion;
  - ≤ 100 KB;
  - its own bg rect, so it reads on both GitHub themes.
- Font: Inter (SIL OFL), embedded as woff2 subset. Use 2 static instances made from the variable font: wght 700 for the name and 500 for the rest.
- No emoji or pictographic characters in README.md (U+2190–2BFF, U+1F000–1FFFF).
- Every `<img>` has alt text. Only GitHub-safe HTML.

## Decisions (rulings; change during plan review)

| Item | Value |
|---|---|
| Banner text | `achmf` (Inter 700, 64px, `#f0f6fc`) / `Software Developer` (500, 26px, `#58a6ff`) / `Information Systems · UPN Veteran Jakarta` (500, 16px, `#8b949e`) |
| Banner accent | Yellow `#facc15` bar, 4px tall, under the name. Width animates 0 → 96px. Faint blue dot grid on the right half for texture (static). |
| Animation | Name fades in and rises 12px (0.6s). Role follows at +0.15s, subline at +0.3s, bar draws at +0.45s. Plays once. |
| Intro | "Software developer building web and mobile products, from database to UI. Information Systems student at UPN Veteran Jakarta." |
| Currently (draft) | Building **KostaHub**, a farm management web app (Next.js, Prisma). Rebuilding **reddog.co.id** with Next.js and Supabase. Studying Information Systems at UPN Veteran Jakarta. |
| Featured projects | Pin cards 2×2: KostaHub, reddog-next, femlife, flavorize |
| Stats | github-stats-extended stats + top-langs side by side, streak below. All use the palette, with `hide_border=false` and border `#30363d`. |
| Contact | shields `for-the-badge`, real brand colors: LinkedIn `0A66C2`, Gmail `EA4335`, Portfolio (logo vercel) `000000`, Instagram `E4405F` |
| Pac-Man | Removed from the README. The `pacman-api/` folder and Vercel project are kept so Vercel builds don't fail; the user may delete both later. |

---

### Task 1: Banner generator

**Files:**
- Rewrite `scripts/build_svgs.py`.
- Add `scripts/fonts/Inter-OFL.txt`.
- Add `scripts/fonts/Inter-Bold.ttf` and `scripts/fonts/Inter-Medium.ttf`, made once from `https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf` with `fontTools.varLib.instancer` at `wght=700, opsz=32` and `wght=500, opsz=14`. Commit only the two static TTFs, not the variable font.
- Delete `scripts/fonts/PressStart2P-Regular.ttf` and `scripts/fonts/OFL.txt`.
- Delete `assets/header.svg`, `footer.svg`, `player.svg`, and `title-*.svg`.
- Output: `assets/banner.svg`.

- [ ] **Step 1:** In `build_svgs.py`, keep `font_face_css(ttf_path, text)`, generalised with a `family` parameter so it can emit two `@font-face` rules (`'IB'` bold, `'IM'` medium). Keep `TTFont(..., recalcTimestamp=False)` and `newline="\n"`. Delete the sprite, star, title, and player code.
- [ ] **Step 2:** `build_banner() -> str`, with viewBox `0 0 1200 280`:
  - full bg rect `#0d1117`, plus a 1px `#30363d` border rect;
  - a dot grid on the right of x≥760: 3px dots every 24px, fill `#58a6ff` opacity .12;
  - texts at x=72 using the sizes, weights, and colors from Decisions;
  - baselines: name y=128, role y=176, subline y=214;
  - yellow bar at x=72 y=146 h=4, width animated by `transform: scaleX` from 0 to 1 with `transform-origin: 72px 0`, final width 96.
- [ ] **Step 3:** Animation CSS:
  - `.in{opacity:0;animation:in .6s ease-out forwards}`
  - `@keyframes in{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}`
  - `.bar{transform:scaleX(0);animation:bar .5s ease-out .45s forwards}`
  - `@keyframes bar{to{transform:scaleX(1)}}`
  - delays as listed in Decisions;
  - `@media (prefers-reduced-motion:reduce){.in,.bar{animation:none;opacity:1;transform:none}}`
- [ ] **Step 4:** Self-checks in `main()`:
  - the file parses as XML and contains both `data:font/woff2;base64,` faces;
  - no script, foreignObject, or `href=`;
  - size ≤ 100 KB;
  - every glyph of every string is present in its subset;
  - the reduced-motion rule names `.in` and `.bar`;
  - text width fits: the name is ≤ 760px wide, measured with the font's real advance widths (`hmtx`), not the monospace estimate.
- [ ] **Step 5:** Run `py scripts/build_svgs.py`. Expected output: `wrote assets/banner.svg`, with no AssertionError. Run it twice; the output must be byte-identical.
- [ ] **Step 6:** Render it in headless Edge at 1200 and 375 px wide. The name must read clearly, and the final state shows the yellow bar.
- [ ] **Step 7:** Commit `feat: professional banner`. Use no attribution.

### Task 2: README rewrite

**Files:** Rewrite `README.md` from scratch, top to bottom:

1. `<img src="assets/banner.svg" alt="achmf, Software Developer, Information Systems at UPN Veteran Jakarta" width="100%">`
2. Intro paragraph, from Decisions.
3. `### Currently`: 3 bullets, from Decisions.
4. `### Tech Stack`: one bold label line followed by one skillicons `<img>` per category. Keep the same icons and order as now, split as:
   - **Languages:** kotlin,java,ts,js,php,html,css,py,cpp
   - **Frontend:** nextjs,react,vue,vite,tailwind,bootstrap
   - **Backend:** nodejs,express,nestjs,laravel,ktor
   - **Mobile:** androidstudio,gradle
   - **Databases:** prisma,supabase,firebase,postgres,mysql,mongodb,sqlite,redis, plus the Neon badge
   - **Cloud & DevOps:** git,github,githubactions,docker,linux,nginx,aws,gcp,cloudflare,vercel,netlify
   - **Tools:** vscode,idea,postman,npm,pnpm,bun,figma,notion, plus the Jira badge
   - **Testing:** jest,vitest,cypress,selenium
   - Use `&theme=dark` and no `perline` (defaults to 15), so each category stays on one line on desktop.
5. `### Featured Projects`: a 2×2 HTML table without borders (`<table>` with `<tr><td>`). Each cell is a pin card `<a href="https://github.com/achmf/<repo>"><img src="https://github-stats-extended.vercel.app/api/pin/?username=achmf&repo=<repo>&bg_color=0d1117&title_color=58a6ff&text_color=c9d1d9&icon_color=facc15&border_color=30363d" alt="<repo>"></a>`.
6. `### GitHub Stats`: stats + top-langs at 49% each, streak below at 100%.
   - Reuse the current URLs with the color params swapped to the palette: title `58a6ff`, text `c9d1d9`, icon `facc15`, bg `0d1117`, border `30363d`.
   - The stats card uses the default title, so drop `custom_title=BATTLE LOG`. Top-langs uses `custom_title=Top Languages`.
   - Streak: `background=0d1117&ring=facc15&fire=facc15&currStreakLabel=58a6ff&sideLabels=58a6ff&currStreakNum=f0f6fc&sideNums=f0f6fc&dates=8b949e&border=30363d`.
7. `### Contact`: the 4 badges, using the brand colors from Decisions and `logoColor=white`, with the same links as now.

- [ ] Checks:
  - the emoji regex passes;
  - the `<img` count equals the `alt="` count;
  - there is no "pixel", "INVENTORY", "STAGE", "BATTLE", "GAME OVER", "CONTINUE?", or `assets/title-` / `player.svg` / `header.svg` / `footer.svg` reference left;
  - every remote image URL returns 200.
- [ ] Commit `refactor: professional profile readme`. Use no attribution.

### Task 3: Publish and verify (controller)

- [ ] Push.
- [ ] Check github.com/achmf at desktop dark and mobile 375 px light:
  - no broken image;
  - no horizontal scroll;
  - the banner animates once and settles;
  - the pin cards are aligned 2×2 on desktop.

## Review Focus

1. Banner font: if the subset misses a glyph (`·`), it falls back to a system font. Covered by the glyph assert.
2. Animation must end static and visible. A wrong `forwards` or a missing reduced-motion override leaves the text invisible. Covered by the Task 1 render check.
3. Pin cards on mobile: a 2-column table at 375 px makes the cards small but not broken. Accept that, or stack them if they become unreadable.
4. Light theme: the cards and banner paint their own dark bg, so they look like dark panels on a white page. This is intended.
