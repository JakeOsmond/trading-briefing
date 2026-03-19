# Market Intelligence Sources

The briefing system draws on several external and internal data sources:

- **Google Trends** (fetched directly via pytrends) — search intent for 11 terms: 5 insurance ("travel insurance", "holiday insurance", "annual travel insurance", "single trip travel insurance", "travel insurance comparison") and 6 holiday ("book holiday", "cheap flights", "package holiday", "all inclusive holiday", "summer holiday", "winter sun"). 2-year rolling window with YoY comparison. Deep links to Google Trends included for each term.
- **AI Insights** (Google Sheet tab) — pre-generated strategic insights, refreshed regularly.
- **Dashboard Metrics** — headline market metrics (direction, value, description).
- **Market Demand Summary** — quarterly demand indices (UK passengers, visits abroad, aviation).
- **Spike Log** — known anomalies and structural breaks (COVID, Thomas Cook collapse, etc.).
- **Travel Events Log** (Google Sheet `1lqLYxLTnfFyBSsIPRyPr8vpr25S7Fhz3p-nlWNToZpU`) — structured log of external events (geopolitical, strikes, holidays, weather) that affect trading. Used to annotate YoY variances.
- **Internal Google Drive docs** — recent pricing changes, campaign briefs, product releases.

When the briefing cites external context, it should always attribute the source (e.g. "According to Google Trends data..." or a link to the article).
