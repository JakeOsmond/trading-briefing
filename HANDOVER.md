# Trading Covered — Session Handover (20 March 2026)

_Use this to resume work in a fresh Claude Code session. Paste or reference this file at the start._

---

## Project Overview

AI-powered daily trading briefing for HX Insurance. ~4,400-line Python pipeline running 23 investigation tracks against BigQuery, synthesised by GPT-5.4, cross-verified by Claude Sonnet, deployed daily at 05:00 UTC to Cloudflare Pages. Includes Phase 0 Context Intelligence (reads Google Drive, auto-learns context) and a 4-stage Google Trends pipeline for Customer Search Intent.

**Repo:** github.com/JakeOsmond/trading-briefing
**Live:** trading-covered.pages.dev (Cloudflare Zero Trust, @holidayextras.com Google OAuth)
**Context Manager:** trading-covered.pages.dev/context-manager.html

## Tech Stack

- Python 3.12 + OpenAI GPT-5.4 (pipeline) + GPT-4.1-mini (trends/context) + Claude Sonnet (verification)
- Google BigQuery (`hx-data-production.commercial_finance`)
- Google Trends via pytrends (direct fetch, no Google Sheet intermediary)
- Cloudflare Pages + Pages Functions + KV (verification + context state)
- GitHub Actions CI/CD (daily 05:00 UTC Mon-Fri)

## Key Files

| File | What |
|------|------|
| `agentic_briefing.py` | Main pipeline (~4,387 lines, core orchestration + Phase 0 + Google Trends) |
| `domains/insurance/tracks.py` | 23 investigation track SQL definitions (1,106 lines) |
| `domains/insurance/baselines.py` | Baseline SQL queries — Phase 1 data extraction |
| `domains/insurance/prompts.py` | 4 LLM system prompts (analysis, follow-up, synthesis, schema) (656 lines) |
| `domains/insurance/config.yaml` | Domain contract: tables, models, thresholds, paths |
| `templates/dashboard.css` | Dashboard CSS (lintable, ESLint in CI) |
| `templates/dashboard.js` | Dashboard JS — trend charts, pill injection, driver interactions |
| `templates/dashboard-verify.js` | Verification + context removal JS |
| `templates/context-manager.css` | Context manager page styles |
| `templates/context-manager.js` | Context manager page JS (add/remove/preview) |
| `scripts/generate-context-manager.py` | Standalone context manager HTML generator |
| `functions/api/ask.js` | Interactive Q&A endpoint (680 lines) |
| `functions/api/verify.js` | Verification + context add/remove/delete API |
| `context/` | Business knowledge (universal/insurance/operational) |
| `context/operational/temporary-context.md` | Auto-expiring temp facts (7-day TTL, ~90 facts) |
| `context/operational/current-market-events.md` | Iran conflict, partner dynamics, pricing |
| `tests/test_pipeline.py` | 39 tests (SQL, confidence, JSON, verification, HTML, config, context) |

## Architecture

8-phase pipeline:
0. **Context Intelligence** — Scan Drive, extract facts with Material Impact Test, dual-model classify, dedup, auto-file
1. **Google Trends** — Fetch 11 base terms (5 insurance + 6 holiday), AI suggests 30 deep-dive terms, fetch those, generate narrative
2. **Baseline** — Static SQL queries (trading, trends, funnel, web) + Google Sheet market data
3. **Investigation Tracks** — 23 deterministic SQL tracks
4. **AI Analysis** — GPT identifies material movers (>£5k GP impact)
5. **Follow-ups** — Up to 10 iterative AI investigation rounds
6. **4b: Trends** — 90-day statistical confidence + holiday awareness
7. **4c: Verification** — Claude cross-checks each finding against SQL evidence
8. **Synthesis** — Two-pass HTML + markdown generation

## Features Implemented (this session — 19-20 March)

### Context Intelligence Tightening
- **Material Impact Test** on all extraction prompts — facts must CAUSE or EXPLAIN trading movements
- Extraction, classification, verify, and dedup prompts all explicitly skip: historical data points, booking stats, definitions, operational processes, document metadata
- Temp context cleaned from **520 → ~90 facts** (the pipeline re-added ~56 genuine facts on next run)
- 13 new tests for context filtering (39 total, all passing)

### Google Trends Integration (replaces Google Sheet)
- **4-stage pipeline**: base terms → AI deep-dive suggestion → fetch deep-dive → narrative
- 11 base terms: 5 insurance ("travel insurance", "holiday insurance", "annual travel insurance", "single trip travel insurance", "travel insurance comparison") + 6 holiday ("book holiday", "cheap flights", "package holiday", "all inclusive holiday", "summer holiday", "winter sun")
- GPT-4.1-mini picks top 3 insurance + top 3 holiday by YoY variance, suggests 5 follow-up terms each (30 total)
- All terms get clickable Google Trends deep links (2-year window, GB geo)
- GPT-4.1-mini generates a daily narrative summary → becomes the Customer Search Intent section content
- Narrative also feeds into the main trading analysis as daily context
- Only terms with >10% absolute YoY change included in narrative
- 24h local cache (.trends_cache/) to avoid rate limits
- Retry with exponential backoff (30/60/120s) on Google Trends 429 errors
- Inter-batch delay increased to 30s for shared CI IPs

