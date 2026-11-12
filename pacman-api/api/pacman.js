import { ArcadeRenderer } from 'pacman-contribution-graph';

// Serves an animated Pac-Man contribution graph for achmf. ?theme=dark for the dark variant.
export default async function handler(req, res) {
	const gameTheme = req.query.theme === 'dark' ? 'github-dark' : 'github';
	try {
		const svg = await new Promise((resolve, reject) => {
			new ArcadeRenderer({
				game: 'pacman',
				platform: 'github',
				username: 'achmf', // fixed on purpose so this endpoint is not an open generator
				gameTheme,
				showMonthLabels: true,
				githubSettings: process.env.GITHUB_TOKEN ? { accessToken: process.env.GITHUB_TOKEN } : undefined,
				svgCallback: resolve
			})
				.start()
				.catch(reject);
		});
		// The generator returns an empty game when the contribution fetch is rate limited; don't let caches keep that.
		if (svg.includes('<frames>0<')) throw new Error('empty game (contribution fetch failed)');
		res.setHeader('Content-Type', 'image/svg+xml');
		res.setHeader('Cache-Control', 'public, max-age=3600, s-maxage=43200, stale-while-revalidate=86400');
		res.status(200).send(svg);
	} catch (error) {
		res.setHeader('Cache-Control', 'no-store');
		res.status(503).send(String(error?.message ?? error));
	}
}
