import { summarize, renderSvg, errorSvg, parseCalendar } from "../render.js";

// Same calendar visitors see on the profile (includes private counts); null keeps the GraphQL calendar.
async function profileCalendar() {
  try {
    const r = await fetch("https://github.com/users/achmf/contributions", { headers: { "User-Agent": "achmf-stats" } });
    return r.ok ? parseCalendar(await r.text()) : null;
  } catch {
    return null;
  }
}

const QUERY = `query { user(login:"achmf") {
  contributionsCollection { restrictedContributionsCount contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } } }
  repositories(ownerAffiliations:OWNER, isFork:false, privacy:PUBLIC, first:100) {
    totalCount nodes { languages(first:10, orderBy:{field:SIZE, direction:DESC}) { edges { size node { name color } } } }
  } } }`;

export default async function handler(req, res) {
  res.setHeader("Content-Type", "image/svg+xml; charset=utf-8");
  try {
    if (!process.env.GITHUB_TOKEN) throw new Error("no token");
    const calP = profileCalendar();
    const r = await fetch("https://api.github.com/graphql", {
      method: "POST",
      headers: { Authorization: `bearer ${process.env.GITHUB_TOKEN}`, "Content-Type": "application/json", "User-Agent": "achmf-stats" },
      body: JSON.stringify({ query: QUERY }),
    });
    const json = await r.json();
    if (!r.ok || json.errors || !json.data?.user) throw new Error("upstream");
    const cal = await calP;
    if (cal) json.data.user.contributionsCollection = { contributionCalendar: cal, restrictedContributionsCount: 0 };
    const svg = renderSvg(summarize(json.data, new Date()));
    res.setHeader("Cache-Control", "public, max-age=3600, s-maxage=21600, stale-while-revalidate=86400");
    res.status(200).send(svg);
  } catch {
    res.setHeader("Cache-Control", "no-store");
    res.status(503).send(errorSvg());
  }
}
