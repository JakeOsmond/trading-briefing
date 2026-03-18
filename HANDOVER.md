# Trading Covered — Session Handover (18 March 2026)

_Use this to resume work in a fresh Claude Code session. Paste or reference this file at the start._

---

## Project Overview

AI-powered daily trading briefing for HX Insurance. ~4,000-line Python pipeline running 23 investigation tracks against BigQuery, synthesised by GPT-5.4, cross-verified by Claude Sonnet, deployed daily at 05:00 UTC to Cloudflare Pages. Now includes Phase 0 Context Intelligence that reads Google Drive and auto-learns new context.

**Repo:** github.com/JakeOsmond/trading-briefing
**Live:** trading-covered.pages.dev (Cloudflare Zero Trust, @holidayextras.com Google OAuth)
**Context Manager:** trading-covered.pages.dev/context-manager.html

## Tech Stack

- Python 3.12 + OpenAI GPT-5.4 (pipeline) + Claude Sonnet (verification)
- Google BigQuery (`hx-data-production.commercial_finance`)
- Cloudflare Pages + Pages Functions + KV (verification + context state)
- GitHub Actions CI/CD (daily 05:00 UTC Mon-Fri)

## Key Files

| File | What |
|------|------|
| `agentic_briefing.py` | Main pipeline (~4,024 lines, core orchestration + Phase 0) |
| `domains/insurance/tracks.py` | 23 investigation track SQL definitions (1,106 lines) |
| `domains/insurance/baselines.py` | Baseline SQL queries — Phase 1 data extraction |
| `domains/insurance/prompts.py` | 4 LLM system prompts (analysis, follow-up, synthesis, schema) |
| `domains/insurance/config.yaml` | Domain contract: tables, models, thresholds, paths |
| `templates/dashboard.css` | Dashboard CSS (lintable, ESLint in CI) |
| `templates/dashboard.js` | Dashboard JS (lintable, node --check in CI) |
| `templates/dashboard-verify.js` | Verification + context removal JS |
| `templates/context-manager.css` | Context manager page styles |
| `templates/context-manager.js` | Context manager page JS (add/remove/preview) |
| `scripts/generate-context-manager.py` | Standalone context manager HTML generator |
| `scripts/inject-ask-context.sh` | Build script: injects schema into ask.js at deploy |
| `scripts/analyze-calibration.py` | Confidence calibration analysis |
| `scripts/track-contribution.py` | Track hit rate analysis |
| `functions/api/ask.js` | Interactive Q&A endpoint (680 lines) |
| `functions/api/verify.js` | Verification + context add/remove/delete API |
| `context/` | Business knowledge (universal/insurance/operational) |
| `context/operational/temporary-context.md` | Auto-expiring temp facts (7-day TTL) |
| `context/operational/current-market-events.md` | Iran conflict, partner dynamics, pricing |
| `docs/adding-a-domain.md` | Step-by-step guide for adding distribution/hotels |
| `tests/test_pipeline.py` | 26 tests (SQL, confidence, JSON, verification, HTML, config) |

## Architecture

7-phase pipeline:
0. **Context Intelligence** — Scan Drive (all shared files), extract facts, dual-model classify (gpt-5-mini vs gpt-4o-mini), dedup, auto-file permanent context, write temporary context with 7-day expiry, AI dedup cleanup
1. **Baseline** — Static SQL queries (trading, trends, funnel, web)
2. **Investigation Tracks** — 23 deterministic SQL tracks
3. **AI Analysis** — GPT identifies material movers (>£5k GP impact)
4. **Follow-ups** — Up to 10 iterative AI investigation rounds
5. **4b: Trends** — 90-day statistical confidence + holiday awareness
6. **4c: Verification** — Claude cross-checks each finding against SQL evidence (matched by driver name, not index)
7. **Synthesis** — Two-pass HTML + markdown generation

## Features Implemented (this session)

### Refactoring (from 8,129 → 4,024 lines)
- CSS/JS extracted to `templates/` (3,008 lines out)
- 4 system prompts extracted to `domains/insurance/prompts.py` (625 lines)
- Baseline SQL builders extracted to `domains/insurance/baselines.py` (179 lines)
- Investigation tracks extracted to `domains/insurance/tracks.py` (1,106 lines)
- Domain config contract (`config.yaml` + config loader)
- `--domain` CLI flag (default: insurance)
- `briefing.py` deleted (1,049 lines dead code)
- Model config abstraction (MODELS dict, 3 roles)

