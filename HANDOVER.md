# Trading Covered — Session Handover (17 March 2026)

_Use this to resume work in a fresh Claude Code session. Paste or reference this file at the start._

---

## Project Overview

AI-powered daily trading briefing for HX Insurance. 8,100+ line Python pipeline running 23 investigation tracks against BigQuery, synthesised by GPT-5.4, cross-verified by Claude Sonnet, deployed daily at 05:00 UTC to Cloudflare Pages.

**Repo:** github.com/JakeOsmond/trading-briefing
**Live:** trading-covered.pages.dev (Cloudflare Zero Trust, @holidayextras.com Google OAuth)
**Current tag:** `alpha-v2`

## Tech Stack

- Python 3.12 + OpenAI GPT-5.4 (pipeline) + Claude Sonnet (verification)
- Google BigQuery (`hx-data-production.commercial_finance`)
- Cloudflare Pages + Pages Functions + KV (verification state)
- GitHub Actions CI/CD (daily 05:00 UTC Mon-Fri)

## Key Files

| File | What |
|------|------|
| `agentic_briefing.py` | Main pipeline (~4,050 lines, core orchestration) |
| `domains/insurance/tracks.py` | 23 investigation track SQL definitions (1,106 lines) |
| `domains/insurance/config.yaml` | Domain contract: tables, models, thresholds, paths |
| `templates/dashboard.css` | Extracted CSS (1,447 lines, lintable) |
| `templates/dashboard.js` | Extracted JS (1,421 lines, lintable) |
| `templates/dashboard-verify.js` | Verification JS (143 lines) |
| `functions/api/ask.js` | Interactive Q&A endpoint (680 lines) |
| `functions/api/verify.js` | Human verification endpoint (KV-backed) |
| `context/` | Business knowledge folder (universal/insurance/operational) |
| `context/insurance/ask-schema-prompt.txt` | Schema prompt for ask.js (injected at deploy) |
| `context/insurance/ask-business-prompt.txt` | Business rules prompt for ask.js (injected at deploy) |
| `scripts/inject-ask-context.sh` | Build script: generates ask.js context at deploy time |
| `SYNTHESIS_TEMPLATE.md` | Output format and tone rules |
| `tests/test_pipeline.py` | 23 tests (SQL autocorrect, confidence, JSON parsing, verification) |
| `RUNBOOK.md` | Operational runbook for when things go wrong |
| `calibration.jsonl` | Confidence vs verification tracking (appended each run) |
| `wrangler.toml` | Cloudflare config + KV namespace binding |

## Architecture

6-phase pipeline:
1. **Baseline** — Static SQL queries (trading, trends, funnel, web)
2. **Investigation Tracks** — 23 deterministic SQL tracks
3. **AI Analysis** — GPT identifies material movers (>£5k GP impact)
4. **Follow-ups** — Up to 10 iterative AI investigation rounds
5. **4b: Trends** — 90-day statistical confidence + holiday awareness
6. **4c: Verification** — Claude cross-checks each finding against SQL evidence
7. **Synthesis** — Two-pass HTML + markdown generation

## Features Implemented

- 5-tier confidence system (Very High → Very Low) with z-scores + persistence
- Holiday awareness (gov.uk bank holidays API + algorithmic school holidays)
- Cross-model verification (OpenAI generates, Claude verifies, human overrides via KV)
- Verification pills with hover tooltips, verify/remove/revert buttons (password-protected)
- Interactive Q&A with BigQuery, chart generation, SQL evidence
- Staleness banner (>20 hours → red warning with re-run link)
- Phase timing in pipeline logs
- Data freshness gate (checks BigQuery partition before running)
- HX Tracker analytics integration
- Confidence calibration logging (calibration.jsonl)
- 23 automated tests in CI (run before every deploy)
- Context folder split for domain migration readiness
- Module boundary annotations (DOMAIN-AGNOSTIC vs INSURANCE-SPECIFIC)

## GitHub Secrets

OPENAI_API_KEY, ANTHROPIC_API_KEY, GCP_SERVICE_ACCOUNT_KEY, CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID, VERIFY_PASSWORD

## Cloudflare Setup

- Zero Trust: Google IdP + @holidayextras.com email policy
- Pages secrets: OPENAI_API_KEY, GCP_SERVICE_ACCOUNT_KEY, ANTHROPIC_API_KEY, VERIFY_PASSWORD
- KV namespace: `VERIFICATION_KV` (id: 45353e04656c415fa471dfc8e70260f7)
- KV binding set in dashboard under Workers & Pages → trading-covered → Settings → Bindings

## Known Issues / Open Items

1. **Read-only BigQuery credentials** — ticket raised with Richard, still using Jake's personal creds
2. ~~**HTML template extraction**~~ — **DONE** (PR #1). CSS/JS extracted to `templates/`. See `context/operational/template-extraction-plan.md`.
3. ~~**Schema duplication**~~ — **DONE** (PR #1). ask.js now imports from generated file. Edit `context/insurance/ask-schema-prompt.txt` for schema changes.
4. **gpt-5.4 model name** — may be internal/early-access. Jay confirmed it's valid for HX's API key. Model names now configurable in `domains/insurance/config.yaml`.
5. **David's TradingUK repo** — norrisnode1/TradingUK has 1,164-line UK Distribution knowledge base (Draft v0.7). Ready to feed into `domains/distribution/` when the time comes.

## Stakeholders

- **Jake Osmond** — Builder, daily user
- **David Norris** — Trading lead, wants scaling to parking/distribution
- **Jason Jack (Jay)** — Technology, PAI creator, technical advisor
- **Richard** — GCP/IAM (pending read-only credentials)
- **Dave Lee** — Helped with Cloudflare Zero Trust setup

## Scaling Vision

Insurance (current) → UK Distribution/Parking → Hotels/Lounges → Europe Trading.

**Monorepo architecture now in place** (PR #1). Adding a new domain:
1. Create `domains/{name}/config.yaml` (tables, models, thresholds)
2. Create `domains/{name}/tracks.py` (investigation SQL for that domain's BigQuery tables)
3. Create `context/{name}/` (domain-specific knowledge files, reuse `universal/`)
4. Add `context/{name}/ask-schema-prompt.txt` + `ask-business-prompt.txt` for Q&A
5. Add per-domain wrangler config and GitHub Actions workflow

David Norris's TradingUK repo (norrisnode1/TradingUK) has the UK Distribution domain knowledge ready to be structured into `domains/distribution/`.

## PAI Config

- PAI name: **Archie** (set in `~/.claude/settings.json` → `daidentity.name`)
- BMAD installed in project (`_bmad/` folder) — party mode available
- PAI project registered at `~/.claude/PAI/USER/PROJECTS/trading-covered.md`

## Archie + BMAD

Archie (PAI) loads automatically every session via `~/.claude/settings.json` hooks — no setup needed. BMAD is installed in the project (`_bmad/` folder) and party mode is always available. In party mode, Archie participates alongside the BMAD agents (Mary, Winston, Amelia, John, Bob, Murat, Sally) as the voice with full project history and Algorithm-grade analysis.

## Resume Prompt

Copy and paste this into a new Claude Code session:

```
Read /Users/jake.osmond/tradingTeam/trading-briefing/HANDOVER.md — this is a handover from a previous session on the Trading Covered project. It contains full project context, architecture, features implemented, known issues, and stakeholder info. Use this as your working knowledge for the session. Archie (PAI) and BMAD party mode are both available. What would you like to work on?
```
