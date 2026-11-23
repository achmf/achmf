# Stats Dashboard and Contact Revamp Plan

**Goal:**
- Remove the Currently and Featured Projects sections.
- Replace the three stock stats cards with one custom, live "dashboard" SVG that matches the banner.
- Replace the Contact badges with circular icon buttons that all work. Email opens Gmail compose.

**Architecture:**
- `scripts/build_svgs.py` (Python, local) grows two jobs:
  - write four static circle buttons, `assets/contact-*.svg`;
  - write `stats-api/font.js`, which holds base64 woff2 Inter subsets so the serverless function needs no font tooling.
- `stats-api/` is a new Vercel project. `api/stats.js` queries GitHub GraphQL with a read-only token from env, renders the dashboard SVG in pure JS, and caches it for 6 h.
- README references the endpoint and the circle assets.

**Spec (user choices, 2026-11-23):**
- Stats: "Dashboard custom" (live data, banner style).
- Contact: circles only, not rectangles.
- Email: Gmail compose.
- No emoji. No Claude attribution in commits.

## Global Constraints

- Palette (same as banner):

  | Name | Hex |
  |---|---|
  | bg | `#0d1117` |
  | border | `#30363d` |
  | text | `#c9d1d9` |
  | muted | `#8b949e` |
  | white | `#f0f6fc` |
  | blue | `#58a6ff` |
  | yellow | `#facc15` |

- Fonts: Inter Bold 700 for numbers, Inter Medium 500 for labels. Both are embedded as woff2 data URIs.
- SVG rules:
  - no script, foreignObject, or external href;
  - CSS `@keyframes` only;
  - each animation plays once with fill-mode `both`, so static renderers show the final state;
  - a `prefers-reduced-motion` rule disables the animations;
  - the SVG paints its own bg.
- Mobile: the dashboard renders at width 100%. Every text must render at ≥ 7 px at 343 px wide.
- Secrets: the GitHub token lives only in Vercel env `GITHUB_TOKEN`, created and pasted by the user. It is never in the repo, never in chat, and never echoed.

## Decisions

| Item | Value |
|---|---|
| Dashboard size | viewBox `0 0 800 360`, card with 1px `#30363d` border and rx 12 |
| Row 1: 4 metrics | **Contributions** (last 365 days), **Current streak** (days), **Longest streak** (days), **Public repos**. Number: Inter 700 36 px `#f0f6fc`. Label: Inter 500 14 px `#8b949e`. 4 equal columns. The current-streak number is yellow `#facc15`. |
| Row 2: activity | Last 30 days of the contribution calendar as 30 vertical bars, max height 72 px, blue `#58a6ff`. Zero days are a 2 px `#30363d` stub. Label "Last 30 days" in muted. Bars grow from the bottom once, staggered 20 ms. |
| Row 3: languages | One stacked bar, 12 px tall, rx 6, made of the top 5 languages by bytes across owned non-fork public repos. Each segment uses GitHub's language color. Below it is a legend: dot + name + %. Segments widen once. |
| Data | GraphQL `user(login:"achmf")`: `contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}`, `repositories(ownerAffiliations:OWNER,isFork:false,privacy:PUBLIC,first:100){totalCount nodes{languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}` |
| Streak rule | Current streak counts back from today. If today has 0, it counts back from yesterday. |
| Cache / errors | Success: `Cache-Control: public, max-age=3600, s-maxage=21600, stale-while-revalidate=86400`. Failure: HTTP 503, `no-store`, and a small SVG card that says "Stats unavailable", so the README never shows a broken image. |
| Username | Hard-coded `achmf`, so the endpoint is not an open generator. |
| Contact circles | 4 files, `assets/contact-{linkedin,email,portfolio,instagram}.svg`. Each is 64×64: a circle with r 31, fill `#0d1117`, stroke `#30363d`, holding a 28 px brand glyph. Glyph colors: LinkedIn `#0A66C2`, Gmail `#EA4335`, Vercel `#f0f6fc`, Instagram `#E4405F`. Glyph paths come from simple-icons (CC0) and are fetched by the generator at build time. |
| Contact links | LinkedIn `https://www.linkedin.com/in/achmf/`; Email `https://mail.google.com/mail/?view=cm&fs=1&to=farizi1412@gmail.com`; Portfolio `https://achmf.vercel.app/`; Instagram `https://www.instagram.com/achmf_/` |
| Contact layout | A centered row, each `<a href><img width="56" alt="<Platform>"></a>` separated by `&nbsp;&nbsp;`. |