### Context Intelligence (Phase 0)
- Reads ALL Google Drive docs shared with the user (up to 100k chars each)
- Two-stage per doc: extract concrete facts (GPT-5.4), then classify each fact
- Dual-model verification: gpt-5-mini vs gpt-4o-mini independently classify, conservative consensus wins
- Permanent facts auto-filed to correct context file (GPT routes)
- Temporary facts written to `temporary-context.md` with 7-day expiry
- AI dedup pass cleans the full temp file every run (keeps earliest version of dupes)
- Per-line word-set dedup prevents duplicates at write time
- Travel Events Log sheet integration
- "What Trading Covered Learned Today" section on briefing with expandable subsections (Permanent on top, Temporary below)

### Context Manager Page (`/context-manager.html`)
- View all context files by category (Universal/Insurance/Operational)
- Click file headers to preview full content inline
- Remove AI-learned items (password-protected, persists via KV + localStorage)
- Add context manually (name + password required, stored in KV, processed next pipeline run)
- Pending adds visible to all users (fetched from KV on page load)
- Standalone generator script — deploys in ~1 min on any push (no full pipeline needed)

### Other Features
- node --check + ESLint for template JS in all 3 CI workflows
- HTML generation smoke test (11 assertions)
- Domain config validation tests (2 tests)
- Session-based verify auth (4h token, authenticate once)
- Chat FAB with welcome prompt and example questions
- Calibration analysis script + CI persists calibration.jsonl
- Track contribution analysis script
- Comprehensive schema docs (every field in both BQ tables)
- Verification pills matched by driver name (not sequential index)

## Known Issues / Active Items

1. **Read-only BigQuery credentials** — still using Jake's personal creds. Richard hasn't responded.
2. **KV fetch in CI** — Python Cloudflare REST API call gets 403. The CLOUDFLARE_API_TOKEN likely lacks KV read permissions. Need to either update the token scope or create a new token with "Workers KV Storage: Edit". The wrangler approach also doesn't work. Manual context adds from the site are stored in KV but the pipeline can't read them until this is fixed.
3. **Context Manager remove for permanent items** — works visually (localStorage hides them) but the actual context file edit only happens on next pipeline run. The KV removal request flow works for pending adds but permanent file edits are deferred.
4. **Phase 0 takes ~10 min** — 30 docs × 2 LLM calls for extraction + ~200 facts × 2 models for verification. Acceptable but slow.
5. **Travel Events Log** — now accessible (Jake shared the sheet). Some rows still classified as "raw data" by the extraction prompt. May need further tuning.

## Context Files Added This Session

### Universal (shared across all domains)
- `hx-group-structure.md` — Group BU structure
- `financial-waterfall.md` — Full Price → GP waterfall
- `reporting-conventions.md` — Standard abbreviations
- `transaction-mechanics.md` — Book date vs stay date, cancellations
- `travel-events.md` — External event categories, ancillary delay theory, Travel Events Log sheet ID

### Insurance
- `platforms-and-partners.md` — Fire Melon/Magenta, idol, Wizard, CTAs, ERGO, Collinson, WorldPay
- `ask-schema-prompt.txt` — Full schema for both BQ tables (every field documented)

### Operational
- `current-market-events.md` — Iran conflict impact, cruise dynamics, pricing, PPC, partners
- `temporary-context.md` — ~450 auto-expiring facts from Drive docs

## GitHub Secrets

OPENAI_API_KEY, ANTHROPIC_API_KEY, GCP_SERVICE_ACCOUNT_KEY, CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID, VERIFY_PASSWORD

## Cloudflare Setup

- Zero Trust: Google IdP + @holidayextras.com email policy
- Pages secrets: OPENAI_API_KEY, GCP_SERVICE_ACCOUNT_KEY, ANTHROPIC_API_KEY, VERIFY_PASSWORD
- KV namespace: `VERIFICATION_KV` (id: 45353e04656c415fa471dfc8e70260f7)
- KV stores: verification overrides, session tokens, pending context adds/removals

## Stakeholders

- **Jake Osmond** — Builder, daily user
- **David Norris** — Trading lead, wants scaling to parking/distribution
- **Jason Jack (Jay)** — Technology, PAI creator, technical advisor
- **Richard** — GCP/IAM (pending read-only credentials)
- **Dave Lee** — Helped with Cloudflare Zero Trust setup

