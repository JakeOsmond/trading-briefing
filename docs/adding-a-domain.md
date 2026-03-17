# Adding a New Domain to Trading Covered

This guide walks through adding a new business domain (e.g., UK Distribution, Hotels) to the Trading Covered pipeline.

## Prerequisites

- BigQuery tables for the new domain (know the project, dataset, table names)
- Domain knowledge (what metrics matter, how to decompose GP, what dimensions to drill by)
- A domain expert to validate the investigation tracks and synthesis output

## Step 1: Create the domain folder

```
domains/{domain_name}/
├── __init__.py          # Empty file
├── config.yaml          # Domain configuration contract
├── tracks.py            # Investigation track SQL definitions
├── baselines.py         # Baseline SQL queries (Phase 1)
└── prompts.py           # LLM system prompts
```

Copy `domains/insurance/` as a starting point. Replace all insurance-specific content.

## Step 2: config.yaml

The config defines everything the pipeline needs to know about this domain.

```yaml
domain: distribution              # Domain identifier (matches folder name)
display_name: "UK Distribution"   # Human-readable name for the dashboard

# BigQuery
bq_project: hx-data-production    # GCP project ID
tables:
  policies: "hx-data-production.dataset.bookings_table"   # Primary transaction table
  web: "hx-data-production.dataset.web_sessions_table"     # Web analytics table

# Market intelligence (optional Google Sheet)
market_sheet_id: "your-sheet-id-here"

# Model assignments
models:
  analyst: "gpt-5.4"              # Main reasoning model
  verifier: "claude-sonnet-4-20250514"  # Cross-verification model
  lightweight: "gpt-5-mini"       # Web search, fallback tasks

# Materiality threshold — findings below this GP impact are filtered out
materiality_gp_impact: 5000       # £5k

# Module paths
tracks_module: "domains.distribution.tracks"
context_path: "context"

# Output
synthesis_template: "SYNTHESIS_TEMPLATE.md"
cloudflare_project: "trading-covered-distribution"

# Pipeline settings
max_investigation_loops: 10
```

**Required fields:** domain, bq_project, tables, models, materiality_gp_impact, tracks_module

## Step 3: tracks.py

Define investigation track SQL queries. Each track compares This Year vs Last Year.

```python
def build_investigation_tracks(dp, policies_table, web_table):
    """Build investigation track SQL queries.

    Args:
        dp: Date params dict (yesterday, week_start, month_start, etc. + LY equivalents)
        policies_table: Fully qualified BQ table name for transactions
        web_table: Fully qualified BQ table name for web analytics

    Returns:
        dict[track_id] -> {name: str, desc: str, sql: str}
    """
    P = policies_table
    W = web_table
    tracks = {}

    tracks['example_track'] = {
        'name': 'Revenue by Channel',
        'desc': 'GP decomposition by distribution channel',
        'sql': f"""
            SELECT 'TY' AS yr, channel, SUM(revenue) AS gp
            FROM {P}
            WHERE date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
            GROUP BY channel
            UNION ALL
            SELECT 'LY', channel, SUM(revenue)
            FROM {P}
            WHERE date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
            GROUP BY channel
        """
    }

    return tracks
```

**Tips:**
- Every track should have TY/LY comparison (UNION ALL pattern)
- Use `SUM()` not `COUNT(*)` for counts — check your domain's counting rules
- Start with 5-10 tracks, add more as you learn what surfaces useful findings
- The pipeline auto-retries failed SQL up to 25 times with AI-assisted fixes

## Step 4: baselines.py

Define the Phase 1 baseline queries that run before investigation tracks.

```python
def get_tables(bq_project):
    """Return fully qualified table names."""
    return {
        "policies": f"`{bq_project}.dataset.bookings_table`",
        "web": f"`{bq_project}.dataset.web_sessions_table`",
    }

POLICIES_TABLE = None
WEB_TABLE = None

def init_tables(bq_project):
    global POLICIES_TABLE, WEB_TABLE
    tables = get_tables(bq_project)
    POLICIES_TABLE = tables["policies"]
    WEB_TABLE = tables["web"]
    return POLICIES_TABLE, WEB_TABLE

def get_date_params(run_date):
    """Return date params dict. Same interface as insurance — copy and adjust."""
    # ... (copy from insurance, adjust if needed)

def build_baseline_trading_sql(dp):
    """Weekly trading summary — GP, volume, splits."""
    # ...

def build_baseline_trend_sql(dp):
    """14-day daily TY trend for the chart."""
    # ...
```

## Step 5: prompts.py

Write LLM system prompts that tell the AI about this domain.

```python
from textwrap import dedent

def build_prompts(trading_context):
    """Build system prompts. Returns dict: schema, analysis, follow_up, synthesis."""

    SCHEMA_KNOWLEDGE = dedent("""\
    ## BIGQUERY TABLE SCHEMAS
    ### `your.table.name`
    Key columns: ...
    """)

    ANALYSIS_SYSTEM = dedent("""\
    You are an expert autonomous {domain} trading analyst...
    """) + SCHEMA_KNOWLEDGE + trading_context

    # ... FOLLOW_UP_SYSTEM, SYNTHESIS_SYSTEM

    return {
        "schema": SCHEMA_KNOWLEDGE,
        "analysis": ANALYSIS_SYSTEM,
        "follow_up": FOLLOW_UP_SYSTEM,
        "synthesis": SYNTHESIS_SYSTEM,
    }
```

## Step 6: Context files

Create `context/{domain_name}/` with domain knowledge:

```
context/
├── universal/           # SHARED — keep as-is
│   ├── trading-framework.md
│   ├── yoy-methodology.md
│   ├── metrics-guide.md
│   └── financial-year.md
├── {domain_name}/       # NEW — domain-specific
│   ├── schema-knowledge.md
│   ├── ask-schema-prompt.txt    # For ask.js injection
│   └── ask-business-prompt.txt  # For ask.js injection
└── operational/         # Adjust as needed
```

## Step 7: Deploy configuration

1. Update `scripts/inject-ask-context.sh` call in CI workflows to pass the domain name
2. Create a new wrangler.toml or Cloudflare Pages project for the domain
3. Add domain-specific GitHub Actions secrets if needed (different GCP project, etc.)

## Step 8: Test locally

```bash
python agentic_briefing.py --domain distribution --date 2026-03-17
```

Check that:
- All tracks execute without SQL errors
- The AI analysis identifies meaningful findings
- The synthesis reads naturally for the domain
- The HTML dashboard renders correctly

## Reference: Insurance domain structure

```
domains/insurance/
├── __init__.py
├── config.yaml          # 39 lines
├── tracks.py            # 1,106 lines (23 tracks)
├── baselines.py         # 197 lines (5 baseline queries)
└── prompts.py           # 650 lines (4 system prompts)
```
