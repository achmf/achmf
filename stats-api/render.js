import { IB, IM } from "./font.js";

const MUTED = "#8b949e";
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;" })[c]);
const dayStr = (d) => d.toISOString().slice(0, 10);
const ago = (today, n) => dayStr(new Date(today.getTime() - n * 864e5));

// Public profile calendar (github.com/users/<u>/contributions) includes private counts the API hides.
// shortcut: scrapes GitHub's HTML, returns null if markup changes so the caller falls back to GraphQL.
export function parseCalendar(html) {
  const total = html.match(/([\d,]+)\s+contributions?\s+in the last year/);
  const dates = new Map();
  for (const [td] of html.matchAll(/<td\b[^>]*ContributionCalendar-day[^>]*>/g)) {
    const date = td.match(/data-date="(\d{4}-\d{2}-\d{2})"/), id = td.match(/\bid="([^"]+)"/);
    if (date && id) dates.set(id[1], date[1]);
  }
  const days = [];
  for (const [, id, text] of html.matchAll(/<tool-tip\b[^>]*\bfor="([^"]+)"[^>]*>([^<]*)<\/tool-tip>/g)) {
    if (!dates.has(id)) continue;
    const n = text.match(/^([\d,]+) contributions?/);
    days.push({ date: dates.get(id), contributionCount: n ? Number(n[1].replace(/,/g, "")) : 0 });
  }
  if (!total || !days.length) return null;
  days.sort((a, b) => (a.date < b.date ? -1 : 1));
  return { totalContributions: Number(total[1].replace(/,/g, "")), weeks: [{ contributionDays: days }] };
}

export function summarize(data, today = new Date()) {
  const u = data.user;
  const cal = u.contributionsCollection.contributionCalendar;
  const t = dayStr(today);
  const counts = new Map();
  for (const w of cal.weeks) for (const d of w.contributionDays) if (d.date <= t) counts.set(d.date, d.contributionCount);

  let longest = 0, run = 0;
  for (const date of [...counts.keys()].sort()) {
    run = counts.get(date) > 0 ? run + 1 : 0;
    longest = Math.max(longest, run);
  }
  let current = 0;
  let i = counts.get(t) > 0 ? 0 : 1; // today empty: count from yesterday
  while (counts.get(ago(today, i)) > 0) { current++; i++; }

  const last30 = Array.from({ length: 30 }, (_, k) => counts.get(ago(today, 29 - k)) || 0);

  const bytes = new Map();
  for (const r of u.repositories.nodes)
    for (const e of r.languages.edges) {
      const l = bytes.get(e.node.name) || { size: 0, color: e.node.color || MUTED };
      l.size += e.size;
      bytes.set(e.node.name, l);
    }
  const top = [...bytes].sort((a, b) => b[1].size - a[1].size).slice(0, 5);
  const sum = top.reduce((a, [, l]) => a + l.size, 0);
  const langs = top.map(([name, l]) => ({ name, color: l.color, pct: Math.round((l.size / sum) * 100) }));
  if (langs.length) langs[0].pct += 100 - langs.reduce((a, l) => a + l.pct, 0); // rounding drift

  // calendar excludes private contributions the viewer can't see; GitHub exposes their count separately
  const total = cal.totalContributions + (u.contributionsCollection.restrictedContributionsCount ?? 0);
  return { total, current, longest, repos: u.repositories.totalCount, last30, langs };
}

const head = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 360" width="800" height="360" role="img" aria-label="GitHub stats">`;
const card = `<rect x="0.5" y="0.5" width="799" height="359" rx="12" fill="#0d1117" stroke="#30363d"/>`;
const fonts = `@font-face{font-family:Inter;font-weight:700;src:url(data:font/woff2;base64,${IB}) format("woff2")}@font-face{font-family:Inter;font-weight:500;src:url(data:font/woff2;base64,${IM}) format("woff2")}`;

export function errorSvg() {
  return `${head.replace('viewBox="0 0 800 360" width="800" height="360"', 'viewBox="0 0 800 120" width="800" height="120"')}<style>${fonts}text{font-family:Inter,sans-serif}</style><rect x="0.5" y="0.5" width="799" height="119" rx="12" fill="#0d1117" stroke="#30363d"/><text x="400" y="70" text-anchor="middle" font-size="20" font-weight="500" fill="${MUTED}">Stats unavailable</text></svg>`;
}

export function renderSvg(s) {
  const css = `${fonts}text{font-family:Inter,sans-serif}.n{font-size:36px;font-weight:700}.l{font-size:17px;font-weight:500;fill:${MUTED}}` +
    `.b,.g{transform-box:fill-box;animation-fill-mode:both;animation-duration:.6s;animation-timing-function:ease-out}` +
    `.b{transform-origin:bottom;animation-name:up}.g{transform-origin:left;animation-name:wide}` +
    `@keyframes up{from{transform:scaleY(0)}to{transform:scaleY(1)}}@keyframes wide{from{transform:scaleX(0)}to{transform:scaleX(1)}}` +
    `@media (prefers-reduced-motion:reduce){.b,.g{animation:none}}`;

  const metrics = [[s.total, "Contributions (year)", "#f0f6fc"], [s.current, "Current streak (days)", "#facc15"], [s.longest, "Longest streak (days)", "#f0f6fc"], [s.repos, "Public repos", "#f0f6fc"]]
    .map(([v, label, c], i) => `<text class="n" x="${100 + i * 200}" y="78" text-anchor="middle" font-size="36" font-weight="700" fill="${c}">${v.toLocaleString("en-US")}</text><text class="l" x="${100 + i * 200}" y="102" text-anchor="middle" font-size="17" font-weight="500">${label}</text>`)
    .join("");

  const max = Math.max(...s.last30);
  const bars = s.last30.map((n, i) => {
    const h = n > 0 ? Math.max(2, Math.round((n / max) * 72)) : 2;
    return `<rect class="b" style="animation-delay:${i * 20}ms" x="${40 + i * 24 + 4}" y="${232 - h}" width="16" height="${h}" rx="2" fill="${n > 0 ? "#58a6ff" : "#30363d"}"/>`;
  }).join("");

  let x = 40, lx = 40;
  const segs = s.langs.map((l, i) => {
    const w = (l.pct / 100) * 720;
    const r = `<rect class="g" style="animation-delay:${i * 80}ms" x="${x.toFixed(2)}" y="280" width="${w.toFixed(2)}" height="12" fill="${esc(l.color)}"/>`;
    x += w;
    return r;
  }).join("");
  const legend = s.langs.map((l) => {
    const txt = `${esc(l.name)} ${l.pct}%`;
    const out = `<circle cx="${lx + 5}" cy="321" r="5" fill="${esc(l.color)}"/><text class="l" x="${lx + 16}" y="326" font-size="17" font-weight="500">${txt}</text>`;
    lx += 16 + txt.length * 9.5 + 22; // shortcut: width estimated, not measured
    return out;
  }).join("");

  return `${head}<style>${css}</style><clipPath id="c"><rect x="40" y="280" width="720" height="12" rx="6"/></clipPath>${card}${metrics}` +
    `<text class="l" x="40" y="150" font-size="17" font-weight="500">Last 30 days</text>${bars}` +
    `<text class="l" x="40" y="268" font-size="17" font-weight="500">Top languages</text><g clip-path="url(#c)">${segs}</g>${legend}</svg>`;
}
