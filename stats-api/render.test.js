import test from "node:test";
import assert from "node:assert/strict";
import { summarize, renderSvg, errorSvg, parseCalendar } from "./render.js";

const TODAY = new Date("2026-11-23T12:00:00Z");
const iso = (n) => new Date(TODAY.getTime() - n * 864e5).toISOString().slice(0, 10);

// counts[i] = contributions i days ago (index 0 = today); 40 days total
function fixture(counts) {
  const days = counts.map((c, i) => ({ date: iso(i), contributionCount: c })).reverse();
  const weeks = [];
  for (let i = 0; i < days.length; i += 7) weeks.push({ contributionDays: days.slice(i, i + 7) });
  const lang = (name, color, size) => ({ size, node: { name, color } });
  return {
    user: {
      contributionsCollection: { contributionCalendar: { totalContributions: 123, weeks } },
      repositories: {
        totalCount: 9,
        nodes: [
          { languages: { edges: [lang("JavaScript", "#f1e05a", 600), lang("C++ & <Co>", null, 100)] } },
          { languages: { edges: [lang("Python", "#3572A5", 200), lang("HTML", "#e34c26", 50), lang("CSS", "#563d7c", 30), lang("Go", "#00ADD8", 20)] } },
        ],
      },
    },
  };
}
// today=0, yesterday..4 days ago active (4 days), gap, then 3-day run, gap, then 10-day run
const base = [0, 1, 2, 1, 1, 0, 1, 1, 1, 0, ...Array(10).fill(2), ...Array(20).fill(0)];

test("streak: today empty counts from yesterday", () => {
  const s = summarize(fixture(base), TODAY);
  assert.equal(s.current, 4);
  assert.equal(s.longest, 10);
  assert.equal(s.total, 123);
  assert.equal(s.repos, 9);
});

test("total adds private (restricted) contributions", () => {
  const f = fixture(base);
  f.user.contributionsCollection.restrictedContributionsCount = 567;
  assert.equal(summarize(f, TODAY).total, 123 + 567);
});

test("streak: today active includes today", () => {
  const s = summarize(fixture([3, ...base.slice(1)]), TODAY);
  assert.equal(s.current, 5);
});

test("last30 has 30 entries, oldest first, ending today", () => {
  const s = summarize(fixture([5, ...base.slice(1)]), TODAY);
  assert.equal(s.last30.length, 30);
  assert.equal(s.last30[29], 5);
});

test("langs: top 5, pct sums to 100, null color falls back", () => {
  const s = summarize(fixture(base), TODAY);
  assert.equal(s.langs.length, 5);
  const sum = s.langs.reduce((a, l) => a + l.pct, 0);
  assert.ok(Math.abs(sum - 100) <= 1, `sum ${sum}`);
  assert.equal(s.langs[0].name, "JavaScript");
  assert.equal(s.langs.find((l) => l.name.startsWith("C++")).color, "#8b949e");
});

test("svg: root, no script, numbers, escaping, animation rules", () => {
  const svg = renderSvg(summarize(fixture(base), TODAY));
  assert.match(svg, /^<svg [^>]*viewBox="0 0 800 360"/);
  assert.match(svg, /<\/svg>\s*$/);
  assert.doesNotMatch(svg, /<script|foreignObject|href=|<image/i);
  for (const n of ["123", "4", "10", "9"]) assert.match(svg, new RegExp(`>${n}<`));
  assert.ok(svg.includes("C++ &amp; &lt;Co&gt;"));
  assert.match(svg, /prefers-reduced-motion:reduce/);
  assert.match(svg, /font-weight:700/);
  assert.match(svg, /font-weight:500/);
});

test("svg: min font-size * 343/800 >= 7", () => {
  for (const svg of [renderSvg(summarize(fixture(base), TODAY)), errorSvg()]) {
    const sizes = [...svg.matchAll(/font-size[:=]"?(\d+(?:\.\d+)?)/g)].map((m) => +m[1]);
    assert.ok(sizes.length > 0);
    assert.ok(Math.min(...sizes) * 343 / 800 >= 7, `min ${Math.min(...sizes)}`);
  }
});

test("errorSvg is generic", () => {
  const e = errorSvg();
  assert.match(e, /Stats unavailable/);
  assert.doesNotMatch(e, /<script/);
});

test("streak number is yellow (no CSS fill override) and thousands are separated", () => {
  const f = fixture(base);
  f.user.contributionsCollection.contributionCalendar.totalContributions = 1234;
  const svg = renderSvg(summarize(f, TODAY));
  assert.doesNotMatch(svg.match(/\.n\{[^}]*\}/)[0], /fill:/);
  assert.match(svg, /<text class="n"[^>]*fill="#facc15"[^>]*>4<\/text>/);
  assert.equal((svg.match(/<text class="n"[^>]*fill="#f0f6fc"/g) || []).length, 3);
  assert.match(svg, />1,234</);
});

test("parseCalendar reads public profile calendar incl. private counts", () => {
  const html = `<h2>1,038
      contributions
        in the last year</h2>
<td data-date="2026-11-22" id="contribution-day-component-0-52" class="ContributionCalendar-day"></td>
<td data-date="2026-11-23" id="contribution-day-component-1-52" class="ContributionCalendar-day"></td>
<tool-tip for="contribution-day-component-0-52" class="sr-only">No contributions on November 22nd.</tool-tip>
<tool-tip for="contribution-day-component-1-52" class="sr-only">1,204 contributions on November 23rd.</tool-tip>`;
  const c = parseCalendar(html);
  assert.equal(c.totalContributions, 1038);
  assert.deepEqual(c.weeks[0].contributionDays, [
    { date: "2026-11-22", contributionCount: 0 },
    { date: "2026-11-23", contributionCount: 1204 },
  ]);
});

test("parseCalendar returns null on unexpected markup", () => {
  assert.equal(parseCalendar("<html>nothing</html>"), null);
});