### Driver Card UI Redesign
- **10-dot persistence infographic** replaces text badges — filled dots show how many of last 10 days the trend was present
- Dots colour-coded: coral=recurring (#FF8A91), amber=emerging (#FFB55F), teal=new (#5FFFF0)
- Label below dots: "8/10 days · Recurring"
- **Pill order locked**: persistence dots → confidence → verification (always all 3 present)
- Drivers without trend data get empty dots + "No data" + "Low confidence" default
- **Trend button moved** from pills to action row (between Ask and GBQ buttons), matching glass-morphism style
- Confidence and verification pills unchanged

### Other
- `pytrends` added to requirements.txt
- `.trends_cache/` added to .gitignore
- market-intelligence.md context file updated to reflect direct Google Trends source
- Context section UI tightened (smaller type, succinct intro)

## Known Issues / Active Items

1. **Google Trends 429 rate limiting** — First pipeline run got rate limited from GitHub Actions IP. Retry logic now in place (30/60/120s backoff). Second run (currently in progress) will test this. If it persists, may need a proxy or pre-cached data approach.
2. **Read-only BigQuery credentials** — Still using Jake's personal creds. Richard hasn't responded.
3. **KV fetch in CI** — Python Cloudflare REST API call gets 403. Token needs "Workers KV Storage: Edit" scope. Manual context adds from the site stored in KV but pipeline can't read them.
4. **Phase 0 takes ~11 min** — 30 docs × LLM calls. Acceptable but slow.
5. **Temp context growing again** — Pipeline added 56 new facts on the 19 March run. The Material Impact Test is much better but could potentially be even stricter.

## GitHub Secrets

OPENAI_API_KEY, ANTHROPIC_API_KEY, GCP_SERVICE_ACCOUNT_KEY, CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID, VERIFY_PASSWORD

## Cloudflare Setup

- Zero Trust: Google IdP + @holidayextras.com email policy
- Pages secrets: OPENAI_API_KEY, GCP_SERVICE_ACCOUNT_KEY, ANTHROPIC_API_KEY, VERIFY_PASSWORD
- KV namespace: `VERIFICATION_KV` (id: 45353e04656c415fa471dfc8e70260f7)

## Stakeholders

- **Jake Osmond** — Builder, daily user
- **David Norris** — Trading lead, wants scaling to parking/distribution
- **Jason Jack (Jay)** — Technology, PAI creator, technical advisor
- **Richard** — GCP/IAM (pending read-only credentials)

## Scaling Vision

Insurance (current) → UK Distribution/Parking → Hotels/Lounges → Europe Trading.
Monorepo architecture in place. Adding a new domain: see `docs/adding-a-domain.md`.
David Norris's TradingUK repo (norrisnode1/TradingUK) has UK Distribution knowledge ready.

## Resume Prompt

Copy and paste this into a new Claude Code session to resume:

```
Read /Users/jake.osmond/tradingTeam/trading-briefing/HANDOVER.md — this is a comprehensive handover from a previous session on the Trading Covered project. Absorb everything in it.

Then load BMAD party mode. The full team works together on everything — every response should include perspectives from the relevant agents. Archie (PAI) is an EQUAL member of the team, not the facilitator or main voice. All agents speak with equal weight.

Here is the context for each agent:

WINSTON (Architect): The pipeline is ~4,400 lines with 8 phases. Key recent addition: a 4-stage Google Trends pipeline (base terms → AI deep-dive → fetch → narrative) that replaces the old Google Sheet source. Google Trends gets 429 rate limited from GitHub Actions — retry logic with exponential backoff is in place but needs monitoring. The KV integration for manual context adds is still broken (403 token permissions).

AMELIA (Dev): The Google Trends integration fetches 11 base terms + 30 AI-suggested deep-dive terms directly via pytrends (2-year window, GB geo). GPT-4.1-mini generates the narrative that becomes the Customer Search Intent section. All terms get clickable Google Trends deep links. The driver cards now use a 10-dot persistence infographic (JS-rendered in initDriverTrends). The trend button moved from pills to the dig-buttons row. If Google Trends 429s persist, consider: (1) a proxy, (2) pre-caching data locally, or (3) running the fetch at a different time.

MURAT (Test): 39 tests pass. Coverage: SQL autocorrect (10), confidence (5), JSON parsing (5), verification (3), HTML smoke (1), domain config (2), context prompt assertions (8), dedup logic (3), context loading (2). The Google Trends functions are not unit tested yet — they depend on live API calls. Consider adding mock-based tests.

MARY (Analyst): Phase 0 now enforces a Material Impact Test — only facts that CAUSE or EXPLAIN trading movements are extracted. The temp context went from ~520 facts to ~90. The Google Trends narrative (GPT-4.1-mini) only includes terms with >10% YoY change. Calibration data is being collected in calibration.jsonl. Run scripts/analyze-calibration.py and scripts/track-contribution.py for quality analysis.

BOB (Scrum Master): Priority backlog:
1. MONITOR: Google Trends 429 retry — does the backoff work on next pipeline run?
2. FIX: KV token permissions (blocks manual context add flow)
3. MONITOR: Phase 0 fact quality — is 90 facts the right level or still too many?
4. PLAN: David's distribution domain (TradingUK repo at norrisnode1/TradingUK)
5. CHASE: Richard on read-only BQ credentials

SALLY (UX): Driver cards redesigned — 10-dot persistence infographic (coral/amber/teal), consistent pill order (dots → confidence → verification), trend button in action row. The context manager is at /context-manager.html. The briefing "What Trading Covered Learned Today" section has a succinct intro. The Chat FAB opens Ask Trading Covered.

JOHN (PM): Trading Covered is self-improving: reads Drive docs daily, extracts useful facts, fetches Google Trends, generates its own search intent narrative. The next domain (UK Distribution/Parking) is architecturally ready. The Google Trends integration is brand new — first successful run pending.

ARCHIE (PAI): Equal team member. Synthesises across agents, spots gaps, challenges assumptions. Has context on the full PAI infrastructure and Jake's preferences. Should contribute opinions on architecture, quality, and priorities — not just facilitate.

What would you like the team to work on?
```