---

### Task 1: Generator — contact circles and font module

**Files:**
- Modify `scripts/build_svgs.py`.
- Output `assets/contact-*.svg` and `stats-api/font.js`.

- [ ] `build_contact(name, path_d, color) -> str` returns a 64×64 SVG with `role="img"` and `aria-label="<Platform>"`. The 24-unit simple-icons path is scaled to 28 px and centered.
- [ ] `write_font_module()` writes `stats-api/font.js` with `export const IB = "<b64>"` and `export const IM = "<b64>"`. The subset covers the chars `0-9 A-Z a-z % , . : / + - ( ) #` and space, plus every char of the labels.
- [ ] Self-checks:
  - each contact SVG parses, has no script or href, and is ≤ 8 KB;
  - `font.js` exists and both strings are non-empty base64;
  - output is byte-identical on a second run.
- [ ] Commit `feat: contact circles and font module for stats api`.

### Task 2: Stats endpoint

**Files:**
- Create `stats-api/package.json` (`"type":"module"`, no dependencies).
- Create `stats-api/vercel.json` (`maxDuration` 15).
- Create `stats-api/api/stats.js`.
- Create `stats-api/render.js`.
- Create `stats-api/render.test.js`.

- [ ] `render.js` exports `summarize(gqlData, today)`, which returns `{total, current, longest, repos, last30:[n…30], langs:[{name,color,pct}…≤5]}`. It also exports `renderSvg(summary)`, which returns an SVG string, and `errorSvg()`. Pure functions, no I/O.
- [ ] `api/stats.js` uses `fetch` to POST to `https://api.github.com/graphql` with `Authorization: bearer ${process.env.GITHUB_TOKEN}`. It then calls summarize and renderSvg and sends the result with the cache headers. On any error, or a missing token, it sends `errorSvg()` with 503 and `no-store`.
- [ ] `render.test.js` uses `node:test` and a small hand-built fixture. It asserts:
  - the streak rule, with today = 0 and with today > 0;
  - `last30` has length 30;
  - the language percentages sum to 100 ± 1;
  - the SVG parses as XML (check with a regex for the root, plus no `<script`) and contains the 4 metric numbers;
  - the minimum font-size × 343/800 is ≥ 7.
- [ ] Run `node --test stats-api/`. All tests must pass.
- [ ] Commit `feat: live stats dashboard endpoint`.

### Task 3: README

- [ ] Delete the `## Currently` and `## Featured Projects` sections.
- [ ] Replace the GitHub Stats block with `<img src="https://achmf-stats.vercel.app/api/stats" alt="GitHub stats for achmf: contributions, streaks, recent activity and top languages" width="100%">`.
- [ ] Replace the Contact block with the centered circle row from Decisions.
- [ ] Checks:
  - the `<img` count equals the `alt="` count;
  - no emoji;
  - no `github-stats-extended` or `streak-stats` remains.
- [ ] Commit `refactor: dashboard stats and circular contact links`. **Do not push.** The controller pushes after the endpoint is live.

### Task 4: Deploy and publish (controller and user)

1. Push the Task 1–2 commits. The README commit can ride along only if the endpoint is already live; otherwise push it last.
2. Import `achmf/achmf` on Vercel as project `achmf-stats`, with root `stats-api`.
3. **The user** creates a GitHub fine-grained token: Public repositories read-only, no extra permissions, 1-year expiry. The user pastes it into the Vercel project's env as `GITHUB_TOKEN`, and the project is redeployed.
4. `curl` the endpoint: it must return 200 with `image/svg+xml`, and the numbers must match the profile.
5. Push the README. Check github.com/achmf at desktop and mobile. All three contact links must open the right page, and Email must open Gmail compose.

## Review Focus

1. A token missing or expired must show the "Stats unavailable" card, not a broken image. Covered by the Task 2 error path.
2. Today with 0 contributions in the morning must not reset the streak. Covered by the Task 2 test.
3. Languages: forks and other people's repos are excluded. Covered by the query filters.
4. The circles must stay crisp at 56 px, and the glyphs must be centered. Checked by a visual render in Task 1.