## Scaling Vision

Insurance (current) → UK Distribution/Parking → Hotels/Lounges → Europe Trading.

**Monorepo architecture in place.** Adding a new domain: see `docs/adding-a-domain.md`.

David Norris's TradingUK repo (norrisnode1/TradingUK) has UK Distribution knowledge (1,164 lines, Draft v0.7) ready for `domains/distribution/`.

## Memory Files (persist across sessions)

Located at `~/.claude/projects/-Users-jake-osmond-tradingTeam/memory/`:
- `hx-trading-domain.md` — Domain knowledge
- `feedback_chart_yoy.md` — Charts must show YoY red/green bars
- `feedback_context_extraction.md` — Phase 0 must extract FACTS not summaries
- `project_tradinguk_david.md` — David's TradingUK repo context
- `project_context_update_feature.md` — Context update section + Drive auto-check
- `project_context_manager_spec.md` — Full context manager page spec

## Resume Prompt

Copy and paste this into a new Claude Code session to resume with the full BMAD party:

```
Read /Users/jake.osmond/tradingTeam/trading-briefing/HANDOVER.md — this is a comprehensive handover from a previous session on the Trading Covered project. Absorb everything in it.

Then load BMAD party mode. The full team needs to pick up where the previous session left off. Here is the context for each agent:

WINSTON (Architect): The codebase went from 8,129 → 4,024 lines via monorepo extraction. The architecture is now: core pipeline in agentic_briefing.py, domain-specific code in domains/insurance/ (tracks, baselines, prompts, config), templates extracted to templates/, context manager as standalone script. Phase 0 Context Intelligence scans Drive, extracts facts, dual-model classifies, auto-files. The KV integration for manual context adds is broken (403 on Cloudflare API — token permissions). This is the #1 technical blocker.

AMELIA (Dev): The KV fetch in CI uses Python + Cloudflare REST API but gets 403. The CLOUDFLARE_API_TOKEN is scoped for Pages deploys, not KV reads. Options: (1) Jake updates the token in GitHub secrets to include "Workers KV Storage: Edit", (2) use a Cloudflare Service Token instead, (3) use wrangler CLI (also failed — likely same token issue). The context manager JS is now a standalone template (templates/context-manager.js) — no more f-string escaping bugs. All JS validated by node --check in CI.

MURAT (Test): 26 tests pass. Coverage: SQL autocorrect (10), confidence (5), JSON parsing (5), verification verdicts (3), HTML smoke test (1), domain config (2). The HTML smoke test catches template loading failures. node --check + ESLint run on all template JS before every deploy. The dedup logic (both temp and permanent) uses per-line word-set comparison now — test with real data to verify the AI dedup cleanup step is effective.

MARY (Analyst): Phase 0 extracts ~200 facts from 30 Drive docs per run. Dual-model verification (gpt-5-mini vs gpt-4o-mini) catches classification disagreements. Temporary facts expire after 7 days. The AI dedup pass runs at the end of Phase 0 to clean the temp file. Calibration.jsonl is being collected — run scripts/analyze-calibration.py to check confidence accuracy. Run scripts/track-contribution.py to see which of the 23 tracks actually contribute to findings.

BOB (Scrum Master): Priority backlog for this session:
1. FIX: KV token permissions (blocks manual context add flow)
2. TEST: Full add/remove flow on context manager page end-to-end
3. MONITOR: Phase 0 fact quality and dedup effectiveness
4. CHASE: Richard on read-only BQ credentials (Jake said don't push today — check if it's been resolved)
5. PLAN: David's distribution domain (TradingUK repo at norrisnode1/TradingUK)

SALLY (UX): The context manager page is at /context-manager.html. It has file previews (click header), add form (name + password + text), remove buttons. The briefing has a "What Trading Covered Learned Today" collapsible section with permanent facts on top and temporary below. The Chat FAB (floating action button, bottom-right) opens the Ask Trading Covered panel with welcome prompts.

JOHN (PM): The product vision: Trading Covered should be self-improving. It reads Drive docs daily, extracts useful trading facts, and builds its own context. Users can add context manually via the Context Manager page. The next domain (UK Distribution/Parking) is ready architecturally — David Norris has 1,164 lines of domain knowledge in his TradingUK repo. The credential blocker (Richard) prevents scaling.

What would you like the team to work on?
```
