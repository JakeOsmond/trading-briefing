#!/usr/bin/env python3
"""
HX Insurance Trading — Agentic Morning Briefing

An autonomous investigation loop:
1. Pulls baseline trading, web, and market data
2. Sends to GPT with tool-use capabilities (SQL, sheets, web search, drive)
3. GPT investigates iteratively — digging deeper where it finds impact
4. Loop continues until nothing new worth investigating
5. Final synthesis: a focused 1-pager on REAL impact drivers only
"""

import os
import sys
import json
import argparse
import datetime
from datetime import date, timedelta
from pathlib import Path
from textwrap import dedent

import openai
import markdown
import google.auth
import google.auth.transport.requests
from google.cloud import bigquery
from googleapiclient.discovery import build

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

def _load_env():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

_load_env()

# Load trading context file (business knowledge for AI prompts)
def _load_trading_context():
    ctx_path = Path(__file__).parent / "trading_context.md"
    if ctx_path.exists():
        return ctx_path.read_text()
    return ""

TRADING_CONTEXT = _load_trading_context()

BQ_PROJECT = "hx-data-production"
MARKET_SHEET_ID = "1RUasLdbB9OiHPJzQClglC7aY5KMH4P-dnzk4v_h-tsg"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL = "gpt-5.4"
BROWSER = "Arc"
MAX_INVESTIGATION_LOOPS = 10

# ---------------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------------

def get_credentials():
    creds, _ = google.auth.default(scopes=[
        "https://www.googleapis.com/auth/bigquery",
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ])
    creds.refresh(google.auth.transport.requests.Request())
    return creds

CREDS = None
BQ_CLIENT = None
SHEETS_SVC = None
DRIVE_SVC = None

def init_services():
    global CREDS, BQ_CLIENT, SHEETS_SVC, DRIVE_SVC
    CREDS = get_credentials()
    BQ_CLIENT = bigquery.Client(project=BQ_PROJECT, credentials=CREDS)
    SHEETS_SVC = build("sheets", "v4", credentials=CREDS, cache_discovery=False)
    DRIVE_SVC = build("drive", "v3", credentials=CREDS, cache_discovery=False)


# ---------------------------------------------------------------------------
# TOOL IMPLEMENTATIONS — these are what GPT can call
# ---------------------------------------------------------------------------

def _autocorrect_sql(sql: str) -> tuple[str, list[str]]:
    """Fix common SQL mistakes instead of rejecting. Returns (corrected_sql, warnings)."""
    import re, calendar
    warnings = []
    corrected = sql
    upper = corrected.upper()

    if "INSURANCE_POLICIES_NEW" in upper:
        # Fix COUNT(*) → SUM(policy_count)
        if re.search(r'\bCOUNT\s*\(\s*\*\s*\)', corrected, re.IGNORECASE):
            corrected = re.sub(r'\bCOUNT\s*\(\s*\*\s*\)', 'SUM(policy_count)', corrected, flags=re.IGNORECASE)
            warnings.append("Auto-corrected COUNT(*) → SUM(policy_count)")
        # Fix COUNT(DISTINCT policy_id) → SUM(policy_count)
        if re.search(r'\bCOUNT\s*\(\s*DISTINCT\s+policy_id\s*\)', corrected, re.IGNORECASE):
            corrected = re.sub(r'\bCOUNT\s*\(\s*DISTINCT\s+policy_id\s*\)', 'SUM(policy_count)', corrected, flags=re.IGNORECASE)
            warnings.append("Auto-corrected COUNT(DISTINCT policy_id) → SUM(policy_count)")
        # Fix COUNT(policy_id) → SUM(policy_count)
        if re.search(r'\bCOUNT\s*\(\s*policy_id\s*\)', corrected, re.IGNORECASE):
            corrected = re.sub(r'\bCOUNT\s*\(\s*policy_id\s*\)', 'SUM(policy_count)', corrected, flags=re.IGNORECASE)
            warnings.append("Auto-corrected COUNT(policy_id) → SUM(policy_count)")
        # Fix AVG(col) → SUM(CAST(col AS FLOAT64))/NULLIF(SUM(policy_count),0)
        # Handle nested parens like AVG(CAST(x AS FLOAT64)) by counting paren depth
        avg_pattern = re.compile(r'\bAVG\s*\(', re.IGNORECASE)
        offset = 0
        while True:
            m = avg_pattern.search(corrected, offset)
            if not m:
                break
            start = m.start()
            paren_start = m.end() - 1  # position of the opening (
            depth = 1
            i = paren_start + 1
            while i < len(corrected) and depth > 0:
                if corrected[i] == '(':
                    depth += 1
                elif corrected[i] == ')':
                    depth -= 1
                i += 1
            if depth == 0:
                inner = corrected[paren_start + 1:i - 1].strip()
                old_text = corrected[start:i]
                # If inner already has CAST(... AS FLOAT64), don't double-wrap
                if re.search(r'CAST\s*\(.+AS\s+FLOAT64\s*\)', inner, re.IGNORECASE):
                    new_text = f"SUM({inner}) / NULLIF(SUM(policy_count), 0)"
                else:
                    new_text = f"SUM(CAST({inner} AS FLOAT64)) / NULLIF(SUM(policy_count), 0)"
                corrected = corrected[:start] + new_text + corrected[i:]
                warnings.append(f"Auto-corrected {old_text[:60]} → SUM/NULLIF pattern")
                offset = start + len(new_text)
            else:
                offset = m.end()
        # Fix EXTRACT(DATE FROM transaction_date)
        if re.search(r'EXTRACT\s*\(\s*DATE\s+FROM\s+transaction_date\s*\)', corrected, re.IGNORECASE):
            corrected = re.sub(r'EXTRACT\s*\(\s*DATE\s+FROM\s+transaction_date\s*\)', 'transaction_date', corrected, flags=re.IGNORECASE)
            warnings.append("Auto-corrected EXTRACT(DATE FROM transaction_date) → transaction_date")

    # Fix invalid dates (e.g. Feb 29 in non-leap year)
    for m in re.finditer(r"'(\d{4})-(\d{2})-(\d{2})'", corrected):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            date(y, mo, d)
        except ValueError:
            max_day = calendar.monthrange(y, mo)[1]
            fixed = f"{y:04d}-{mo:02d}-{min(d, max_day):02d}"
            corrected = corrected.replace(m.group(0), f"'{fixed}'")
            warnings.append(f"Auto-corrected invalid date '{m.group(0)}' → '{fixed}'")

    return corrected, warnings


def _autofix_track_sql(sql: str, error_msg: str) -> str:
    """Attempt to auto-fix SQL based on the BQ error message. Returns fixed SQL or original."""
    import re
    fixed = sql

    # Type mismatch on certificate_id join (INT64 vs STRING)
    if "INT64, STRING" in error_msg or "STRING, INT64" in error_msg:
        # Find joins where certificate_id types mismatch and add CAST
        # Pattern: p.certificate_id = X.certificate_id (where p is policies with INT)
        fixed = re.sub(
            r'(\w+)\.certificate_id\s*=\s*(\w+)\.certificate_id',
            lambda m: f'CAST({m.group(1)}.certificate_id AS STRING) = {m.group(2)}.certificate_id',
            fixed
        )

    # Column not found errors
    col_match = re.search(r'Unrecognized name:\s*(\w+)', error_msg)
    if col_match:
        bad_col = col_match.group(1)
        # Common column name fixes
        col_fixes = {
            'commission': 'total_paid_commission_value',
            'gross_premium_written': 'total_gross_inc_ipt',
            'gross_underwriter_cost': 'total_net_to_underwriter_inc_gadget',
            'discount_applied': 'total_discount_value',
            'is_renewal': "distribution_channel = 'Renewals'",
            'cover_level': 'cover_level_name',
            'medical_score_band': 'max_medical_score_grouped',
            'product_name': 'product',
        }
        if bad_col in col_fixes:
            fixed = fixed.replace(bad_col, col_fixes[bad_col])

    # Ambiguous column reference — qualify with table alias
    amb_match = re.search(r'Column name (\w+) is ambiguous', error_msg)
    if amb_match:
        # Can't reliably fix without knowing context, but try common ones
        pass

    return fixed


def _ai_fix_sql(sql: str, error_msg: str) -> str:
    """Use AI to fix a SQL query that failed, with full schema context."""
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=MODEL,
            max_completion_tokens=2048,
            messages=[
                {"role": "system", "content": f"""You are a BigQuery SQL expert. Fix the failing SQL query.
You have FULL knowledge of the table schemas:

{SCHEMA_KNOWLEDGE}

RULES:
- Output ONLY the fixed SQL query, nothing else — no markdown, no explanation
- Preserve the original intent of the query
- Fix the specific error described
- Use correct column names from the schema above
- SUM(policy_count) for counts, NEVER COUNT(*)
- SUM(CAST(col AS FLOAT64)) / NULLIF(SUM(policy_count), 0) for averages, NEVER AVG()
"""},
                {"role": "user", "content": f"""This SQL query failed:

```sql
{sql}
```

Error message:
{error_msg}

Fix it and return ONLY the corrected SQL."""}
            ],
        )
        fixed = response.choices[0].message.content or ""
        # Strip markdown code fences if present
        fixed = re.sub(r'^```(?:sql)?\s*\n?', '', fixed.strip())
        fixed = re.sub(r'\n?```\s*$', '', fixed.strip())
        return fixed.strip()
    except Exception as e:
        print(f"    ⚠️ AI SQL fix failed: {e}")
        return sql


def tool_run_sql(sql: str) -> str:
    """Execute a SQL query against BigQuery and return results as JSON. Auto-retries on error."""
    corrected, warnings = _autocorrect_sql(sql)
    for w in warnings:
        print(f"    ⚠️  {w}")
    if corrected != sql:
        sql = corrected

    max_retries = 25
    current_sql = sql
    used_ai_fix = False
    for attempt in range(1, max_retries + 1):
        try:
            print(f"    🔍 Running SQL: {current_sql[:120]}...")
            job = BQ_CLIENT.query(current_sql)
            rows = [dict(r) for r in job.result()]
            result = json.dumps(rows[:200], indent=2, default=str)
            if len(rows) > 200:
                result += f"\n... ({len(rows)} total rows, showing first 200)"
            if warnings:
                result = "⚠️ SQL was auto-corrected: " + "; ".join(warnings) + "\n\n" + result
            if used_ai_fix:
                result = "🤖 SQL was AI-corrected after error\n\n" + result
            return result
        except Exception as e:
            error_msg = str(e)
            if attempt < max_retries:
                # Try deterministic fix first
                fixed = _autofix_track_sql(current_sql, error_msg)
                if fixed != current_sql:
                    print(f"    🔧 Auto-fixing SQL error and retrying ({attempt}/{max_retries})...")
                    current_sql = fixed
                    continue
                # If deterministic fix didn't change anything, try AI fix
                print(f"    🤖 Deterministic fix failed — asking AI to fix SQL ({attempt}/{max_retries})...")
                ai_fixed = _ai_fix_sql(current_sql, error_msg)
                if ai_fixed != current_sql:
                    current_sql = ai_fixed
                    used_ai_fix = True
                    # Re-apply autocorrect on AI's output too
                    recorrected, new_warnings = _autocorrect_sql(current_sql)
                    if recorrected != current_sql:
                        current_sql = recorrected
                        warnings.extend(new_warnings)
                    continue
            return f"SQL Error (after {attempt} attempts): {error_msg}"


def tool_fetch_market_data(sheet_tab: str, cell_range: str = "A1:Z500") -> str:
    """Fetch data from a tab in the market intelligence Google Sheet."""
    try:
        print(f"    📈 Fetching sheet: {sheet_tab}!{cell_range}")
        range_str = f"{sheet_tab}!{cell_range}"
        resp = SHEETS_SVC.spreadsheets().values().get(
            spreadsheetId=MARKET_SHEET_ID, range=range_str
        ).execute()
        rows = resp.get("values", [])
        if rows:
            headers = rows[0]
            data = [dict(zip(headers, row)) for row in rows[1:]]
            return json.dumps(data[:100], indent=2)
        return "No data found"
    except Exception as e:
        return f"Sheets Error: {e}"


def tool_web_search(query: str) -> str:
    """Search the web for market context, competitor info, or industry news. Returns results with source URLs."""
    try:
        print(f"    🌐 Web search: {query}")
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        # Use web_search_preview tool for real web results with URLs
        resp = client.responses.create(
            model="gpt-4.1-mini",
            tools=[{"type": "web_search_preview"}],
            input=f"""Search the web for the latest information about: {query}

Focus on UK travel insurance market, competitors, regulatory changes, travel trends, and news.
For EVERY fact or claim, include the source URL in markdown link format: [Source Name](URL).
Be specific with dates, numbers, and always cite your sources.""",
        )
        # Extract the text output from the response
        result_text = ""
        for item in resp.output:
            if item.type == "message":
                for block in item.content:
                    if block.type == "output_text":
                        result_text += block.text
        return result_text if result_text else "No web results found."
    except Exception as e:
        # Fall back to regular chat completion if web_search_preview not available
        print(f"    ⚠ Web search tool failed ({e}), falling back to knowledge-based search...")
        try:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            resp = client.chat.completions.create(
                model="gpt-4.1-mini",
                max_completion_tokens=1500,
                messages=[
                    {"role": "system", "content": "You are a research assistant. Provide the most recent and relevant information about this query. Focus on UK travel insurance market, competitors, regulatory changes, and travel trends. Be specific with dates, numbers, and name your sources (e.g. 'according to the Financial Times', 'per Google Trends data')."},
                    {"role": "user", "content": f"What is the latest information about: {query}"},
                ],
            )
            return resp.choices[0].message.content
        except Exception as e2:
            return f"Web search error: {e2}"


def tool_scan_drive(keywords: str, days_back: int = 14) -> str:
    """Scan Google Drive for recently modified docs matching keywords."""
    try:
        print(f"    📂 Scanning Drive for: {keywords}")
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=days_back)).isoformat() + "Z"
        query = f"modifiedTime > '{cutoff}' and trashed = false"
        resp = DRIVE_SVC.files().list(
            q=query,
            fields="files(id, name, mimeType, modifiedTime, lastModifyingUser)",
            orderBy="modifiedTime desc",
            pageSize=100,
        ).execute()

        kw_list = [k.strip().lower() for k in keywords.split(",")]
        # Exclude Adventures/Shortbreaks area of business — not relevant to insurance
        exclude_kw = ["wb", "warner", "pau", "paulton", "adventures", "shortbreaks", "short breaks", "attraction"]
        relevant = []
        for f in resp.get("files", []):
            name_lower = f["name"].lower()
            # Skip files belonging to Adventures/Shortbreaks business area
            if any(ex in name_lower for ex in exclude_kw):
                continue
            if any(kw in name_lower for kw in kw_list):
                relevant.append({
                    "name": f["name"],
                    "modified": f["modifiedTime"],
                    "modified_by": f.get("lastModifyingUser", {}).get("displayName", "Unknown"),
                })
        return json.dumps(relevant[:30], indent=2)
    except Exception as e:
        return f"Drive error: {e}"


# Map of tool names to functions
TOOL_FUNCTIONS = {
    "run_sql": tool_run_sql,
    "fetch_market_data": tool_fetch_market_data,
    "web_search": tool_web_search,
    "scan_drive": tool_scan_drive,
}

# ---------------------------------------------------------------------------
# TOOL DEFINITIONS for OpenAI function calling
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": "Execute a SQL query against Google BigQuery. CRITICAL RULES for insurance_policies_new: (1) NEVER use COUNT(*) or COUNT(DISTINCT policy_id) — always SUM(policy_count), (2) NEVER use AVG() on financial columns — always SUM(col)/NULLIF(SUM(policy_count),0), (3) transaction_date is DATE — never EXTRACT(DATE FROM it). For web table: use COUNT(DISTINCT visitor_id) for users, COUNT(DISTINCT session_id) for sessions. Always use project-qualified table names.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "The BigQuery SQL query to execute. Must use fully qualified table names like `hx-data-production.commercial_finance.insurance_policies_new`."
                    }
                },
                "required": ["sql"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_market_data",
            "description": "Fetch data from the market intelligence Google Sheet. Available tabs: 'Market Demand Summary', 'AI Insights', 'Dashboard Section Trends', 'Dashboard Metrics', 'Dashboard Weekly', 'Insurance Intent', 'Data Freshness', 'Spike Log', 'Global Aviation', 'ONS Travel', 'UK Passengers', 'Holiday Intent'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sheet_tab": {
                        "type": "string",
                        "description": "The tab name in the Google Sheet to fetch data from."
                    },
                    "cell_range": {
                        "type": "string",
                        "description": "Cell range to fetch, e.g. 'A1:Z500'. Defaults to 'A1:Z500'.",
                        "default": "A1:Z500"
                    }
                },
                "required": ["sheet_tab"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search for external market context — competitor moves, regulatory changes, travel trends, airline news, industry events. Use this when internal data alone can't explain a trend.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query. Be specific, e.g. 'UK travel insurance market March 2026 competitor pricing' or 'FCA travel insurance medical conditions regulation 2026'."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scan_drive",
            "description": "Scan Google Drive for recently modified documents that might explain trading changes. Returns doc names, modification dates, and who modified them.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "Comma-separated keywords to filter docs by name, e.g. 'pricing,scheme,medical,discount,campaign'"
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "How many days back to search. Default 14.",
                        "default": 14
                    }
                },
                "required": ["keywords"]
            }
        }
    }
]


# ---------------------------------------------------------------------------
# TABLE SCHEMA KNOWLEDGE — injected into the system prompt
# ---------------------------------------------------------------------------

SCHEMA_KNOWLEDGE = dedent("""\
## BIGQUERY TABLE SCHEMAS

### `hx-data-production.commercial_finance.insurance_policies_new`
The core insurance policy table. Every policy transaction is a row. CRITICAL RULES:
- Multiple rows per booking: includes New Issue, Contra, MTA Debit, Cancellation, Client Details Update, UnCancel
- NEVER use COUNT(*), COUNT(policy_id), or COUNT(DISTINCT policy_id) for policy counts — INFLATED figures
- To count policies: SUM(policy_count) — policy_count is SIGNED (positive for new, negative for cancellations)
  SUM gives the correct net count. This is the ONLY way to count policies.
- To get TRUE GP: SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) across ALL transaction types (contras are negative)
- To get AVG GP per policy: SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
- To get AVG customer price: SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
- NEVER use AVG() on financial columns — rows are NOT one-per-policy, so AVG is meaningless
- To compare YoY: use 364-day offset (matches day-of-week)
- transaction_date is already DATE type — do NOT use EXTRACT(DATE FROM transaction_date), just use transaction_date directly in WHERE/CASE
- COVID years 2020-2021 are structural breaks

Key columns:
- policy_id, certificate_id, transaction_type, transaction_date, transaction_datetime, policy_count
- brand, agent_id, agent_code, agent_name, agent_group
- campaign_id, campaign_name, campaign_discount_perc
- policy_type (Annual / Single), scheme_id, scheme_name, scheme_version
- destination, destination_group, highest_rated_country
- family_group, trip_value, travel_start_date, travel_end_date, duration
- issue_date, quote_date, cancellation_date, cancellation_reason
- cover_level_name (Bronze/Classic/Silver/Gold/Deluxe/Elite/Adventure), cover_level_tier
- channel (e.g. 'Direct - Standard', 'Direct - Medical', 'Aggregator - Standard', 'Partner Referral - Medical')
- distribution_channel (Direct / Aggregator / Partner Referral / Renewals)
- booking_source (Web / Phone / etc), transaction_source, converted_by
- customer_type (New / Existing), customer_type_insurance_only
- customer_id, customer_region, customer_area
- medical_split, max_medical_score, max_medical_score_grouped, has_undiagnosed_condition, screened_pax
- max_age_at_purchase, pax, adults, children
- underwriter, insurance_group, product
- policy_renewal_year, auto_renew_opt_in
- FINANCIALS (all BIGNUMERIC, cast to FLOAT64 for aggregation):
  - total_gross_inc_ipt, total_gross_exc_ipt, total_ipt
  - total_net_to_underwriter_inc_gadget, total_net_to_underwriter_exc_mand_gadget
  - total_gross_exc_ipt_ntu_comm (THIS IS GP — gross profit after underwriter and commission)
  - total_gross_exc_ipt_ntu (GP before commission)
  - base_gross_inc_ipt, base_gross_exc_ipt, base_commission, base_net_to_underwriter_*
  - option_gross_inc_ipt, option_commission, option_net_to_underwriter
  - medical_gross_inc_ipt, medical_commission, medical_net_to_underwriter
  - total_gadget_gross_inc_ipt, total_gadget_commission, total_gadget_net_to_uw
  - total_paid_commission_perc, total_paid_commission_value
  - base_discount_value, addon_discount_value, total_discount_value
  - campaign_commission_perc, campaign_commission_value

DERIVED KPIs:
- Discount rate = SUM(CAST(total_discount_value AS FLOAT64)) / NULLIF(SUM(CAST(total_gross_inc_ipt AS FLOAT64)) + SUM(CAST(total_discount_value AS FLOAT64)), 0)
  This gives the true average discount as a % of the pre-discount price (i.e. discount / (gross + discount)).
  Use this when investigating whether discounting is driving margin changes.

### `hx-data-production.commercial_finance.insurance_web_utm_4`
Session-level web analytics joined to policies. Multiple rows per session (one per event/stage).
CRITICAL RULES:
- For unique users: COUNT(DISTINCT visitor_id)
- For unique sessions: COUNT(DISTINCT session_id)
- booking_flow_stage = 'Search' is WHERE THE CUSTOMER SEES A PRICE (key conversion gate)
- Stages: null → Other → Search → Quote → Add-ons → Checkout → Account → Post-booking
- This table is WEB-ONLY — no call center data. Use booking_source in policies table to distinguish.

Key columns:
- session_id, visitor_id, certificate_id, policy_id
- scheme_search, insurance_group, scheme_id, scheme_name, scheme_type
- session_start_date, session_seconds, session_landing_path, session_landing_agent
- session_browser_name, device_type ('mobile', 'computer', 'tablet', 'smarttv')
- page_type, page_path, page_agent, page_datetime_start
- event_name, event_type, event_value, event_start_datetime
- booking_flow_stage (null / Other / Search / Quote / Add-ons / Checkout / Account / Post-booking)
- travel_start_date, travel_end_date, duration
- certificate_gross, certificate_ipt, certificate_nett
- certificate_uw1_ex_ipt, certificate_uw2_ex_ipt, certificate_margin
- total_gross, total_gp
- passenger_count, region_name, scheme_type_status
- policy_screening_gross, policy_screening_margin
- campaign, source, medium, channel (UTM attribution)
- utm_id, used_syd, customer_type, med_session, Multiple_search

#### EVENT TYPES (event_type column):
- 'click' (262M rows) — user interactions. Key event_names for clicks:
  - 'engine_search_button' — user hits SEARCH on landing page (start of quote journey)
  - 'continue-button' / 'continue_button' — progresses through funnel steps
  - 'select_product' — user selects a product on landing page
  - 'book-button' — user clicks BOOK (checkout intent)
  - 'go-to-checkout' — proceeds to checkout
  - 'basket-add-product' — adds product to basket
  - 'annual_only' — toggles annual filter
  - 'verisk-continue' — continues past medical screening
  - 'trigger_question/1' through 'trigger_question/4' — gatekeeper screening questions
  - 'holiday_value' — enters holiday value
  - 'travellers' — selects traveller count
- 'auto_capture' (250M) — automatic page/element tracking
- 'customer_state' (96M) — session state tracking
- 'focus' (57M) — form field focus events
- 'capture' (50M) — form value captures. Key event_names:
  - 'coverType' with event_value 'S' (single) or 'A' (annual)
  - 'travellers' with event_value '1','2','3','4' etc.
  - 'travelType' with event_value '3','5','6' etc.
  - 'destination' — destination selection
  - 'payment_form_mount' — payment form loaded
  - 'support_widget__chat_message_customer' — live chat initiated
- 'public_capture' (23M) — public/non-auth captures
- 'ecommerce' (29K) — booking actions: 'cancel-booking', 'amend-booking' with booking refs

#### PAGE TYPES (page_type column) — the customer journey:
- 'landing' (216M) — entry page, product selection, search engine
- 'gatekeeper/description/1' (55M) — screening/eligibility questions
- 'screening' (74M) — medical screening (Verisk)
- 'extra_details' (158M) — trip details, traveller info
- 'search_results' (65M) — QUOTE PAGE where customer sees price
- 'addon_results' (18M) — upsell/cross-sell add-ons
- 'checkout_new_user' (38M) / 'checkout_authenticated' (39M) / 'checkout_recognised' (8M) — payment
- 'payment_authentication' (6M) — 3DS/payment auth
- 'just_booked' (8M) — confirmation page
- 'booking_actions' (27M) — post-booking management
- 'your_trips' / 'view_booking' / 'amend_booking' / 'cancel_booking' — account actions

#### DEVICE SPLIT:
- 'mobile' ~50.3%, 'computer' ~46.3%, 'tablet' ~3.1%
- Mobile has MORE sessions but potentially different conversion — always segment by device

#### SESSION FLAGS:
- used_syd (bool) — used "Screen Your Destinations" tool (~0.3% of sessions)
- med_session (bool) — session involved medical screening (~12% of sessions)
- Multiple_search ('Yes'/'No') — user did multiple quote searches (~3.5% of sessions)

#### KEY FUNNEL CLICK PATTERNS (by page_type):
- landing → 'select_product' (2.9M sessions), 'engine_search_button' (1.7M sessions)
- gatekeeper → 'continue-button' (2.8M sessions)
- extra_details → 'continue_button' (1.8M sessions)
- screening → 'continue-button' (1.0M sessions)
These click counts vs page views give DROP-OFF rates at each funnel step.

### GOOGLE SHEETS: Market Intelligence
Sheet ID: 1RUasLdbB9OiHPJzQClglC7aY5KMH4P-dnzk4v_h-tsg
Tabs available:
- 'Market Demand Summary' — quarterly demand indices (UK passengers, visits abroad, aviation, combined)
- 'AI Insights' — pre-generated strategic insights (section_key, insight_text, generated_at)
- 'Dashboard Section Trends' — term-level trends (section, term, current, peak, change_pct, trending)
- 'Dashboard Metrics' — headline metrics (metric_key, value, direction, description)
- 'Dashboard Weekly' — weekly combined/holiday/insurance index scores
- 'Insurance Intent' — Google Trends data for insurance search terms (date, source, metric_name, normalised_value, is_spike)
- 'Holiday Intent' — Google Trends for holiday terms
- 'Spike Log' — known anomalies (date, source, metric_name, spike_event — includes COVID, Thomas Cook etc)
- 'Global Aviation', 'ONS Travel', 'UK Passengers' — macro travel data
""")


# ---------------------------------------------------------------------------
# BASELINE DATA QUERIES (Phase 1)
# ---------------------------------------------------------------------------

POLICIES_TABLE = f"`{BQ_PROJECT}.commercial_finance.insurance_policies_new`"
WEB_TABLE = f"`{BQ_PROJECT}.commercial_finance.insurance_web_utm_4`"


def get_date_params(run_date):
    """Return a dict of date strings for SQL parameterisation based on run_date."""
    yesterday = run_date
    week_start = run_date - timedelta(days=7)
    month_start = run_date - timedelta(days=28)
    yesterday_ly = run_date - timedelta(days=364)
    week_start_ly = week_start - timedelta(days=364)
    month_start_ly = month_start - timedelta(days=364)
    return {
        "yesterday": str(yesterday),
        "week_start": str(week_start),
        "month_start": str(month_start),
        "yesterday_ly": str(yesterday_ly),
        "week_start_ly": str(week_start_ly),
        "month_start_ly": str(month_start_ly),
        "trend_start": str(run_date - timedelta(days=14)),
        "trend_start_ly": str(run_date - timedelta(days=14) - timedelta(days=364)),
    }


def build_baseline_trading_sql(dp):
    """Build the baseline trading SQL with explicit date literals."""
    return f"""
WITH daily AS (
  SELECT 'yesterday' AS period,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
    SUM(policy_count) AS new_policies,
    SUM(CASE WHEN policy_type='Annual' THEN policy_count ELSE 0 END) AS annual_policies,
    SUM(CASE WHEN policy_type='Single' THEN policy_count ELSE 0 END) AS single_policies,
    SUM(CASE WHEN transaction_type='Cancellation' THEN policy_count ELSE 0 END) AS cancellations,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_customer_price
  FROM {POLICIES_TABLE} WHERE transaction_date = DATE('{dp["yesterday"]}')
),
daily_ly AS (
  SELECT 'yesterday_ly' AS period,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
    SUM(policy_count) AS new_policies,
    SUM(CASE WHEN policy_type='Annual' THEN policy_count ELSE 0 END) AS annual_policies,
    SUM(CASE WHEN policy_type='Single' THEN policy_count ELSE 0 END) AS single_policies,
    SUM(CASE WHEN transaction_type='Cancellation' THEN policy_count ELSE 0 END) AS cancellations,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_customer_price
  FROM {POLICIES_TABLE} WHERE transaction_date = DATE('{dp["yesterday_ly"]}')
),
weekly AS (
  SELECT 'trailing_7d' AS period,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
    SUM(policy_count) AS new_policies,
    SUM(CASE WHEN policy_type='Annual' THEN policy_count ELSE 0 END) AS annual_policies,
    SUM(CASE WHEN policy_type='Single' THEN policy_count ELSE 0 END) AS single_policies,
    SUM(CASE WHEN transaction_type='Cancellation' THEN policy_count ELSE 0 END) AS cancellations,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_customer_price
  FROM {POLICIES_TABLE} WHERE transaction_date BETWEEN DATE('{dp["week_start"]}') AND DATE('{dp["yesterday"]}')
),
weekly_ly AS (
  SELECT 'trailing_7d_ly' AS period,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
    SUM(policy_count) AS new_policies,
    SUM(CASE WHEN policy_type='Annual' THEN policy_count ELSE 0 END) AS annual_policies,
    SUM(CASE WHEN policy_type='Single' THEN policy_count ELSE 0 END) AS single_policies,
    SUM(CASE WHEN transaction_type='Cancellation' THEN policy_count ELSE 0 END) AS cancellations,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_customer_price
  FROM {POLICIES_TABLE} WHERE transaction_date BETWEEN DATE('{dp["week_start_ly"]}') AND DATE('{dp["yesterday_ly"]}')
),
monthly AS (
  SELECT 'trailing_28d' AS period,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
    SUM(policy_count) AS new_policies,
    SUM(CASE WHEN policy_type='Annual' THEN policy_count ELSE 0 END) AS annual_policies,
    SUM(CASE WHEN policy_type='Single' THEN policy_count ELSE 0 END) AS single_policies,
    SUM(CASE WHEN transaction_type='Cancellation' THEN policy_count ELSE 0 END) AS cancellations,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_customer_price
  FROM {POLICIES_TABLE} WHERE transaction_date BETWEEN DATE('{dp["month_start"]}') AND DATE('{dp["yesterday"]}')
),
monthly_ly AS (
  SELECT 'trailing_28d_ly' AS period,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
    SUM(policy_count) AS new_policies,
    SUM(CASE WHEN policy_type='Annual' THEN policy_count ELSE 0 END) AS annual_policies,
    SUM(CASE WHEN policy_type='Single' THEN policy_count ELSE 0 END) AS single_policies,
    SUM(CASE WHEN transaction_type='Cancellation' THEN policy_count ELSE 0 END) AS cancellations,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_customer_price
  FROM {POLICIES_TABLE} WHERE transaction_date BETWEEN DATE('{dp["month_start_ly"]}') AND DATE('{dp["yesterday_ly"]}')
)
SELECT * FROM daily UNION ALL SELECT * FROM daily_ly
UNION ALL SELECT * FROM weekly UNION ALL SELECT * FROM weekly_ly
UNION ALL SELECT * FROM monthly UNION ALL SELECT * FROM monthly_ly
"""


def build_baseline_trend_sql(dp):
    """Build the 14-day trend SQL with explicit date literals."""
    return f"""
SELECT transaction_date,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS daily_gp,
  SUM(policy_count) AS new_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM {POLICIES_TABLE}
WHERE transaction_date BETWEEN DATE('{dp["trend_start"]}') AND DATE('{dp["yesterday"]}')
GROUP BY transaction_date ORDER BY transaction_date
"""


def build_baseline_trend_ly_sql(dp):
    """Build the 14-day LY trend SQL (364-day offset) for YoY chart comparison."""
    return f"""
SELECT transaction_date,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS daily_gp,
  SUM(policy_count) AS new_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM {POLICIES_TABLE}
WHERE transaction_date BETWEEN DATE('{dp["trend_start_ly"]}') AND DATE('{dp["yesterday_ly"]}')
GROUP BY transaction_date ORDER BY transaction_date
"""


def build_baseline_funnel_sql(dp):
    """Build the funnel SQL with explicit date literals."""
    return f"""
SELECT 'trailing_7d' AS period, booking_flow_stage,
  COUNT(DISTINCT visitor_id) AS unique_visitors,
  COUNT(DISTINCT session_id) AS unique_sessions,
  COUNT(DISTINCT CASE WHEN certificate_id IS NOT NULL THEN session_id END) AS converting_sessions
FROM {WEB_TABLE}
WHERE session_start_date BETWEEN DATE('{dp["week_start"]}') AND DATE('{dp["yesterday"]}')
GROUP BY booking_flow_stage
UNION ALL
SELECT 'trailing_7d_ly', booking_flow_stage,
  COUNT(DISTINCT visitor_id),
  COUNT(DISTINCT session_id),
  COUNT(DISTINCT CASE WHEN certificate_id IS NOT NULL THEN session_id END)
FROM {WEB_TABLE}
WHERE session_start_date BETWEEN DATE('{dp["week_start_ly"]}') AND DATE('{dp["yesterday_ly"]}')
GROUP BY booking_flow_stage
"""


def build_baseline_web_engagement_sql(dp):
    """Build the web engagement SQL with explicit date literals."""
    return f"""
SELECT 'trailing_7d' AS period, device_type,
  COUNT(DISTINCT session_id) AS sessions,
  COUNT(DISTINCT visitor_id) AS visitors,
  COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Search' THEN session_id END) AS search_sessions,
  COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Checkout' THEN session_id END) AS checkout_sessions,
  COUNT(DISTINCT CASE WHEN page_type = 'just_booked' THEN session_id END) AS booked_sessions,
  COUNT(DISTINCT CASE WHEN event_type = 'click' AND event_name = 'engine_search_button' THEN session_id END) AS search_btn_clicks,
  COUNT(DISTINCT CASE WHEN event_type = 'click' AND event_name = 'book-button' THEN session_id END) AS book_btn_clicks,
  COUNT(DISTINCT CASE WHEN med_session = TRUE THEN session_id END) AS medical_sessions,
  COUNT(DISTINCT CASE WHEN Multiple_search = 'Yes' THEN session_id END) AS multi_search_sessions
FROM {WEB_TABLE}
WHERE session_start_date BETWEEN DATE('{dp["week_start"]}') AND DATE('{dp["yesterday"]}')
  AND device_type IN ('mobile', 'computer', 'tablet')
GROUP BY device_type
UNION ALL
SELECT 'trailing_7d_ly', device_type,
  COUNT(DISTINCT session_id),
  COUNT(DISTINCT visitor_id),
  COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Search' THEN session_id END),
  COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Checkout' THEN session_id END),
  COUNT(DISTINCT CASE WHEN page_type = 'just_booked' THEN session_id END),
  COUNT(DISTINCT CASE WHEN event_type = 'click' AND event_name = 'engine_search_button' THEN session_id END),
  COUNT(DISTINCT CASE WHEN event_type = 'click' AND event_name = 'book-button' THEN session_id END),
  COUNT(DISTINCT CASE WHEN med_session = TRUE THEN session_id END),
  COUNT(DISTINCT CASE WHEN Multiple_search = 'Yes' THEN session_id END)
FROM {WEB_TABLE}
WHERE session_start_date BETWEEN DATE('{dp["week_start_ly"]}') AND DATE('{dp["yesterday_ly"]}')
  AND device_type IN ('mobile', 'computer', 'tablet')
GROUP BY device_type
"""


# ---------------------------------------------------------------------------
# INVESTIGATION TRACKS — deterministic SQL covering all trading dimensions
# ---------------------------------------------------------------------------

def build_investigation_tracks(dp):
    """Build all investigation track SQL queries. Each compares TY vs LY in one query."""
    P = POLICIES_TABLE
    W = WEB_TABLE
    tracks = {}

    # Track 1: Channel × Product Matrix — the core GP decomposition
    tracks['channel_product_mix'] = {
        'name': 'Channel × Product Matrix',
        'desc': 'GP decomposition by distribution channel and policy type',
        'sql': f"""
SELECT 'TY' AS yr, distribution_channel, policy_type,
    SUM(policy_count) AS policies,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price,
    SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_commission,
    SUM(CAST(total_discount_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_discount
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY distribution_channel, policy_type
UNION ALL
SELECT 'LY', distribution_channel, policy_type,
    SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_discount_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY distribution_channel, policy_type
"""
    }

    # Track 2: Scheme performance — top schemes ranked by GP
    tracks['scheme_performance'] = {
        'name': 'Scheme Performance',
        'desc': 'Individual scheme GP, volume, and pricing',
        'sql': f"""
SELECT 'TY' AS yr, scheme_name,
    SUM(policy_count) AS policies,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY scheme_name
HAVING ABS(SUM(policy_count)) >= 5
UNION ALL
SELECT 'LY', scheme_name,
    SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY scheme_name
HAVING ABS(SUM(policy_count)) >= 5
ORDER BY gp DESC
"""
    }

    # Track 3: Medical vs Non-Medical
    tracks['medical_profile'] = {
        'name': 'Medical vs Non-Medical',
        'desc': 'Risk segment decomposition — medical screening impact on margin',
        'sql': f"""
SELECT 'TY' AS yr,
    CASE WHEN max_medical_score > 0 THEN 'Medical' ELSE 'Non-medical' END AS medical_flag,
    max_medical_score_grouped, policy_type, distribution_channel,
    SUM(policy_count) AS policies,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp,
    SUM(CAST(medical_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_medical_premium,
    SUM(CAST(medical_net_to_underwriter AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_medical_uw_cost
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY medical_flag, max_medical_score_grouped, policy_type, distribution_channel
UNION ALL
SELECT 'LY' AS yr,
    CASE WHEN max_medical_score > 0 THEN 'Medical' ELSE 'Non-medical' END AS medical_flag,
    max_medical_score_grouped, policy_type, distribution_channel,
    SUM(policy_count) AS policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp,
    SUM(CAST(medical_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_medical_premium,
    SUM(CAST(medical_net_to_underwriter AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_medical_uw_cost
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY medical_flag, max_medical_score_grouped, policy_type, distribution_channel
"""
    }

    # Track 4: Cover Level Mix
    tracks['cover_level_mix'] = {
        'name': 'Cover Level & Upsell Mix',
        'desc': 'Customer tier choices and add-on attach rates',
        'sql': f"""
SELECT 'TY' AS yr, cover_level_name, cover_level_tier,
    SUM(policy_count) AS policies,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(base_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_base_price,
    SUM(CAST(option_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_option_price,
    SUM(CAST(total_gadget_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gadget_price,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY cover_level_name, cover_level_tier
UNION ALL
SELECT 'LY', cover_level_name, cover_level_tier,
    SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
    SUM(CAST(base_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(option_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_gadget_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY cover_level_name, cover_level_tier
"""
    }

    # Track 5: Commission & Partner Economics
    tracks['commission_partners'] = {
        'name': 'Commission & Partner Economics',
        'desc': 'Cost structure by agent, partner, and distribution channel',
        'sql': f"""
SELECT 'TY' AS yr, insurance_group, distribution_channel,
    SUM(policy_count) AS policies,
    SUM(CAST(total_paid_commission_value AS FLOAT64)) AS total_commission,
    SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_commission,
    SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(NULLIF(SUM(CAST(total_gross_inc_ipt AS FLOAT64)), 0), 0) AS commission_rate,
    SUM(CAST(campaign_commission_value AS FLOAT64)) AS campaign_commission,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY insurance_group, distribution_channel
HAVING ABS(SUM(policy_count)) >= 3
UNION ALL
SELECT 'LY', insurance_group, distribution_channel,
    SUM(policy_count), SUM(CAST(total_paid_commission_value AS FLOAT64)),
    SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(NULLIF(SUM(CAST(total_gross_inc_ipt AS FLOAT64)), 0), 0),
    SUM(CAST(campaign_commission_value AS FLOAT64)),
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY insurance_group, distribution_channel
HAVING ABS(SUM(policy_count)) >= 3
"""
    }

    # Track 6: Customer Demographics (Age & Type)
    tracks['customer_demographics'] = {
        'name': 'Customer Demographics',
        'desc': 'Age profile and new vs existing customer dynamics',
        'sql': f"""
SELECT 'TY' AS yr, customer_type, customer_type_insurance_only,
    CASE
        WHEN max_age_at_purchase < 35 THEN 'Under 35'
        WHEN max_age_at_purchase BETWEEN 35 AND 54 THEN '35-54'
        WHEN max_age_at_purchase BETWEEN 55 AND 69 THEN '55-69'
        WHEN max_age_at_purchase BETWEEN 70 AND 79 THEN '70-79'
        WHEN max_age_at_purchase >= 80 THEN '80+'
    END AS age_band,
    SUM(policy_count) AS policies,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY customer_type, customer_type_insurance_only, age_band
UNION ALL
SELECT 'LY' AS yr, customer_type, customer_type_insurance_only,
    CASE
        WHEN max_age_at_purchase < 35 THEN 'Under 35'
        WHEN max_age_at_purchase BETWEEN 35 AND 54 THEN '35-54'
        WHEN max_age_at_purchase BETWEEN 55 AND 69 THEN '55-69'
        WHEN max_age_at_purchase BETWEEN 70 AND 79 THEN '70-79'
        WHEN max_age_at_purchase >= 80 THEN '80+'
    END AS age_band,
    SUM(policy_count) AS policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY customer_type, customer_type_insurance_only, age_band
"""
    }

    # Track 7: Destination Mix
    tracks['destination_mix'] = {
        'name': 'Destination & Region Mix',
        'desc': 'Geographic patterns — destination groups and customer regions',
        'sql': f"""
SELECT 'TY' AS yr, destination_group,
    SUM(policy_count) AS policies,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY destination_group
UNION ALL
SELECT 'LY', destination_group,
    SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY destination_group
"""
    }

    # Track 8: Cancellation Analysis
    tracks['cancellations'] = {
        'name': 'Cancellation Analysis',
        'desc': 'Cancellation patterns by reason, channel, and policy type',
        'sql': f"""
SELECT 'TY' AS yr, cancellation_reason, policy_type, distribution_channel,
    SUM(policy_count) AS cancellations,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp_impact
FROM {P}
WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
  AND transaction_type = 'Cancellation'
GROUP BY cancellation_reason, policy_type, distribution_channel
UNION ALL
SELECT 'LY', cancellation_reason, policy_type, distribution_channel,
    SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
FROM {P}
WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
  AND transaction_type = 'Cancellation'
GROUP BY cancellation_reason, policy_type, distribution_channel
"""
    }

    # Track 9: Renewal Performance
    tracks['renewals'] = {
        'name': 'Renewal Performance',
        'desc': 'Renewal cohort analysis — retention, pricing, auto-renew',
        'sql': f"""
SELECT 'TY' AS yr, policy_renewal_year, auto_renew_opt_in,
    SUM(policy_count) AS policies,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price
FROM {P}
WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
  AND distribution_channel = 'Renewals'
GROUP BY policy_renewal_year, auto_renew_opt_in
UNION ALL
SELECT 'LY', policy_renewal_year, auto_renew_opt_in,
    SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
FROM {P}
WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
  AND distribution_channel = 'Renewals'
GROUP BY policy_renewal_year, auto_renew_opt_in
"""
    }

    # Track 10: Web Funnel — detailed page-level, device-specific conversion
    tracks['web_funnel_detailed'] = {
        'name': 'Web Funnel (Detailed)',
        'desc': 'Page-level conversion by device — where users drop off',
        'sql': f"""
SELECT 'TY' AS yr, device_type, page_type,
    COUNT(DISTINCT session_id) AS page_sessions,
    COUNT(DISTINCT CASE WHEN event_type = 'click' AND event_name IN
        ('engine_search_button','continue-button','continue_button','select_product',
         'book-button','go-to-checkout','verisk-continue')
        THEN session_id END) AS action_sessions
FROM {W}
WHERE session_start_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
  AND page_type IN ('landing','gatekeeper/description/1','extra_details',
    'screening','search_results','addon_results','checkout_new_user',
    'checkout_authenticated','just_booked')
  AND device_type IN ('mobile','computer','tablet')
GROUP BY device_type, page_type
UNION ALL
SELECT 'LY', device_type, page_type,
    COUNT(DISTINCT session_id),
    COUNT(DISTINCT CASE WHEN event_type = 'click' AND event_name IN
        ('engine_search_button','continue-button','continue_button','select_product',
         'book-button','go-to-checkout','verisk-continue')
        THEN session_id END)
FROM {W}
WHERE session_start_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
  AND page_type IN ('landing','gatekeeper/description/1','extra_details',
    'screening','search_results','addon_results','checkout_new_user',
    'checkout_authenticated','just_booked')
  AND device_type IN ('mobile','computer','tablet')
GROUP BY device_type, page_type
"""
    }

    # Track 11: Day-of-Week Patterns
    tracks['day_of_week'] = {
        'name': 'Day-of-Week Patterns',
        'desc': 'Daily GP pattern within the trailing week — spot individual bad days',
        'sql': f"""
SELECT 'TY' AS yr, transaction_date,
    FORMAT_DATE('%A', transaction_date) AS day_name,
    SUM(policy_count) AS policies,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY transaction_date
UNION ALL
SELECT 'LY', transaction_date,
    FORMAT_DATE('%A', transaction_date),
    SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY transaction_date
ORDER BY transaction_date
"""
    }

    # Track 12: Discount & Campaign Effectiveness
    tracks['discounts_campaigns'] = {
        'name': 'Discount & Campaign Effectiveness',
        'desc': 'Discount penetration and campaign ROI',
        'sql': f"""
SELECT 'TY' AS yr,
    CASE WHEN CAST(total_discount_value AS FLOAT64) != 0 THEN 'Discounted' ELSE 'Full price' END AS discount_flag,
    campaign_name,
    SUM(policy_count) AS policies,
    SUM(CAST(total_discount_value AS FLOAT64)) AS total_discounts,
    SUM(CAST(total_discount_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_discount,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY discount_flag, campaign_name
HAVING ABS(SUM(policy_count)) >= 2
UNION ALL
SELECT 'LY' AS yr,
    CASE WHEN CAST(total_discount_value AS FLOAT64) != 0 THEN 'Discounted' ELSE 'Full price' END AS discount_flag,
    campaign_name,
    SUM(policy_count) AS policies, SUM(CAST(total_discount_value AS FLOAT64)) AS total_discounts,
    SUM(CAST(total_discount_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_discount,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY discount_flag, campaign_name
HAVING ABS(SUM(policy_count)) >= 2
"""
    }

    # Track 13: Cruise vs Non-Cruise
    tracks['cruise'] = {
        'name': 'Cruise vs Non-Cruise',
        'desc': 'Cruise segment performance — partner and scheme analysis',
        'sql': f"""
SELECT 'TY' AS yr,
    CASE WHEN LOWER(scheme_name) LIKE '%cruise%' OR LOWER(campaign_name) LIKE '%cru%' THEN 'Cruise' ELSE 'Non-Cruise' END AS cruise_flag,
    distribution_channel, agent_name,
    SUM(policy_count) AS policies,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY cruise_flag, distribution_channel, agent_name
HAVING ABS(SUM(policy_count)) >= 2
UNION ALL
SELECT 'LY' AS yr,
    CASE WHEN LOWER(scheme_name) LIKE '%cruise%' OR LOWER(campaign_name) LIKE '%cru%' THEN 'Cruise' ELSE 'Non-Cruise' END AS cruise_flag,
    distribution_channel, agent_name,
    SUM(policy_count) AS policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY cruise_flag, distribution_channel, agent_name
HAVING ABS(SUM(policy_count)) >= 2
"""
    }

    # -----------------------------------------------------------------------
    # CROSS-TABLE TRACKS — joining web behaviour to trading outcomes
    # -----------------------------------------------------------------------

    # Track 14: Session-to-GP Bridge — device × scheme × medical screening
    tracks['web_to_gp_bridge'] = {
        'name': 'Session-to-GP Bridge (Device × Scheme × Medical)',
        'desc': 'Which web journeys (device, scheme, medical screening) produce the highest and lowest GP per converting session? Joins every converting web session to its policy outcome to show where high-value customers actually come from.',
        'sql': f"""
WITH converting_sessions_ty AS (
    SELECT
        w.session_id,
        w.device_type,
        w.scheme_name AS web_scheme,
        MAX(CASE WHEN w.med_session = TRUE THEN 1 ELSE 0 END) AS had_medical,
        MAX(w.certificate_id) AS certificate_id
    FROM {W} w
    WHERE w.session_start_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
      AND w.certificate_id IS NOT NULL
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type, w.scheme_name
),
joined_ty AS (
    SELECT
        'TY' AS yr,
        cs.device_type,
        cs.web_scheme,
        CASE WHEN cs.had_medical = 1 THEN 'Medical' ELSE 'Non-medical' END AS medical_flag,
        SUM(p.policy_count) AS policies,
        SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
        SUM(CAST(p.total_gross_inc_ipt AS FLOAT64)) AS total_gross,
        SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_gp_per_policy,
        COUNT(DISTINCT cs.session_id) AS converting_sessions,
        SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(COUNT(DISTINCT cs.session_id), 0) AS gp_per_session
    FROM converting_sessions_ty cs
    JOIN {P} p ON CAST(p.certificate_id AS STRING) = cs.certificate_id
    WHERE p.transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
    GROUP BY cs.device_type, cs.web_scheme, medical_flag
    HAVING ABS(SUM(p.policy_count)) >= 3
),
converting_sessions_ly AS (
    SELECT
        w.session_id,
        w.device_type,
        w.scheme_name AS web_scheme,
        MAX(CASE WHEN w.med_session = TRUE THEN 1 ELSE 0 END) AS had_medical,
        MAX(w.certificate_id) AS certificate_id
    FROM {W} w
    WHERE w.session_start_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
      AND w.certificate_id IS NOT NULL
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type, w.scheme_name
),
joined_ly AS (
    SELECT
        'LY' AS yr,
        cs.device_type,
        cs.web_scheme,
        CASE WHEN cs.had_medical = 1 THEN 'Medical' ELSE 'Non-medical' END AS medical_flag,
        SUM(p.policy_count) AS policies,
        SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
        SUM(CAST(p.total_gross_inc_ipt AS FLOAT64)) AS total_gross,
        SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_gp_per_policy,
        COUNT(DISTINCT cs.session_id) AS converting_sessions,
        SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(COUNT(DISTINCT cs.session_id), 0) AS gp_per_session
    FROM converting_sessions_ly cs
    JOIN {P} p ON CAST(p.certificate_id AS STRING) = cs.certificate_id
    WHERE p.transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
    GROUP BY cs.device_type, cs.web_scheme, medical_flag
    HAVING ABS(SUM(p.policy_count)) >= 3
)
SELECT * FROM joined_ty
UNION ALL
SELECT * FROM joined_ly
ORDER BY total_gp DESC
"""
    }

    # Track 15: Funnel Drop-off by GP Value Tier
    tracks['funnel_value_dropoff'] = {
        'name': 'Funnel Drop-off by Value Tier',
        'desc': 'Compares the web funnel for sessions that converted into high-GP vs low-GP policies vs sessions that never converted. Shows where high-value customers drop off vs low-value ones, revealing if the funnel is optimised for the wrong customer.',
        'sql': f"""
WITH policy_values_ty AS (
    SELECT certificate_id,
        SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS policy_gp,
        MAX(policy_type) AS policy_type
    FROM {P}
    WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
      AND certificate_id IS NOT NULL
    GROUP BY certificate_id
),
session_values_ty AS (
    SELECT w.session_id, w.device_type,
        MAX(w.certificate_id) AS certificate_id,
        MAX(pv.policy_gp) AS policy_gp,
        MAX(pv.policy_type) AS policy_type,
        CASE
            WHEN MAX(pv.policy_gp) IS NULL THEN 'Non-converter'
            WHEN MAX(pv.policy_gp) >= 50 THEN 'High GP (50+)'
            WHEN MAX(pv.policy_gp) >= 20 THEN 'Mid GP (20-50)'
            ELSE 'Low GP (<20)'
        END AS value_tier
    FROM {W} w
    LEFT JOIN policy_values_ty pv ON CAST(pv.certificate_id AS STRING) = w.certificate_id
    WHERE w.session_start_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type
)
SELECT 'TY' AS yr, sv.value_tier, sv.device_type,
    COUNT(DISTINCT sv.session_id) AS sessions,
    COUNT(DISTINCT CASE WHEN w2.booking_flow_stage = 'Search' THEN sv.session_id END) AS reached_search,
    COUNT(DISTINCT CASE WHEN w2.page_type = 'search_results' THEN sv.session_id END) AS reached_results,
    COUNT(DISTINCT CASE WHEN w2.page_type = 'screening' THEN sv.session_id END) AS reached_screening,
    COUNT(DISTINCT CASE WHEN w2.booking_flow_stage = 'Checkout' THEN sv.session_id END) AS reached_checkout,
    COUNT(DISTINCT CASE WHEN w2.page_type = 'just_booked' THEN sv.session_id END) AS reached_booked
FROM session_values_ty sv
JOIN {W} w2 ON w2.session_id = sv.session_id
    AND w2.session_start_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY sv.value_tier, sv.device_type

UNION ALL

SELECT 'LY' AS yr, sv.value_tier, sv.device_type,
    COUNT(DISTINCT sv.session_id),
    COUNT(DISTINCT CASE WHEN w2.booking_flow_stage = 'Search' THEN sv.session_id END),
    COUNT(DISTINCT CASE WHEN w2.page_type = 'search_results' THEN sv.session_id END),
    COUNT(DISTINCT CASE WHEN w2.page_type = 'screening' THEN sv.session_id END),
    COUNT(DISTINCT CASE WHEN w2.booking_flow_stage = 'Checkout' THEN sv.session_id END),
    COUNT(DISTINCT CASE WHEN w2.page_type = 'just_booked' THEN sv.session_id END)
FROM (
    SELECT w.session_id, w.device_type,
        MAX(w.certificate_id) AS certificate_id,
        CASE
            WHEN MAX(pv.policy_gp) IS NULL THEN 'Non-converter'
            WHEN MAX(pv.policy_gp) >= 50 THEN 'High GP (50+)'
            WHEN MAX(pv.policy_gp) >= 20 THEN 'Mid GP (20-50)'
            ELSE 'Low GP (<20)'
        END AS value_tier
    FROM {W} w
    LEFT JOIN (
        SELECT certificate_id,
            SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS policy_gp
        FROM {P}
        WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
          AND certificate_id IS NOT NULL
        GROUP BY certificate_id
    ) pv ON CAST(pv.certificate_id AS STRING) = w.certificate_id
    WHERE w.session_start_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type
) sv
JOIN {W} w2 ON w2.session_id = sv.session_id
    AND w2.session_start_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY sv.value_tier, sv.device_type
"""
    }

    # Track 16: Annual vs Single Conversion Path — YoY shift
    tracks['annual_vs_single_conversion'] = {
        'name': 'Annual vs Single Conversion Path (YoY)',
        'desc': 'How does the web-to-purchase path differ for annual vs single trip policies? Compares conversion rates, multi-search behaviour, medical screening involvement, and GP yield for each policy type. Shows if annual customers are being lost somewhere specific in the funnel.',
        'sql': f"""
WITH sessions_with_outcome_ty AS (
    SELECT
        w.session_id,
        w.device_type,
        MAX(CASE WHEN w.med_session = TRUE THEN 1 ELSE 0 END) AS had_medical,
        MAX(CASE WHEN w.Multiple_search = 'Yes' THEN 1 ELSE 0 END) AS had_multi_search,
        MAX(CASE WHEN w.booking_flow_stage = 'Search' THEN 1 ELSE 0 END) AS reached_search,
        MAX(CASE WHEN w.booking_flow_stage = 'Checkout' THEN 1 ELSE 0 END) AS reached_checkout,
        MAX(CASE WHEN w.page_type = 'just_booked' THEN 1 ELSE 0 END) AS booked,
        MAX(w.certificate_id) AS certificate_id
    FROM {W} w
    WHERE w.session_start_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type
),
with_policy_ty AS (
    SELECT s.*,
        p.policy_type,
        SUM(p.policy_count) AS policies,
        SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
    FROM sessions_with_outcome_ty s
    LEFT JOIN {P} p ON CAST(p.certificate_id AS STRING) = s.certificate_id
        AND p.transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
    GROUP BY s.session_id, s.device_type, s.had_medical, s.had_multi_search,
             s.reached_search, s.reached_checkout, s.booked, s.certificate_id, p.policy_type
)
SELECT 'TY' AS yr,
    COALESCE(policy_type, 'No conversion') AS policy_type,
    device_type,
    COUNT(DISTINCT session_id) AS total_sessions,
    SUM(reached_search) AS search_sessions,
    SUM(reached_checkout) AS checkout_sessions,
    SUM(booked) AS booked_sessions,
    SUM(had_medical) AS medical_sessions,
    SUM(had_multi_search) AS multi_search_sessions,
    SUM(gp) AS total_gp,
    SUM(gp) / NULLIF(SUM(CASE WHEN booked = 1 THEN 1 ELSE 0 END), 0) AS gp_per_booked_session,
    SUM(policies) AS total_policies
FROM with_policy_ty
GROUP BY policy_type, device_type

UNION ALL

SELECT 'LY' AS yr,
    COALESCE(p.policy_type, 'No conversion') AS policy_type,
    s.device_type,
    COUNT(DISTINCT s.session_id) AS total_sessions,
    SUM(s.reached_search) AS search_sessions,
    SUM(s.reached_checkout) AS checkout_sessions,
    SUM(s.booked) AS booked_sessions,
    SUM(s.had_medical) AS medical_sessions,
    SUM(s.had_multi_search) AS multi_search_sessions,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(CASE WHEN s.booked = 1 THEN 1 ELSE 0 END), 0) AS gp_per_booked_session,
    SUM(p.policy_count) AS total_policies
FROM (
    SELECT
        w.session_id, w.device_type,
        MAX(CASE WHEN w.med_session = TRUE THEN 1 ELSE 0 END) AS had_medical,
        MAX(CASE WHEN w.Multiple_search = 'Yes' THEN 1 ELSE 0 END) AS had_multi_search,
        MAX(CASE WHEN w.booking_flow_stage = 'Search' THEN 1 ELSE 0 END) AS reached_search,
        MAX(CASE WHEN w.booking_flow_stage = 'Checkout' THEN 1 ELSE 0 END) AS reached_checkout,
        MAX(CASE WHEN w.page_type = 'just_booked' THEN 1 ELSE 0 END) AS booked,
        MAX(w.certificate_id) AS certificate_id
    FROM {W} w
    WHERE w.session_start_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type
) s
LEFT JOIN {P} p ON CAST(p.certificate_id AS STRING) = s.certificate_id
    AND p.transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY p.policy_type, s.device_type
"""
    }

    # Track 17: Multi-Search GP Impact
    tracks['multi_search_gp_impact'] = {
        'name': 'Multi-Search Session GP Impact',
        'desc': 'Do sessions where users search multiple times convert better or worse, and what is the GP impact? Breaks down by device and policy type to show whether multi-search is a sign of engaged shoppers or confused users.',
        'sql': f"""
WITH session_profile_ty AS (
    SELECT
        w.session_id,
        w.device_type,
        MAX(CASE WHEN w.Multiple_search = 'Yes' THEN 'Multi-search' ELSE 'Single-search' END) AS search_type,
        MAX(CASE WHEN w.med_session = TRUE THEN 1 ELSE 0 END) AS had_medical,
        MAX(CASE WHEN w.page_type = 'just_booked' THEN 1 ELSE 0 END) AS converted,
        MAX(w.certificate_id) AS certificate_id
    FROM {W} w
    WHERE w.session_start_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type
)
SELECT 'TY' AS yr,
    sp.search_type,
    sp.device_type,
    COUNT(DISTINCT sp.session_id) AS total_sessions,
    SUM(sp.converted) AS converted_sessions,
    SAFE_DIVIDE(SUM(sp.converted), COUNT(DISTINCT sp.session_id)) AS conversion_rate,
    SUM(p.policy_count) AS policies,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_gp_per_policy,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(sp.converted), 0) AS gp_per_converted_session,
    MAX(p.policy_type) AS dominant_policy_type,
    SUM(sp.had_medical) AS medical_sessions
FROM session_profile_ty sp
LEFT JOIN {P} p ON CAST(p.certificate_id AS STRING) = sp.certificate_id
    AND p.transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY sp.search_type, sp.device_type

UNION ALL

SELECT 'LY' AS yr, sp.search_type, sp.device_type,
    COUNT(DISTINCT sp.session_id),
    SUM(sp.converted),
    SAFE_DIVIDE(SUM(sp.converted), COUNT(DISTINCT sp.session_id)),
    SUM(p.policy_count),
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)),
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0),
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(sp.converted), 0),
    MAX(p.policy_type),
    SUM(sp.had_medical)
FROM (
    SELECT w.session_id, w.device_type,
        MAX(CASE WHEN w.Multiple_search = 'Yes' THEN 'Multi-search' ELSE 'Single-search' END) AS search_type,
        MAX(CASE WHEN w.med_session = TRUE THEN 1 ELSE 0 END) AS had_medical,
        MAX(CASE WHEN w.page_type = 'just_booked' THEN 1 ELSE 0 END) AS converted,
        MAX(w.certificate_id) AS certificate_id
    FROM {W} w
    WHERE w.session_start_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type
) sp
LEFT JOIN {P} p ON CAST(p.certificate_id AS STRING) = sp.certificate_id
    AND p.transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY sp.search_type, sp.device_type
"""
    }

    # Track 18: Medical Screening Funnel × Device — conversion and GP
    tracks['medical_screening_funnel'] = {
        'name': 'Medical Screening Funnel by Device',
        'desc': 'How does the medical screening step specifically affect conversion and GP by device? Compares sessions that hit the screening page vs those that did not, and tracks their conversion rate and resulting GP. Reveals if medical screening is a conversion killer on mobile.',
        'sql': f"""
WITH session_screening_ty AS (
    SELECT
        w.session_id,
        w.device_type,
        MAX(CASE WHEN w.page_type = 'screening' THEN 1 ELSE 0 END) AS hit_screening,
        MAX(CASE WHEN w.med_session = TRUE THEN 1 ELSE 0 END) AS med_session,
        MAX(CASE WHEN w.booking_flow_stage = 'Search' THEN 1 ELSE 0 END) AS reached_search,
        MAX(CASE WHEN w.page_type = 'search_results' THEN 1 ELSE 0 END) AS reached_results,
        MAX(CASE WHEN w.booking_flow_stage = 'Checkout' THEN 1 ELSE 0 END) AS reached_checkout,
        MAX(CASE WHEN w.page_type = 'just_booked' THEN 1 ELSE 0 END) AS booked,
        MAX(w.certificate_id) AS certificate_id
    FROM {W} w
    WHERE w.session_start_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type
)
SELECT 'TY' AS yr,
    ss.device_type,
    CASE
        WHEN ss.hit_screening = 1 AND ss.med_session = 1 THEN 'Screening + Medical declared'
        WHEN ss.hit_screening = 1 AND ss.med_session = 0 THEN 'Screening (no medical)'
        ELSE 'No screening page'
    END AS screening_segment,
    COUNT(DISTINCT ss.session_id) AS sessions,
    SUM(ss.reached_search) AS search_sessions,
    SUM(ss.reached_results) AS results_sessions,
    SUM(ss.reached_checkout) AS checkout_sessions,
    SUM(ss.booked) AS booked_sessions,
    SAFE_DIVIDE(SUM(ss.booked), COUNT(DISTINCT ss.session_id)) AS conversion_rate,
    SUM(p.policy_count) AS policies,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_gp_per_policy,
    SUM(CAST(p.total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_price,
    SUM(CAST(p.medical_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_medical_premium
FROM session_screening_ty ss
LEFT JOIN {P} p ON CAST(p.certificate_id AS STRING) = ss.certificate_id
    AND p.transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY ss.device_type, screening_segment

UNION ALL

SELECT 'LY' AS yr, ss.device_type,
    CASE
        WHEN ss.hit_screening = 1 AND ss.med_session = 1 THEN 'Screening + Medical declared'
        WHEN ss.hit_screening = 1 AND ss.med_session = 0 THEN 'Screening (no medical)'
        ELSE 'No screening page'
    END AS screening_segment,
    COUNT(DISTINCT ss.session_id),
    SUM(ss.reached_search), SUM(ss.reached_results),
    SUM(ss.reached_checkout), SUM(ss.booked),
    SAFE_DIVIDE(SUM(ss.booked), COUNT(DISTINCT ss.session_id)),
    SUM(p.policy_count),
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)),
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0),
    SUM(CAST(p.total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0),
    SUM(CAST(p.medical_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0)
FROM (
    SELECT w.session_id, w.device_type,
        MAX(CASE WHEN w.page_type = 'screening' THEN 1 ELSE 0 END) AS hit_screening,
        MAX(CASE WHEN w.med_session = TRUE THEN 1 ELSE 0 END) AS med_session,
        MAX(CASE WHEN w.booking_flow_stage = 'Search' THEN 1 ELSE 0 END) AS reached_search,
        MAX(CASE WHEN w.page_type = 'search_results' THEN 1 ELSE 0 END) AS reached_results,
        MAX(CASE WHEN w.booking_flow_stage = 'Checkout' THEN 1 ELSE 0 END) AS reached_checkout,
        MAX(CASE WHEN w.page_type = 'just_booked' THEN 1 ELSE 0 END) AS booked,
        MAX(w.certificate_id) AS certificate_id
    FROM {W} w
    WHERE w.session_start_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type
) ss
LEFT JOIN {P} p ON CAST(p.certificate_id AS STRING) = ss.certificate_id
    AND p.transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY ss.device_type, screening_segment
"""
    }

    # Track 19: Cover Level Upsell from Web — what users search vs what they buy
    tracks['web_cover_level_outcome'] = {
        'name': 'Web Insurance Group to Cover Level Outcome',
        'desc': 'Joins the insurance_group seen during web sessions to the actual cover level purchased. Reveals whether users who browse on different schemes/groups end up buying higher or lower cover, and how GP differs. Identifies upsell opportunities and mismatches between web browsing and purchase.',
        'sql': f"""
WITH web_sessions_ty AS (
    SELECT
        w.session_id,
        w.device_type,
        MAX(w.insurance_group) AS web_insurance_group,
        MAX(w.scheme_name) AS web_scheme,
        MAX(w.certificate_id) AS certificate_id
    FROM {W} w
    WHERE w.session_start_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
      AND w.certificate_id IS NOT NULL
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type
)
SELECT 'TY' AS yr,
    ws.web_insurance_group,
    ws.device_type,
    p.cover_level_name,
    p.cover_level_tier,
    p.policy_type,
    SUM(p.policy_count) AS policies,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_gp,
    SUM(CAST(p.total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_price,
    SUM(CAST(p.option_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_option_premium,
    SUM(CAST(p.total_gadget_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_gadget_premium,
    COUNT(DISTINCT ws.session_id) AS converting_sessions
FROM web_sessions_ty ws
JOIN {P} p ON CAST(p.certificate_id AS STRING) = ws.certificate_id
    AND p.transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY ws.web_insurance_group, ws.device_type, p.cover_level_name, p.cover_level_tier, p.policy_type
HAVING ABS(SUM(p.policy_count)) >= 2

UNION ALL

SELECT 'LY' AS yr,
    ws.web_insurance_group, ws.device_type,
    p.cover_level_name, p.cover_level_tier, p.policy_type,
    SUM(p.policy_count),
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)),
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0),
    SUM(CAST(p.total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0),
    SUM(CAST(p.option_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0),
    SUM(CAST(p.total_gadget_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0),
    COUNT(DISTINCT ws.session_id)
FROM (
    SELECT w.session_id, w.device_type,
        MAX(w.insurance_group) AS web_insurance_group,
        MAX(w.certificate_id) AS certificate_id
    FROM {W} w
    WHERE w.session_start_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
      AND w.certificate_id IS NOT NULL
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type
) ws
JOIN {P} p ON CAST(p.certificate_id AS STRING) = ws.certificate_id
    AND p.transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY ws.web_insurance_group, ws.device_type, p.cover_level_name, p.cover_level_tier, p.policy_type
HAVING ABS(SUM(p.policy_count)) >= 2
"""
    }

    # Track 20: Session Depth vs Policy Outcome
    tracks['session_depth_outcome'] = {
        'name': 'Session Engagement Depth vs Trading Outcome',
        'desc': 'Measures how deep into the funnel sessions go (by counting distinct page types visited) and links that to conversion and GP. Separates sessions into light browsers (1-2 pages), engaged browsers (3-4 pages), and deep explorers (5+), then shows conversion rate and GP for each depth bucket by device. Answers: are we losing money because people bounce early, or because deep-funnel users are not converting?',
        'sql': f"""
WITH session_depth_ty AS (
    SELECT
        w.session_id,
        w.device_type,
        COUNT(DISTINCT w.page_type) AS pages_visited,
        MAX(CASE WHEN w.page_type = 'just_booked' THEN 1 ELSE 0 END) AS converted,
        MAX(w.certificate_id) AS certificate_id
    FROM {W} w
    WHERE w.session_start_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type
),
bucketed_ty AS (
    SELECT *,
        CASE
            WHEN pages_visited <= 2 THEN '1-2 pages (light)'
            WHEN pages_visited <= 4 THEN '3-4 pages (engaged)'
            ELSE '5+ pages (deep)'
        END AS depth_bucket
    FROM session_depth_ty
)
SELECT 'TY' AS yr,
    b.depth_bucket,
    b.device_type,
    COUNT(DISTINCT b.session_id) AS sessions,
    SUM(b.converted) AS converted_sessions,
    SAFE_DIVIDE(SUM(b.converted), COUNT(DISTINCT b.session_id)) AS conversion_rate,
    SUM(p.policy_count) AS policies,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_gp,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(b.converted), 0) AS gp_per_converted_session
FROM bucketed_ty b
LEFT JOIN {P} p ON CAST(p.certificate_id AS STRING) = b.certificate_id
    AND p.transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY b.depth_bucket, b.device_type

UNION ALL

SELECT 'LY' AS yr, b.depth_bucket, b.device_type,
    COUNT(DISTINCT b.session_id),
    SUM(b.converted),
    SAFE_DIVIDE(SUM(b.converted), COUNT(DISTINCT b.session_id)),
    SUM(p.policy_count),
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)),
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0),
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(b.converted), 0)
FROM (
    SELECT sd.*,
        CASE
            WHEN sd.pages_visited <= 2 THEN '1-2 pages (light)'
            WHEN sd.pages_visited <= 4 THEN '3-4 pages (engaged)'
            ELSE '5+ pages (deep)'
        END AS depth_bucket
    FROM (
        SELECT w.session_id, w.device_type,
            COUNT(DISTINCT w.page_type) AS pages_visited,
            MAX(CASE WHEN w.page_type = 'just_booked' THEN 1 ELSE 0 END) AS converted,
            MAX(w.certificate_id) AS certificate_id
        FROM {W} w
        WHERE w.session_start_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
          AND w.device_type IN ('mobile','computer','tablet')
        GROUP BY w.session_id, w.device_type
    ) sd
) b
LEFT JOIN {P} p ON CAST(p.certificate_id AS STRING) = b.certificate_id
    AND p.transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY b.depth_bucket, b.device_type
"""
    }

    # Track 21: Cost Decomposition — commission, NTU, IPT, UW as % of gross
    tracks['cost_decomposition'] = {
        'name': 'Cost Decomposition vs Price Growth',
        'desc': 'Breaks out commission, underwriter cost, IPT, and net GP as a percentage of total gross price paid by the customer. Compares whether each cost line grew faster or slower than the price customers paid, split by channel and policy type. Answers: is margin shrinking because costs are rising faster than revenue, or because of mix?',
        'sql': f"""
SELECT 'TY' AS yr, distribution_channel, policy_type,
    SUM(policy_count) AS policies,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) AS total_gross,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price,
    SUM(CAST(total_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_ipt,
    SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_commission,
    SUM(CAST(total_net_to_underwriter_inc_gadget AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_uw_cost,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp,
    -- As % of gross price
    SAFE_DIVIDE(SUM(CAST(total_ipt AS FLOAT64)), SUM(CAST(total_gross_inc_ipt AS FLOAT64))) AS ipt_pct_of_gross,
    SAFE_DIVIDE(SUM(CAST(total_paid_commission_value AS FLOAT64)), SUM(CAST(total_gross_inc_ipt AS FLOAT64))) AS commission_pct_of_gross,
    SAFE_DIVIDE(SUM(CAST(total_net_to_underwriter_inc_gadget AS FLOAT64)), SUM(CAST(total_gross_inc_ipt AS FLOAT64))) AS uw_pct_of_gross,
    SAFE_DIVIDE(SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)), SUM(CAST(total_gross_inc_ipt AS FLOAT64))) AS gp_margin_pct,
    -- Discount as % of gross
    SAFE_DIVIDE(SUM(CAST(total_discount_value AS FLOAT64)), SUM(CAST(total_gross_inc_ipt AS FLOAT64))) AS discount_pct_of_gross,
    -- Medical and gadget components
    SUM(CAST(medical_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_medical_premium,
    SUM(CAST(total_gadget_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gadget_premium,
    SUM(CAST(option_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_option_premium
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY distribution_channel, policy_type
UNION ALL
SELECT 'LY', distribution_channel, policy_type,
    SUM(policy_count),
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)),
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_net_to_underwriter_inc_gadget AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SAFE_DIVIDE(SUM(CAST(total_ipt AS FLOAT64)), SUM(CAST(total_gross_inc_ipt AS FLOAT64))),
    SAFE_DIVIDE(SUM(CAST(total_paid_commission_value AS FLOAT64)), SUM(CAST(total_gross_inc_ipt AS FLOAT64))),
    SAFE_DIVIDE(SUM(CAST(total_net_to_underwriter_inc_gadget AS FLOAT64)), SUM(CAST(total_gross_inc_ipt AS FLOAT64))),
    SAFE_DIVIDE(SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)), SUM(CAST(total_gross_inc_ipt AS FLOAT64))),
    SAFE_DIVIDE(SUM(CAST(total_discount_value AS FLOAT64)), SUM(CAST(total_gross_inc_ipt AS FLOAT64))),
    SUM(CAST(medical_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_gadget_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(option_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY distribution_channel, policy_type
"""
    }

    # Track 22: Conversion-to-GP Bridge — web traffic × conversion rate × avg GP by device
    tracks['conversion_gp_bridge'] = {
        'name': 'Traffic × Conversion × Price × GP Bridge',
        'desc': 'Decomposes the web funnel into: sessions × session-to-search rate × search-to-book rate, by device. Separately shows policy-level GP decomposition (volume × price × margin%). Answers: is it a traffic problem, a conversion problem, a price problem, or a cost problem?',
        'sql': f"""
SELECT 'TY' AS yr, 'web' AS source, device_type,
    COUNT(DISTINCT session_id) AS sessions,
    COUNT(DISTINCT visitor_id) AS visitors,
    COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Search' THEN session_id END) AS search_sessions,
    COUNT(DISTINCT CASE WHEN page_type = 'just_booked' THEN session_id END) AS booked_sessions,
    SAFE_DIVIDE(
        COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Search' THEN session_id END),
        COUNT(DISTINCT session_id)
    ) AS session_to_search,
    SAFE_DIVIDE(
        COUNT(DISTINCT CASE WHEN page_type = 'just_booked' THEN session_id END),
        COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Search' THEN session_id END)
    ) AS search_to_book
FROM {W}
WHERE session_start_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
  AND device_type IN ('mobile','computer','tablet')
GROUP BY device_type

UNION ALL

SELECT 'LY', 'web', device_type,
    COUNT(DISTINCT session_id),
    COUNT(DISTINCT visitor_id),
    COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Search' THEN session_id END),
    COUNT(DISTINCT CASE WHEN page_type = 'just_booked' THEN session_id END),
    SAFE_DIVIDE(
        COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Search' THEN session_id END),
        COUNT(DISTINCT session_id)
    ),
    SAFE_DIVIDE(
        COUNT(DISTINCT CASE WHEN page_type = 'just_booked' THEN session_id END),
        COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Search' THEN session_id END)
    )
FROM {W}
WHERE session_start_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
  AND device_type IN ('mobile','computer','tablet')
GROUP BY device_type
"""
    }

    return tracks


# ---------------------------------------------------------------------------
# SYSTEM PROMPT — the analyst's brain
# ---------------------------------------------------------------------------

ANALYSIS_SYSTEM = dedent("""\
You are an expert autonomous insurance trading analyst for Holiday Extras (HX).

You have been given COMPREHENSIVE investigation data: baseline trading metrics,
22 deterministic investigation tracks covering every trading dimension (each comparing
this year vs last year), INCLUDING 7 cross-table tracks that JOIN web session behaviour
to policy trading outcomes (tracks 14-20), PLUS 2 cost/revenue decomposition tracks (21-22), AND full market intelligence from Google Sheets.

The cross-table tracks are particularly powerful — they connect the dots between web
journeys and trading results:
- web_to_gp_bridge: Which device/scheme/medical journeys produce the highest GP
- funnel_value_dropoff: Where high-value vs low-value customers drop off
- annual_vs_single_conversion: How annual vs single conversion paths differ
- multi_search_gp_impact: Whether multi-search sessions convert better and GP impact
- medical_screening_funnel: Medical screening's specific effect on conversion by device
- web_cover_level_outcome: What users browse vs what they actually buy
- session_depth_outcome: Session engagement depth linked to GP outcomes
- cost_decomposition: Commission, UW, IPT, discount as % of gross — are costs growing faster than price?
- conversion_gp_bridge: Traffic × conversion × price × margin decomposition by device

Your job is to ANALYZE all of this data and produce structured findings.

## LIFETIME VALUE STRATEGY (critical — DO NOT flag annual pricing as a problem)

HX deliberately runs NEGATIVE MARGINS on annual policies via aggregators.
Annual pricing is ALWAYS managed internally. Do NOT flag negative margins on
annual policies as a problem, concern, or action item.

Instead focus on: VOLUME trends, SINGLE TRIP losses, CONVERSION changes,
MIX SHIFTS, MARKET CONTEXT, COMMISSION changes.

## TRAFFIC & CONVERSION — ALWAYS DECOMPOSE

For EVERY growth or decline you identify, decompose the movement into its traffic and
conversion components. Traffic is often the dominant driver, so never attribute a change
purely to pricing, mix, or margin without first checking whether traffic moved.

- **Traffic**: Sessions/visits YoY and WoW by channel (direct, aggregator, renewal).
  If traffic is up or down significantly, say so prominently — it usually explains a
  large portion of volume and GP changes.
- **Conversion**: Search-to-book rate, session-to-search rate, quote-to-buy rate.
  If conversion shifted, quantify it and explain what drove the change (device mix,
  medical screening, cover level, etc.).
- **The bridge**: Always think Traffic × Conversion × Average GP = Total GP.
  When explaining a mover, state which of these three levers moved and by how much.
  e.g. "Direct single-trip GP fell £8k — mostly traffic (sessions down 12% YoY) with
  conversion flat and average GP slightly up."

## YOUR TASK

1. **MATERIAL MOVERS**: You MUST ALWAYS identify exactly 8 movers — the 8 segments with the
   largest absolute weekly GP impact. There is NO minimum threshold — even if the movement is
   small, list it. NEVER return an empty material_movers list. Rank by absolute £ impact. For each:
   - Quantify the exact £ impact
   - **ALWAYS decompose into traffic × conversion × average GP** — state which lever(s) moved
   - Traffic changes are often the biggest driver — never skip this. Quote session/visit YoY %
   - If conversion moved, explain why (device mix, medical screening, funnel changes, etc.)
   - Identify the root cause (volume? price? mix? commission? conversion? traffic?)
   - Cross-reference with market intelligence data
   - Explain whether this is temporary or structural
   - **PERSISTENCE CHECK**: Look at the last 10 trading days for this metric. Count how many
     days the movement was in the same direction (e.g. GP below last year on 8 of 10 days):
     - **RECURRING** (7+ of last 10 days consistent): A persistent pattern. Gets 5 drill-downs.
     - **EMERGING** (5-6 of last 10 days consistent): Building momentum, not yet entrenched. Gets 4 drill-downs.
     - **NEW** (fewer than 5 of last 10 days): A recent shift or one-off. Gets 3 drill-downs.
     State the count explicitly in your detail, e.g. "This has been negative on 8 of the last 10 days."

2. **CROSS-REFERENCES**: Look for connections between tracks:
   - Does a mix shift in one track explain a margin change in another?
   - Does a demographic shift explain a conversion change?
   - Do market trends explain internal volume changes?

3. **FOLLOW-UP QUESTIONS**: You MUST identify follow-up items:
   - 1 scan_drive call to check for recent pricing/campaign/release docs (insurance only)
   - 1 web_search for external market context
   - **RECURRING movers** (persistence="recurring"): 5 SQL drill-down queries each
   - **EMERGING movers** (persistence="emerging"): 4 SQL drill-down queries each
   - **NEW movers** (persistence="new"): 3 SQL drill-down queries each
   For example: 3 recurring + 3 emerging + 2 new = 3×5 + 3×4 + 2×3 = 33 SQL queries.
   Each SQL drill for a mover must explore a DIFFERENT dimension. Label them:
   `-- Mover N drill M: [what you're investigating]`
   Choose dimensions from: cover_level_name, scheme_name, booking_source (web vs phone),
   device_type (direct only — NOT for aggregators/renewals), age, max_medical_score_grouped,
   product, trip_duration_band, days_to_travel, cover_area, cruise flag, number_of_travellers,
   discount_value, commission fields

4. **RECONCILIATION**: Sum all identified £ drivers. Compare to the headline GP
   variance. Flag any unexplained residual >£5k.

## OUTPUT FORMAT

Output ONLY raw JSON (no markdown code fences, no commentary before or after).
Use negative numbers for negative values (not +2500, just 2500 or -2500).

{
  "status": "analyzed",
  "material_movers": [
    {
      "driver": "Short name",
      "impact_gbp_weekly": 5000,
      "direction": "down",
      "detail": "Full explanation with numbers",
      "evidence": "Which tracks proved this",
      "cross_references": "How this connects to other findings",
      "temporary_or_structural": "temporary / structural",
      "persistence": "new / recurring / emerging",
      "segment_filter": "SQL WHERE clause that isolates this segment, e.g. distribution_channel='Direct' AND policy_type='Single Trip'",
      "metric": "The primary metric being tracked, e.g. 'gp' or 'policy_count' or 'avg_gp'"
    }
  ],
  "conversion": {
    "session_to_search_ty": 0.55,
    "session_to_search_ly": 0.58,
    "search_to_book_ty": 0.08,
    "search_to_book_ly": 0.09,
    "funnel_bottlenecks": "Where in the funnel and on which device",
    "detail": "Explanation"
  },
  "market_context": "How external trends connect to internal numbers",
  "follow_up_questions": [
    {
      "question": "What specific thing to investigate",
      "why": "What gap this fills in the story",
      "tool": "run_sql",
      "args": {"sql": "SELECT ..."}
    }
  ],
  "reconciliation": {
    "headline_gp_variance": 5000,
    "explained_total": 4200,
    "unexplained_residual": 800
  },
  "track_coverage": {
    "channel_product_mix": "Key finding or 'No material movement'",
    "scheme_performance": "...",
    "medical_profile": "...",
    "cover_level_mix": "...",
    "commission_partners": "...",
    "customer_demographics": "...",
    "destination_mix": "...",
    "cancellations": "...",
    "renewals": "...",
    "web_funnel_detailed": "...",
    "day_of_week": "...",
    "discounts_campaigns": "...",
    "cruise": "...",
    "web_to_gp_bridge": "...",
    "funnel_value_dropoff": "...",
    "annual_vs_single_conversion": "...",
    "multi_search_gp_impact": "...",
    "medical_screening_funnel": "...",
    "web_cover_level_outcome": "...",
    "session_depth_outcome": "...",
    "cost_decomposition": "...",
    "conversion_gp_bridge": "..."
  }
}
""") + SCHEMA_KNOWLEDGE + ("\n\n## BUSINESS CONTEXT (from trading_context.md)\n" + TRADING_CONTEXT if TRADING_CONTEXT else "")


FOLLOW_UP_SYSTEM = dedent("""\
You are an expert insurance trading analyst for Holiday Extras (HX).
You have already analyzed 22 investigation tracks (13 trading + 7 cross-table web×trading + 2 cost/conversion decomposition)
and identified material movers. Now you are investigating SPECIFIC follow-up questions
to fill gaps in the story and build the full picture.

## YOUR TOOLS
1. **run_sql** — query BigQuery (auto-corrects common mistakes)
2. **fetch_market_data** — pull from Google Sheets market intelligence
3. **web_search** — external market context, competitor news, regulatory changes.
   Returns results WITH SOURCE URLs — always preserve these URLs in your findings so
   the synthesis stage can cite them in the briefing.
4. **scan_drive** — recently modified Google Drive docs (pricing, campaigns, releases).
   IMPORTANT: scan_drive searches YOUR Google Drive files — only files you own or that are
   shared with you. This means insurance-related documents. Files about Adventures/Shortbreaks
   (WB, Paultons, Warner Brothers) are automatically filtered out — you only care about
   insurance (cover) documents.

## INVESTIGATION PROTOCOL — DEEP DIVES PER MOVER (persistence-aware)

Each mover has a `persistence` field set during analysis:
- **"recurring"** = issue shows in both 7d AND 28d trends (same direction). These get **5 SQL drills** each.
- **"new"** = only appears in 7d data, or reversed in 28d. These get **3 SQL drills** each.

This means typical total: 24-40 SQL follow-up queries depending on how many are recurring.

**IMPORTANT: Label every SQL query with the mover number and drill number in a comment.**
Format: `-- Mover N drill M: [description of what you're investigating]`
Example: `-- Mover 2 drill 1: Aggregator growth broken out by booking_source (web vs call centre)`

For RECURRING movers, drills 4-5 should go DEEPER than drills 1-3:
- Drill 4: Compare the issue across multiple recent weeks (is it accelerating or decelerating?)
- Drill 5: Cross-cut with a second dimension (e.g. cover_level × booking_source) to find the exact sub-segment

### Round 1 — BREADTH + CONTEXT (mandatory, use ALL 4 tool types + first drills)
- **scan_drive**: Check for recent internal changes — insurance only
- **web_search**: External market context for the biggest movers
- **fetch_market_data**: Pull AI Insights tab — read EVERY insight, they are ALL relevant
- **run_sql**: First drill on movers 1-3 (3 queries)

### Round 2 — DRILL MOVERS 1-4 (mandatory)
Run 8+ SQL queries: drills 2-3 for movers 1-3, plus all 3 drills for mover 4
- Each drill explores a DIFFERENT dimension than the previous drills for that mover

### Round 3 — DRILL MOVERS 5-8 (mandatory)
Run 8+ SQL queries: 2 drills for each of movers 5-8
- Same approach — find the sub-dimension that explains WHY each mover moved

### Round 4 — COMPLETE REMAINING DRILLS (mandatory)
Run remaining drill 3 for movers 5-8 (4+ queries)
- Ensure every mover has exactly 3 completed drills
- Cross-reference findings with market intelligence data

### Round 5 — EMERGING + RECURRING DEEP DIVES (mandatory if any emerging/recurring movers exist)
Run drill 4 for ALL emerging movers and drills 4-5 for ALL recurring movers:
- Drill 4: Week-over-week trend for this specific segment (last 4-6 weeks) — is it getting worse?
- Drill 5 (RECURRING only): Cross-dimensional cut to isolate the exact sub-segment driving it

### Round 6 — COMPLETE RECURRING DRILLS + RECONCILE
- Finish any remaining drill 5s for recurring movers
- Check reconciliation: >£2k unexplained GP residual?

### Round 7+ — RECONCILE AND OUTPUT
- Check: every NEW mover has 3 drills? Every EMERGING mover has 4 drills? Every RECURRING mover has 5 drills?
- Output refined findings as JSON

## DRILL-DOWN DIMENSIONS (choose the most relevant for each mover)
- **cover_level_name** — Gold/Silver/Bronze breakdown
- **policy_type** — Annual vs Single trip
- **booking_source** — Web vs Phone (call centre vs online). KEY METRIC for understanding channel behaviour
- **device_type** — Mobile/Desktop/Tablet (from web table — only relevant for Direct channel, NOT for aggregators or renewals)
- **medical_screened** / **max_medical_score_grouped** — medical vs non-medical
- **cruise** — cruise vs non-cruise (via scheme_name/campaign_name containing 'cruise'/'CRU')
- **age** / age bands — customer age profile
- **trip_duration** / **trip_duration_band** — trip length
- **days_to_travel** — booking lead time / lag
- **product** — product name
- **scheme_name** — specific scheme within channel
- **cover_area** — Europe/Worldwide/UK
- **number_of_travellers** — group size
- **discount rate** — calculated as: SUM(total_discount_value) / (SUM(total_gross_inc_ipt) + SUM(total_discount_value)).
  This gives the true average discount rate as a % of the pre-discount price. Use this when investigating
  whether discounting is driving margin changes.
- **commission** fields — commission rates (total_paid_commission_value, total_paid_commission_perc)

### WEB vs TRADING DIMENSION RULES
- **Aggregators** and **Renewals** do NOT have a conventional web journey in our data — drill these
  ONLY via the trading table (insurance_policies_new). Do NOT try to join web data for these channels.
- **Direct** channel DOES have web journey data — you CAN drill by device_type, page_type, funnel stage
  for direct channel movers using the web table (insurance_web_utm_4)
- **booking_source** (Web/Phone) is available for ALL channels in the trading table

For each mover, pick 3 DIFFERENT dimensions across the 3 drills to build a complete picture.
Example for "Direct Single Trip margin drop":
  - Drill 1: by cover_level_name + scheme_name (which products?)
  - Drill 2: by booking_source + age band (who's buying how?)
  - Drill 3: by device_type via web table (where in the online funnel?)

## MINIMUM REQUIREMENTS BEFORE OUTPUT
- Each NEW mover MUST have exactly 3 SQL drill-downs
- Each EMERGING mover MUST have exactly 4 SQL drill-downs (3 standard + 1 deep)
- Each RECURRING mover MUST have exactly 5 SQL drill-downs (3 standard + 2 deep)
- ALL AI Insights from the market sheet must be read and incorporated
- At least 1 scan_drive result incorporated
- At least 1 web_search result incorporated
- Total SQL follow-up queries: minimum 24 (more if recurring movers exist)

## CRITICAL SQL RULES for insurance_policies_new:
- SUM(policy_count) for policy counts — NEVER COUNT(*)
- SUM(CAST(col AS FLOAT64)) / NULLIF(SUM(policy_count), 0) for averages — NEVER AVG()
- transaction_date is DATE — use directly, no EXTRACT()
- Fully qualified table names: `hx-data-production.commercial_finance.insurance_policies_new`

## OUTPUT RULES
- For EVERY tool call, explain WHY you are making it and what gap it fills
- After all follow-ups, output your refined findings as JSON matching the analysis structure
- Include any new material_movers discovered, updated market_context, and recent_changes

## LIFETIME VALUE NOTE
Annual policy pricing is ALWAYS managed internally.
Do NOT flag annual margins as problems. Single trip losses ARE problems.
""") + SCHEMA_KNOWLEDGE + ("\n\n## BUSINESS CONTEXT (from trading_context.md)\n" + TRADING_CONTEXT if TRADING_CONTEXT else "")


SYNTHESIS_SYSTEM = dedent("""\
You are producing the HX Insurance Daily Trading Briefing. Your reader is a commercial
manager who has 30 seconds before their first meeting. They are not an analyst. They need
to know: what happened, is it good or bad, and what should I do about it.

## VOICE AND TONE RULES

1. **Write like a sharp colleague talking across the desk**, not like a report. Say "we sold"
   not "policy volume increased". Say "margin got squeezed" not "per-policy GP contracted".
2. **Every number needs context.** Never say "GP was £168k". Say "GP was £168k — down £11k
   on last year, about 6% worse." Always give the direction, the size of the change, and what it means.
3. **Round aggressively.** £892.67 becomes "about £900". £10,864 becomes "£11k". 14.3% becomes "14%".
4. **No jargon without translation.** "GP" is fine. But don't say "attach rate compression"
   — say "fewer people are adding gadget cover or upgrades".
5. **Short sentences.** If a sentence has a comma followed by another clause followed by another comma, break it up.
6. **Never pad.** If a dimension had no meaningful movement, do not mention it at all. Silence means "nothing to report."
7. **Every claim must state its timeframe.** Never say "GP dropped £11k" — say "GP dropped £11k
   over the last 7 days vs the same week last year." Never say "volumes are up" — say "yesterday's
   volumes were up 12% vs the same day last year." Valid timeframes: "yesterday vs same day last year",
   "over the last 7 days vs same period last year", "trailing 28 days", "week-on-week". The reader
   must always know WHEN you are talking about.

## CRITICAL BUSINESS CONTEXT

- HX deliberately runs negative margins on ANNUAL policies — this is an acquisition strategy.
  Annual volume growth is ALWAYS good news. NEVER flag annual negative margins as a problem or suggest repricing annuals.
- Single trip losses have no renewal pathway. These ARE problems worth flagging.
- Frame annual growth as: "We're investing in future renewal income."
- **TRAFFIC & CONVERSION are primary levers.** When explaining any growth or decline, always
  reference whether traffic (sessions/visits) and/or conversion rates contributed. Traffic is
  usually the biggest factor — if sessions are up 15% YoY, say so prominently. Don't just say
  "volume is up" without explaining whether that's traffic-driven or conversion-driven.

## OUTPUT FORMAT

The briefing has exactly 3 tiers. The reader should get the full picture from Tier 1 alone
(10 seconds). Tier 2 adds colour (30 seconds). Tier 3 is optional drill-down.

FORMAT (markdown):

---
# HX Trading Briefing — {DD Mon YYYY}

## {HEADLINE}

_One sentence. What is the single most important thing that happened? Write it like a newspaper
headline expanded into one line. No emoji. No hedging. MUST include the timeframe (e.g. "yesterday",
"over the last week", "this week vs last year")._

---

## At a Glance

- {traffic light emoji} **{Short label}** — {One sentence with numbers and context}
- {traffic light emoji} **{Short label}** — {One sentence with numbers and context}
- {traffic light emoji} **{Short label}** — {One sentence with numbers and context}

_3 to 5 bullets maximum. Each bullet is ONE sentence. Use:_
- 🔴 for things losing us money or getting worse
- 🟢 for things making us money or improving
- 🟡 for things to watch that aren't yet a problem

_Order: biggest £ impact first, regardless of colour._

---

## What's Driving This

_This section contains ONLY the dimensions that moved materially. Each block is max 2 sentences
of plain English plus a SQL dig block. **Order: RECURRING issues first (biggest £ first within
recurring), then NEW issues (biggest £ first within new).** This prioritises persistent problems
that need deeper attention over one-off movements._

### {Driver name} `RECURRING` or `EMERGING` or `NEW`

{Sentence 1: What happened, in plain English, with rounded numbers and YOY/WOW context. ALWAYS mention traffic and/or conversion if they contributed — e.g. "sessions were up 15% but conversion dipped" or "traffic drove most of this, up 20% YoY".}
{Sentence 2: Why it happened — the cause, not just the symptom. Decompose into traffic × conversion × avg GP where relevant. For RECURRING issues, also note how long this has been going on (e.g. "This is the third straight week of decline").}

```sql-dig
{SQL query using real date literals, fully qualified table names, correct aggregation rules}
```

_Repeat for ALL 8 material movers. Every mover gets a block — no exceptions.
Each driver heading MUST include `RECURRING`, `EMERGING`, or `NEW` as a tag after the name._

---

## Customer Search Intent

_{3–6 sentences focused on Google Trends data and customer search behaviour. **Cite your sources.**
For every claim, attribute it: "According to Google Trends data..." or "Insurance Intent data shows..."
If a Google Trends link is available, include it as a markdown link.

Cover:
- How has travel insurance search intent changed vs last year? (specific % YoY)
- Which destinations, trip types, or products are trending up or down?
- Any notable spikes or dips in search volume and possible causes?
- Use data from the Insurance Intent and Dashboard Metrics tabs. Be specific with numbers.

Format source citations as: **Source:** [Name](URL) or **Source:** Google Sheets — Insurance Intent tab}_

---

## News & Market Context

_{4–8 sentences covering external factors that explain WHY trading numbers moved. **Every claim must cite a source.**
This section should feel like a mini market briefing — credible, specific, and well-sourced.

Cover as many of these as the data supports:
- Global news affecting travel demand (airline capacity, strikes, weather, geopolitical events)
- Competitor activity (pricing moves, new products, marketing campaigns)
- Regulatory or FCA changes affecting insurance
- Economic factors (consumer confidence, exchange rates, fuel prices)
- Travel trends (destination popularity, booking patterns)

For web search results, include the source as a markdown link: [Article Title](URL).
For AI Insights from the Google Sheet, cite as: **Source:** AI Insights — [insight name].
For Google Drive documents, cite as: **Source:** Internal — [document name].

If the market is genuinely quiet, say so in one sentence with a source confirming it.}_

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | {Specific action} | {Tied to a driver above} | ~£{X}k/week |
| 2 | {Specific action} | {Tied to a driver above} | ~£{X}k/week |

_Max 5 rows. Ordered by £ impact. Every action must link back to a driver above.
No vague actions like "monitor closely" — say what to actually do._

---

_Generated {HH:MM DD Mon YYYY} | {N} investigation tracks | {model}_

## WHAT TO SKIP

Do NOT include a section if the data shows no material movement. Specifically:
- Medical/non-medical: Only mention if margin or volume shifted meaningfully
- Cruise: Only mention if there's a notable change
- Customer demographics: Only mention if age/group mix shifted enough to affect GP
- Day-of-week patterns: Only mention if there's an actionable anomaly
- Discounts: Only mention if discount penetration changed enough to matter
- Cancellations: Only mention if cancellation rate or pattern changed
- Commission/partner economics: Only mention if partner margins shifted

If in doubt: does this change the reader's understanding or their next action? If no, leave it out.

## WHAT NEVER TO SKIP

ALWAYS cover ALL of these — there is NO minimum threshold:
- The overall GP number (headline + At a Glance)
- ALL 8 material movers: RECURRING first (by £ impact), then EMERGING (by £ impact), then NEW (by £ impact)
- Every mover gets a "What's Driving This" block with 2 sentences + SQL dig + RECURRING/EMERGING/NEW tag
- The At a Glance section should have 5 bullets covering the top 5 movers

## SQL DIG BLOCK RULES

- Use REAL DATE LITERALS (e.g., '2026-03-02'), never variables or functions
- Fully qualified table names: `hx-data-production.commercial_finance.insurance_policies_new`
- Policy counts: SUM(policy_count) — NEVER COUNT(*)
- Averages: SUM(CAST(col AS FLOAT64)) / NULLIF(SUM(policy_count), 0) — NEVER AVG()
- Web data: COUNT(DISTINCT session_id) or COUNT(DISTINCT visitor_id)
- transaction_date is DATE type — use directly, no EXTRACT()
- There is NO "period" column — never reference it

## ANTI-PATTERNS (do not do these)

- "Policy volume increased while per-policy GP contracted" → Say: "We sold more policies but made less on each one"
- "Attach rate compression observed" → Say: "Fewer people are adding extras like gadget cover"
- "Channel mix shift towards aggregator distribution" → Say: "More sales came through price comparison sites"
- Paragraphs longer than 3 sentences
- Sections with no material movement
- Numbers without YOY or WOW context
- Actions without a £ value attached
- Emoji in the headline (emoji is ONLY used for traffic light dots in At a Glance)

## LENGTH TARGET

The entire briefing, excluding SQL dig blocks, should be **under 600 words**. The extra allowance is for
source citations in the Customer Search Intent and News & Market Context sections — these sections should
be thorough and well-sourced. If you're over 600 words, cut from the What's Driving This descriptions first.
""") + ("\n\n## BUSINESS CONTEXT (from trading_context.md)\n" + TRADING_CONTEXT if TRADING_CONTEXT else "")


# ---------------------------------------------------------------------------
# THE AGENTIC LOOP
# ---------------------------------------------------------------------------

def _fetch_sheet_tab(tab_name, cell_range="A1:Z500"):
    """Fetch a single Google Sheet tab, returning list of dicts. Returns [] on error."""
    try:
        range_str = f"{tab_name}!{cell_range}"
        resp = SHEETS_SVC.spreadsheets().values().get(
            spreadsheetId=MARKET_SHEET_ID, range=range_str
        ).execute()
        rows = resp.get("values", [])
        if rows:
            headers = rows[0]
            return [dict(zip(headers, r)) for r in rows[1:]]
        return []
    except Exception as e:
        print(f"  ⚠ Failed to fetch sheet tab '{tab_name}': {e}")
        return []


def run_baseline_queries(date_params):
    """Phase 1: Pull all baseline data using explicit date parameters."""
    print("\n📊 Phase 1: Pulling baseline data...")
    trading = [dict(r) for r in BQ_CLIENT.query(build_baseline_trading_sql(date_params)).result()]
    print("  ✓ Trading summary")
    trend = [dict(r) for r in BQ_CLIENT.query(build_baseline_trend_sql(date_params)).result()]
    print("  ✓ 14-day trend")
    trend_ly = [dict(r) for r in BQ_CLIENT.query(build_baseline_trend_ly_sql(date_params)).result()]
    print("  ✓ 14-day trend LY")
    funnel = [dict(r) for r in BQ_CLIENT.query(build_baseline_funnel_sql(date_params)).result()]
    print("  ✓ Web funnel")
    web_engagement = [dict(r) for r in BQ_CLIENT.query(build_baseline_web_engagement_sql(date_params)).result()]
    print("  ✓ Web engagement (device, clicks, medical)")

    # Fetch ALL important Google Sheet tabs
    print("  Fetching market intelligence sheets...")

    ai_insights = _fetch_sheet_tab("AI Insights", "A1:Z500")
    print("  ✓ AI Insights (full)")

    market_demand = _fetch_sheet_tab("Market Demand Summary", "A1:Z500")
    print("  ✓ Market Demand Summary")

    section_trends = _fetch_sheet_tab("Dashboard Section Trends", "A1:Z500")
    print("  ✓ Dashboard Section Trends")

    dashboard_metrics = _fetch_sheet_tab("Dashboard Metrics", "A1:Z500")
    print("  ✓ Dashboard Metrics")

    dashboard_weekly = _fetch_sheet_tab("Dashboard Weekly", "A1:Z500")
    # Keep only last 20 rows for weekly data
    if len(dashboard_weekly) > 20:
        dashboard_weekly = dashboard_weekly[-20:]
    print("  ✓ Dashboard Weekly (recent 20 rows)")

    insurance_intent = _fetch_sheet_tab("Insurance Intent", "A1:Z500")
    # Keep only last 30 rows for insurance intent
    if len(insurance_intent) > 30:
        insurance_intent = insurance_intent[-30:]
    print("  ✓ Insurance Intent (recent 30 rows)")

    spike_log = _fetch_sheet_tab("Spike Log", "A1:Z500")
    print("  ✓ Spike Log")

    return {
        "trading": trading,
        "trend": trend,
        "trend_ly": trend_ly,
        "funnel": funnel,
        "web_engagement": web_engagement,
        "ai_insights": ai_insights,
        "market_demand_summary": market_demand,
        "section_trends": section_trends,
        "dashboard_metrics": dashboard_metrics,
        "dashboard_weekly": dashboard_weekly,
        "insurance_intent": insurance_intent,
        "spike_log": spike_log,
    }


def run_investigation_tracks(date_params):
    """Phase 2: Run ALL investigation tracks deterministically via BigQuery."""
    print("\n🔬 Phase 2: Running 22 investigation tracks...")
    tracks = build_investigation_tracks(date_params)
    results = {}
    errors = []

    for track_id, track in tracks.items():
        sql = track['sql']
        max_retries = 25
        success = False
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                if attempt == 1:
                    print(f"  📊 {track['name']}...")
                else:
                    print(f"     🔄 Retry {attempt}/{max_retries}...")
                job = BQ_CLIENT.query(sql)
                rows = [dict(r) for r in job.result()]
                results[track_id] = {
                    'name': track['name'],
                    'desc': track['desc'],
                    'data': rows[:300],
                    'row_count': len(rows),
                }
                print(f"     ✓ {len(rows)} rows")
                success = True
                break
            except Exception as e:
                last_error = str(e)
                print(f"     ⚠ Error (attempt {attempt}): {last_error[:120]}")
                if attempt >= max_retries:
                    break
                # Try deterministic auto-fix first
                fixed = _autofix_track_sql(sql, last_error)
                if fixed and fixed != sql:
                    print(f"     🔧 Auto-fixing and retrying...")
                    sql = fixed
                    continue
                # Deterministic fix didn't help — try AI fix
                print(f"     🤖 Asking AI to fix track SQL...")
                ai_fixed = _ai_fix_sql(sql, last_error)
                if ai_fixed and ai_fixed != sql:
                    sql = ai_fixed
                    # Re-apply autocorrect on AI output
                    recorrected, _ = _autocorrect_sql(sql)
                    if recorrected != sql:
                        sql = recorrected
                    continue
                # Both fixes returned same SQL — retry anyway (AI may produce different fix next time)
                print(f"     ⚠ Fix attempts returned same SQL — retrying with error context...")
                continue

        if not success:
            print(f"     ⚠ Failed after {max_retries} attempts: {last_error[:150]}")
            errors.append({'track': track_id, 'error': last_error})
            results[track_id] = {
                'name': track['name'],
                'desc': track['desc'],
                'data': [],
                'row_count': 0,
                'error': last_error,
            }

    if errors:
        print(f"  ⚠ {len(errors)} track(s) had errors")
    print(f"  ✓ All tracks complete")
    return results


def run_ai_analysis(baseline_data, track_results, run_date):
    """Phase 3: AI analyzes ALL track results and identifies material movers."""
    print("\n🧠 Phase 3: AI analysis of all investigation tracks...")

    analysis_date = run_date.strftime("%A %d %B %Y")
    yesterday = str(run_date)
    week_start = str(run_date - timedelta(days=7))

    # Build a compact summary of track results (trim large tracks to key rows)
    compact_tracks = {}
    for tid, tr in track_results.items():
        data = tr['data']
        # For large result sets, keep top rows by absolute GP impact
        if len(data) > 50:
            data = data[:50]
        compact_tracks[tid] = {
            'name': tr['name'],
            'desc': tr['desc'],
            'row_count': tr['row_count'],
            'data': data,
        }

    prompt = f"""The date being analysed is {analysis_date} (trailing 7 days: {week_start} to {yesterday}).

## BASELINE TRADING METRICS
```json
{json.dumps(baseline_data['trading'], indent=2, default=str)}
```

## WEB FUNNEL BASELINE
```json
{json.dumps(baseline_data['funnel'], indent=2, default=str)}
```

## WEB ENGAGEMENT BASELINE
```json
{json.dumps(baseline_data['web_engagement'], indent=2, default=str)}
```

## MARKET INTELLIGENCE (Google Sheets)
### AI Insights
```json
{json.dumps(baseline_data.get('ai_insights', []), indent=2, default=str)}
```
### Insurance Intent (Google Trends)
```json
{json.dumps(baseline_data.get('insurance_intent', [])[:15], indent=2, default=str)}
```
### Dashboard Section Trends
```json
{json.dumps(baseline_data.get('section_trends', [])[:20], indent=2, default=str)}
```
### Market Demand Summary
```json
{json.dumps(baseline_data.get('market_demand_summary', [])[:10], indent=2, default=str)}
```
### Spike Log
```json
{json.dumps(baseline_data.get('spike_log', [])[:10], indent=2, default=str)}
```

## INVESTIGATION TRACK RESULTS (22 tracks, each comparing TY vs LY)
```json
{json.dumps(compact_tracks, indent=2, default=str)}
```

Analyze ALL of this data. Identify every material mover, cross-reference between
tracks, and specify follow-up questions for gaps. Output as JSON per the system prompt."""

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=MODEL,
        max_completion_tokens=32768,
        messages=[
            {"role": "system", "content": ANALYSIS_SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )

    analysis_text = response.choices[0].message.content or ""
    finish_reason = response.choices[0].finish_reason
    print(f"  ✓ Analysis complete ({len(analysis_text)} chars, finish_reason={finish_reason})")

    if finish_reason == "length":
        print("  ⚠ WARNING: Analysis was TRUNCATED — output hit token limit!")

    # Parse the JSON findings — handle code fences and common JSON issues
    analysis = _parse_llm_json(analysis_text)

    # Diagnostic: check if material_movers was captured
    movers = analysis.get("material_movers", [])
    if not movers:
        print(f"  ⚠ WARNING: No material_movers found in parsed analysis!")
        print(f"  ⚠ Parsed keys: {list(analysis.keys())}")
        # If we got raw_analysis back, the JSON parse failed entirely
        if "raw_analysis" in analysis:
            print(f"  ⚠ JSON parsing failed — got raw_analysis fallback. First 500 chars: {analysis_text[:500]}")
    else:
        print(f"  ✓ Found {len(movers)} material movers")

    return analysis


def _parse_llm_json(text: str) -> dict:
    """Parse JSON from LLM output, handling code fences, formatting issues, and truncation."""
    import re

    def _fix_common_issues(s):
        """Fix common LLM JSON formatting issues."""
        s = re.sub(r':\s*\+(\d)', r': \1', s)  # +2500 → 2500
        s = re.sub(r':\s*(-?\d{1,3}),(\d{3}),(\d{3})', r': \1\2\3', s)  # 1,234,567 → 1234567
        s = re.sub(r':\s*(-?\d{1,3}),(\d{3})', r': \1\2', s)  # -3,487 → -3487
        s = re.sub(r',\s*}', '}', s)  # trailing commas
        s = re.sub(r',\s*]', ']', s)  # trailing commas in arrays
        return s

    def _try_repair(s):
        """Try to repair truncated JSON by closing open brackets."""
        repair = s.rstrip()
        # Remove trailing partial key-value (after last complete value)
        repair = re.sub(r',\s*"[^"]*"?\s*:?\s*"?[^"{}[\]]*$', '', repair)
        # Close any open strings
        if repair.count('"') % 2 == 1:
            repair += '"'
        # Count and close open brackets/braces
        open_brackets = repair.count('[') - repair.count(']')
        open_braces = repair.count('{') - repair.count('}')
        repair += ']' * max(0, open_brackets)
        repair += '}' * max(0, open_braces)
        repair = re.sub(r',\s*}', '}', repair)
        repair = re.sub(r',\s*]', ']', repair)
        return repair

    # Strip markdown code fences
    cleaned = text.replace("```json", "").replace("```", "")

    # Find the outermost JSON object
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start < 0:
        return {"status": "analyzed", "raw_analysis": text}

    if end > start:
        json_str = _fix_common_issues(cleaned[start:end])
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        # Try repair
        try:
            return json.loads(_try_repair(json_str))
        except json.JSONDecodeError:
            pass

    # If we get here, the full object didn't parse — likely truncated.
    # Try to repair from the start of the JSON to the end of text.
    json_str = _fix_common_issues(cleaned[start:])
    try:
        repaired = _try_repair(json_str)
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    # Last resort: try to extract material_movers array directly from the text.
    # Even if the full JSON is broken, the movers array at the top might be complete.
    # Use a balanced-bracket approach instead of non-greedy regex to handle escaped quotes
    mm_start = cleaned.find('"material_movers"')
    if mm_start >= 0:
        arr_start = cleaned.find('[', mm_start)
        if arr_start >= 0:
            # Find the matching closing bracket by counting depth
            depth = 0
            arr_end = -1
            for i in range(arr_start, len(cleaned)):
                c = cleaned[i]
                if c == '[': depth += 1
                elif c == ']': depth -= 1
                if depth == 0:
                    arr_end = i + 1
                    break
            if arr_end > arr_start:
                try:
                    movers_str = _fix_common_issues(cleaned[arr_start:arr_end])
                    movers = json.loads(movers_str)
                    print(f"  ⚠ Full JSON parse failed but extracted {len(movers)} material_movers directly")
                    return {"status": "analyzed", "material_movers": movers, "raw_analysis": text}
                except json.JSONDecodeError:
                    pass

    # Try an even more aggressive extraction — find all complete mover objects
    # Use json.loads validation rather than relying solely on regex for boundaries
    mover_objects = []
    for m in re.finditer(r'\{\s*"driver"\s*:', cleaned):
        # From each potential mover start, try expanding until we find valid JSON
        start = m.start()
        depth = 0
        for i in range(start, min(start + 2000, len(cleaned))):
            if cleaned[i] == '{': depth += 1
            elif cleaned[i] == '}': depth -= 1
            if depth == 0:
                try:
                    obj = json.loads(_fix_common_issues(cleaned[start:i+1]))
                    if 'driver' in obj:
                        mover_objects.append(obj)
                except json.JSONDecodeError:
                    pass
                break
    if mover_objects:
        print(f"  ⚠ Extracted {len(mover_objects)} mover objects via regex fallback")
        return {"status": "analyzed", "material_movers": mover_objects, "raw_analysis": text}

    return {"status": "analyzed", "raw_analysis": text}


def run_ai_follow_ups(analysis, baseline_data, run_date):
    """Phase 4: Execute AI-recommended follow-up queries with working memory."""
    print("\n🔍 Phase 4: AI-driven follow-up investigations...")

    follow_up_questions = analysis.get("follow_up_questions", [])
    # Safety net: if analysis didn't generate follow-ups, create mandatory ones
    if not follow_up_questions:
        print("  ⚠ No follow-ups from analysis — generating mandatory baseline follow-ups")
        movers = analysis.get("material_movers", [])
        top_mover = movers[0].get("driver", "the biggest GP mover") if movers else "GP changes"
        follow_up_questions = [
            {"question": f"Drill deeper into {top_mover}", "why": "The #1 driver needs more detail", "tool": "run_sql",
             "args": {"sql": "-- placeholder: will be generated by the LLM"}},
            {"question": "Check for recent internal changes", "why": "Were there pricing/campaign/release changes?", "tool": "scan_drive",
             "args": {"keywords": "pricing,scheme,medical,discount,campaign,release"}},
            {"question": "External market context", "why": "Something external may explain internal trends", "tool": "web_search",
             "args": {"query": "UK travel insurance market March 2026 competitor pricing trends"}},
        ]

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    follow_up_log = []

    # Working memory — accumulates findings across follow-up rounds
    working_memory = f"""## ANALYSIS FINDINGS SO FAR
Material movers: {json.dumps(analysis.get('material_movers', []), indent=2, default=str)[:2000]}
Conversion: {json.dumps(analysis.get('conversion', {}), indent=2, default=str)[:500]}
Market context: {str(analysis.get('market_context', ''))[:500]}
"""

    # Build initial messages with follow-up questions and tools
    analysis_date = run_date.strftime("%A %d %B %Y")
    messages = [
        {"role": "system", "content": FOLLOW_UP_SYSTEM},
        {"role": "user", "content": f"""Date: {analysis_date}. run_date = {run_date}.

{working_memory}

## FOLLOW-UP QUESTIONS TO INVESTIGATE
{json.dumps(follow_up_questions, indent=2, default=str)}

Additionally, scan Google Drive for any recent internal changes (pricing docs, campaigns,
releases) and check the market intelligence sheet for any additional context.

For EVERY tool call, explain WHY in your response text before calling the tool.
Investigate all follow-up questions, then output your refined findings as JSON."""},
    ]

    MAX_FOLLOW_UP_ROUNDS = 10
    for round_num in range(1, MAX_FOLLOW_UP_ROUNDS + 1):
        print(f"\n  --- Follow-up round {round_num} ---")

        # Force tool usage for first 7 rounds (recurring movers need 5 drills each)
        choice = "required" if round_num <= 7 else "auto"
        response = client.chat.completions.create(
            model=MODEL,
            max_completion_tokens=8192,
            messages=messages,
            tools=TOOLS,
            tool_choice=choice,
        )

        msg = response.choices[0].message
        messages.append(msg)

        reasoning = msg.content or ""
        if reasoning:
            print(f"  💭 {reasoning[:150]}...")

        if not msg.tool_calls:
            # Done — parse refined findings
            print(f"  ✓ Follow-ups complete after {round_num} rounds")
            final_text = msg.content or ""
            refined = _parse_llm_json(final_text)
            if "raw_analysis" in refined:
                refined = {"raw_follow_up": refined.get("raw_analysis", final_text)}
            return refined, follow_up_log

        # Execute tool calls
        print(f"  GPT requesting {len(msg.tool_calls)} tool call(s):")
        round_results_summary = []
        for tc in msg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments)
            print(f"    → {fn_name}({list(fn_args.keys())})")

            fn = TOOL_FUNCTIONS.get(fn_name)
            result = fn(**fn_args) if fn else f"Unknown tool: {fn_name}"

            follow_up_log.append({
                "round": round_num,
                "phase": "follow_up",
                "tool": fn_name,
                "args": fn_args,
                "result_preview": result[:500],
                "reasoning": reasoning,
            })

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

            # Summarize for working memory
            round_results_summary.append(
                f"- {fn_name}: {result[:200]}..."
            )

        # Update working memory with condensed results (context eviction)
        working_memory += f"\n## Follow-up Round {round_num} Summary\n"
        working_memory += "\n".join(round_results_summary[:5]) + "\n"

        # Add round-specific nudge messages
        if round_num < MAX_FOLLOW_UP_ROUNDS:
            if round_num == 1:
                nudge = (
                    f"Round 1 (breadth) complete. You should now have Drive scan, web search, "
                    f"market data, and drill 1 for movers 1-3. Now run drills 2-3 for movers 1-3, "
                    f"plus all 3 drills for mover 4 (8+ SQL queries). Remember: label each query "
                    f"'-- Mover N drill M: [what you're investigating]'. Each drill must use a "
                    f"DIFFERENT dimension than the other drills for that mover."
                )
            elif round_num == 2:
                nudge = (
                    f"Round 2 complete — movers 1-4 should have 3 drills each (12 drills total so far). "
                    f"Now drill movers 5-8: run 2 drills each (8 SQL queries). Remember to use "
                    f"booking_source, device_type (direct only), cover_level, age, medical, scheme "
                    f"and other relevant dimensions. Label every query."
                )
            elif round_num == 3:
                nudge = (
                    f"Round 3 complete — movers 5-8 should each have 2 drills. "
                    f"Now run drill 3 for movers 5-8 (4 more SQL queries) to complete the picture. "
                    f"Every mover must have exactly 3 drills before you can output."
                )
            elif round_num == 4:
                nudge = (
                    f"Round 4 complete. All 8 movers should now have 3 drills each (24 total). "
                    f"Now check which movers are marked as RECURRING (persistence='recurring'). "
                    f"For EACH recurring mover, you need 2 more drills (drills 4-5): "
                    f"Drill 4 = week-over-week trend for this segment (last 4-6 weeks). "
                    f"Drill 5 = cross-dimensional cut to isolate the exact sub-segment. "
                    f"Run these now."
                )
            elif round_num == 5:
                nudge = (
                    f"Round 5 complete. Continue running drill 4-5 for any remaining RECURRING "
                    f"movers. If all recurring drills are done, output your refined findings as JSON."
                )
            elif round_num == 6:
                nudge = (
                    f"Round 6 complete. All recurring movers should have 5 drills, all new movers "
                    f"should have 3 drills. Output your refined findings as JSON now. Every mover "
                    f"must reference ALL its drill-down findings and include the persistence flag."
                )
            else:
                nudge = (
                    f"Round {round_num} complete. Output your refined findings as JSON now."
                )
            messages.append({"role": "user", "content": nudge})

    # Hit max rounds
    print(f"  ⚠ Hit max follow-up rounds ({MAX_FOLLOW_UP_ROUNDS})")
    return {"raw_follow_up": "Max follow-up rounds reached"}, follow_up_log


def run_synthesis(baseline_data, analysis, follow_up_results, track_results, run_date):
    """Phase 5: Two-pass synthesis — draft then self-critique."""
    print("\n📝 Phase 5: Synthesising final briefing (two-pass)...")

    analysis_date = run_date.strftime("%A %d %B %Y")
    yesterday = str(run_date)
    week_start = str(run_date - timedelta(days=7))
    week_start_ly = str(run_date - timedelta(days=7) - timedelta(days=364))
    yesterday_ly = str(run_date - timedelta(days=364))

    # Merge analysis and follow-up findings
    merged_findings = dict(analysis)
    if isinstance(follow_up_results, dict):
        # Merge any additional material movers from follow-ups
        fu_movers = follow_up_results.get("material_movers", [])
        if fu_movers:
            merged_findings.setdefault("material_movers", []).extend(fu_movers)
        # Merge market context
        fu_context = follow_up_results.get("market_context", "")
        if fu_context:
            merged_findings["market_context"] = str(merged_findings.get("market_context", "")) + " " + str(fu_context)
        # Merge recent changes
        fu_changes = follow_up_results.get("recent_changes", "")
        if fu_changes:
            merged_findings["recent_changes"] = str(merged_findings.get("recent_changes", "")) + " " + str(fu_changes)

    prompt = f"""The date being analysed is {analysis_date}.
run_date = {run_date}

USE THESE DATE LITERALS in all sql-dig blocks (do NOT use a 'period' column — it doesn't exist):
- Yesterday: transaction_date = '{yesterday}'
- Trailing 7d: transaction_date BETWEEN '{week_start}' AND '{yesterday}'
- Trailing 7d LY: transaction_date BETWEEN '{week_start_ly}' AND '{yesterday_ly}'

## BASELINE METRICS
```json
{json.dumps(baseline_data['trading'], indent=2, default=str)}
```

## 14-DAY TREND
```json
{json.dumps(baseline_data['trend'], indent=2, default=str)}
```

## MARKET INTELLIGENCE — AI Insights (read ALL of these, every insight matters for News & Market Context)
```json
{json.dumps(baseline_data.get('ai_insights', []), indent=2, default=str)}
```

## CUSTOMER SEARCH INTENT — Insurance Intent / Google Trends (use for the "Customer Search Intent" section)
```json
{json.dumps(baseline_data.get('insurance_intent', []), indent=2, default=str)}
```

## DASHBOARD METRICS (search volume, demand signals)
```json
{json.dumps(baseline_data.get('dashboard_metrics', [])[:20], indent=2, default=str)}
```

## INVESTIGATED FINDINGS (from 22 tracks + AI analysis + follow-ups)
```json
{json.dumps(merged_findings, indent=2, default=str)}
```

## TRACK COVERAGE SUMMARY
{json.dumps({tid: tr['name'] + ': ' + str(tr['row_count']) + ' rows' for tid, tr in track_results.items()}, indent=2)}

Now produce the final briefing following the 3-tier format exactly:
1. Headline (one sentence, like a newspaper)
2. At a Glance (5 traffic light bullets, biggest £ first)
3. What's Driving This (ALL 8 movers: RECURRING first by £, then EMERGING by £, then NEW by £. Each needs RECURRING/EMERGING/NEW tag, 2 sentences + sql-dig)
4. Customer Search Intent (Google Trends / search behaviour data)
5. News & Market Context (AI Insights, competitor activity, external factors)
6. Actions table (max 5, with £ values)

Stay under 500 words (excluding sql-dig blocks). Write like a sharp colleague, not a report.
Round numbers aggressively. Every claim needs a £ figure and YoY context."""

    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    # Pass 1: Draft
    print("  📝 Pass 1: Draft...")
    draft_response = client.chat.completions.create(
        model=MODEL,
        max_completion_tokens=4096,
        messages=[
            {"role": "system", "content": SYNTHESIS_SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )
    draft = draft_response.choices[0].message.content or ""

    # Pass 2: Self-critique and refine
    print("  🔍 Pass 2: Self-critique...")
    critique_prompt = f"""Review this draft trading briefing against the investigation findings.

## DRAFT BRIEFING
{draft}

## INVESTIGATION FINDINGS
{json.dumps(merged_findings, indent=2, default=str)[:4000]}

CHECK:
1. Every £ claim has a specific number from the data (no made-up figures)
2. Every action item is specific enough to execute
3. The headline accurately reflects the single biggest impact
4. ALL material movers from the findings are covered (not just the top 2-3)
5. Annual policy margins are framed as strategic, not problematic
6. SQL dig blocks use real dates ({week_start} to {yesterday}), not a "period" column
7. Market intelligence is referenced with specific data points
8. Renewal and medical/cruise findings are included if material
9. Every numerical claim states an explicit timeframe (e.g. "over the last 7 days", "yesterday vs last year") — no orphaned numbers without a time reference

Fix any issues and output the FINAL revised briefing in the same markdown format.
If the draft is already good, output it unchanged."""

    critique_response = client.chat.completions.create(
        model=MODEL,
        max_completion_tokens=4096,
        messages=[
            {"role": "system", "content": SYNTHESIS_SYSTEM},
            {"role": "user", "content": critique_prompt},
        ],
    )
    final = critique_response.choices[0].message.content or draft
    print("  ✓ Synthesis complete")
    return final


# ---------------------------------------------------------------------------
# DRIVER TREND DATA — 14-day daily series per material mover
# ---------------------------------------------------------------------------

def _infer_segment_filter(mover):
    """Infer a SQL WHERE clause fragment from the mover name and description."""
    name = (mover.get("driver", "") + " " + mover.get("detail", "")).lower()
    parts = []

    # Channel
    if "aggregator" in name:
        parts.append("distribution_channel='Aggregator'")
    elif "direct" in name and "partner" not in name:
        parts.append("distribution_channel='Direct'")
    elif "partner" in name or "referral" in name:
        parts.append("distribution_channel='Partner Referral'")
    elif "renewal" in name:
        parts.append("distribution_channel='Renewals'")

    # Policy type
    if "single" in name and "annual" not in name:
        parts.append("policy_type='Single'")
    elif "annual" in name and "single" not in name:
        parts.append("policy_type='Annual'")

    # Cover level
    for level in ["Bronze", "Classic", "Silver", "Gold", "Deluxe", "Elite", "Adventure"]:
        if level.lower() in name:
            parts.append(f"cover_level_name='{level}'")
            break

    # Medical
    if "medical" in name and "non-medical" not in name:
        parts.append("medical_split='Medical'")

    return " AND ".join(parts) if parts else ""


def _compute_persistence(ty_vals, ly_vals, direction):
    """Count how many of the last 10 days moved in the mover's direction.
    Returns (count_consistent, total_days, label)."""
    n = min(len(ty_vals), len(ly_vals), 10)
    if n == 0:
        return 0, 0, "new"
    # Take last 10 days
    ty_tail = ty_vals[-n:]
    ly_tail = ly_vals[-n:]
    if direction == "down":
        consistent = sum(1 for t, l in zip(ty_tail, ly_tail) if t < l)
    else:
        consistent = sum(1 for t, l in zip(ty_tail, ly_tail) if t > l)
    if consistent >= 7:
        return consistent, n, "recurring"
    elif consistent >= 5:
        return consistent, n, "emerging"
    else:
        return consistent, n, "new"


def collect_driver_trends(analysis, run_date):
    """Run a 14-day daily GP query for each material mover to power inline trend charts."""
    movers = analysis.get("material_movers", [])
    if not movers:
        return {}

    driver_trends = {}
    yesterday = run_date - datetime.timedelta(days=1)
    start_date = yesterday - datetime.timedelta(days=13)  # 14 days
    ly_start = start_date - datetime.timedelta(days=364)
    ly_end = yesterday - datetime.timedelta(days=364)

    for i, mover in enumerate(movers):
        driver_name = mover.get("driver", f"Mover {i+1}")
        seg_filter = mover.get("segment_filter", "") or _infer_segment_filter(mover)
        metric = mover.get("metric", "gp")

        # Build the metric expression
        if metric == "policy_count":
            metric_expr = "SUM(policy_count)"
            metric_label = "Policies"
        elif metric == "avg_gp":
            metric_expr = "SUM(CAST(gp AS FLOAT64)) / NULLIF(SUM(policy_count), 0)"
            metric_label = "Avg GP"
        else:
            metric_expr = "SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))"
            metric_label = "GP"

        # If no segment_filter, skip — we can't generate a meaningful trend
        if not seg_filter:
            print(f"  ⚠ No segment_filter for mover '{driver_name}' — skipping trend")
            continue

        sql = f"""
SELECT
  transaction_date AS dt,
  {metric_expr} AS val
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{yesterday.strftime('%Y-%m-%d')}'
  AND {seg_filter}
GROUP BY transaction_date
ORDER BY transaction_date
"""
        sql_ly = f"""
SELECT
  transaction_date AS dt,
  {metric_expr} AS val
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '{ly_start.strftime('%Y-%m-%d')}' AND '{ly_end.strftime('%Y-%m-%d')}'
  AND {seg_filter}
GROUP BY transaction_date
ORDER BY transaction_date
"""
        try:
            print(f"  📈 Trend for '{driver_name}'...")
            ty_result = tool_run_sql(sql)
            ly_result = tool_run_sql(sql_ly)
            ty_rows = json.loads(ty_result.split("\n\n")[-1]) if "auto-corrected" in ty_result or "AI-corrected" in ty_result else json.loads(ty_result)
            ly_rows = json.loads(ly_result.split("\n\n")[-1]) if "auto-corrected" in ly_result or "AI-corrected" in ly_result else json.loads(ly_result)
            ty_parsed = [{"dt": str(r.get("dt", "")), "val": float(r.get("val", 0))} for r in ty_rows]
            ly_parsed = [{"dt": str(r.get("dt", "")), "val": float(r.get("val", 0))} for r in ly_rows]
            direction = mover.get("direction", "down")
            consistent, total, label = _compute_persistence(
                [d["val"] for d in ty_parsed],
                [d["val"] for d in ly_parsed],
                direction
            )
            driver_trends[driver_name] = {
                "ty": ty_parsed,
                "ly": ly_parsed,
                "metric_label": metric_label,
                "direction": direction,
                "persistence": label,
                "consistent_days": consistent,
                "total_days": total,
            }
        except Exception as e:
            print(f"  ⚠ Trend query failed for '{driver_name}': {e}")
            continue

    print(f"  ✓ Collected trends for {len(driver_trends)} drivers")
    return driver_trends


# ---------------------------------------------------------------------------
# HTML DASHBOARD (same as before but using the new data)
# ---------------------------------------------------------------------------

def generate_dashboard_html(briefing_md, trading_data, trend_data, today_str, investigation_log=None, run_date=None, trend_data_ly=None, driver_trends=None):
    """Generate styled dark-mode dashboard with interactive charts and SQL dig buttons."""
    import re

    # Convert sql-dig blocks into clickable buttons before markdown processing
    sql_counter = [0]
    def replace_sql_dig(match):
        sql_counter[0] += 1
        sql = match.group(1).strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        btn_id = f"sql-{sql_counter[0]}"
        ask_id = f"ask-{sql_counter[0]}"
        return (
            f'<div class="dig-wrap">'
            f'<div class="dig-buttons">'
            f'<button class="ask-driver-btn" onclick="openDriverAsk(\'{ask_id}\')">Ask about this</button>'
            f'<button class="dig-btn" onclick="toggleSQL(\'{btn_id}\')">Dig into this in GBQ</button>'
            f'</div>'
            f'<pre class="dig-sql" id="{btn_id}" style="display:none"><code>{sql}</code>'
            f'<button class="copy-btn" onclick="copySQL(\'{btn_id}\')">Copy</button></pre>'
            f'<div class="driver-ask-panel" id="{ask_id}" style="display:none">'
            f'<div class="ask-input-wrap">'
            f'<input type="text" class="ask-input" placeholder="Ask a question about this driver..." '
            f'onkeydown="if(event.key===\'Enter\')submitDriverAsk(\'{ask_id}\')">'
            f'<button class="ask-submit" onclick="submitDriverAsk(\'{ask_id}\')">Go</button>'
            f'</div>'
            f'<div class="ask-response" id="{ask_id}-response"></div>'
            f'</div>'
            f'</div>'
        )

    processed_md = re.sub(r'```sql-dig\n(.*?)```', replace_sql_dig, briefing_md, flags=re.DOTALL)
    # Strip any "review notes" / "checks against findings" appended by the LLM after the briefing
    # These are meta-commentary, not trading content — wrap in muted italic if present
    import re as _re
    review_patterns = [
        r'\n---\n+\*\*(?:Review|Check|Note|Verification).*$',
        r'\n---\n+_(?:Generated|Review|Check).*$',
    ]
    review_block = ""
    for pat in review_patterns:
        match = _re.search(pat, processed_md, _re.DOTALL | _re.IGNORECASE)
        if match:
            review_block = match.group(0)
            processed_md = processed_md[:match.start()]
            break

    html_body = markdown.markdown(processed_md, extensions=["tables", "fenced_code"])

    # If there was a review block, add it as muted italic at the end
    if review_block:
        review_html = markdown.markdown(review_block.strip(), extensions=["tables"])
        html_body += f'<div style="color:rgba(148,163,184,0.5);font-style:italic;font-size:11px;line-height:1.6;margin-top:20px;border-top:1px solid var(--border);padding-top:12px">{review_html}</div>'

    # Color-code directional markers — ↑ good in green, ↓ bad in red
    html_body = html_body.replace(
        '↑ good', '<span style="color:var(--green-bright);font-weight:700">↑ good</span>'
    ).replace(
        '↓ bad', '<span style="color:var(--red-bright);font-weight:700">↓ bad</span>'
    )

    # Replace At a Glance emoji dots — apply shimmer/flash/pulse to the bold label text
    def _glance_replace(emoji, css_class, html):
        # Pattern: emoji (optional whitespace) <strong>text</strong>
        return re.sub(
            re.escape(emoji) + r'\s*<strong>(.*?)</strong>',
            rf'<strong class="{css_class}">\1</strong>',
            html
        )
    html_body = _glance_replace('\U0001f534', 'glance-bad', html_body)   # 🔴 → red flash
    html_body = _glance_replace('\U0001f7e2', 'glance-good', html_body)  # 🟢 → green shimmer
    html_body = _glance_replace('\U0001f7e1', 'glance-watch', html_body) # 🟡 → amber pulse

    # Replace RECURRING/NEW text tags with styled badges in driver headings
    html_body = re.sub(
        r'<code>RECURRING</code>',
        '<span class="badge-recurring">Recurring</span>',
        html_body
    )
    html_body = re.sub(
        r'<code>NEW</code>',
        '<span class="badge-new">New</span>',
        html_body
    )
    html_body = re.sub(
        r'<code>EMERGING</code>',
        '<span class="badge-emerging">Emerging</span>',
        html_body
    )
    # Also handle if LLM outputs without backticks
    html_body = re.sub(
        r'(?<=</h3>)\s*RECURRING\b',
        ' <span class="badge-recurring">Recurring</span>',
        html_body
    )
    html_body = re.sub(
        r'(?<=</h3>)\s*EMERGING\b',
        ' <span class="badge-emerging">Emerging</span>',
        html_body
    )
    html_body = re.sub(
        r'(?<=</h3>)\s*NEW\b',
        ' <span class="badge-new">New</span>',
        html_body
    )
    # Handle inline RECURRING/EMERGING/NEW within h3 tags
    html_body = re.sub(
        r'\s*RECURRING\s*</h3>',
        ' <span class="badge-recurring">Recurring</span></h3>',
        html_body
    )
    html_body = re.sub(
        r'\s*EMERGING\s*</h3>',
        ' <span class="badge-emerging">Emerging</span></h3>',
        html_body
    )
    html_body = re.sub(
        r'\s*NEW\s*</h3>',
        ' <span class="badge-new">New</span></h3>',
        html_body
    )

    # Add section IDs to h2 tags for deep linking from headline tile
    def _add_section_id(match):
        heading_text = re.sub(r'<[^>]+>', '', match.group(1))  # strip inner HTML tags
        slug = re.sub(r'[^a-z0-9]+', '-', heading_text.lower().strip()).strip('-')
        return f'<h2 id="section-{slug}">{match.group(1)}</h2>'
    html_body = re.sub(r'<h2>(.*?)</h2>', _add_section_id, html_body)

    # Also add IDs to h3 (driver) headings for linking to specific movers
    # Embed ALL driver trend data as a global JS object — matching happens client-side
    _all_trends_for_js = {}
    if driver_trends:
        for key, td in driver_trends.items():
            ty = td.get("ty", [])
            ly = td.get("ly", [])
            direction = td.get("direction", "down")
            recovery = False
            if len(ty) >= 2 and len(ly) >= 2:
                ty_last2 = [ty[-2]["val"], ty[-1]["val"]]
                ly_last2 = [ly[-2]["val"], ly[-1]["val"]]
                if direction == "down":
                    recovery = ty_last2[0] > ly_last2[0] and ty_last2[1] > ly_last2[1]
                else:
                    recovery = ty_last2[0] < ly_last2[0] and ty_last2[1] < ly_last2[1]
            _all_trends_for_js[key] = {**td, "recovery": recovery}

    # ── Python-side heading-to-trend matching (replaces JS fuzzy matching) ──
    _trend_keys = list(_all_trends_for_js.keys()) if _all_trends_for_js else []
    _high_weight = {'direct','aggregator','partner','renewal','renewals','annual','annuals',
                    'single','bronze','classic','silver','gold','deluxe','elite','medical',
                    'med','cruise','scheme','europe','worldwide','destination'}
    _stop_words = {'the','a','an','in','on','of','for','and','is','are','was','gp','margin',
                   'recurring','emerging','new','trend','overall','total','general','gross',
                   'profit','fall','decline','drop','rise','increase','collapse','weakness',
                   'not','concern','policies','policy','slight','from','lower','higher','trading'}

    def _tokenize(text):
        clean = re.sub(r'<[^>]+>', '', text).lower()
        clean = re.sub(r'[^a-z0-9/\s-]', ' ', clean)
        tokens = []
        for w in clean.split():
            for part in w.split('/'):
                part = part.strip('-')
                if len(part) > 1 and part not in _stop_words:
                    tokens.append(part)
        return tokens

    def _match_score(heading_tokens, key_tokens):
        h_set = set(heading_tokens)
        k_set = set(key_tokens)
        shared = h_set & k_set
        if not shared:
            return 0, 0
        score = sum(3 if t in _high_weight else 1 for t in shared)
        return score, len(shared)

    # Compute all pairwise scores and do greedy-best assignment
    _all_scores = []
    # Pre-tokenize trend keys
    _key_tokens = {k: _tokenize(k) for k in _trend_keys}

    _driver_idx = [0]
    _heading_texts = []  # collect heading texts on first pass

    def _collect_headings(match):
        heading_text = re.sub(r'<[^>]+>', '', match.group(1))
        _heading_texts.append(heading_text)
        return match.group(0)  # return unchanged
    re.sub(r'<h3>(.*?)</h3>', _collect_headings, html_body)

    # Build heading tokens
    _heading_tokens = [_tokenize(h) for h in _heading_texts]

    # Compute all pairwise scores
    for h_idx, h_toks in enumerate(_heading_tokens):
        for k_idx, k in enumerate(_trend_keys):
            score, matches = _match_score(h_toks, _key_tokens[k])
            if matches >= 1 and (score >= 3 or matches >= 2):
                _all_scores.append((score, matches, h_idx, k_idx))

    # Sort by score desc, then matches desc
    _all_scores.sort(key=lambda x: (-x[0], -x[1]))
    _used_h = set()
    _used_k = set()
    _h_to_k = {}  # heading index -> trend key
    for score, matches, h_idx, k_idx in _all_scores:
        if h_idx in _used_h or k_idx in _used_k:
            continue
        _used_h.add(h_idx)
        _used_k.add(k_idx)
        _h_to_k[h_idx] = _trend_keys[k_idx]

    def _add_driver_id(match):
        heading_text = re.sub(r'<[^>]+>', '', match.group(1))
        slug = re.sub(r'[^a-z0-9]+', '-', heading_text.lower().strip()).strip('-')
        idx = _driver_idx[0]
        _driver_idx[0] += 1
        tid = f'trend-{idx}'
        # Embed matched trend key directly as data attribute
        trend_key = _h_to_k.get(idx, '')
        trend_attr = f' data-trend-key="{trend_key}"' if trend_key else ''
        h3_tag = f'<h3 id="driver-{slug}" data-driver-idx="{idx}"{trend_attr}>{match.group(1)}'
        h3_tag += (
            f' <button class="view-trend-btn" onclick="toggleMatchedTrend(\'{tid}\',this)" '
            f'data-trend-id="{tid}" style="display:none">'
            f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
            f'<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>'
            f'Trend</button>'
        )
        h3_tag += f'</h3><div id="{tid}" class="yoy-trend-container"></div>'
        return h3_tag
    html_body = re.sub(r'<h3>(.*?)</h3>', _add_driver_id, html_body)

    ty = next((r for r in trading_data if r["period"] == "yesterday"), {})
    ly = next((r for r in trading_data if r["period"] == "yesterday_ly"), {})
    w_ty = next((r for r in trading_data if r["period"] == "trailing_7d"), {})
    w_ly = next((r for r in trading_data if r["period"] == "trailing_7d_ly"), {})
    m_ty = next((r for r in trading_data if r["period"] == "trailing_28d"), {})
    m_ly = next((r for r in trading_data if r["period"] == "trailing_28d_ly"), {})

    def pct(a, b):
        if not b: return 0
        return ((a - b) / abs(b)) * 100
    def fmt_pct(val):
        return f"{'+' if val >= 0 else ''}{val:.1f}%"
    def status_color(val):
        if val >= 2: return "#00B0A6"
        if val >= -2: return "#FFB55F"
        return "#FF5F68"

    gp_pct = pct(ty.get("total_gp", 0), ly.get("total_gp", 1))
    vol_pct = pct(ty.get("new_policies", 0), ly.get("new_policies", 1))
    gppp_pct = pct(ty.get("avg_gp_per_policy", 0), ly.get("avg_gp_per_policy", 1))
    price_pct = pct(ty.get("avg_customer_price", 0), ly.get("avg_customer_price", 1))
    w_gp_pct = pct(w_ty.get("total_gp", 0), w_ly.get("total_gp", 1))
    m_gp_pct = pct(m_ty.get("total_gp", 0), m_ly.get("total_gp", 1))

    if m_gp_pct >= 2:
        status_text, status_bg = "ON TRACK", "#00B0A6"
    elif m_gp_pct >= -5:
        status_text, status_bg = "WATCH", "#FFB55F"
    else:
        status_text, status_bg = "ACTION NEEDED", "#FF5F68"

    # Build interactive chart data as JSON for JS — pair TY with LY for YoY comparison
    chart_data_json = "[]"
    if trend_data:
        # Build LY lookup: map each LY date +364 days back to its GP value
        from datetime import timedelta as _td
        ly_lookup = {}
        if trend_data_ly:
            for lr in trend_data_ly:
                ly_date = lr.get("transaction_date")
                if ly_date:
                    # The TY equivalent of this LY date is +364 days
                    if hasattr(ly_date, "isoformat"):
                        ty_equiv = ly_date + _td(days=364)
                        ly_lookup[str(ty_equiv)] = float(lr.get("daily_gp", 0))
                    else:
                        from datetime import date as _dt
                        try:
                            ly_d = _dt.fromisoformat(str(ly_date))
                            ty_equiv = ly_d + _td(days=364)
                            ly_lookup[str(ty_equiv)] = float(lr.get("daily_gp", 0))
                        except Exception:
                            pass

        chart_items = []
        gp_vals = [float(r.get("daily_gp", 0)) for r in trend_data]
        avg_gp = sum(gp_vals) / len(gp_vals) if gp_vals else 0
        for r in trend_data:
            d = str(r.get("transaction_date", ""))
            gp = float(r.get("daily_gp", 0))
            pols = int(r.get("new_policies", 0))
            gppp = float(r.get("avg_gp_per_policy", 0))
            ly_gp = ly_lookup.get(d, 0)
            yoy_pct = round(((gp - ly_gp) / ly_gp) * 100, 1) if ly_gp else None
            yoy_abs = round(gp - ly_gp, 0) if ly_gp else None
            chart_items.append({
                "date": d, "gp": round(gp, 0), "policies": pols,
                "gppp": round(gppp, 2), "above_avg": gp >= avg_gp,
                "ly_gp": round(ly_gp, 0), "yoy_pct": yoy_pct, "yoy_abs": yoy_abs
            })
        chart_data_json = json.dumps(chart_items)

    # Serialize all driver trends for client-side matching
    driver_trends_json = json.dumps(_all_trends_for_js) if _all_trends_for_js else "{}"

    # ── Pre-compute distinct field values for AI chat ──
    field_discovery = {}
    try:
        _policy_disc_sql = """
        SELECT
            ARRAY_AGG(DISTINCT policy_type IGNORE NULLS LIMIT 25) AS policy_type,
            ARRAY_AGG(DISTINCT distribution_channel IGNORE NULLS LIMIT 25) AS distribution_channel,
            ARRAY_AGG(DISTINCT channel IGNORE NULLS LIMIT 25) AS channel,
            ARRAY_AGG(DISTINCT scheme_name IGNORE NULLS LIMIT 40) AS scheme_name,
            ARRAY_AGG(DISTINCT cover_level_name IGNORE NULLS LIMIT 25) AS cover_level_name,
            ARRAY_AGG(DISTINCT booking_source IGNORE NULLS LIMIT 25) AS booking_source,
            ARRAY_AGG(DISTINCT device_type IGNORE NULLS LIMIT 25) AS device_type,
            ARRAY_AGG(DISTINCT medical_split IGNORE NULLS LIMIT 25) AS medical_split,
            ARRAY_AGG(DISTINCT max_medical_score_grouped IGNORE NULLS LIMIT 25) AS max_medical_score_grouped,
            ARRAY_AGG(DISTINCT customer_type IGNORE NULLS LIMIT 25) AS customer_type,
            ARRAY_AGG(DISTINCT trip_duration_band IGNORE NULLS LIMIT 25) AS trip_duration_band,
            ARRAY_AGG(DISTINCT days_to_travel IGNORE NULLS LIMIT 25) AS days_to_travel,
            ARRAY_AGG(DISTINCT max_age_at_purchase IGNORE NULLS LIMIT 25) AS max_age_at_purchase,
            ARRAY_AGG(DISTINCT insurance_group IGNORE NULLS LIMIT 40) AS insurance_group
        FROM `hx-data-production.commercial_finance.insurance_policies_new`
        WHERE transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        """
        _web_disc_sql = """
        SELECT
            ARRAY_AGG(DISTINCT booking_flow_stage IGNORE NULLS LIMIT 25) AS booking_flow_stage,
            ARRAY_AGG(DISTINCT page_type IGNORE NULLS LIMIT 40) AS page_type,
            ARRAY_AGG(DISTINCT event_name IGNORE NULLS LIMIT 40) AS event_name,
            ARRAY_AGG(DISTINCT customer_type IGNORE NULLS LIMIT 25) AS customer_type
        FROM `hx-data-production.commercial_finance.insurance_web_utm_4`
        WHERE session_start_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        """
        _p_rows = [dict(r) for r in BQ_CLIENT.query(_policy_disc_sql).result()]
        _w_rows = [dict(r) for r in BQ_CLIENT.query(_web_disc_sql).result()]
        if _p_rows:
            field_discovery["policies"] = {k: v for k, v in _p_rows[0].items() if v}
        if _w_rows:
            field_discovery["web"] = {k: v for k, v in _w_rows[0].items() if v}
        print(f"    📋 Field discovery complete: {sum(len(v) for v in field_discovery.values())} fields")
    except Exception as e:
        print(f"    ⚠ Field discovery failed (non-fatal): {e}")
    field_discovery_json = json.dumps(field_discovery, default=str)

    # Extract investigation data from the log dict
    _track_results = investigation_log.get("track_results", {}) if isinstance(investigation_log, dict) else {}
    _follow_up_log = investigation_log.get("follow_up_log", []) if isinstance(investigation_log, dict) else []
    inv_count = len(_track_results) + len(_follow_up_log) if (_track_results or _follow_up_log) else 0
    # Banner date is set dynamically via JS to always show today's date when viewed
    day_name = ""
    now_str = datetime.datetime.now().strftime("%H:%M %d %b %Y")

    # Build investigation trail HTML — human-readable story of the investigation
    inv_trail_html = ""
    track_results = investigation_log.get("track_results", {}) if isinstance(investigation_log, dict) else {}
    follow_up_log = investigation_log.get("follow_up_log", []) if isinstance(investigation_log, dict) else investigation_log if isinstance(investigation_log, list) else []
    analysis_data = investigation_log.get("analysis", {}) if isinstance(investigation_log, dict) else {}
    follow_up_data = investigation_log.get("follow_up_results", {}) if isinstance(investigation_log, dict) else {}

    inv_items = []
    step_num = 0

    # --- Helper: human-readable track names for the narrative ---
    TRACK_PLAIN_NAMES = {
        'channel_product_mix': 'how sales break down by channel (direct, aggregator, partners) and product type',
        'scheme_performance': 'which insurance schemes are selling best and worst',
        'medical_profile': 'how customers with medical conditions are affecting margins',
        'cover_level_mix': 'which cover levels (Bronze, Silver, Gold, etc.) customers are choosing',
        'commission_partners': 'how much we are paying partners and agents in commission',
        'customer_demographics': 'the age profile and new-vs-returning customer split',
        'destination_mix': 'where customers are travelling to and how that affects profit',
        'cancellations': 'cancellation volumes and why customers are cancelling',
        'renewals': 'how our renewal book is performing and retention trends',
        'web_funnel_detailed': 'where visitors are dropping off on the website before buying',
        'day_of_week': 'whether any specific days were unusually good or bad',
        'discounts_campaigns': 'how discounts and marketing campaigns are affecting profit per policy',
        'cruise': 'how the cruise segment is performing versus standard travel',
        'web_to_gp_bridge': 'which web journeys (device, scheme, medical) produce the most profit per session',
        'funnel_value_dropoff': 'where high-value vs low-value customers are dropping off in the funnel',
        'annual_vs_single_conversion': 'how the web-to-purchase path differs for annual vs single trip customers',
        'multi_search_gp_impact': 'whether customers who search multiple times convert better or worse',
        'medical_screening_funnel': 'how the medical screening step affects conversion rates by device',
        'web_cover_level_outcome': 'what users browse online vs what they actually end up buying',
        'session_depth_outcome': 'how deep into the website people go and whether that leads to better sales',
        'cost_decomposition': 'how commission, underwriter costs, IPT, and discounts compare as a % of price paid — and whether costs grew faster than revenue',
        'conversion_gp_bridge': 'decomposing GP into traffic × conversion × price × margin to find which lever moved most',
    }

    # Step 1: The Opening Look — "We started by looking at every angle..."
    if track_results:
        step_num += 1
        checked_areas = []
        for tid, tr in track_results.items():
            plain = TRACK_PLAIN_NAMES.get(tid, tr.get("desc", tid))
            checked_areas.append(plain)
        areas_text = ", ".join(checked_areas[:-1]) + f", and {checked_areas[-1]}" if len(checked_areas) > 1 else checked_areas[0] if checked_areas else ""

        narrative = (
            f"We started by looking at <strong>every angle</strong> of yesterday's trading. "
            f"That means {len(track_results)} separate checks, each comparing this year against the same period last year. "
            f"We looked at {areas_text}."
        )

        track_list_html = ""
        for tid, tr in track_results.items():
            rows = tr.get('row_count', 0)
            err = tr.get('error', '')
            icon = "&#10003;" if not err else "&#9888;"
            status_class = "trail-result-error" if err else "trail-result"
            plain = TRACK_PLAIN_NAMES.get(tid, tr.get("desc", tid))
            track_list_html += (
                f'<div class="trail-call">'
                f'<div class="trail-call-header">{icon} <strong>{tr["name"]}</strong></div>'
                f'<div class="trail-call-summary">{plain.capitalize()}</div>'
                f'<div class="{status_class}" style="font-size:11px">{rows} data points returned{" &mdash; Error: " + err if err else ""}</div>'
                f'</div>'
            )

        inv_items.append(
            f'<div class="trail-step" data-animate="card">'
            f'<div class="trail-connector"></div>'
            f'<div class="trail-dot"><span class="trail-dot-num">{step_num}</span></div>'
            f'<div class="trail-content glass-card">'
            f'<div class="trail-round-header">'
            f'<span class="trail-round">Step {step_num}</span>'
            f'<span class="trail-round-desc">Looked at every angle of trading</span>'
            f'<span class="trail-round-meta">{len(track_results)} areas checked</span>'
            f'</div>'
            f'<div class="trail-reasoning">{narrative}</div>'
            f'<details class="trail-call-details"><summary>See what we checked</summary>'
            f'<div class="trail-calls">{track_list_html}</div>'
            f'</details>'
            f'</div></div>'
        )

    # Step 2: "The biggest things we found..." — Material Movers
    if analysis_data:
        step_num += 1
        movers = analysis_data.get("material_movers", [])
        track_coverage = analysis_data.get("track_coverage", {})
        reconciliation = analysis_data.get("reconciliation", {})

        # If movers not at top level, try parsing from raw_analysis string
        if not movers and "raw_analysis" in analysis_data:
            import re as _re
            raw_str = analysis_data["raw_analysis"]
            def _fix_json(s):
                """Fix common AI-generated JSON issues."""
                s = _re.sub(r'(?<=\d),(?=\d{3})', '', s)  # -1,189 -> -1189
                s = _re.sub(r'(?<=\d)_(?=\d)', '', s)     # -10_865 -> -10865
                s = _re.sub(r',\s*([}\]])', r'\1', s)     # trailing commas
                return s
            # Try full JSON parse
            try:
                parsed = json.loads(_fix_json(raw_str))
                movers = parsed.get("material_movers", movers)
                track_coverage = parsed.get("track_coverage", track_coverage)
                reconciliation = parsed.get("reconciliation", reconciliation)
            except (json.JSONDecodeError, ValueError):
                # Try extracting just the material_movers array
                fixed = _fix_json(raw_str)
                mm_match = _re.search(r'"material_movers"\s*:\s*\[', fixed)
                if mm_match:
                    start = mm_match.start()
                    depth = 0
                    for i, c in enumerate(fixed[start:]):
                        if c == '[': depth += 1
                        elif c == ']': depth -= 1
                        if depth == 0 and i > 0:
                            snippet = '{' + fixed[start:start+i+1] + '}'
                            try:
                                movers = json.loads(snippet).get("material_movers", [])
                            except (json.JSONDecodeError, ValueError):
                                pass
                            break

        # Try to pull movers from follow-up results too if analysis didn't have them
        if not movers and follow_up_data:
            movers = follow_up_data.get("material_movers", [])
        if movers:
            biggest = movers[0]
            biggest_name = biggest.get("driver", biggest.get("name", "an unknown factor"))
            biggest_impact = abs(biggest.get("impact_gbp_weekly", biggest.get("total_gp", 0)))
            biggest_dir = "up" if biggest.get("direction") == "up" else "down"
            narrative = (
                f"From all that data, we identified <strong>{len(movers)} things moving the numbers</strong>. "
                f"The biggest was <strong>{biggest_name}</strong>, "
                f'which is pushing GP <strong>{biggest_dir} by about &pound;{biggest_impact:,.0f} per week</strong>. '
                f"Here they are, ranked by how much money they represent:"
            )
        else:
            # Show a useful summary even when structured movers weren't parsed
            raw = analysis_data.get("raw_analysis", "")
            if raw:
                # Extract a readable snippet from the raw analysis
                snippet = raw[:600].replace("<", "&lt;").replace(">", "&gt;")
                narrative = (
                    "The AI completed its analysis but the structured data couldn't be fully parsed from the response. "
                    f"Here's what the AI found:<br><br><em style='font-size:0.9em;opacity:0.85'>{snippet}...</em>"
                )
            else:
                narrative = (
                    "The analysis completed but the structured mover data wasn't captured properly. "
                    "Check the investigation JSON for the full findings."
                )

        movers_html = ""
        for rank, mv in enumerate(movers[:8], 1):
            direction = mv.get("direction", "")
            impact = mv.get("impact_gbp_weekly", 0)
            color = "var(--green)" if direction == "up" else "var(--red)" if direction == "down" else "var(--muted)"
            arrow = "&#9650;" if direction == "up" else "&#9660;" if direction == "down" else "&#9654;"
            temp_struct = mv.get("temporary_or_structural", "")
            badge = ""
            if temp_struct:
                badge_color = "var(--yellow)" if "temp" in temp_struct.lower() else "var(--accent-light)"
                badge = f' <span style="font-size:10px;padding:2px 8px;border-radius:10px;background:rgba(148,163,184,0.1);color:{badge_color};margin-left:6px">{temp_struct.capitalize()}</span>'
            detail_text = mv.get("detail", "")[:250].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            movers_html += (
                f'<div style="padding:10px 14px;margin:6px 0;background:rgba(15,23,42,0.5);border-radius:10px;border:1px solid var(--border);display:flex;gap:12px;align-items:flex-start">'
                f'<div style="min-width:28px;text-align:center;font-size:14px;font-weight:800;color:var(--muted);padding-top:2px">{rank}</div>'
                f'<div style="flex:1">'
                f'<div style="margin-bottom:4px"><span style="color:{color};font-weight:700;font-size:14px">{arrow} &pound;{abs(impact):,.0f}/wk</span>'
                f' &mdash; <strong>{mv.get("driver", "?")}</strong>{badge}</div>'
                f'<div style="font-size:12px;color:#cbd5e1;line-height:1.6">{detail_text}</div>'
                f'</div></div>'
            )

        recon_html = ""
        if reconciliation:
            headline = reconciliation.get("headline_gp_variance", 0)
            explained = reconciliation.get("explained_total", 0)
            residual = reconciliation.get("unexplained_residual", 0)
            headline_dir = "up" if headline > 0 else "down"
            recon_html = (
                f'<div style="margin-top:14px;padding:12px 16px;background:rgba(84,46,145,0.08);border-radius:10px;font-size:12px;line-height:1.7">'
                f'<strong>The maths check:</strong> Overall GP moved &pound;{abs(headline):,.0f} {headline_dir} this week. '
                f'The drivers above account for &pound;{abs(explained):,.0f} of that. '
            )
            if abs(residual) > 0:
                recon_html += f'That leaves &pound;{abs(residual):,.0f} unexplained &mdash; likely spread across many small movements.'
            else:
                recon_html += 'That fully explains the movement.'
            recon_html += '</div>'

        coverage_html = ""
        for tid, finding in track_coverage.items():
            plain_name = TRACK_PLAIN_NAMES.get(tid, tid)
            finding_text = str(finding)[:150].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            coverage_html += (
                f'<div style="font-size:12px;color:#cbd5e1;padding:4px 0;line-height:1.6">'
                f'<strong style="color:var(--text)">{plain_name.capitalize()}</strong>: {finding_text}</div>'
            )

        inv_items.append(
            f'<div class="trail-step" data-animate="card">'
            f'<div class="trail-connector"></div>'
            f'<div class="trail-dot"><span class="trail-dot-num">{step_num}</span></div>'
            f'<div class="trail-content glass-card">'
            f'<div class="trail-round-header">'
            f'<span class="trail-round">Step {step_num}</span>'
            f'<span class="trail-round-desc">Found the biggest movers</span>'
            f'<span class="trail-round-meta">{len(movers)} material drivers identified</span>'
            f'</div>'
            f'<div class="trail-reasoning">{narrative}</div>'
            f'<div style="margin:12px 0">{movers_html}</div>'
            f'{recon_html}'
            f'<details class="trail-call-details"><summary>See findings from every area we checked</summary>'
            f'<div style="padding:8px 0">{coverage_html}</div>'
            f'</details>'
            f'</div></div>'
        )

    # Step 3+: Follow-up Investigations — one sub-step per round
    if follow_up_log:
        tool_icons = {"run_sql": "&#128269;", "fetch_market_data": "&#128200;", "web_search": "&#127760;", "scan_drive": "&#128194;"}
        base_step = step_num  # will be 2 after analysis step

        # Group follow_up_log entries by round
        from collections import OrderedDict
        rounds_map = OrderedDict()
        for entry in follow_up_log:
            rnd = entry.get("round", 0)
            if rnd not in rounds_map:
                rounds_map[rnd] = []
            rounds_map[rnd].append(entry)

        # Round descriptions for the sub-step headers
        round_descs = {
            1: "Context gathering — internal docs, market data, web search",
            2: "Deep dives into movers 1–4",
            3: "Deep dives into movers 5–8",
            4: "Completing remaining drill-downs",
            5: "Final checks and gap-filling",
            6: "Verifying and consolidating findings",
        }

        for rnd, rnd_entries in rounds_map.items():
            step_num += 1
            sub_label = f"{base_step + 1}.{rnd}"
            round_desc = round_descs.get(rnd, f"Follow-up round {rnd}")
            rnd_tool_count = len(rnd_entries)

            rnd_items_html = ""

            # AI decision card at the top of each round
            first_reasoning = ""
            for e in rnd_entries:
                r = (e.get("reasoning", "") or "").strip()
                if r:
                    first_reasoning = r
                    break
            if first_reasoning:
                clean_reasoning = first_reasoning[:250]
                if len(first_reasoning) > 250:
                    clean_reasoning = clean_reasoning.rsplit(' ', 1)[0] + '...'
                safe_reasoning = clean_reasoning.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                rnd_items_html += (
                    f'<div style="padding:10px 14px;margin:6px 0;border-radius:10px;'
                    f'background:rgba(120,80,200,0.08);border:1px solid rgba(120,80,200,0.18)">'
                    f'<div style="font-size:11px;color:#b89aff;font-weight:700;margin-bottom:3px">'
                    f'&#129504; AI Decision</div>'
                    f'<div style="font-size:12px;color:#cbd5e1;line-height:1.6">'
                    f'{safe_reasoning}</div>'
                    f'</div>'
                )

            # Individual tool calls within this round
            for entry in rnd_entries:
                tool = entry.get("tool", "unknown")
                args_val = entry.get("args", {})
                preview = (entry.get("result_preview", "") or "")[:200]
                icon = tool_icons.get(tool, "&#9881;")

                if tool == "run_sql":
                    raw_sql_str = (args_val.get("sql", "") or "").upper()
                    sql_desc_parts = []
                    dim_keywords = {
                        'DISTRIBUTION_CHANNEL': 'distribution channel',
                        'POLICY_TYPE': 'policy type (annual vs single)',
                        'COVER_LEVEL': 'cover level',
                        'SCHEME_NAME': 'insurance scheme',
                        'DEVICE_TYPE': 'device type',
                        'CUSTOMER_TYPE': 'customer type (new vs existing)',
                        'MAX_MEDICAL_SCORE': 'medical risk score',
                        'MEDICAL_SPLIT': 'medical screening',
                        'CANCELLATION_REASON': 'cancellation reasons',
                        'DESTINATION_GROUP': 'destination',
                        'AGENT_NAME': 'partner/agent',
                        'CAMPAIGN_NAME': 'marketing campaign',
                        'BOOKING_SOURCE': 'booking source (web vs call centre)',
                        'INSURANCE_GROUP': 'insurance group',
                        'AUTO_RENEW': 'auto-renewal',
                        'RENEWAL': 'renewals',
                        'COMMISSION': 'commission costs',
                        'DISCOUNT': 'discounts',
                        'TRANSACTION_DATE': 'daily breakdown',
                        'DAYS_TO_TRAVEL': 'booking lead time',
                        'TRIP_DURATION': 'trip duration',
                        'NUMBER_OF_TRAVELLERS': 'group size',
                    }
                    for kw, label in dim_keywords.items():
                        if kw in raw_sql_str and ('GROUP BY' in raw_sql_str or 'WHERE' in raw_sql_str):
                            sql_desc_parts.append(label)
                    if len(sql_desc_parts) > 3:
                        sql_desc_parts = sql_desc_parts[:3]

                    sql_comment = ""
                    raw_sql_full = args_val.get("sql", "") or ""
                    for line in raw_sql_full.split('\n'):
                        line = line.strip()
                        if line.startswith('--') and len(line) > 5:
                            sql_comment = line[2:].strip()[:120]
                            break

                    if sql_comment:
                        safe_comment = sql_comment.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        what_text = f'Drilled into the data: <strong>{safe_comment}</strong>'
                    elif sql_desc_parts:
                        what_text = f'Drilled into the data by <strong>{", ".join(sql_desc_parts)}</strong>'
                    else:
                        what_text = "Ran a targeted data query to investigate further"

                elif tool == "fetch_market_data":
                    tab = args_val.get("sheet_tab", "market data")
                    what_text = f'Pulled the latest figures from our <strong>{tab}</strong> market tracker'
                elif tool == "web_search":
                    query = args_val.get("query", "")
                    safe_q = query[:150].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    what_text = f'Searched the web for: <em>&ldquo;{safe_q}&rdquo;</em>'
                elif tool == "scan_drive":
                    keywords = args_val.get("keywords", "")
                    safe_kw = keywords[:100].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    what_text = f'Scanned recent internal documents for anything related to: <em>{safe_kw}</em>'
                else:
                    what_text = f"Used {tool}"

                raw_query = ""
                if tool == "run_sql":
                    raw_sql = (args_val.get("sql", "") or "")[:500].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    raw_query = f'<details class="trail-call-details"><summary>Show technical detail</summary><div class="trail-call-query"><code>{raw_sql}</code></div></details>'

                safe_preview = preview.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") if preview else ""
                result_snippet = f'<div class="trail-result" style="margin-top:6px">{safe_preview}</div>' if safe_preview else ""

                rnd_items_html += (
                    f'<div class="trail-call" style="padding:10px 14px">'
                    f'<div style="font-size:13px;color:var(--text);margin-bottom:4px">{icon} {what_text}</div>'
                    f'{raw_query}{result_snippet}</div>'
                )

            inv_items.append(
                f'<div class="trail-step" data-animate="card">'
                f'<div class="trail-connector"></div>'
                f'<div class="trail-dot"><span class="trail-dot-num">{sub_label}</span></div>'
                f'<div class="trail-content glass-card">'
                f'<div class="trail-round-header">'
                f'<span class="trail-round">Step {sub_label}</span>'
                f'<span class="trail-round-desc">{round_desc}</span>'
                f'<span class="trail-round-meta">{rnd_tool_count} {"check" if rnd_tool_count == 1 else "checks"}</span>'
                f'</div>'
                f'<div class="trail-calls">{rnd_items_html}</div>'
                f'</div></div>'
            )

    # Step 4: "Wrote and checked the briefing"
    step_num += 1
    inv_items.append(
        f'<div class="trail-step" data-animate="card">'
        f'<div class="trail-connector"></div>'
        f'<div class="trail-dot"><span class="trail-dot-num">{step_num}</span></div>'
        f'<div class="trail-content glass-card">'
        f'<div class="trail-round-header">'
        f'<span class="trail-round">Step {step_num}</span>'
        f'<span class="trail-round-desc">Wrote and checked the briefing</span>'
        f'<span class="trail-round-meta">Draft, review, final</span>'
        f'</div>'
        f'<div class="trail-reasoning">'
        f'Finally, we wrote up everything into the briefing above. We then reviewed our own work: '
        f'checking that every pound figure traces back to real data, that every action item is specific enough to act on, '
        f'and that nothing material was left out. Where we spotted gaps, we revised before publishing.</div>'
        f'</div></div>'
    )

    inv_trail_html = "\n".join(inv_items)

    # Build the trail section with human-readable intro
    total_tracks = len(track_results) if track_results else 0
    total_follow_ups = len(follow_up_log) if follow_up_log else 0
    total_movers = len(analysis_data.get("material_movers", []) or follow_up_data.get("material_movers", [])) if (analysis_data or follow_up_data) else 0

    inv_trail_section = ""
    if track_results or follow_up_log:
        inv_trail_section = (
            '<div class="section-gap trail-section" data-animate="reveal">'
            '<div class="section-title">How We Investigated This</div>'
            '<p class="trail-intro">'
            f'This briefing is not a guess. Before writing a single word, we checked <strong>{total_tracks} different areas</strong> of yesterday\'s trading data, '
            f'identified <strong>{total_movers} things that are meaningfully moving the numbers</strong>, '
            f'ran <strong>{total_follow_ups} follow-up checks</strong> to understand <em>why</em> those movements happened, '
            'and then wrote the briefing with a built-in review step. '
            'Here is exactly what we did.</p>'
            '<button class="trail-toggle" id="trailToggle" onclick="toggleTrail()">'
            '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M4 6l4 4 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
            f' Show full investigation trail'
            '</button>'
            f'<div class="trail-body" id="trailBody">{inv_trail_html}</div>'
            '</div>'
        )

    # ── Build Headline Tile ──
    # Extract the headline (first h2 in the briefing — this is the one-sentence summary)
    headline_match = re.search(r'<h2[^>]*>(.*?)</h2>', html_body)
    headline_text = ""
    if headline_match:
        headline_text = re.sub(r'<[^>]+>', '', headline_match.group(1)).strip()

    # Extract At a Glance items for the "Also..." section
    glance_items = re.findall(r'<li>(.*?)</li>', html_body[:html_body.find('</ul>') + 6] if '</ul>' in html_body else html_body)
    # Build all driver heading slugs for fuzzy matching
    all_driver_headings = re.findall(r'<h3 id="driver-([^"]+)">(.*?)</h3>', html_body)
    driver_slug_lookup = []  # [(slug, plain_name), ...]
    for slug, heading_html in all_driver_headings:
        plain = re.sub(r'<[^>]+>', '', heading_html).strip().lower()
        driver_slug_lookup.append((slug, plain))

    def _find_best_driver_slug(keyword_text):
        """Find the driver heading slug that best matches a glance keyword."""
        kw = keyword_text.lower()
        # Exact slug match
        kw_slug = re.sub(r'[^a-z0-9]+', '-', kw).strip('-')
        for slug, plain in driver_slug_lookup:
            if slug == kw_slug:
                return slug
        # Fuzzy: check if the keyword words appear in any driver name
        kw_words = set(w for w in kw.split() if len(w) > 3)
        best_slug, best_score = None, 0
        for slug, plain in driver_slug_lookup:
            plain_words = set(plain.split())
            overlap = len(kw_words & plain_words)
            if overlap > best_score:
                best_score = overlap
                best_slug = slug
        # Also try: does any driver name contain the keyword or vice versa
        if not best_slug or best_score == 0:
            for slug, plain in driver_slug_lookup:
                if kw in plain or plain in kw:
                    return slug
                # Check if any significant keyword word appears in driver name
                for w in kw_words:
                    if w in plain:
                        return slug
        return best_slug if best_score > 0 else None

    # Build "also" items from glance items (skip the first one which is the headline topic)
    also_items = []
    for item in glance_items[1:5]:  # take items 2-5
        clean = re.sub(r'<[^>]+>', '', item).strip()
        # Try to find the bold keyword for linking
        bold_match = re.search(r'<strong[^>]*>(.*?)</strong>', item)
        if bold_match:
            keyword = re.sub(r'<[^>]+>', '', bold_match.group(1)).strip()
            matched_slug = _find_best_driver_slug(keyword)
            if matched_slug:
                also_items.append(f'<a href="#driver-{matched_slug}">{clean}</a>')
            else:
                # Fall back to linking to "What's Driving This" section
                also_items.append(f'<a href="#section-what-s-driving-this">{clean}</a>')
        else:
            also_items.append(clean)

    # Build headline HTML with key terms bolded and linked
    def _linkify_headline(text):
        """Turn the headline into HTML where key terms are interactive."""
        if not text:
            return "Yesterday's trading briefing is ready."
        # Find terms that match h3 driver headings in the content
        driver_headings = re.findall(r'<h3 id="driver-([^"]+)">(.*?)</h3>', html_body)
        linked_words = set()  # track which character positions are already linked
        result = text
        for slug, heading_html in driver_headings[:3]:  # top 3 drivers
            driver_name = re.sub(r'<[^>]+>', '', heading_html).strip()
            # Try meaningful multi-word chunks first, then individual words
            candidates = [driver_name] + [w for w in driver_name.split() if len(w) > 4]
            for word_chunk in candidates:
                # Search only in the original plain text, not in inserted HTML
                pattern = re.compile(re.escape(word_chunk), re.IGNORECASE)
                match = pattern.search(text)
                if match and match.start() not in linked_words:
                    original = text[match.start():match.end()]
                    replacement = f'<a href="#driver-{slug}" class="hl-keyword">{original}</a>'
                    # Replace in result string — find the original word (not inside an HTML tag)
                    result = re.sub(
                        r'(?<!["\w])' + re.escape(original) + r'(?!["\w])',
                        replacement, result, count=1
                    )
                    linked_words.add(match.start())
                    break
        return result

    headline_html = _linkify_headline(headline_text)

    # Colour-code directional terms in the headline for clarity
    # IMPORTANT: only replace in text OUTSIDE of HTML tags to avoid corrupting attributes
    def _colour_outside_tags(html, patterns, css_class):
        """Apply colour spans only to text segments outside HTML tags."""
        # Split into tag vs text segments
        parts = re.split(r'(<[^>]+>)', html)
        for i, part in enumerate(parts):
            if part.startswith('<'):
                continue  # skip HTML tags entirely
            for pat in patterns:
                part = re.sub(pat, rf'<span class="{css_class}">\1</span>', part, flags=re.IGNORECASE)
            parts[i] = part
        return ''.join(parts)

    # Negative/bad indicators → red
    headline_html = _colour_outside_tags(headline_html,
        [r'(down\s+£[\d,.]+k?)', r'(fell\s+[\d,.]+%?)', r'(dropped?\s+[\d,.]+%?)',
         r'(lost?\s+£[\d,.]+k?)', r'(negative\s+margins?)', r'(squeeze\w*)', r'(shrink\w*)',
         r'(worse)', r'(decline\w*)', r'(losing)'], 'hl-down')
    # Positive/good indicators → green
    headline_html = _colour_outside_tags(headline_html,
        [r'(up\s+£[\d,.]+k?)', r'(rose\s+[\d,.]+%?)', r'(grew\s+[\d,.]+%?)',
         r'(growth)', r'(rising\s+fast)', r'(record\s+\w+)', r'(rising)',
         r'(strong\w*)', r'(gain\w*)', r'(improving)'], 'hl-up')
    # Neutral/watch indicators → amber
    headline_html = _colour_outside_tags(headline_html,
        [r'(despite)', r'(flat)', r'(mixed)', r'(watch\w*)'], 'hl-neutral')
    # Bold monetary amounts — only outside tags
    headline_html = _colour_outside_tags(headline_html,
        [r'(£[\d,.]+k?)'], 'hl-down')  # money amounts get bold via strong
    # Wrap standalone £ amounts in <strong> outside tags
    parts = re.split(r'(<[^>]+>)', headline_html)
    for i, part in enumerate(parts):
        if not part.startswith('<'):
            parts[i] = re.sub(r'(?<!>)(£[\d,.]+k?)', r'<strong>\1</strong>', part)
    headline_html = ''.join(parts)

    also_html = " &middot; ".join(also_items) if also_items else ""

    # Link to main sections
    section_links = []
    for sid, label in [("section-at-a-glance", "At a Glance"), ("section-what-s-driving-this", "What's Driving This"),
                       ("section-customer-search-intent", "Search Intent"), ("section-actions", "Actions")]:
        if f'id="{sid}"' in html_body:
            section_links.append(f'<a href="#{sid}">{label}</a>')

    headline_tile_html = f"""<div class="section-gap">
<div class="headline-tile glass-card" data-animate="card">
<div class="hl-main">{headline_html}</div>
{f'<div class="hl-also"><strong>Also:</strong> {also_html}</div>' if also_html else ''}
{f'<div class="hl-also" style="margin-top:6px;font-size:11px;opacity:0.6">Jump to: {" &middot; ".join(section_links)}</div>' if section_links else ''}
</div>
</div>"""

    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trading Covered</title>
<link rel="icon" type="image/png" href="https://dmy0b9oeprz0f.cloudfront.net/holidayextras.co.uk/brand-guidelines/logo-tags/png/better-future.png">
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
/* ── Custom Properties — HX Brand ── */
:root{{
  --bg:#1a0e2e;
  --bg-gradient:linear-gradient(165deg,#1a0e2e 0%,#221340 40%,#2a1850 100%);
  --surface:rgba(84,46,145,0.12);
  --surface-solid:#2a1850;
  --surface2:rgba(84,46,145,0.2);
  --border:rgba(146,95,255,0.2);
  --border-hover:rgba(146,95,255,0.4);
  --text:#f1f5f9;
  --muted:#b8a9d4;
  --accent:#542E91;
  --accent-light:#925FFF;
  --accent-glow:rgba(84,46,145,0.35);
  --yellow:#FDDC06;
  --green:#00B0A6;
  --green-bright:#00D4C8;
  --red:#FF5F68;
  --red-bright:#FF8A91;
  --amber:#FFB55F;
  --blue:#3AA6FF;
  --r:16px;
  --glass-blur:blur(12px);
  --glass-border:1px solid rgba(253,220,6,0.06);
}}

/* ── Reset & Base ── */
*{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth;overflow-x:hidden;overflow-y:auto;height:auto}}
[id^="section-"],[id^="driver-"]{{scroll-margin-top:60px}}
body{{
  font-family:'Nunito',system-ui,-apple-system,sans-serif;
  background:var(--bg);
  background-image:var(--bg-gradient);
  color:var(--text);
  line-height:1.65;
  -webkit-font-smoothing:antialiased;
  min-height:100vh;
  height:auto;
  overflow-x:hidden;
  overflow-y:auto;
  position:relative;
}}

/* Dot pattern background texture */
body::before{{
  content:'';
  position:fixed;
  inset:0;
  background-image:radial-gradient(rgba(84,46,145,0.08) 1px,transparent 1px);
  background-size:24px 24px;
  pointer-events:none;
  z-index:0;
}}

.c{{max-width:1140px;margin:0 auto;padding:36px 28px 120px;position:relative;z-index:1;overflow-x:hidden}}

/* ── Glass morphism card base ── */
.glass-card{{
  background:var(--surface);
  backdrop-filter:var(--glass-blur);
  -webkit-backdrop-filter:var(--glass-blur);
  border-radius:var(--r);
  border:var(--glass-border);
  box-shadow:0 4px 24px rgba(0,0,0,0.2),inset 0 1px 0 rgba(255,255,255,0.04);
}}

/* ── Scroll animations — bidirectional (in on scroll down, out on scroll up) ── */
[data-animate]{{
  opacity:1;
  transform:translateY(0) scale(1);
}}
[data-animate].animate-ready{{
  opacity:0;
  transform:translateY(18px);
  transition:opacity 0.5s cubic-bezier(.16,1,.3,1),transform 0.5s cubic-bezier(.16,1,.3,1);
}}
[data-animate="card"].animate-ready{{
  transform:translateY(14px);
}}
[data-animate].in-view{{
  opacity:1;
  transform:translateY(0) scale(1);
}}
/* When scrolled OUT of view — stay fully visible, no hide/blur */
[data-animate].out-view-top{{
  opacity:1;
  transform:translateY(0) scale(1);
}}
[data-animate].out-view-bottom{{
  opacity:1;
  transform:translateY(0) scale(1);
}}

/* ── Subtle "alive" animations ── */

/* (Floating card animation removed — was causing scroll jank) */

/* Refresh button styling */
.refresh-btn{{
  display:inline-flex;align-items:center;gap:6px;
  padding:6px 16px;border-radius:20px;
  font-size:10px;font-weight:700;letter-spacing:.8px;
  background:rgba(84,46,145,0.15);color:#925FFF;
  border:1px solid rgba(84,46,145,0.35);
  box-shadow:0 0 20px rgba(84,46,145,0.15);
  cursor:pointer;
  transition:all 0.3s ease;
  text-transform:uppercase;
}}
.refresh-btn:hover{{
  background:rgba(84,46,145,0.25);
  box-shadow:0 0 30px rgba(84,46,145,0.3);
  transform:scale(1.05);
}}
.refresh-btn:active{{transform:scale(0.97)}}
.refresh-btn svg{{
  width:14px;height:14px;
  transition:transform 0.4s ease;
}}
.refresh-btn:hover svg{{transform:rotate(180deg)}}

/* Collapse animation for refresh */
@keyframes collapse-down{{
  0%{{transform:scaleY(1);opacity:1;transform-origin:top}}
  100%{{transform:scaleY(0);opacity:0;transform-origin:top}}
}}
.section-gap.collapsing,.grid4.collapsing{{
  animation:collapse-down 0.5s cubic-bezier(.4,0,.2,1) forwards;
}}

/* Breathing glow on glass cards */
@keyframes border-breathe{{
  0%,100%{{border-color:rgba(146,95,255,0.10);box-shadow:0 4px 24px rgba(0,0,0,0.2),inset 0 1px 0 rgba(255,255,255,0.04)}}
  50%{{border-color:rgba(146,95,255,0.22);box-shadow:0 4px 24px rgba(0,0,0,0.2),inset 0 1px 0 rgba(255,255,255,0.04),0 0 20px rgba(84,46,145,0.08)}}
}}
.glass-card{{
  animation:border-breathe 4s ease-in-out infinite;
}}
.glass-card:nth-child(2){{animation-delay:1s}}
.glass-card:nth-child(3){{animation-delay:2s}}
.glass-card:nth-child(4){{animation-delay:3s}}

/* Soft parallax on dot pattern background */
@keyframes dots-drift{{
  0%{{background-position:0 0}}
  100%{{background-position:24px 24px}}
}}
body::before{{
  animation:dots-drift 20s linear infinite;
}}

/* Ambient gradient orbs floating behind content */
body::after{{
  content:'';position:fixed;top:-50%;left:-50%;
  width:200%;height:200%;
  background:
    radial-gradient(ellipse 600px 600px at 20% 30%,rgba(84,46,145,0.06),transparent),
    radial-gradient(ellipse 400px 400px at 75% 60%,rgba(253,220,6,0.03),transparent),
    radial-gradient(ellipse 500px 500px at 50% 80%,rgba(0,176,166,0.04),transparent);
  pointer-events:none;z-index:0;
  animation:orb-drift 30s ease-in-out infinite alternate;
}}
@keyframes orb-drift{{
  0%{{transform:translate(0,0)}}
  100%{{transform:translate(30px,-20px)}}
}}

/* Subtle shine on HX yellow headings */
@keyframes text-glow{{
  0%,100%{{text-shadow:0 0 0 transparent}}
  50%{{text-shadow:0 0 16px rgba(253,220,6,0.18)}}
}}
.nar h2{{
  animation:text-glow 5s ease-in-out infinite;
}}

/* Section title slide-underline */
@keyframes underline-grow{{
  from{{width:0}}
  to{{width:40px}}
}}
.section-title{{position:relative;padding-bottom:8px}}
.section-title::after{{
  content:'';display:block;height:2px;
  background:linear-gradient(90deg,var(--yellow),transparent);
  margin-top:6px;
  animation:underline-grow 0.8s ease-out forwards;
}}

/* Metric value shimmer on hover */
@keyframes val-shimmer{{
  0%{{background-position:-200% center}}
  100%{{background-position:200% center}}
}}
.card .val,.pcard .pv{{
  background:linear-gradient(110deg,var(--text) 40%,var(--yellow) 50%,var(--text) 60%);
  background-size:200% auto;
  -webkit-background-clip:text;
  -webkit-text-fill-color:transparent;
  background-clip:text;
}}
.card:hover .val,.pcard:hover .pv{{
  animation:val-shimmer 1.5s ease-in-out;
}}

/* Positive metric pulse */
.chg-up{{
  transition:transform 0.4s cubic-bezier(.34,1.56,.64,1),color 0.3s ease-out,text-shadow 0.3s ease-out;
}}
.chg-up.metric-active{{
  transform:scale(1.15);
  color:var(--green-bright);
  text-shadow:0 0 10px rgba(0,176,166,0.35);
}}
/* Negative metric sink */
.chg-dn{{
  transition:transform 0.4s cubic-bezier(.34,1.56,.64,1),color 0.3s ease-out,text-shadow 0.3s ease-out;
}}
.chg-dn.metric-active{{
  transform:translateY(3px) scale(0.95);
  color:var(--red-bright);
  text-shadow:0 0 10px rgba(255,95,104,0.35);
}}

/* Card label icon pulse */
@keyframes label-dot{{
  0%,100%{{opacity:0.4}}
  50%{{opacity:1}}
}}
.card .lbl::before{{
  content:'';display:inline-block;width:6px;height:6px;border-radius:50%;
  margin-right:6px;vertical-align:middle;
  background:var(--accent-light);
  animation:label-dot 3s ease-in-out infinite;
}}
.card:nth-child(1) .lbl::before{{background:var(--yellow)}}
.card:nth-child(2) .lbl::before{{background:var(--blue)}}
.card:nth-child(3) .lbl::before{{background:var(--green)}}
.card:nth-child(4) .lbl::before{{background:var(--amber)}}

/* Chart bar hover glow */
.bar{{position:relative}}
.bar::after{{
  content:'';position:absolute;inset:-2px;border-radius:8px 8px 0 0;
  opacity:0;transition:opacity .2s;
  background:inherit;filter:blur(6px);z-index:-1;
}}
.bar:hover::after{{opacity:0.4}}

/* Narrative blockquote enter animation */
@keyframes quote-slide{{
  from{{transform:translateX(-8px);opacity:0}}
  to{{transform:translateX(0);opacity:1}}
}}
.nar blockquote{{
  animation:quote-slide 0.6s ease-out;
}}

/* Dig button subtle hover only — no pulse */

/* Table row hover */
.nar tr:hover td{{background:rgba(84,46,145,0.08);transition:background 0.2s}}

/* Good/bad color in narrative */
.nar strong:has(+ *){{}} /* fallback */

/* Scrollbar styling */
::-webkit-scrollbar{{width:6px}}
::-webkit-scrollbar-track{{background:transparent}}
::-webkit-scrollbar-thumb{{background:rgba(146,95,255,0.3);border-radius:3px}}
::-webkit-scrollbar-thumb:hover{{background:rgba(146,95,255,0.5)}}

/* Loading skeleton shimmer for cards before countup */
@keyframes skeleton-shimmer{{
  0%{{opacity:0.6}}
  50%{{opacity:1}}
  100%{{opacity:0.6}}
}}

/* ── More micro animations ── */

/* Hover ripple on cards */
.card,.pcard{{position:relative;overflow:hidden}}
.card::before,.pcard::before{{
  content:'';position:absolute;inset:0;
  background:radial-gradient(circle at var(--mx,50%) var(--my,50%),rgba(146,95,255,0.12) 0%,transparent 60%);
  opacity:0;transition:opacity 0.3s;pointer-events:none;z-index:0;
}}
.card:hover::before,.pcard:hover::before{{opacity:1}}

/* Section divider glow pulse */
.nar hr{{position:relative;overflow:visible}}
.nar hr::after{{
  content:'';position:absolute;left:50%;top:-1px;
  width:60px;height:3px;transform:translateX(-50%);
  background:linear-gradient(90deg,transparent,var(--accent-light),transparent);
  border-radius:2px;
  animation:hr-pulse 4s ease-in-out infinite;
}}
@keyframes hr-pulse{{
  0%,100%{{opacity:0.3;width:60px}}
  50%{{opacity:0.7;width:120px}}
}}

/* Stagger animation for grid items */
.grid4 .card:nth-child(1),.grid3 .pcard:nth-child(1){{animation-delay:0ms}}
.grid4 .card:nth-child(2),.grid3 .pcard:nth-child(2){{animation-delay:80ms}}
.grid4 .card:nth-child(3),.grid3 .pcard:nth-child(3){{animation-delay:160ms}}
.grid4 .card:nth-child(4){{animation-delay:240ms}}

/* Tooltip entrance bounce */
@keyframes tooltip-bounce{{
  0%{{transform:translateX(-50%) scale(0.8) translateY(8px);opacity:0}}
  60%{{transform:translateX(-50%) scale(1.03) translateY(-2px);opacity:1}}
  100%{{transform:translateX(-50%) scale(1) translateY(0);opacity:1}}
}}
.bar-col:hover .tooltip{{animation:tooltip-bounce 0.25s ease-out forwards}}

/* Focus ring on interactive elements */
.dig-btn:focus-visible,.trail-toggle:focus-visible{{
  outline:2px solid var(--accent-light);
  outline-offset:2px;
}}

/* (status-ping removed — replaced by refresh button) */

/* Card sub text fade in */
.card .sub{{
  opacity:0.6;
  transition:opacity 0.3s;
}}
.card:hover .sub{{opacity:1}}

/* HX logo subtle spin on hover */
.hdr img{{transition:transform 0.6s cubic-bezier(.34,1.56,.64,1)}}
.hdr img:hover{{transform:rotate(15deg) scale(1.1)}}

/* Action plan numbers pulse */
.nar ol li::marker{{color:var(--yellow)}}
@keyframes action-glow{{
  0%,100%{{text-shadow:0 0 0 transparent}}
  50%{{text-shadow:0 0 8px rgba(253,220,6,0.2)}}
}}
.nar ol li strong:first-child{{animation:action-glow 3s ease-in-out infinite}}

/* Trail toggle arrow bounce */
@keyframes arrow-bounce{{
  0%,100%{{transform:translateY(0)}}
  50%{{transform:translateY(3px)}}
}}
.trail-toggle svg{{animation:arrow-bounce 2s ease-in-out infinite}}
.trail-toggle.open svg{{animation:none;transform:rotate(180deg)}}

/* ── Banner — floating with rounded edges ── */
.banner-wrap{{
  margin:0 0 16px;
  position:relative;
  overflow:hidden;
  border-radius:16px;
  box-shadow:0 8px 32px rgba(0,0,0,0.4),0 0 20px rgba(84,46,145,0.2);
  border:1px solid rgba(146,95,255,0.15);
}}
.banner-img{{
  width:100%;
  display:block;
  height:auto;
  object-fit:cover;
  border-radius:16px;
}}
.banner-date{{
  position:absolute;
  bottom:12px;right:20px;
  font-size:12px;font-weight:600;
  color:rgba(255,255,255,0.7);
  text-shadow:0 1px 4px rgba(0,0,0,0.5);
  letter-spacing:.3px;
}}

/* ── Fixed floating toolbar — pill shape ── */
.hdr{{
  display:flex;
  justify-content:flex-end;
  align-items:center;
  gap:8px;
  padding:8px 20px;
  position:fixed;
  top:12px;
  right:12px;
  z-index:1000;
  background:rgba(15,18,30,0.6);
  backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);
  border-radius:9999px;
  border:1px solid rgba(146,95,255,0.25);
  box-shadow:0 4px 24px rgba(0,0,0,0.3),0 0 12px rgba(84,46,145,0.15),inset 0 1px 0 rgba(255,255,255,0.04);
}}
.hdr:hover{{
  border-color:rgba(146,95,255,0.45);
  box-shadow:0 4px 24px rgba(0,0,0,0.3),0 0 20px rgba(84,46,145,0.25),inset 0 1px 0 rgba(255,255,255,0.06);
}}
/* (badge CSS removed — replaced by .refresh-btn above) */
.inv-badge{{
  background:rgba(255,95,104,0.10);color:#FF8A91;
  border:1px solid rgba(255,95,104,0.25);
  padding:6px 14px 6px 24px;border-radius:20px;
  font-size:10px;font-weight:700;margin-left:8px;
  cursor:pointer;position:relative;
  transition:background 0.2s,border-color 0.2s;
  letter-spacing:.3px;
}}
.inv-badge::before{{
  content:'';position:absolute;left:10px;top:50%;transform:translateY(-50%);
  width:6px;height:6px;border-radius:50%;background:#FF5F68;
  animation:inv-pulse 2s ease-in-out infinite;
}}
@keyframes inv-pulse{{
  0%,100%{{opacity:1;box-shadow:0 0 4px rgba(255,95,104,0.4)}}
  50%{{opacity:0.5;box-shadow:0 0 10px rgba(255,95,104,0.8)}}
}}

/* At a Glance — traffic light text effects */
@keyframes glance-shimmer{{
  0%{{background-position:200% center}}
  100%{{background-position:-200% center}}
}}
@keyframes glance-amber-pulse{{
  0%,100%{{color:#FFC44F}}
  50%{{color:rgba(255,255,255,0.9)}}
}}
.glance-good{{
  color:#00D4C8;
  font-weight:800;
  font-size:1.05em;
}}
.glance-bad{{
  color:#FF4F58;
  animation:glance-flash 2.5s ease-in-out infinite;
  font-weight:800;
  font-size:1.05em;
}}
@keyframes glance-flash{{
  0%,100%{{color:#FF4F58}}
  50%{{color:rgba(255,255,255,0.9)}}
}}
.glance-watch{{
  color:#FFC44F;
  animation:glance-amber-pulse 3s ease-in-out infinite;
  font-weight:800;
  font-size:1.05em;
}}

/* Persistence badges for What's Driving This */
.badge-recurring{{
  display:inline-block;
  font-size:9px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;
  background:rgba(255,95,104,0.12);color:#FF8A91;
  border:1px solid rgba(255,95,104,0.25);
  padding:2px 8px;border-radius:10px;
  margin-left:8px;vertical-align:middle;
}}
.badge-emerging{{
  display:inline-block;
  font-size:9px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;
  background:rgba(255,181,95,0.12);color:#FFB55F;
  border:1px solid rgba(255,181,95,0.25);
  padding:2px 8px;border-radius:10px;
  margin-left:8px;vertical-align:middle;
}}
.badge-new{{
  display:inline-block;
  font-size:9px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;
  background:rgba(0,176,166,0.12);color:#5FFFF0;
  border:1px solid rgba(0,176,166,0.25);
  padding:2px 8px;border-radius:10px;
  margin-left:8px;vertical-align:middle;
}}
.badge-recovery{{
  display:inline-block;
  font-size:9px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;
  background:rgba(0,212,200,0.15);color:#00D4C8;
  border:1px solid rgba(0,212,200,0.3);
  padding:2px 8px;border-radius:10px;
  margin-left:8px;vertical-align:middle;
  animation:recovery-pulse 2s ease-in-out infinite;
}}
@keyframes recovery-pulse{{
  0%,100%{{opacity:0.85}} 50%{{opacity:1;box-shadow:0 0 8px rgba(0,212,200,0.3)}}
}}
/* ── View Trend button ── */
.view-trend-btn{{
  display:inline-flex;align-items:center;gap:5px;
  font-size:10px;font-weight:600;letter-spacing:.3px;
  background:rgba(146,95,255,0.08);color:rgba(146,95,255,0.85);
  border:1px solid rgba(146,95,255,0.2);border-radius:10px;
  padding:3px 10px;margin-left:8px;vertical-align:middle;
  cursor:pointer;font-family:inherit;transition:all 0.2s;
}}
.view-trend-btn:hover{{
  background:rgba(146,95,255,0.15);border-color:rgba(146,95,255,0.4);
  color:rgba(146,95,255,1);
}}
.view-trend-btn svg{{width:12px;height:12px}}
/* YoY trend bar chart */
.yoy-trend-wrap{{
  margin:12px 0 16px;padding:14px 16px;
  background:rgba(15,23,42,0.5);border:1px solid var(--border);
  border-radius:12px;overflow:hidden;
}}
.yoy-trend-wrap.loading{{
  border:2px solid transparent;
  background:
    rgba(15,23,42,0.5),
    conic-gradient(from var(--ai-spin,0deg),transparent 40%,rgba(146,95,255,0.6) 70%,rgba(95,200,255,0.4) 85%,transparent 100%);
  background-origin:border-box;
  background-clip:padding-box,border-box;
  animation:ai-border-spin 1.8s linear infinite;
  min-height:60px;
  display:flex;align-items:center;justify-content:center;
  font-size:12px;color:var(--muted);font-style:italic;
}}
.yoy-trend-header{{
  display:flex;justify-content:space-between;align-items:center;
  margin-bottom:10px;font-size:11px;color:var(--muted);
}}
.yoy-bar-row{{
  display:flex;align-items:center;gap:8px;margin:3px 0;
  font-size:10px;color:var(--muted);
}}
.yoy-bar-date{{width:36px;text-align:right;flex-shrink:0}}
.yoy-bar-track{{flex:1;height:18px;background:rgba(255,255,255,0.03);border-radius:4px;overflow:hidden;position:relative}}
.yoy-bar{{
  height:100%;border-radius:4px;
  transition:width 0.6s cubic-bezier(.16,1,.3,1);
  min-width:2px;
}}
.yoy-bar.positive{{background:linear-gradient(90deg,rgba(0,176,166,0.5),rgba(0,176,166,0.8))}}
.yoy-bar.negative{{background:linear-gradient(90deg,rgba(255,95,104,0.8),rgba(255,95,104,0.5))}}
.yoy-bar-val{{width:52px;text-align:right;flex-shrink:0;font-variant-numeric:tabular-nums}}
.yoy-bar-pct{{width:48px;text-align:right;flex-shrink:0;font-weight:600}}
.yoy-bar-pct.positive{{color:#00B0A6}}
.yoy-bar-pct.negative{{color:#FF5F68}}
.yoy-trendline-wrap{{margin-top:10px;height:40px;position:relative}}
.yoy-trendline-wrap canvas{{width:100%;height:100%}}

.inv-badge:hover{{
  background:rgba(255,95,104,0.18);
  border-color:rgba(255,95,104,0.5);
}}
.inv-badge .inv-tooltip{{
  position:absolute;top:calc(100% + 10px);right:0;
  background:var(--surface-solid);border:1px solid var(--border);
  border-radius:12px;padding:12px 16px;width:280px;
  font-size:12px;color:var(--text);line-height:1.6;
  opacity:0;pointer-events:none;z-index:99999;
  transition:opacity 0.2s,transform 0.2s;
  transform:translateY(-4px);
  box-shadow:0 8px 32px rgba(0,0,0,0.4);
}}
.inv-badge .inv-tooltip::before{{
  content:'';position:absolute;top:-6px;right:20px;
  width:12px;height:12px;background:var(--surface-solid);
  border-left:1px solid var(--border);border-top:1px solid var(--border);
  transform:rotate(45deg);
}}
.inv-badge:hover .inv-tooltip{{
  opacity:1;transform:translateY(0);pointer-events:auto;
}}

/* Archive button */
.archive-btn{{
  display:inline-flex;align-items:center;gap:6px;
  padding:6px 14px;border-radius:20px;
  font-size:10px;font-weight:700;letter-spacing:.5px;
  background:rgba(148,163,184,0.08);color:#94A3B8;
  border:1px solid rgba(148,163,184,0.2);
  cursor:pointer;
  transition:all 0.2s ease;
  text-transform:uppercase;
}}
.archive-btn:hover{{
  background:rgba(148,163,184,0.15);
  color:#CBD5E1;
  border-color:rgba(148,163,184,0.4);
}}

/* Archive overlay */
.archive-overlay{{
  position:fixed;top:0;left:0;right:0;bottom:0;
  background:rgba(0,0,0,0.7);backdrop-filter:blur(8px);
  z-index:10000;display:none;
  justify-content:center;align-items:center;
  animation:archive-fadein 0.3s ease;
}}
.archive-overlay.open{{display:flex}}
@keyframes archive-fadein{{from{{opacity:0}} to{{opacity:1}}}}
.archive-panel{{
  background:var(--surface-solid);
  border:1px solid var(--border);
  border-radius:16px;
  width:min(600px, 90vw);
  max-height:80vh;
  overflow:hidden;
  box-shadow:0 20px 60px rgba(0,0,0,0.5);
  display:flex;flex-direction:column;
}}
.archive-header{{
  padding:20px 24px;
  border-bottom:1px solid var(--border);
  display:flex;justify-content:space-between;align-items:center;
}}
.archive-header h2{{margin:0;font-size:16px;font-weight:700;color:var(--text)}}
.archive-close{{
  background:none;border:none;color:var(--muted);cursor:pointer;
  font-size:20px;padding:4px 8px;border-radius:8px;
  transition:background 0.2s;
}}
.archive-close:hover{{background:rgba(255,255,255,0.1);color:var(--text)}}
.archive-list{{
  overflow-y:auto;padding:12px 0;flex:1;
}}
.archive-item{{
  display:flex;align-items:center;gap:14px;
  padding:12px 24px;
  cursor:pointer;
  transition:background 0.15s;
  border-bottom:1px solid rgba(148,163,184,0.05);
}}
.archive-item:hover{{background:rgba(84,46,145,0.08)}}
.archive-date{{
  font-size:13px;font-weight:700;color:var(--text);
  min-width:100px;
}}
.archive-headline{{
  font-size:12px;color:var(--muted);
  flex:1;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}}
.archive-size{{
  font-size:10px;color:rgba(148,163,184,0.5);
  min-width:50px;text-align:right;
}}
.archive-empty{{
  padding:40px 24px;text-align:center;color:var(--muted);font-size:13px;
}}

/* ── Metric cards (top 4) ── */
.grid4{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}}
.card{{
  padding:20px 22px;
  transition:transform 0.2s ease-out,box-shadow 0.2s ease-out,border-color 0.2s ease-out;
  cursor:default;
}}
.card:hover{{
  transform:translateY(-4px) scale(1.02);
  box-shadow:0 8px 32px rgba(0,0,0,0.3),0 0 20px var(--accent-glow);
  border-color:var(--border-hover);
}}
.card .lbl{{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1.2px;font-weight:600}}
.card .val{{font-size:30px;font-weight:800;letter-spacing:-1.5px;margin:6px 0;font-variant-numeric:tabular-nums}}
.chg{{display:inline-block;font-size:12px;font-weight:700;padding:3px 10px;border-radius:8px;transition:transform 0.3s ease-out,color 0.3s ease-out}}
.chg-up{{background:rgba(0,176,166,0.12);color:var(--green)}}
.chg-up.metric-active{{transform:scale(1.15);color:var(--green-bright)}}
.chg-dn{{background:rgba(255,95,104,0.12);color:var(--red)}}
.chg-dn.metric-active{{transform:translateY(3px);color:var(--red-bright)}}
.chg-fl{{background:rgba(245,158,11,0.1);color:var(--amber)}}
.card .sub{{font-size:11px;color:var(--muted);margin-top:6px}}

/* ── Headline tile (full-width hero above key metrics) ── */
.headline-tile{{
  padding:28px 32px;
  margin-bottom:20px;
  position:relative;
  overflow:hidden;
}}
.headline-tile::before{{
  content:'';position:absolute;inset:0;
  background:linear-gradient(135deg,rgba(84,46,145,0.15) 0%,rgba(253,220,6,0.04) 100%);
  pointer-events:none;
}}
.headline-tile .hl-main{{
  font-size:17px;font-weight:700;line-height:1.6;color:var(--text);
  position:relative;z-index:1;
}}
.headline-tile .hl-main a{{
  color:var(--text);text-decoration:none;
  border-bottom:1px dotted rgba(253,220,6,0.3);
  transition:border-color 0.2s;
}}
.headline-tile .hl-main a:hover{{border-bottom-color:var(--yellow)}}
.hl-keyword{{
  color:var(--yellow);
  font-weight:800;
  display:inline-block;
  cursor:pointer;
  transition:transform 0.2s ease-out,text-shadow 0.2s ease,filter 0.2s ease,box-shadow 0.2s ease;
  text-decoration:none;
  padding:1px 4px;
  border-radius:4px;
  position:relative;
}}
.hl-keyword:hover{{
  transform:translateY(-3px) scale(1.1);
  text-shadow:0 0 16px rgba(253,220,6,0.6),0 0 30px rgba(253,220,6,0.3);
  filter:brightness(1.2);
  background:rgba(253,220,6,0.08);
  box-shadow:0 4px 16px rgba(253,220,6,0.15);
}}
/* Directional colour coding in headline */
.hl-up{{
  color:var(--green-bright);
  font-weight:800;
  display:inline-block;
  padding:1px 4px;
  border-radius:4px;
  cursor:default;
  transition:transform 0.2s ease-out,text-shadow 0.2s ease,background 0.2s ease,box-shadow 0.2s ease;
}}
.hl-up:hover{{
  transform:translateY(-3px) scale(1.1);
  text-shadow:0 0 16px rgba(0,212,200,0.6),0 0 30px rgba(0,212,200,0.3);
  background:rgba(0,176,166,0.1);
  box-shadow:0 4px 16px rgba(0,176,166,0.15);
}}
.hl-down{{
  color:var(--red-bright);
  font-weight:800;
  display:inline-block;
  padding:1px 4px;
  border-radius:4px;
  cursor:default;
  transition:transform 0.2s ease-out,color 0.2s ease;
}}
.hl-down:hover{{
  transform:translateY(-2px) scale(1.05);
  color:#fff;
}}
.hl-neutral{{
  color:var(--amber);
  font-weight:800;
  display:inline-block;
  padding:1px 4px;
  border-radius:4px;
  cursor:default;
  transition:transform 0.2s ease-out,color 0.2s ease;
}}
.hl-neutral:hover{{
  transform:translateY(-2px) scale(1.05);
  color:#fff;
}}
.headline-tile .hl-also{{
  font-size:12px;color:var(--muted);margin-top:10px;line-height:1.7;
  position:relative;z-index:1;
}}
.headline-tile .hl-also strong{{color:#b8a9d4}}
.headline-tile .hl-also a{{
  color:var(--muted);text-decoration:none;
  border-bottom:1px dotted rgba(184,169,212,0.3);
  transition:color 0.2s,border-color 0.2s;
}}
.headline-tile .hl-also a:hover{{color:var(--text);border-bottom-color:var(--text)}}

/* ── Period cards (3-col) ── */
.grid3{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:24px}}
.pcard{{
  padding:20px;text-align:center;
  transition:transform 0.2s ease-out,box-shadow 0.2s ease-out;
}}
.pcard:hover{{
  transform:translateY(-4px) scale(1.02);
  box-shadow:0 8px 32px rgba(0,0,0,0.3),0 0 20px var(--accent-glow);
}}
.pcard .pl{{font-size:11px;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.8px}}
.pcard .pv{{font-size:26px;font-weight:800;letter-spacing:-1px;margin:8px 0}}

/* ── Interactive chart ── */
.chart-wrap{{padding:24px;margin-bottom:24px;position:relative;overflow:visible}}
.chart-wrap .st{{font-size:12px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.8px;margin-bottom:16px}}
.chart-container{{position:relative;height:180px;display:flex;align-items:flex-end;gap:4px;overflow:visible;min-width:0;padding-top:80px}}
.bar-col{{flex:1 1 0;display:flex;flex-direction:column;align-items:center;cursor:pointer;position:relative;min-width:0}}
.bar{{
  border-radius:6px 6px 0 0;width:80%;min-width:14px;
  transition:opacity .15s,transform .15s;
  transform-origin:bottom center;
}}
.bar.animate-in{{
  animation:bar-grow 0.6s ease-out forwards;
}}
@keyframes bar-grow{{
  from{{transform:scaleY(0)}}
  to{{transform:scaleY(1)}}
}}
.bar:hover{{opacity:.8;transform:scaleY(1.03)}}
.bar-label{{font-size:9px;color:var(--muted);margin-top:6px;white-space:nowrap}}
.avg-line{{
  position:absolute;left:0;right:0;height:2px;
  background:rgba(253,220,6,0.25);
  pointer-events:none;z-index:2;
}}
.avg-line::after{{
  content:'AVG';position:absolute;right:0;top:-16px;
  font-size:9px;font-weight:700;color:var(--muted);letter-spacing:.5px;
}}
.avg-line-inner{{
  width:0;height:100%;background:var(--muted);
  transition:width 1.2s ease-out;
}}
.avg-line.animate-in .avg-line-inner{{width:100%}}
.tooltip{{
  position:absolute;bottom:100%;left:50%;
  transform:translateX(-50%) scale(0.85);
  background:rgba(10,15,30,0.92);
  backdrop-filter:blur(16px);
  -webkit-backdrop-filter:blur(16px);
  border:1px solid var(--border);
  border-radius:12px;padding:12px 16px;
  font-size:12px;white-space:nowrap;pointer-events:none;
  opacity:0;transition:opacity .2s ease-out,transform .2s ease-out;
  z-index:99999;
  overflow:visible;
  box-shadow:0 8px 32px rgba(0,0,0,.5);
}}
.bar-col:hover .tooltip{{opacity:1;transform:translateX(-50%) scale(1)}}
.yoy-bar-col:hover .tooltip{{opacity:1;transform:translateX(-50%) scale(1)}}
.tooltip .tt-date{{font-weight:700;color:var(--text);margin-bottom:6px}}
.tooltip .tt-row{{color:var(--muted);line-height:1.7}}
.tooltip .tt-val{{color:var(--text);font-weight:600}}
.tooltip .tt-yoy-up{{color:#00D4C8;font-weight:600}}
.tooltip .tt-yoy-down{{color:#FF5F68;font-weight:600}}
/* YoY Growth chart */
.yoy-chart-container{{position:relative;height:120px;display:flex;align-items:center;gap:4px;overflow:visible;min-width:0}}
.yoy-bar-col{{flex:1 1 0;display:flex;flex-direction:column;align-items:center;cursor:pointer;position:relative;min-width:0;height:100%}}
.yoy-bar-area{{position:relative;flex:1;width:100%;display:flex;flex-direction:column;align-items:center}}
.yoy-bar{{width:80%;min-width:14px;border-radius:4px;position:absolute;transform-origin:center}}
.yoy-bar.animate-in{{animation:bar-grow 0.6s ease-out forwards}}
.yoy-zero-line{{position:absolute;left:0;right:0;height:1px;background:var(--border);top:50%;pointer-events:none;z-index:1}}

/* ── Narrative / analysis body ── */
.nar{{padding:36px 40px;margin-bottom:24px}}
.nar h1{{display:none}}
.nar h2{{
  font-size:16px;font-weight:700;color:var(--yellow);
  margin:32px 0 12px;padding-bottom:10px;
  border-bottom:1px solid var(--border);
}}
.nar h2:first-of-type{{margin-top:0}}
.nar h3{{font-size:14px;font-weight:700;color:var(--text);margin:20px 0 8px}}
.nar p{{font-size:13.5px;color:#cbd5e1;margin-bottom:12px;line-height:1.8}}
.nar blockquote{{
  border-left:3px solid var(--yellow);padding:14px 18px;margin:16px 0;
  background:rgba(253,220,6,0.04);border-radius:0 10px 10px 0;
  font-weight:600;font-size:13.5px;
}}
.nar ul,.nar ol{{padding-left:22px;margin-bottom:12px}}
.nar li{{font-size:13.5px;color:#cbd5e1;margin-bottom:6px;line-height:1.7}}
.nar strong{{color:#f1f5f9}}
.nar a{{color:var(--accent-light);text-decoration:none;border-bottom:1px dotted rgba(146,95,255,0.4);transition:color 0.2s,border-color 0.2s}}
.nar a:hover{{color:var(--yellow);border-bottom-color:var(--yellow)}}
.nar table{{width:100%;border-collapse:separate;border-spacing:0;margin:16px 0;font-size:12px;border-radius:10px;overflow:hidden}}
.nar th{{background:rgba(51,65,85,0.6);color:var(--text);padding:11px 15px;text-align:left;font-weight:600;font-size:10px;text-transform:uppercase;letter-spacing:.6px}}
.nar td{{padding:11px 15px;border-bottom:1px solid var(--border);color:#cbd5e1}}
.nar tr:last-child td{{border-bottom:none}}
.nar code{{background:rgba(51,65,85,0.5);padding:2px 7px;border-radius:5px;font-size:11.5px;color:var(--green)}}
.nar pre{{background:rgba(12,18,34,0.8);padding:18px;border-radius:10px;overflow-x:auto;border:1px solid var(--border);margin:12px 0}}
.nar pre code{{background:none;padding:0;color:var(--muted);font-size:11.5px;line-height:1.8}}
.nar hr{{border:none;border-top:1px solid var(--border);margin:24px 0}}

/* ── SQL dig buttons (glass-morphism) ── */
.dig-wrap{{margin:14px 0}}
.dig-btn{{
  background:rgba(84,46,145,0.06);
  color:#b8a9d4;
  border:1px solid rgba(84,46,145,0.15);
  border-radius:10px;padding:8px 16px;
  font-size:11px;font-weight:500;cursor:pointer;font-family:inherit;
  transition:all .2s ease-out;
  display:inline-flex;align-items:center;gap:6px;
  backdrop-filter:blur(8px);
  -webkit-backdrop-filter:blur(8px);
  letter-spacing:.2px;
}}
.dig-btn:hover{{
  background:rgba(84,46,145,0.15);
  border-color:rgba(84,46,145,0.4);
  box-shadow:0 0 16px rgba(84,46,145,0.15);
  transform:translateY(-1px);
}}
.dig-sql{{
  background:rgba(12,18,34,0.85) !important;
  backdrop-filter:blur(12px);
  -webkit-backdrop-filter:blur(12px);
  border:1px solid rgba(84,46,145,0.2) !important;
  border-radius:10px;margin-top:10px;position:relative;
}}
.dig-sql code{{color:#c4a5ff !important;font-size:12px !important}}
/* SQL syntax-like coloring */
.dig-sql code .kw{{color:#925FFF}}
.dig-sql code .str{{color:#34d399}}
.copy-btn{{
  position:absolute;top:10px;right:10px;
  background:rgba(51,65,85,0.6);
  backdrop-filter:blur(8px);
  color:var(--muted);
  border:1px solid var(--border);border-radius:8px;
  padding:5px 12px;font-size:11px;cursor:pointer;font-family:inherit;
  transition:all .15s ease-out;
}}
.copy-btn:hover{{color:var(--text);background:rgba(71,85,105,0.6)}}

/* ── Dig button row ── */
.dig-buttons{{display:flex;gap:8px;flex-wrap:wrap}}

/* ── Ask-about-this driver panel ── */
.ask-driver-btn{{
  background:rgba(0,176,166,0.06);
  color:#5FFFF0;
  border:1px solid rgba(0,176,166,0.2);
  border-radius:10px;padding:8px 16px;
  font-size:11px;font-weight:500;cursor:pointer;font-family:inherit;
  transition:all .2s ease-out;
  display:inline-flex;align-items:center;gap:6px;
  backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);
  letter-spacing:.2px;
}}
.ask-driver-btn:hover{{
  background:rgba(0,176,166,0.15);border-color:rgba(0,176,166,0.4);
  box-shadow:0 0 16px rgba(0,176,166,0.15);transform:translateY(-1px);
}}
.driver-ask-panel{{
  margin-top:10px;padding:14px;
  background:rgba(12,18,34,0.6);border:1px solid var(--border);
  border-radius:12px;backdrop-filter:blur(12px);
}}
.ask-input-wrap{{display:flex;gap:8px}}
.ask-input{{
  flex:1;background:rgba(30,41,59,0.8);border:1px solid var(--border);
  border-radius:8px;padding:10px 14px;color:var(--text);font-size:13px;
  font-family:inherit;outline:none;transition:border-color 0.2s;
}}
.ask-input:focus{{border-color:rgba(0,176,166,0.5)}}
.ask-submit{{
  background:rgba(0,176,166,0.15);color:#5FFFF0;border:1px solid rgba(0,176,166,0.3);
  border-radius:8px;padding:10px 18px;font-size:12px;font-weight:600;
  cursor:pointer;font-family:inherit;transition:all 0.2s;
}}
.ask-submit:hover{{background:rgba(0,176,166,0.25);border-color:rgba(0,176,166,0.5)}}
.ask-response{{
  margin-top:12px;font-size:13px;color:#cbd5e1;line-height:1.7;
  display:flex;flex-direction:column;gap:10px;
}}
.ask-response .ask-loading{{
  color:var(--muted);font-style:italic;
  padding:12px 16px;border-radius:12px;
  border:2px solid transparent;
  background:
    rgba(30,41,59,0.6),
    conic-gradient(from var(--ai-spin,0deg),transparent 40%,rgba(146,95,255,0.6) 70%,rgba(95,200,255,0.4) 85%,transparent 100%);
  background-origin:border-box;
  background-clip:padding-box,border-box;
  animation:ai-border-spin 1.8s linear infinite;
}}
.ask-response .ask-answer{{white-space:pre-wrap}}
.ask-response .ask-sql-used{{
  margin-top:8px;font-size:11px;color:var(--muted);
  background:rgba(12,18,34,0.5);border:1px solid var(--border);
  border-radius:8px;padding:10px;max-height:100px;overflow-y:auto;
}}
.ask-response .ask-error{{color:#FF5F68}}
.ask-clarification{{
  display:block;color:#FFB55F;font-style:italic;
  padding:8px 12px;background:rgba(255,181,95,0.06);
  border-left:3px solid rgba(255,181,95,0.4);border-radius:4px;
  margin:4px 0;line-height:1.5;
}}

/* ── Chat panel ── */
.chat-panel{{
  position:fixed;top:0;right:0;bottom:0;width:420px;max-width:100vw;
  background:rgba(10,15,30,0.95);backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);
  border-left:1px solid rgba(146,95,255,0.2);
  z-index:10000;display:flex;flex-direction:column;
  box-shadow:-8px 0 40px rgba(0,0,0,0.5);
  transition:transform 0.3s ease-out;
}}
.chat-header{{
  display:flex;justify-content:space-between;align-items:center;
  padding:18px 20px;border-bottom:1px solid var(--border);
}}
.chat-title{{font-weight:700;font-size:15px;color:var(--text);letter-spacing:.3px}}
.chat-close{{
  background:none;border:none;color:var(--muted);font-size:24px;cursor:pointer;
  padding:0 4px;transition:color 0.2s;
}}
.chat-close:hover{{color:var(--text)}}
.chat-messages{{
  flex:1;overflow-y:auto;padding:16px 20px;
  display:flex;flex-direction:column;gap:14px;
}}
.chat-msg{{max-width:90%;padding:12px 16px;border-radius:12px;font-size:13px;line-height:1.7}}
.chat-msg.user{{
  align-self:flex-end;background:rgba(146,95,255,0.15);
  color:var(--text);border:1px solid rgba(146,95,255,0.2);
}}
.chat-msg.assistant{{
  align-self:flex-start;background:rgba(30,41,59,0.6);
  color:#cbd5e1;border:1px solid var(--border);white-space:pre-wrap;
}}
.chat-msg.assistant .chat-sql-count{{
  display:inline-block;margin-top:8px;font-size:10px;color:var(--muted);
  background:rgba(51,65,85,0.4);padding:2px 8px;border-radius:6px;
}}
.chat-msg.assistant .view-sql-btn{{
  display:inline-block;margin-top:8px;margin-left:6px;font-size:10px;
  color:#5fc8ff;background:rgba(95,200,255,0.1);border:1px solid rgba(95,200,255,0.3);
  padding:2px 10px;border-radius:6px;cursor:pointer;font-family:inherit;
  transition:all 0.2s;
}}
.chat-msg.assistant .view-sql-btn:hover{{background:rgba(95,200,255,0.2);}}
.chat-sql-detail{{
  display:none;margin-top:10px;background:rgba(15,23,42,0.8);border:1px solid var(--border);
  border-radius:8px;padding:12px;font-size:11px;max-height:300px;overflow-y:auto;
}}
.chat-sql-detail.open{{display:block;}}
.chat-sql-detail pre{{
  margin:0;white-space:pre-wrap;word-break:break-all;color:#93c5fd;font-size:11px;line-height:1.5;
}}
.chat-sql-detail .sql-block{{margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid rgba(148,163,184,0.15);}}
.chat-sql-detail .sql-block:last-child{{border-bottom:none;margin-bottom:0;padding-bottom:0;}}
.chat-sql-detail .sql-label{{font-size:9px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:var(--muted);margin-bottom:4px;}}
.chat-sql-detail .sql-copy-btn{{
  float:right;font-size:9px;color:#5fc8ff;background:none;border:1px solid rgba(95,200,255,0.3);
  padding:1px 8px;border-radius:4px;cursor:pointer;font-family:inherit;
}}
.chat-sql-detail .sql-copy-btn:hover{{background:rgba(95,200,255,0.15);}}
/* ── AI response styled components ── */
.ai-metrics{{display:flex;flex-wrap:wrap;gap:10px;margin:10px 0;}}
.ai-metric-card{{
  flex:1 1 120px;min-width:100px;
  background:rgba(15,23,42,0.7);border:1px solid var(--border);border-radius:10px;
  padding:12px 14px;text-align:center;
}}
.ai-metric-label{{font-size:10px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);margin-bottom:4px;}}
.ai-metric-value{{font-size:20px;font-weight:700;color:#f1f5f9;line-height:1.2;}}
.ai-metric-change{{font-size:11px;margin-top:4px;font-weight:600;}}
.ai-metric-change.up{{color:#34d399;}}
.ai-metric-change.down{{color:#f87171;}}
.ai-metric-change.flat{{color:var(--muted);}}
p.ai-summary{{
  font-size:13px;line-height:1.6;color:#e2e8f0;margin:10px 0;
  border-left:3px solid rgba(95,200,255,0.4);padding-left:12px;
}}
p.ai-summary strong{{color:#fff;}}
h4.ai-section-heading{{
  font-size:12px;text-transform:uppercase;letter-spacing:.8px;
  color:var(--accent);margin:16px 0 8px;padding-bottom:4px;
  border-bottom:1px solid rgba(148,163,184,0.15);
}}
table.ai-table{{
  width:100%;border-collapse:collapse;font-size:12px;margin:8px 0;
}}
table.ai-table th{{
  text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:.5px;
  color:var(--muted);padding:6px 10px;border-bottom:1px solid var(--border);
}}
table.ai-table td{{
  padding:5px 10px;border-bottom:1px solid rgba(148,163,184,0.08);color:#cbd5e1;
}}
table.ai-table td.up{{color:#34d399;font-weight:600;}}
table.ai-table td.down{{color:#f87171;font-weight:600;}}
table.ai-table tr:last-child td{{border-bottom:none;}}
table.ai-table tr:hover td{{background:rgba(51,65,85,0.3);}}
/* Override white-space for styled HTML responses */
.chat-msg.assistant .ai-metrics,
.chat-msg.assistant .ai-summary,
.chat-msg.assistant .ai-section-heading,
.chat-msg.assistant .ai-table{{white-space:normal;}}
.chat-msg.loading{{
  color:var(--muted);font-style:italic;
  border:2px solid transparent;
  background:
    rgba(30,41,59,0.6),
    conic-gradient(from var(--ai-spin,0deg),transparent 40%,rgba(146,95,255,0.6) 70%,rgba(95,200,255,0.4) 85%,transparent 100%);
  background-origin:border-box;
  background-clip:padding-box,border-box;
  animation:ai-border-spin 1.8s linear infinite;
}}
@keyframes ai-border-spin{{
  0%{{--ai-spin:0deg}}
  100%{{--ai-spin:360deg}}
}}
@property --ai-spin{{
  syntax:'<angle>';
  inherits:false;
  initial-value:0deg;
}}
/* AI loading stepper */
.ai-loading-steps{{display:flex;flex-direction:column;gap:6px;}}
.ai-step{{
  display:flex;align-items:center;gap:8px;
  font-size:12px;color:var(--muted);
  opacity:0;transform:translateY(6px);
  max-height:30px;overflow:hidden;
  transition:opacity 0.4s ease,transform 0.4s ease,color 0.4s ease,max-height 0.3s ease;
}}
.ai-step.active{{opacity:1;transform:translateY(0);color:rgba(146,95,255,0.9);}}
.ai-step.done{{opacity:0.5;transform:translateY(0);color:var(--muted);}}
.ai-step-icon{{width:14px;height:14px;flex-shrink:0;}}
.ai-step.active .ai-step-icon{{animation:ai-step-pulse 1.2s ease-in-out infinite;}}
@keyframes ai-step-pulse{{
  0%,100%{{opacity:0.5;transform:scale(0.9)}}
  50%{{opacity:1;transform:scale(1.1)}}
}}
.ai-step.done .ai-step-icon svg{{stroke:rgba(95,255,200,0.6)}}
.ai-step-dot{{
  width:6px;height:6px;border-radius:50%;
  background:rgba(146,95,255,0.6);
  margin:0 4px;
}}
.ai-step.active .ai-step-dot{{animation:ai-dot-pulse 1s ease-in-out infinite;background:rgba(146,95,255,0.9);}}
.ai-step.done .ai-step-dot{{background:rgba(95,255,200,0.4);}}
@keyframes ai-dot-pulse{{
  0%,100%{{transform:scale(1);opacity:0.6}}
  50%{{transform:scale(1.4);opacity:1}}
}}
.chat-input-wrap{{
  display:flex;gap:8px;padding:14px 20px;border-top:1px solid var(--border);
  background:rgba(15,23,42,0.8);
}}
.chat-input{{
  flex:1;background:rgba(30,41,59,0.8);border:1px solid var(--border);
  border-radius:10px;padding:12px 16px;color:var(--text);font-size:13px;
  font-family:inherit;outline:none;transition:border-color 0.2s;
}}
.chat-input:focus{{border-color:rgba(146,95,255,0.5)}}
.chat-send{{
  background:rgba(146,95,255,0.15);color:var(--accent-light);
  border:1px solid rgba(146,95,255,0.3);border-radius:10px;
  padding:12px 14px;cursor:pointer;transition:all 0.2s;display:flex;align-items:center;
}}
.chat-send:hover{{background:rgba(146,95,255,0.25);border-color:rgba(146,95,255,0.5)}}
.chat-reply-wrap{{
  display:flex;gap:8px;padding:8px 0;margin-top:8px;
}}
.chat-reply-input{{
  flex:1;background:rgba(30,41,59,0.8);border:1px solid var(--border);
  border-radius:10px;padding:10px 14px;color:var(--text);font-size:13px;
  font-family:inherit;outline:none;transition:border-color 0.2s;
}}
.chat-reply-input:focus{{border-color:rgba(146,95,255,0.5)}}
.chat-reply-send{{
  background:rgba(146,95,255,0.15);color:var(--accent-light);
  border:1px solid rgba(146,95,255,0.3);border-radius:10px;
  padding:10px 14px;cursor:pointer;transition:all 0.2s;display:flex;align-items:center;
}}
.chat-toggle-btn{{
  background:rgba(0,176,166,0.08);color:#5FFFF0;
  border:1px solid rgba(0,176,166,0.2);border-radius:20px;
  padding:6px 14px;font-size:11px;font-weight:600;cursor:pointer;
  font-family:inherit;transition:all 0.2s;
  display:inline-flex;align-items:center;gap:6px;
}}
.chat-toggle-btn:hover{{
  background:rgba(0,176,166,0.15);border-color:rgba(0,176,166,0.4);
  box-shadow:0 0 12px rgba(0,176,166,0.15);
}}

/* ── Investigation trail ── */
.trail-section{{margin-bottom:24px}}
.trail-toggle{{
  background:rgba(84,46,145,0.08);
  color:#E2E0EB;
  border:1px solid rgba(84,46,145,0.2);
  border-radius:12px;padding:12px 24px;
  font-size:13px;font-weight:600;cursor:pointer;font-family:inherit;
  transition:all .2s ease-out;
  display:flex;align-items:center;gap:10px;
  backdrop-filter:blur(8px);
  width:100%;justify-content:center;
}}
.trail-toggle:hover{{
  background:rgba(84,46,145,0.15);
  border-color:rgba(84,46,145,0.4);
  box-shadow:0 0 20px rgba(84,46,145,0.1);
  color:#fff;
}}
.trail-toggle svg{{transition:transform .3s ease-out}}
.trail-toggle.open svg{{transform:rotate(180deg)}}
.trail-body{{max-height:0;overflow:hidden;transition:max-height 0.5s ease-out,margin-top 0.3s ease-out;padding-left:24px;margin-top:0}}
.trail-body.open{{overflow:visible;margin-top:20px}}
.trail-step{{position:relative;padding-left:44px;margin-bottom:24px}}
.trail-connector{{
  position:absolute;left:13px;top:28px;bottom:-24px;width:2px;
  background:linear-gradient(to bottom,var(--accent-light),rgba(84,46,145,0.08));
}}
.trail-step:last-child .trail-connector{{display:none}}
.trail-dot{{
  position:absolute;left:-2px;top:6px;width:32px;height:24px;
  border-radius:12px;border:2px solid var(--accent-light);
  background:var(--bg);z-index:1;
  box-shadow:0 0 12px var(--accent-glow);
  display:flex;align-items:center;justify-content:center;
}}
.trail-dot-num{{font-size:9px;font-weight:800;color:var(--accent-light);white-space:nowrap}}
@keyframes dot-pulse{{
  0%,100%{{box-shadow:0 0 8px var(--accent-glow)}}
  50%{{box-shadow:0 0 16px rgba(146,95,255,0.4)}}
}}
.trail-dot{{animation:dot-pulse 3s ease-in-out infinite}}
.trail-intro{{font-size:13px;color:#cbd5e1;line-height:1.7;margin-bottom:20px}}
.trail-intro strong{{color:var(--yellow)}}
.trail-content{{padding:18px 22px}}
.trail-round-header{{display:flex;align-items:center;gap:12px;margin-bottom:10px;flex-wrap:wrap}}
.trail-round{{font-size:10px;font-weight:700;color:var(--accent-light);text-transform:uppercase;letter-spacing:1px;white-space:nowrap}}
.trail-round-desc{{font-size:13px;font-weight:700;color:var(--text)}}
.trail-round-meta{{font-size:11px;color:var(--muted);margin-left:auto}}
.trail-reasoning{{
  font-size:13px;color:#e2d6f0;margin-bottom:14px;line-height:1.7;
  padding:12px 16px;
  background:rgba(84,46,145,0.08);
  border-left:3px solid var(--accent-light);
  border-radius:0 10px 10px 0;
}}
.trail-reasoning strong{{color:var(--accent-light);font-size:10px;text-transform:uppercase;letter-spacing:.8px;display:block;margin-bottom:4px}}
.trail-calls{{display:flex;flex-direction:column;gap:10px}}
.trail-call{{background:rgba(15,23,42,0.5);border:1px solid var(--border);border-radius:8px;padding:12px 16px;transition:border-color 0.2s}}
.trail-call:hover{{border-color:var(--border-hover)}}
.trail-call-header{{font-size:12px;margin-bottom:4px}}
.trail-call-header strong{{color:var(--text)}}
.trail-call-summary{{font-size:12px;color:#cbd5e1;margin-bottom:6px;font-style:italic}}
.trail-call-details{{margin-top:4px}}
.trail-call-details summary{{
  font-size:11px;color:var(--accent-light);cursor:pointer;
  padding:4px 0;user-select:none;
  transition:color 0.2s;
}}
.trail-call-details summary:hover{{color:var(--yellow)}}
.trail-call-details[open] summary{{margin-bottom:8px}}
.trail-call-query{{margin-bottom:6px}}
.trail-call-query code{{font-size:11px;color:var(--muted);word-break:break-all;display:block;max-height:120px;overflow-y:auto;line-height:1.5}}
.trail-result{{font-size:11px;color:var(--muted);line-height:1.5;opacity:0.7;max-height:80px;overflow-y:auto;border-top:1px solid var(--border);padding-top:6px;margin-top:4px}}
.trail-result-error{{font-size:11px;color:var(--red);line-height:1.5;border-top:1px solid var(--border);padding-top:6px;margin-top:4px}}

/* ── Section spacing ── */
.section-gap{{margin-bottom:48px}}

/* ── Section title ── */
.section-title{{
  font-size:12px;font-weight:700;color:var(--muted);
  text-transform:uppercase;letter-spacing:1.2px;
  margin-bottom:16px;padding-left:2px;
}}

/* ── Footer ── */
.foot{{
  text-align:center;padding:24px;
  color:var(--muted);font-size:11px;
  border-top:1px solid var(--border);margin-top:16px;
  display:flex;flex-direction:column;gap:6px;align-items:center;
}}
.foot-brand{{font-size:10px;color:rgba(148,163,184,0.5);letter-spacing:.5px}}

/* ── Responsive ── */
@media(max-width:1024px){{
  .grid4{{grid-template-columns:repeat(2,1fr)}}
  .grid3{{grid-template-columns:repeat(2,1fr)}}
  .headline-tile{{padding:24px 22px}}
  .banner-wrap{{margin-top:48px}}
}}
@media(max-width:640px){{
  .grid4{{grid-template-columns:1fr}}
  .grid3{{grid-template-columns:1fr}}
  .nar{{padding:22px 16px}}
  .nar table{{font-size:11px;display:block;overflow-x:auto;-webkit-overflow-scrolling:touch}}
  .nar th,.nar td{{padding:8px 10px;white-space:nowrap}}
  .chart-container{{height:130px;padding-top:60px;overflow:hidden}}
  .chart-wrap{{padding:16px;overflow:hidden}}
  .yoy-chart-container{{height:90px;overflow:hidden}}
  .chart-wrap .st{{font-size:10px;letter-spacing:.5px;margin-bottom:10px}}
  .bar-col .tooltip{{display:none !important}}
  .banner-wrap{{margin:52px 0 10px;border-radius:12px}}
  .banner-img{{border-radius:12px}}
  .banner-date{{font-size:10px;bottom:8px;right:12px}}
  .hdr{{top:8px;right:8px;padding:6px 14px;gap:6px}}
  .hdr>div{{flex-wrap:wrap;gap:4px}}
  .c{{padding:20px 16px;overflow-x:hidden}}
  .card .val{{font-size:22px}}
  .pcard .pv{{font-size:20px}}
  .trail-step{{padding-left:32px}}
  .trail-body{{padding-left:8px}}
  .dig-wrap pre{{font-size:10px}}
  .headline-tile{{padding:20px 16px}}
  .headline-tile .hl-main{{font-size:15px;line-height:1.5}}
  .headline-tile .hl-also{{font-size:11px}}
  .inv-badge{{padding:4px 10px 4px 18px;font-size:9px}}
  .archive-btn,.refresh-btn,.chat-toggle-btn{{font-size:10px;padding:5px 10px}}
  .chat-panel{{width:100vw}}
  .driver-ask-panel{{padding:10px}}
  .ask-input{{font-size:12px;padding:8px 10px}}
}}
</style></head><body>
<div id="staging-banner" style="display:none;background:linear-gradient(90deg,#f59e0b,#f97316);color:#000;text-align:center;padding:6px 12px;font-size:12px;font-weight:700;letter-spacing:1px;text-transform:uppercase;position:sticky;top:0;z-index:9999;">&#9888; Staging Environment &mdash; Changes here are not live</div>
<script>if(location.hostname.includes('staging'))document.getElementById('staging-banner').style.display='block';</script>
<div class="c">

<!-- Banner -->
<div class="banner-wrap">
<img src="tradingCoveredBanner.png" alt="Trading Covered by Holiday Extras" class="banner-img">
<div class="banner-date" id="banner-date"></div>
<script>!function(){{var d=new Date(),days=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'],months=['January','February','March','April','May','June','July','August','September','October','November','December'];document.getElementById('banner-date').textContent=days[d.getDay()]+' '+d.getDate()+' '+months[d.getMonth()]+' '+d.getFullYear()}}()</script>
</div>

<!-- Sticky toolbar — buttons only -->
<div class="hdr">
<div style="display:flex;align-items:center;gap:8px;width:100%;justify-content:flex-end"><button class="chat-toggle-btn" onclick="toggleChat()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>Ask</button><button class="refresh-btn" onclick="triggerRefresh()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>Refresh</button><button class="archive-btn" onclick="toggleArchive()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px"><path d="M21 8v13H3V8"/><path d="M1 3h22v5H1z"/><path d="M10 12h4"/></svg>Archive</button>{"<span class='inv-badge' onclick='openInvestigations()'>" + str(inv_count) + " investigations<span class='inv-tooltip'>Trading Covered ran <strong>" + str(inv_count) + " automated checks</strong> across trading data, web analytics, market intelligence, and internal documents before writing this briefing.<br><br><strong>Click to see exactly what was investigated.</strong></span></span>" if inv_count else ""}</div>
</div>

<!-- Headline Tile — one-sentence takeaway -->
{headline_tile_html}

<!-- Key Metrics — cards animate individually, parent wrapper does NOT -->
<div class="section-gap">
<div class="section-title">Key Metrics &mdash; Yesterday vs Last Year</div>
<div class="grid4">
<div class="card glass-card" data-animate="card" style="transition-delay:0ms"><div class="lbl">Yesterday's GP</div><div class="val" data-countup data-target="{ty.get('total_gp',0):.0f}" data-prefix="&pound;">&pound;{ty.get('total_gp',0):,.0f}</div><div class="chg {"chg-up" if gp_pct>=0 else "chg-dn"}" data-metric>{fmt_pct(gp_pct)} vs same day LY</div><div class="sub">Same day LY: &pound;{ly.get('total_gp',0):,.0f}</div></div>
<div class="card glass-card" data-animate="card" style="transition-delay:80ms"><div class="lbl">Yesterday's Policies</div><div class="val" data-countup data-target="{ty.get('new_policies',0)}" data-prefix="">{ty.get('new_policies',0):,}</div><div class="chg {"chg-up" if vol_pct>=0 else "chg-dn"}" data-metric>{fmt_pct(vol_pct)} vs same day LY</div><div class="sub">Same day LY: {ly.get('new_policies',0):,}</div></div>
<div class="card glass-card" data-animate="card" style="transition-delay:160ms"><div class="lbl">Yesterday's GP / Policy</div><div class="val" data-countup data-target="{ty.get('avg_gp_per_policy',0):.2f}" data-prefix="&pound;" data-decimals="2">&pound;{ty.get('avg_gp_per_policy',0):.2f}</div><div class="chg {"chg-up" if gppp_pct>=0 else "chg-dn"}" data-metric>{fmt_pct(gppp_pct)} vs same day LY</div><div class="sub">Same day LY: &pound;{ly.get('avg_gp_per_policy',0):.2f}</div></div>
<div class="card glass-card" data-animate="card" style="transition-delay:240ms"><div class="lbl">Yesterday's Avg Price</div><div class="val" data-countup data-target="{ty.get('avg_customer_price',0):.0f}" data-prefix="&pound;">&pound;{ty.get('avg_customer_price',0):.0f}</div><div class="chg {"chg-fl" if abs(price_pct)<2 else ("chg-up" if price_pct>=0 else "chg-dn")}" data-metric>{fmt_pct(price_pct)} vs same day LY</div><div class="sub">Same day LY: &pound;{ly.get('avg_customer_price',0):.0f}</div></div>
</div>
</div>

<!-- Period Comparison — cards animate individually -->
<div class="section-gap">
<div class="section-title">Period Comparison &mdash; GP vs Last Year</div>
<div class="grid3">
<div class="pcard glass-card" data-animate="card" style="transition-delay:0ms"><div class="pl">Yesterday</div><div class="pv" data-countup data-target="{ty.get('total_gp',0):.0f}" data-prefix="&pound;">&pound;{ty.get('total_gp',0):,.0f}</div><div style="color:{status_color(gp_pct)};font-size:14px;font-weight:700" data-metric class="chg {"chg-up" if gp_pct>=0 else "chg-dn"}">{fmt_pct(gp_pct)} YoY</div></div>
<div class="pcard glass-card" data-animate="card" style="transition-delay:80ms"><div class="pl">Trailing 7 Days</div><div class="pv" data-countup data-target="{w_ty.get('total_gp',0):.0f}" data-prefix="&pound;">&pound;{w_ty.get('total_gp',0):,.0f}</div><div style="color:{status_color(w_gp_pct)};font-size:14px;font-weight:700" data-metric class="chg {"chg-up" if w_gp_pct>=0 else "chg-dn"}">{fmt_pct(w_gp_pct)} vs same 7d LY</div></div>
<div class="pcard glass-card" data-animate="card" style="transition-delay:160ms"><div class="pl">Trailing 28 Days</div><div class="pv" data-countup data-target="{m_ty.get('total_gp',0):.0f}" data-prefix="&pound;">&pound;{m_ty.get('total_gp',0):,.0f}</div><div style="color:{status_color(m_gp_pct)};font-size:14px;font-weight:700" data-metric class="chg {"chg-up" if m_gp_pct>=0 else "chg-dn"}">{fmt_pct(m_gp_pct)} vs same 28d LY</div></div>
</div>
</div>

<!-- Chart — simple reveal, no blur/scale -->
<div class="section-gap" data-animate="reveal">
<div class="section-title">14-Day GP Trend</div>
<div class="chart-wrap glass-card">
<div class="st">14-Day GP Trend &mdash; hover for detail (green = YoY growth, red = YoY decline)</div>
<div class="chart-container" id="trendChart"></div>
</div>
</div>

<!-- Narrative / Analysis — simple reveal -->
<div class="section-gap" data-animate="reveal">
<div class="section-title">Trading Briefing</div>
<div class="nar glass-card">{html_body}</div>
</div>

<!-- Investigation Trail -->
{inv_trail_section}

<!-- Footer -->
<div class="foot">
<div>Generated {now_str} &middot; {inv_count} investigations ({len(track_results) if track_results else 0} tracks + {len(follow_up_log) if follow_up_log else 0} follow-ups) via {MODEL} &middot; Data: BigQuery + Sheets + Drive + Web</div>
<div class="foot-brand">Trading Covered &mdash; Powered by AI for Holiday Extras</div>
</div>

</div><!-- /.c -->

<script>
/* ── Staging: route API calls to production (preview deployments have no secrets) ── */
window.__apiBase=location.hostname.includes('staging')?'https://trading-covered.pages.dev':'';

/* ── Pre-loaded driver trend data (keyed by driver name) ── */
window.__driverTrends={driver_trends_json};

/* ── Pre-computed field values for AI chat (from pipeline) ── */
window.__fieldDiscovery={field_discovery_json};

/* ── Chart ── */
const data={chart_data_json};
const chart=document.getElementById('trendChart');
let chartBuilt=false;

function buildChart(){{
  if(chartBuilt||!data.length) return;
  chartBuilt=true;
  const maxGP=Math.max(...data.map(d=>d.gp));
  const minGP=Math.min(...data.map(d=>d.gp));
  const range=maxGP-minGP||1;
  const avgGP=data.reduce((s,d)=>s+d.gp,0)/data.length;
  const avgH=((avgGP-minGP)/range)*150+20;
  const dayNames=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  const monthNames=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

  data.forEach((d,i)=>{{
    const col=document.createElement('div');col.className='bar-col';
    const h=((d.gp-minGP)/range)*150+20;
    /* Green = YoY growth (GP > LY), Red = YoY decline */
    const isGrowth=d.ly_gp>0?d.gp>=d.ly_gp:true;
    const gradTop=isGrowth?'#00D4C8':'#FF8A91';
    const gradBot=isGrowth?'#00B0A6':'#FF5F68';
    const dateObj=new Date(d.date+'T00:00:00');
    const dateLabel=dayNames[dateObj.getDay()]+' '+dateObj.getDate();
    const fullDate=dayNames[dateObj.getDay()]+' '+dateObj.getDate()+' '+monthNames[dateObj.getMonth()];
    /* YoY tooltip values */
    const yoyPct=d.yoy_pct!==null?d.yoy_pct:null;
    const yoyAbs=d.yoy_abs!==null?d.yoy_abs:null;
    const yoyClass=yoyPct!==null?(yoyPct>=0?'tt-yoy-up':'tt-yoy-down'):'tt-val';
    const yoySign=yoyPct!==null&&yoyPct>=0?'+':'';
    const yoyAbsSign=yoyAbs!==null&&yoyAbs>=0?'+':'';
    col.innerHTML=`
      <div class="tooltip">
        <div class="tt-date">${{fullDate}}</div>
        <div class="tt-row">TY GP: <span class="tt-val" style="color:${{gradTop}}">&pound;${{d.gp.toLocaleString()}}</span></div>
        <div class="tt-row">LY GP: <span class="tt-val">&pound;${{d.ly_gp?d.ly_gp.toLocaleString():'N/A'}}</span></div>
        ${{yoyPct!==null?`<div class="tt-row">YoY: <span class="${{yoyClass}}">${{yoyAbsSign}}&pound;${{yoyAbs.toLocaleString()}} (${{yoySign}}${{yoyPct}}%)</span></div>`:''}}
        <div class="tt-row">Policies TY: <span class="tt-val">${{d.policies.toLocaleString()}}</span></div>
      </div>
      <div class="bar animate-in" style="height:${{h}}px;background:linear-gradient(to top,${{gradBot}},${{gradTop}});animation-delay:${{i*60}}ms;transform:scaleY(0)"></div>
      <div class="bar-label">${{dateLabel}}</div>`;
    chart.appendChild(col);
  }});

  /* Average line */
  const avgLine=document.createElement('div');
  avgLine.className='avg-line';
  avgLine.style.bottom=avgH+'px';
  avgLine.innerHTML='<div class="avg-line-inner"></div>';
  chart.appendChild(avgLine);
  requestAnimationFrame(()=>{{
    requestAnimationFrame(()=>{{avgLine.classList.add('animate-in')}});
  }});

}}

/* ── SQL dig toggle/copy ── */
function toggleSQL(id){{
  const el=document.getElementById(id);
  if(el.style.display==='none'){{
    el.style.display='block';
    /* Basic SQL keyword highlighting */
    const code=el.querySelector('code');
    if(code&&!code.dataset.highlighted){{
      code.dataset.highlighted='1';
      const keywords=/\\b(SELECT|FROM|WHERE|AND|OR|GROUP BY|ORDER BY|JOIN|LEFT|RIGHT|INNER|ON|AS|IN|NOT|NULL|IS|BETWEEN|LIKE|LIMIT|OFFSET|HAVING|UNION|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TABLE|INTO|VALUES|SET|CASE|WHEN|THEN|ELSE|END|COUNT|SUM|AVG|MIN|MAX|DISTINCT|WITH|OVER|PARTITION BY|ROW_NUMBER|RANK|DENSE_RANK|COALESCE|CAST|EXTRACT|DATE|TIMESTAMP|INTERVAL|TRUE|FALSE|ASC|DESC|EXISTS|ANY|ALL|EXCEPT|INTERSECT|CROSS|FULL|OUTER|NATURAL|USING|RECURSIVE|LATERAL|WINDOW|FILTER|WITHIN|ARRAY_AGG|STRING_AGG|UNNEST|STRUCT|SAFE_DIVIDE|IF|IFNULL|NULLIF|FORMAT_DATE|DATE_DIFF|DATE_ADD|DATE_SUB|DATE_TRUNC|PARSE_DATE|CURRENT_DATE|CURRENT_TIMESTAMP|GENERATE_DATE_ARRAY|LAG|LEAD)\\b/gi;
      const strings=/'([^']*)'/g;
      let html=code.innerHTML;
      html=html.replace(strings,`<span class="str">'$1'</span>`);
      html=html.replace(keywords,(m)=>'<span class="kw">'+m+'</span>');
      code.innerHTML=html;
    }}
  }}else{{
    el.style.display='none';
  }}
}}
function copySQL(id){{
  const el=document.getElementById(id);
  const sql=el.querySelector('code').innerText;
  navigator.clipboard.writeText(sql).then(()=>{{
    const btn=el.querySelector('.copy-btn');
    btn.textContent='Copied!';
    setTimeout(()=>btn.textContent='Copy',2000);
  }});
}}

/* ── Ask about this driver ── */
/* ── Animated AI loading stepper ── */
const AI_STEPS_INITIAL=[
  'Connecting to BigQuery…',
  'Checking today\\'s date…',
  'Writing SQL query…',
  'Running query against BigQuery…',
  'Analysing results…',
  'Running follow-up query…',
  'Verifying figures…',
  'Formatting answer…'
];
const AI_STEPS_SLOW=[
  'Taking longer than usual — still working on it…',
  'Still crunching the numbers — complex query running…',
  'Hang tight — pulling additional data…',
  'Still processing — cross-referencing results…',
  'Working through a deeper analysis…',
  'Nearly there — refining the answer…',
  'Still going — validating the figures…',
  'Wrapping up the analysis…',
  'Running final checks on the data…',
  'Almost done — formatting the response…'
];
const AI_STEP_FINAL='Preparing your answer…';

function createAILoadingEl(){{
  const container=document.createElement('div');
  container.className='ai-loading-steps';
  return container;
}}

function startAILoadingStepper(container){{
  let stepIdx=0;
  let phase='initial';
  let slowIdx=0;
  const MAX_VISIBLE=4;
  const startTime=Date.now();

  function addStep(text){{
    if(container._stopped) return;
    const prev=container.querySelector('.ai-step.active');
    if(prev){{prev.classList.remove('active');prev.classList.add('done');}}
    const steps=container.querySelectorAll('.ai-step');
    if(steps.length>=MAX_VISIBLE){{
      const oldest=steps[0];
      oldest.style.opacity='0';
      oldest.style.transform='translateY(-10px)';
      oldest.style.maxHeight='0';
      oldest.style.marginBottom='0';
      oldest.style.paddingTop='0';
      oldest.style.paddingBottom='0';
      oldest.style.transition='all 0.3s ease';
      setTimeout(()=>oldest.remove(),300);
    }}
    const step=document.createElement('div');
    step.className='ai-step';
    step.innerHTML='<span class="ai-step-dot"></span><span>'+text+'</span>';
    container.appendChild(step);
    requestAnimationFrame(()=>requestAnimationFrame(()=>step.classList.add('active')));
    const scrollParent=container.closest('.chat-messages')||container.closest('.ask-response');
    if(scrollParent) scrollParent.scrollTop=scrollParent.scrollHeight;
  }}

  function tick(){{
    if(container._stopped) return;
    const elapsed=Date.now()-startTime;
    if(phase==='initial'){{
      if(stepIdx<AI_STEPS_INITIAL.length){{
        addStep(AI_STEPS_INITIAL[stepIdx]);
        stepIdx++;
        if(elapsed>=30000){{ phase='slow'; container._timer=setTimeout(tick,2000); return; }}
        const timings=[800,2000,3000,5000,4000,5000,4000,5000];
        container._timer=setTimeout(tick,timings[Math.min(stepIdx-1,timings.length-1)]);
      }} else {{
        if(elapsed>=30000){{ phase='slow'; container._timer=setTimeout(tick,2000); }}
        else {{ container._timer=setTimeout(tick,3000); }}
      }}
    }} else if(phase==='slow'){{
      if(slowIdx<AI_STEPS_SLOW.length){{
        addStep(AI_STEPS_SLOW[slowIdx]);
        slowIdx++;
        container._timer=setTimeout(tick,20000);
      }} else {{
        phase='final';
        addStep(AI_STEP_FINAL);
      }}
    }}
  }}

  tick();
  return container;
}}

function stopAILoadingStepper(container){{
  container._stopped=true;
  if(container._timer) clearTimeout(container._timer);
  const active=container.querySelector('.ai-step.active');
  if(active){{active.classList.remove('active');active.classList.add('done');}}
}}

/* ── Fuzzy-match heading text to best driver trend key ── */
const __trendUsed=new Set();
function _matchTrend(headingText){{
  const trends=window.__driverTrends||{{}};
  const keys=Object.keys(trends);
  if(!keys.length) return null;
  const stop=new Set(['the','a','an','and','or','of','in','on','to','for','is','from','by','with','not','recurring','emerging','new','trend']);
  function tokens(s){{
    return s.toLowerCase().replace(/[^a-z0-9\\s/]/g,' ').split(/\\s+/)
      .flatMap(w=>w.split('/')).filter(w=>w.length>1&&!stop.has(w));
  }}
  const hTokens=new Set(tokens(headingText));
  let bestKey=null,bestScore=0;
  for(const key of keys){{
    if(__trendUsed.has(key)) continue;
    const kTokens=new Set(tokens(key));
    let overlap=0;
    for(const t of hTokens) if(kTokens.has(t)) overlap++;
    const score=overlap/Math.min(hTokens.size,kTokens.size);
    if(score>bestScore&&overlap>=1){{bestScore=score;bestKey=key;}}
  }}
  if(bestKey&&bestScore>=0.25){{
    __trendUsed.add(bestKey);
    return trends[bestKey];
  }}
  return null;
}}

/* ── Toggle matched trend chart (pre-loaded, instant) ── */
function toggleMatchedTrend(trendId, btn){{
  const container=document.getElementById(trendId);
  if(!container) return;

  /* Toggle off */
  if(container.querySelector('.yoy-trend-wrap')){{
    container.innerHTML='';
    return;
  }}

  /* Get heading text and match to trend data */
  const h3=btn.closest('h3');
  const heading=h3?h3.textContent.replace(/Trend.*/,'').replace(/Recovery/g,'').trim():'Driver';
  let data=container._matchedData;
  if(!data){{
    data=_matchTrend(heading);
    container._matchedData=data;
  }}
  if(!data){{
    /* Fallback to live API fetch */
    fetchDriverTrend(trendId,btn);
    return;
  }}
  try{{
    const trendResult={{ty:data.ty.map(d=>({{dt:d.dt,gp:d.val,vol:0}})),ly:data.ly.map(d=>({{dt:d.dt,gp:d.val,vol:0}}))}};
    renderYoYTrend(container, trendResult, heading, data);
    /* Update button with persistence info */
    const cd=data.consistent_days||0;
    const td=data.total_days||10;
    btn.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>Trend ('+cd+'/'+td+'d)';
    /* Insert recovery badge if applicable */
    if(data.recovery&&h3&&!h3.querySelector('.badge-recovery')){{
      const badge=document.createElement('span');
      badge.className='badge-recovery';
      badge.textContent='Recovery';
      const trendBtn=h3.querySelector('.view-trend-btn');
      if(trendBtn) h3.insertBefore(badge,trendBtn);
    }}
  }}catch(e){{
    container.innerHTML='<div class="yoy-trend-wrap" style="padding:12px;font-size:12px;color:var(--muted)">Error: '+e.message+'</div>';
  }}
}}

/* ── Fetch and render YoY trend bar chart for recurring/emerging drivers ── */
function fetchDriverTrend(trendId, btn){{
  const container=document.getElementById(trendId);
  if(!container) return;

  /* Toggle: if already shown, hide */
  if(container.querySelector('.yoy-trend-wrap')&&!container.querySelector('.loading')){{
    container.innerHTML='';
    btn.textContent='Trend';
    return;
  }}

  /* Get driver context from heading */
  const h3=btn.closest('h3');
  const headingText=h3?h3.textContent.replace('Trend','').trim():'';

  /* Build dates: 14 days ending yesterday */
  const now=new Date();
  const yesterday=new Date(now);yesterday.setDate(now.getDate()-1);
  const start=new Date(yesterday);start.setDate(yesterday.getDate()-13);
  const lyEnd=new Date(yesterday);lyEnd.setDate(yesterday.getDate()-364);
  const lyStart=new Date(start);lyStart.setDate(start.getDate()-364);

  function fmt(d){{return d.toISOString().slice(0,10)}}

  /* Ask AI to write the segment filter SQL for this driver */
  container.innerHTML='<div class="yoy-trend-wrap loading">Loading trend data…</div>';
  btn.textContent='Loading…';

  /* Use the ask endpoint to get the AI to write + run a trend query */
  fetch((window.__apiBase||'')+'/api/ask',{{
    method:'POST',
    headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{
      question:'Return ONLY a JSON object with a single key "segment_filter" containing a SQL WHERE clause fragment that isolates this segment: "'+headingText+'". Examples: "distribution_channel=\\'Direct\\' AND policy_type=\\'Single\\'", "cover_level_name=\\'Bronze\\'". Return ONLY valid JSON, no explanation.',
      mode:'general'
    }})
  }})
  .then(r=>r.json())
  .then(data=>{{
    /* Try to extract segment_filter from the AI response */
    let segFilter='1=1';
    try{{
      const answer=data.answer||'';
      const jsonMatch=answer.match(/\\{{[^{{}}]*"segment_filter"[^{{}}]*\\}}/);
      if(jsonMatch){{
        segFilter=JSON.parse(jsonMatch[0]).segment_filter||'1=1';
      }}else{{
        /* Try to find a WHERE clause fragment */
        const whereMatch=answer.match(/(?:distribution_channel|policy_type|cover_level_name|insurance_group)[^"\\n]{{5,120}}/i);
        if(whereMatch) segFilter=whereMatch[0].replace(/[`]/g,"'");
      }}
    }}catch(e){{}}

    /* Now run the actual trend queries */
    const tySQL=`SELECT transaction_date AS dt, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp, SUM(policy_count) AS vol FROM \\`hx-data-production.commercial_finance.insurance_policies_new\\` WHERE transaction_date BETWEEN '${{fmt(start)}}' AND '${{fmt(yesterday)}}' AND ${{segFilter}} GROUP BY transaction_date ORDER BY transaction_date`;
    const lySQL=`SELECT transaction_date AS dt, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp, SUM(policy_count) AS vol FROM \\`hx-data-production.commercial_finance.insurance_policies_new\\` WHERE transaction_date BETWEEN '${{fmt(lyStart)}}' AND '${{fmt(lyEnd)}}' AND ${{segFilter}} GROUP BY transaction_date ORDER BY transaction_date`;

    return fetch((window.__apiBase||'')+'/api/ask',{{
      method:'POST',
      headers:{{'Content-Type':'application/json'}},
      body:JSON.stringify({{
        mode:'trend',
        trend_sql:{{ty:tySQL,ly:lySQL}}
      }})
    }});
  }})
  .then(r=>r.json())
  .then(result=>{{
    if(result.error){{
      container.innerHTML='<div class="yoy-trend-wrap" style="padding:12px;font-size:12px;color:var(--muted)">Could not load trend: '+result.error+'</div>';
      btn.textContent='Trend';
      return;
    }}
    renderYoYTrend(container, result.trend, headingText, null);
    btn.textContent='Hide trend';
  }})
  .catch(err=>{{
    container.innerHTML='<div class="yoy-trend-wrap" style="padding:12px;font-size:12px;color:var(--muted)">Error: '+err.message+'</div>';
    btn.textContent='Trend';
  }});
}}

function renderYoYTrend(container, trendData, title, meta){{
  const tyRows=trendData.ty||[];
  const lyRows=trendData.ly||[];
  if(!tyRows.length){{
    container.innerHTML='<div class="yoy-trend-wrap" style="padding:12px;font-size:12px;color:var(--muted)">No data returned.</div>';
    return;
  }}

  /* Compute persistence from the data if not provided */
  const direction=(meta&&meta.direction)||'down';
  let consistentDays=meta&&meta.consistent_days;
  let totalDays=meta&&meta.total_days;
  let persistenceLabel=meta&&meta.persistence;

  if(consistentDays==null){{
    const n=Math.min(tyRows.length,lyRows.length,10);
    const tyTail=tyRows.slice(-n);
    const lyTail=lyRows.slice(-n);
    let count=0;
    for(let i=0;i<n;i++){{
      const tv=parseFloat(tyTail[i].gp)||0;
      const lv=parseFloat(lyTail[i].gp)||0;
      if(direction==='down'?tv<lv:tv>lv) count++;
    }}
    consistentDays=count;totalDays=n;
    persistenceLabel=count>=7?'recurring':count>=5?'emerging':'new';
  }}

  /* Match TY and LY by index (both should be 14 days, aligned by day-of-week) */
  const maxGP=Math.max(...tyRows.map(r=>Math.abs(parseFloat(r.gp)||0)),...lyRows.map(r=>Math.abs(parseFloat(r.gp)||0)),1);

  /* Detect recovery: last 2 days both improving vs LY */
  const isRecovery=meta&&meta.recovery;
  let recoveryDetected=isRecovery;
  if(recoveryDetected==null&&tyRows.length>=2&&lyRows.length>=2){{
    const ty1=parseFloat(tyRows[tyRows.length-2].gp)||0;
    const ty2=parseFloat(tyRows[tyRows.length-1].gp)||0;
    const ly1=parseFloat(lyRows[lyRows.length-2].gp)||0;
    const ly2=parseFloat(lyRows[lyRows.length-1].gp)||0;
    if(direction==='down') recoveryDetected=(ty1>ly1&&ty2>ly2);
    else recoveryDetected=(ty1<ly1&&ty2<ly2);
  }}

  /* Persistence summary */
  const persColor=persistenceLabel==='recurring'?'#FF8A91':persistenceLabel==='emerging'?'#FFB55F':'#5FFFF0';
  const recoveryHTML=recoveryDetected?
    `<div style="font-size:10px;font-weight:700;color:#00D4C8;padding:2px 8px;background:rgba(0,212,200,0.12);border:1px solid rgba(0,212,200,0.25);border-radius:10px;animation:recovery-pulse 2s ease-in-out infinite">⬆ Recovery — last 2 days improving</div>`:'';
  const persHTML=`<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;padding:8px 12px;background:rgba(255,255,255,0.02);border-radius:8px;border:1px solid var(--border);flex-wrap:wrap">`+
    `<div style="font-size:11px;color:var(--muted)">Persistence threshold</div>`+
    `<div style="display:flex;gap:2px;align-items:center">`+
    Array.from({{length:totalDays}},(_, i)=>{{
      /* last N days: color each dot by whether it was consistent */
      const idx=tyRows.length-totalDays+i;
      const tv=idx>=0?parseFloat(tyRows[idx].gp)||0:0;
      const lv=idx>=0&&lyRows[idx]?parseFloat(lyRows[idx].gp)||0:0;
      const hit=direction==='down'?tv<lv:tv>lv;
      const dotColor=hit?persColor:'rgba(255,255,255,0.12)';
      return `<div style="width:8px;height:16px;border-radius:2px;background:${{dotColor}};transition:background 0.3s"></div>`;
    }}).join('')+
    `</div>`+
    `<div style="font-size:11px;font-weight:700;color:${{persColor}}">${{consistentDays}}/${{totalDays}} days ${{direction}}</div>`+
    `<div style="font-size:10px;color:var(--muted);margin-left:auto">`+
    (persistenceLabel==='recurring'?'≥7 = Recurring':persistenceLabel==='emerging'?'5–6 = Emerging':'<5 = New')+
    `</div>`+recoveryHTML+`</div>`;

  let barsHTML='';
  tyRows.forEach((row,i)=>{{
    const dt=new Date(row.dt+'T00:00:00');
    const dayLabel=(dt.getMonth()+1)+'/'+dt.getDate();
    const tyGP=parseFloat(row.gp)||0;
    const lyGP=(lyRows[i]&&parseFloat(lyRows[i].gp))||0;
    const yoyPct=lyGP?((tyGP-lyGP)/Math.abs(lyGP))*100:0;
    const isPos=tyGP>=lyGP;
    const barW=Math.max((Math.abs(tyGP)/maxGP)*100,2);
    const pctClass=isPos?'positive':'negative';

    barsHTML+=
      `<div class="yoy-bar-row">`+
      `<div class="yoy-bar-date">${{dayLabel}}</div>`+
      `<div class="yoy-bar-track"><div class="yoy-bar ${{pctClass}}" style="width:0%"></div></div>`+
      `<div class="yoy-bar-val">£${{Math.round(tyGP).toLocaleString()}}</div>`+
      `<div class="yoy-bar-pct ${{pctClass}}">${{isPos?'+':''}}${{yoyPct.toFixed(0)}}%</div>`+
      `</div>`;
  }});

  /* Trendline canvas */
  const wrap=document.createElement('div');
  wrap.className='yoy-trend-wrap';
  wrap.innerHTML=
    `<div class="yoy-trend-header"><span>${{title}} — 14 day daily GP</span><span>YoY growth coloured</span></div>`+
    persHTML+
    barsHTML+
    `<div class="yoy-trendline-wrap"><canvas></canvas></div>`;
  container.innerHTML='';
  container.appendChild(wrap);

  /* Animate bars in */
  requestAnimationFrame(()=>{{
    const bars=wrap.querySelectorAll('.yoy-bar');
    tyRows.forEach((row,i)=>{{
      const tyGP=parseFloat(row.gp)||0;
      const barW=Math.max((Math.abs(tyGP)/maxGP)*100,2);
      if(bars[i]) bars[i].style.width=barW+'%';
    }});
  }});

  /* Draw trend line on canvas */
  const canvas=wrap.querySelector('canvas');
  if(canvas){{
    const ctx=canvas.getContext('2d');
    const dpr=window.devicePixelRatio||1;
    const rect=canvas.parentElement;
    const w=rect.clientWidth;const h=40;
    canvas.width=w*dpr;canvas.height=h*dpr;
    canvas.style.width=w+'px';canvas.style.height=h+'px';
    ctx.scale(dpr,dpr);

    const vals=tyRows.map(r=>parseFloat(r.gp)||0);
    const lyVals=lyRows.map(r=>parseFloat(r.gp)||0);
    const allVals=[...vals,...lyVals];
    const mn=Math.min(...allVals);const mx=Math.max(...allVals);
    const range=mx-mn||1;

    function drawTrendLine(data,color,width,dashed){{
      if(!data.length) return;
      ctx.beginPath();ctx.strokeStyle=color;ctx.lineWidth=width;
      ctx.setLineDash(dashed?[4,3]:[]);
      const step=w/(data.length-1||1);
      data.forEach((v,i)=>{{
        const x=i*step;
        const y=2+(1-(v-mn)/range)*(h-4);
        if(i===0) ctx.moveTo(x,y);else ctx.lineTo(x,y);
      }});
      ctx.stroke();
    }}

    drawTrendLine(lyVals,'rgba(255,255,255,0.15)',1.5,true);
    drawTrendLine(vals,'rgba(146,95,255,0.85)',2,false);

    /* Dot on last TY value */
    if(vals.length){{
      const lastX=(vals.length-1)*(w/(vals.length-1||1));
      const lastY=2+(1-(vals[vals.length-1]-mn)/range)*(h-4);
      ctx.beginPath();
      ctx.arc(lastX,lastY,3,0,Math.PI*2);
      ctx.fillStyle='rgba(146,95,255,1)';ctx.fill();
    }}
  }}
}}

/* Per-driver conversation history — keyed by panel id */
const driverHistory={{}};

function openDriverAsk(id){{
  const panel=document.getElementById(id);
  if(!panel) return;
  const isOpen=panel.style.display!=='none';
  panel.style.display=isOpen?'none':'block';
  if(!isOpen){{
    panel.querySelector('.ask-input').focus();
  }}
}}

function getDriverContext(panel){{
  const wrap=panel.closest('.dig-wrap');
  let ctx='';
  if(wrap){{
    let prev=wrap.previousElementSibling;
    while(prev){{
      if(prev.tagName==='H3'||prev.tagName==='P'){{
        ctx+=prev.textContent+'\\n';
      }}
      if(prev.tagName==='H3') break;
      prev=prev.previousElementSibling;
    }}
  }}
  return ctx;
}}

function buildSqlButton(sqlQueries){{
  if(!sqlQueries||!sqlQueries.length) return '';
  const successful=sqlQueries.filter(q=>q.success);
  if(!successful.length) return '';
  const uid='sql-'+Math.random().toString(36).slice(2,8);
  let html='<button class="view-sql-btn" data-sql-uid="'+uid+'">View SQL</button>';
  html+='<div id="'+uid+'" class="chat-sql-detail">';
  successful.forEach((q,i)=>{{
    const escaped=q.sql.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    html+='<div class="sql-block"><div class="sql-label">Query '+(i+1)+' ('+q.rows+' row'+(q.rows===1?'':'s')+')'
      +'<button class="sql-copy-btn">Copy</button></div>'
      +'<pre>'+escaped+'</pre></div>';
  }});
  html+='</div>';
  return html;
}}

/* Delegate click handlers for SQL view/copy buttons */
document.addEventListener('click',function(e){{
  const sqlBtn=e.target.closest('.view-sql-btn');
  if(sqlBtn){{
    const uid=sqlBtn.getAttribute('data-sql-uid');
    const d=document.getElementById(uid);
    if(d){{
      d.classList.toggle('open');
      sqlBtn.textContent=d.classList.contains('open')?'Hide SQL':'View SQL';
    }}
    return;
  }}
  const copyBtn=e.target.closest('.sql-copy-btn');
  if(copyBtn){{
    const pre=copyBtn.closest('.sql-block').querySelector('pre');
    navigator.clipboard.writeText(pre.textContent).then(()=>{{
      copyBtn.textContent='Copied!';
      setTimeout(()=>copyBtn.textContent='Copy',1500);
    }});
  }}
}});

function addDriverMessage(responseDiv,role,content){{
  const msg=document.createElement('div');
  msg.className='chat-msg '+role;
  if(role==='assistant') msg.innerHTML=content;
  else msg.textContent=content;
  responseDiv.appendChild(msg);
}}

function addDriverReplyInput(responseDiv,id){{
  /* Remove any existing reply inputs */
  responseDiv.querySelectorAll('.chat-reply-wrap').forEach(el=>el.remove());
  const wrap=document.createElement('div');
  wrap.className='chat-reply-wrap';
  wrap.innerHTML='<input type="text" class="chat-input chat-reply-input" placeholder="Ask a follow-up…">'
    +'<button class="chat-send chat-reply-send" onclick="submitDriverReply(this,\\''+id+'\\')"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:16px;height:16px"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg></button>';
  responseDiv.appendChild(wrap);
  const inp=wrap.querySelector('.chat-reply-input');
  inp.addEventListener('keydown',function(e){{if(e.key==='Enter')submitDriverReply(wrap.querySelector('.chat-reply-send'),id)}});
  inp.focus();
}}

function submitDriverAsk(id){{
  const panel=document.getElementById(id);
  const input=panel.querySelector('.ask-input');
  const responseDiv=document.getElementById(id+'-response');
  const question=input.value.trim();
  if(!question) return;

  /* Init history for this driver */
  if(!driverHistory[id]) driverHistory[id]=[];
  const driverContext=getDriverContext(panel);

  /* Show user message */
  addDriverMessage(responseDiv,'user',question);
  input.value='';
  input.style.display='none';
  input.closest('.ask-input-wrap').querySelector('.ask-submit').style.display='none';

  /* Loading stepper */
  const loader=createAILoadingEl();
  const loadingWrap=document.createElement('div');
  loadingWrap.className='chat-msg assistant loading';
  loadingWrap.appendChild(loader);
  responseDiv.appendChild(loadingWrap);
  startAILoadingStepper(loader);

  driverHistory[id].push({{role:'user',content:question}});

  fetch((window.__apiBase||'')+'/api/ask',{{
    method:'POST',
    headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{
      question:question,
      driver_context:driverContext,
      conversation_history:driverHistory[id].slice(-10),
      mode:'driver',
      field_discovery:window.__fieldDiscovery||null
    }})
  }})
  .then(r=>r.json())
  .then(data=>{{
    stopAILoadingStepper(loader);
    loadingWrap.remove();
    let content=data.answer||data.error||'No response';
    if(data.needs_clarification){{
      content='<span class="ask-clarification">🤔 '+content+'</span>';
    }} else if(data.sql_queries&&data.sql_queries.length>0){{
      content+='<span class="chat-sql-count">'+data.sql_queries.length+' SQL quer'+(data.sql_queries.length===1?'y':'ies')+' · '+data.rounds+' round'+(data.rounds===1?'':'s')+'</span>';
      content+=buildSqlButton(data.sql_queries);
    }}
    addDriverMessage(responseDiv,'assistant',content);
    driverHistory[id].push({{role:'assistant',content:data.answer||''}});
    addDriverReplyInput(responseDiv,id);
  }})
  .catch(err=>{{
    stopAILoadingStepper(loader);
    loadingWrap.remove();
    addDriverMessage(responseDiv,'assistant','<span class="ask-error">Failed to connect: '+err.message+'</span>');
    addDriverReplyInput(responseDiv,id);
  }});
}}

function submitDriverReply(btn,id){{
  const wrap=btn.closest('.chat-reply-wrap');
  const input=wrap.querySelector('.chat-reply-input');
  const question=input.value.trim();
  if(!question) return;

  const responseDiv=document.getElementById(id+'-response');
  const panel=document.getElementById(id);
  const driverContext=getDriverContext(panel);

  /* Convert reply input to user message */
  const userMsg=document.createElement('div');
  userMsg.className='chat-msg user';
  userMsg.textContent=question;
  wrap.replaceWith(userMsg);

  /* Loading */
  const loader=createAILoadingEl();
  const loadingWrap=document.createElement('div');
  loadingWrap.className='chat-msg assistant loading';
  loadingWrap.appendChild(loader);
  responseDiv.appendChild(loadingWrap);
  startAILoadingStepper(loader);

  if(!driverHistory[id]) driverHistory[id]=[];
  driverHistory[id].push({{role:'user',content:question}});

  fetch((window.__apiBase||'')+'/api/ask',{{
    method:'POST',
    headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{
      question:question,
      driver_context:driverContext,
      conversation_history:driverHistory[id].slice(-10),
      mode:'driver',
      field_discovery:window.__fieldDiscovery||null
    }})
  }})
  .then(r=>r.json())
  .then(data=>{{
    stopAILoadingStepper(loader);
    loadingWrap.remove();
    let content=data.answer||data.error||'No response';
    if(data.needs_clarification){{
      content='<span class="ask-clarification">🤔 '+content+'</span>';
    }} else if(data.sql_queries&&data.sql_queries.length>0){{
      content+='<span class="chat-sql-count">'+data.sql_queries.length+' SQL quer'+(data.sql_queries.length===1?'y':'ies')+' · '+data.rounds+' round'+(data.rounds===1?'':'s')+'</span>';
      content+=buildSqlButton(data.sql_queries);
    }}
    addDriverMessage(responseDiv,'assistant',content);
    driverHistory[id].push({{role:'assistant',content:data.answer||''}});
    addDriverReplyInput(responseDiv,id);
  }})
  .catch(err=>{{
    stopAILoadingStepper(loader);
    loadingWrap.remove();
    addDriverMessage(responseDiv,'assistant','<span class="ask-error">Connection error: '+err.message+'</span>');
    addDriverReplyInput(responseDiv,id);
  }});
}}

/* ── General chat panel ── */
let chatHistory=[];
function toggleChat(){{
  const panel=document.getElementById('chatPanel');
  const isOpen=panel.style.display!=='none';
  panel.style.display=isOpen?'none':'flex';
  if(!isOpen){{
    /* Show input bar on first open */
    const inputWrap=document.querySelector('.chat-input-wrap');
    inputWrap.style.display='flex';
    document.getElementById('chatInput').focus();
  }}
}}

function submitChat(){{
  const inputWrap=document.querySelector('.chat-input-wrap');
  const input=document.getElementById('chatInput');
  const messagesDiv=document.getElementById('chatMessages');
  const question=input.value.trim();
  if(!question) return;

  /* Add user message bubble */
  const userMsg=document.createElement('div');
  userMsg.className='chat-msg user';
  userMsg.textContent=question;
  messagesDiv.appendChild(userMsg);

  /* Hide the input bar — it becomes just a sent message */
  inputWrap.style.display='none';
  input.value='';

  /* Add animated loading stepper */
  const loadingMsg=document.createElement('div');
  loadingMsg.className='chat-msg assistant loading';
  const chatLoader=createAILoadingEl();
  loadingMsg.appendChild(chatLoader);
  startAILoadingStepper(chatLoader);
  messagesDiv.appendChild(loadingMsg);
  messagesDiv.scrollTop=messagesDiv.scrollHeight;

  chatHistory.push({{role:'user',content:question}});

  fetch((window.__apiBase||'')+'/api/ask',{{
    method:'POST',
    headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{
      question:question,
      conversation_history:chatHistory.slice(-10),
      mode:'general',
      field_discovery:window.__fieldDiscovery||null
    }})
  }})
  .then(r=>r.json())
  .then(data=>{{
    stopAILoadingStepper(chatLoader);
    messagesDiv.removeChild(loadingMsg);

    const assistantMsg=document.createElement('div');
    assistantMsg.className='chat-msg assistant';
    let content=data.answer||data.error||'No response';
    if(data.needs_clarification){{
      content='<span class="ask-clarification">🤔 '+content+'</span>';
    }} else if(data.sql_queries&&data.sql_queries.length>0){{
      content+='\\n<span class="chat-sql-count">'+data.sql_queries.length+' SQL quer'+(data.sql_queries.length===1?'y':'ies')+' · '+data.rounds+' round'+(data.rounds===1?'':'s')+'</span>';
      content+=buildSqlButton(data.sql_queries);
    }}
    assistantMsg.innerHTML=content;
    messagesDiv.appendChild(assistantMsg);

    chatHistory.push({{role:'assistant',content:data.answer||''}});

    /* Add a new reply input inline at the bottom of the transcript */
    addChatReplyInput(messagesDiv);
    messagesDiv.scrollTop=messagesDiv.scrollHeight;
  }})
  .catch(err=>{{
    messagesDiv.removeChild(loadingMsg);
    const errMsg=document.createElement('div');
    errMsg.className='chat-msg assistant';
    errMsg.innerHTML='<span class="ask-error">Connection error: '+err.message+'</span>';
    messagesDiv.appendChild(errMsg);
    /* Still offer a reply input */
    addChatReplyInput(messagesDiv);
    messagesDiv.scrollTop=messagesDiv.scrollHeight;
  }});
}}

function addChatReplyInput(container){{
  /* Remove any existing inline reply inputs */
  container.querySelectorAll('.chat-reply-wrap').forEach(el=>el.remove());

  const wrap=document.createElement('div');
  wrap.className='chat-reply-wrap';
  wrap.innerHTML='<input type="text" class="chat-input chat-reply-input" placeholder="Ask a follow-up...">'
    +'<button class="chat-send chat-reply-send" onclick="submitChatReply(this)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:16px;height:16px"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg></button>';
  container.appendChild(wrap);
  const replyInput=wrap.querySelector('.chat-reply-input');
  replyInput.addEventListener('keydown',function(e){{if(e.key==='Enter')submitChatReply(wrap.querySelector('.chat-reply-send'))}});
  replyInput.focus();
}}

function submitChatReply(btn){{
  const wrap=btn.closest('.chat-reply-wrap');
  const input=wrap.querySelector('.chat-reply-input');
  const question=input.value.trim();
  if(!question) return;

  const messagesDiv=document.getElementById('chatMessages');

  /* Convert this reply input into a user message */
  const userMsg=document.createElement('div');
  userMsg.className='chat-msg user';
  userMsg.textContent=question;
  wrap.replaceWith(userMsg);

  /* Animated loading stepper */
  const loadingMsg=document.createElement('div');
  loadingMsg.className='chat-msg assistant loading';
  const replyLoader=createAILoadingEl();
  loadingMsg.appendChild(replyLoader);
  startAILoadingStepper(replyLoader);
  messagesDiv.appendChild(loadingMsg);
  messagesDiv.scrollTop=messagesDiv.scrollHeight;

  chatHistory.push({{role:'user',content:question}});

  fetch((window.__apiBase||'')+'/api/ask',{{
    method:'POST',
    headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{
      question:question,
      conversation_history:chatHistory.slice(-10),
      mode:'general',
      field_discovery:window.__fieldDiscovery||null
    }})
  }})
  .then(r=>r.json())
  .then(data=>{{
    stopAILoadingStepper(replyLoader);
    messagesDiv.removeChild(loadingMsg);
    const assistantMsg=document.createElement('div');
    assistantMsg.className='chat-msg assistant';
    let content=data.answer||data.error||'No response';
    if(data.needs_clarification){{
      content='<span class="ask-clarification">🤔 '+content+'</span>';
    }} else if(data.sql_queries&&data.sql_queries.length>0){{
      content+='\\n<span class="chat-sql-count">'+data.sql_queries.length+' SQL quer'+(data.sql_queries.length===1?'y':'ies')+' · '+data.rounds+' round'+(data.rounds===1?'':'s')+'</span>';
      content+=buildSqlButton(data.sql_queries);
    }}
    assistantMsg.innerHTML=content;
    messagesDiv.appendChild(assistantMsg);
    chatHistory.push({{role:'assistant',content:data.answer||''}});
    addChatReplyInput(messagesDiv);
    messagesDiv.scrollTop=messagesDiv.scrollHeight;
  }})
  .catch(err=>{{
    messagesDiv.removeChild(loadingMsg);
    const errMsg=document.createElement('div');
    errMsg.className='chat-msg assistant';
    errMsg.innerHTML='<span class="ask-error">Connection error: '+err.message+'</span>';
    messagesDiv.appendChild(errMsg);
    addChatReplyInput(messagesDiv);
    messagesDiv.scrollTop=messagesDiv.scrollHeight;
  }});
}}

/* ── Investigation trail toggle ── */
function toggleTrail(){{
  const body=document.getElementById('trailBody');
  const btn=document.getElementById('trailToggle');
  if(!body||!btn) return;
  const willOpen=!body.classList.contains('open');
  if(willOpen){{
    body.style.maxHeight=body.scrollHeight+'px';
    body.classList.add('open');
    btn.classList.add('open');
    /* After transition, remove max-height cap so content is never clipped */
    setTimeout(function(){{body.style.maxHeight='none';}},700);
  }}else{{
    /* Set explicit height first so transition works for closing */
    body.style.maxHeight=body.scrollHeight+'px';
    body.offsetHeight; /* force reflow */
    body.style.maxHeight='0';
    body.classList.remove('open');
    btn.classList.remove('open');
  }}
  const isOpen=willOpen;
  /* Update button text — find text node after svg */
  const nodes=btn.childNodes;
  for(let i=0;i<nodes.length;i++){{
    if(nodes[i].nodeType===3&&nodes[i].textContent.trim()){{
      nodes[i].textContent=isOpen?' Hide full investigation trail':' Show full investigation trail';
      break;
    }}
  }}
}}

/* ── Open investigations from toolbar badge ── */
function openInvestigations(){{
  const section=document.querySelector('.trail-section');
  const body=document.getElementById('trailBody');
  if(!section) return;
  /* Open the trail if it's closed */
  if(body&&!body.classList.contains('open')){{
    toggleTrail();
  }}
  /* Scroll so the section header is right below the sticky toolbar */
  setTimeout(function(){{
    const hdr=document.querySelector('.hdr');
    const offset=hdr?hdr.offsetHeight+8:50;
    const top=section.getBoundingClientRect().top+window.scrollY-offset;
    window.scrollTo({{top:top,behavior:'smooth'}});
  }},100);
}}

/* ── Scroll-reactive animations — BIDIRECTIONAL ── */
(function(){{
  /* Enable animation classes — content visible by default without JS */
  document.querySelectorAll('[data-animate]').forEach(el=>el.classList.add('animate-ready'));

  let chartBuilt=false;

  /* 1. MAIN OBSERVER — ONE-WAY reveal only, never hides content once visible */
  const mainRevealed=new WeakSet();
  const mainObs=new IntersectionObserver((entries)=>{{
    entries.forEach(e=>{{
      if(e.isIntersecting&&!mainRevealed.has(e.target)){{
        mainRevealed.add(e.target);
        e.target.classList.add('in-view');
        e.target.classList.remove('out-view-top','out-view-bottom','animate-ready');
        /* Build chart on first reveal */
        if(!chartBuilt&&e.target.querySelector('#trendChart')){{
          chartBuilt=true;buildChart();
        }}
      }}
    }});
  }},{{threshold:0.15,rootMargin:'0px 0px 60px 0px'}});
  document.querySelectorAll('[data-animate]').forEach(el=>mainObs.observe(el));

  /* 3. Metric pulse on scroll — positive grows, negative sinks */
  const metricObs=new IntersectionObserver((entries)=>{{
    entries.forEach(e=>{{
      if(e.isIntersecting){{e.target.classList.add('metric-active');}}
      else{{e.target.classList.remove('metric-active');}}
    }});
  }},{{threshold:0.5}});
  document.querySelectorAll('[data-metric]').forEach(el=>metricObs.observe(el));

  /* 4. CountUp animation */
  const counted=new WeakSet();
  const countObs=new IntersectionObserver((entries)=>{{
    entries.forEach(e=>{{
      if(e.isIntersecting&&!counted.has(e.target)){{
        counted.add(e.target);
        const el=e.target;
        const raw=el.dataset.target||'0';
        const target=parseFloat(raw.replace(/,/g,''));
        const prefix=el.dataset.prefix||'';
        const decimals=parseInt(el.dataset.decimals||'0');
        const dur=800;const start=performance.now();
        function tick(now){{
          const p=Math.min((now-start)/dur,1);
          const eased=1-Math.pow(1-p,3);
          el.innerHTML=prefix+(target*eased).toLocaleString(undefined,{{minimumFractionDigits:decimals,maximumFractionDigits:decimals}});
          if(p<1) requestAnimationFrame(tick);
        }}
        requestAnimationFrame(tick);
      }}
    }});
  }},{{threshold:0.2}});
  document.querySelectorAll('[data-countup]').forEach(el=>countObs.observe(el));

  /* 5. Staggered reveal for narrative sub-elements — ONE-WAY fade in only, never hides */
  const narRevealed=new WeakSet();
  const narObs=new IntersectionObserver((entries)=>{{
    entries.forEach(e=>{{
      if(e.isIntersecting&&!narRevealed.has(e.target)){{
        narRevealed.add(e.target);
        e.target.style.opacity='1';
        e.target.style.transform='translateY(0)';
      }}
    }});
  }},{{threshold:0.01,rootMargin:'0px 0px 60px 0px'}});
  document.querySelectorAll('.nar h2,.nar blockquote,.nar table,.dig-wrap,.nar>p,.nar>ul,.nar>ol').forEach((el,i)=>{{
    el.style.opacity='0';
    el.style.transform='translateY(16px)';
    el.style.transition=`opacity 0.45s cubic-bezier(.16,1,.3,1) ${{(i%6)*40}}ms, transform 0.45s cubic-bezier(.16,1,.3,1) ${{(i%6)*40}}ms`;
    narObs.observe(el);
  }});

  /* 6. Immediately reveal anything already in viewport on load */
  requestAnimationFrame(()=>{{
    document.querySelectorAll('[data-animate]').forEach(el=>{{
      const rect=el.getBoundingClientRect();
      if(rect.top<window.innerHeight&&rect.bottom>0){{
        el.classList.add('in-view');
      }}
    }});
    if(!chartBuilt){{
      const cc=document.getElementById('trendChart');
      if(cc&&cc.getBoundingClientRect().top<window.innerHeight){{chartBuilt=true;buildChart();}}
    }}
  }});

  /* 7. Mouse-tracking hover ripple on cards */
  document.querySelectorAll('.card,.pcard').forEach(el=>{{
    el.addEventListener('mousemove',(e)=>{{
      const rect=el.getBoundingClientRect();
      el.style.setProperty('--mx',((e.clientX-rect.left)/rect.width*100)+'%');
      el.style.setProperty('--my',((e.clientY-rect.top)/rect.height*100)+'%');
    }});
  }});

  /* Hover sparkle on metric values */
  document.querySelectorAll('.card .val,.pcard .pv').forEach(el=>{{
    el.addEventListener('mouseenter',()=>{{
      el.style.transition='letter-spacing 0.3s ease-out';
      el.style.letterSpacing='-0.5px';
      setTimeout(()=>{{el.style.letterSpacing='-1.5px'}},150);
    }});
  }});

  /* 9. Progress indicator — thin bar at top showing scroll progress */
  const bar=document.createElement('div');
  bar.style.cssText='position:fixed;top:0;left:0;height:2px;background:linear-gradient(90deg,var(--accent),var(--yellow));z-index:999;transition:width 0.1s linear;width:0';
  document.body.appendChild(bar);
  window.addEventListener('scroll',()=>{{
    const pct=(window.scrollY/(document.body.scrollHeight-window.innerHeight))*100;
    bar.style.width=pct+'%';
  }},{{passive:true}});

  /* 10. Init driver trend badges + buttons from computed data */
  (function initDriverTrends(){{
    const trends=window.__driverTrends||{{}};
    if(!Object.keys(trends).length) return;
    const headings=document.querySelectorAll('h3[data-driver-idx]');

    headings.forEach(h3=>{{
      const trendKey=h3.getAttribute('data-trend-key');
      const btn=h3.querySelector('.view-trend-btn');
      const tid=btn?btn.getAttribute('data-trend-id'):null;

      /* No trend data for this heading — leave as-is */
      if(!trendKey||!trends[trendKey]) return;

      const td=trends[trendKey];
      const p=td.persistence||'new';
      const cd=td.consistent_days||0;
      const tot=td.total_days||10;
      const recovery=td.recovery||false;

      if(tid){{
        const container=document.getElementById(tid);
        if(container) container._matchedData=td;
      }}

      /* Remove old AI-written badge and replace with computed one */
      const oldBadge=h3.querySelector('.badge-recurring,.badge-emerging,.badge-new');
      if(oldBadge) oldBadge.remove();

      if(p==='recurring'||p==='emerging'){{
        const badge=document.createElement('span');
        badge.className=p==='recurring'?'badge-recurring':'badge-emerging';
        badge.textContent=p==='recurring'?'Recurring':'Emerging';
        if(btn) h3.insertBefore(badge,btn);
        else h3.appendChild(badge);

        if(btn){{
          btn.style.display='';
          btn.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>Trend ('+cd+'/'+tot+'d)';
        }}

        if(recovery){{
          const recBadge=document.createElement('span');
          recBadge.className='badge-recovery';
          recBadge.textContent='Recovery';
          if(btn) h3.insertBefore(recBadge,btn);
          else h3.appendChild(recBadge);
        }}
      }} else {{
        const badge=document.createElement('span');
        badge.className='badge-new';
        badge.textContent='New';
        if(btn) h3.insertBefore(badge,btn);
        else h3.appendChild(badge);
      }}
    }});
  }})();
}})();

/* (Sticky section label removed — replaced by banner) */

/* Refresh button — cascading collapse animation */
function triggerRefresh(){{
  const sections=document.querySelectorAll('.section-gap, .grid4, .grid3');
  sections.forEach((el,i)=>{{
    setTimeout(()=>{{
      el.classList.add('collapsing');
    }}, i * 80);
  }});
  setTimeout(()=>{{
    window.location.reload();
  }}, Math.max(sections.length * 80 + 500, 600));
}}

/* ── Archive viewer ── */
let archiveOpen = false;
function toggleArchive(){{
  const overlay = document.getElementById('archiveOverlay');
  archiveOpen = !archiveOpen;
  if(archiveOpen){{
    overlay.classList.add('open');
    loadArchive();
  }} else {{
    overlay.classList.remove('open');
  }}
}}
function loadArchive(){{
  const list = document.getElementById('archiveList');
  list.innerHTML = '<div class="archive-empty">Loading...</div>';
  fetch('archive.json')
    .then(r => r.ok ? r.json() : [])
    .then(entries => {{
      if(!entries.length){{
        list.innerHTML = '<div class="archive-empty">No archived briefings yet.</div>';
        return;
      }}
      list.innerHTML = entries.map(e => {{
        const d = new Date(e.date + 'T00:00:00');
        const dayName = d.toLocaleDateString('en-GB', {{weekday:'short'}});
        const dateStr = d.toLocaleDateString('en-GB', {{day:'numeric',month:'short',year:'numeric'}});
        return `<div class="archive-item" onclick="window.location.href='${{e.file}}'">
          <span class="archive-date">${{dayName}} ${{dateStr}}</span>
          <span class="archive-headline">${{e.headline || '—'}}</span>
          <span class="archive-size">${{e.size_kb}}kb</span>
        </div>`;
      }}).join('');
    }})
    .catch(() => {{
      list.innerHTML = '<div class="archive-empty">Could not load archive. Run the briefing to generate archive.json.</div>';
    }});
}}
// Close archive on escape or clicking outside
document.addEventListener('keydown', e => {{
  if(e.key === 'Escape' && archiveOpen) toggleArchive();
}});
</script>

<!-- Archive overlay -->
<div id="archiveOverlay" class="archive-overlay" onclick="if(event.target===this)toggleArchive()">
  <div class="archive-panel">
    <div class="archive-header">
      <h2>Briefing Archive</h2>
      <button class="archive-close" onclick="toggleArchive()">&times;</button>
    </div>
    <div id="archiveList" class="archive-list"></div>
  </div>
</div>

<!-- Chat Panel — Ask Trading Covered -->
<div id="chatPanel" class="chat-panel" style="display:none">
  <div class="chat-header">
    <span class="chat-title">Ask Trading Covered</span>
    <button class="chat-close" onclick="toggleChat()">&times;</button>
  </div>
  <div class="chat-messages" id="chatMessages"></div>
  <div class="chat-input-wrap">
    <input type="text" id="chatInput" class="chat-input" placeholder="Ask anything about today's trading data..."
           onkeydown="if(event.key==='Enter')submitChat()">
    <button class="chat-send" onclick="submitChat()">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:16px;height:16px"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
    </button>
  </div>
</div>

</body></html>"""


# ---------------------------------------------------------------------------
def _generate_archive_index(briefings_dir: str):
    """Generate archive.json listing all dated briefings for the archive viewer."""
    from pathlib import Path as _P
    import re as _re
    entries = []
    for f in sorted(_P(briefings_dir).glob("????-??-??.html"), reverse=True):
        date_str = f.stem
        size_kb = round(f.stat().st_size / 1024, 1)
        # Try to extract headline from the HTML
        content = f.read_text()[:5000]
        headline_match = _re.search(r'<h2[^>]*>(.*?)</h2>', content)
        headline = headline_match.group(1).strip() if headline_match else ""
        # Clean HTML tags from headline
        headline = _re.sub(r'<[^>]+>', '', headline)
        entries.append({
            "date": date_str,
            "file": f.name,
            "size_kb": size_kb,
            "headline": headline[:120],
        })
    _P(briefings_dir).joinpath("archive.json").write_text(
        json.dumps(entries, indent=2)
    )
    print(f"  📚 Archive index: {len(entries)} briefings")


# MAIN
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="HX Insurance Trading — Agentic Morning Briefing")
    parser.add_argument("--date", type=str, default=None,
                        help="Run for a specific date (YYYY-MM-DD). Defaults to yesterday.")
    parser.add_argument("--from", dest="from_date", type=str, default=None,
                        help="Start of date range (YYYY-MM-DD). Use with --to.")
    parser.add_argument("--to", dest="to_date", type=str, default=None,
                        help="End of date range (YYYY-MM-DD). Use with --from.")
    args = parser.parse_args()

    # Determine run_date (the "yesterday" equivalent — the most recent trading day to analyse)
    if args.date:
        run_date = date.fromisoformat(args.date)
    elif args.from_date and args.to_date:
        # When a range is given, run_date is the end of the range (most recent day)
        run_date = date.fromisoformat(args.to_date)
    else:
        run_date = date.today() - timedelta(days=1)

    # Build date params for SQL
    dp = get_date_params(run_date)

    # If --from/--to provided, override week_start and month_start to match the range
    if args.from_date and args.to_date:
        from_dt = date.fromisoformat(args.from_date)
        dp["week_start"] = str(from_dt)
        dp["month_start"] = str(from_dt)
        dp["week_start_ly"] = str(from_dt - timedelta(days=364))
        dp["month_start_ly"] = str(from_dt - timedelta(days=364))

    print("=" * 60)
    print("  HX INSURANCE TRADING — AGENTIC BRIEFING")
    print(f"  Analysing: {run_date.strftime('%A %d %B %Y')}")
    if args.from_date and args.to_date:
        print(f"  Date range: {args.from_date} to {args.to_date}")
    print("=" * 60)

    if not OPENAI_API_KEY:
        print("\n⚠️  Set OPENAI_API_KEY in .env file")
        return

    print("\n🔐 Authenticating...")
    init_services()

    # Phase 1: Baseline
    baseline = run_baseline_queries(dp)

    for row in baseline["trading"]:
        if row.get("period") == "yesterday_ly":
            print(f"  LY equiv GP:  £{row['total_gp']:,.2f} | Policies: {row['new_policies']}")
        elif row.get("period") == "yesterday":
            print(f"\n  Yesterday GP: £{row['total_gp']:,.2f} | Policies: {row['new_policies']}")

    # Phase 2: Deterministic investigation tracks
    track_results = run_investigation_tracks(dp)

    # Phase 3: AI analysis of track results
    analysis = run_ai_analysis(baseline, track_results, run_date)

    # Phase 4: AI-driven follow-up investigations
    follow_up_results, follow_up_log = run_ai_follow_ups(analysis, baseline, run_date)

    # Phase 5: Two-pass synthesis
    briefing = run_synthesis(baseline, analysis, follow_up_results, track_results, run_date)

    # Phase 5b: Collect per-driver trend data for inline charts
    print("\n📈 Phase 5b: Collecting driver trend data...")
    driver_trends = collect_driver_trends(analysis, run_date)

    # Bundle investigation data for the trail
    inv_log = {
        "track_results": track_results,
        "analysis": analysis,
        "follow_up_results": follow_up_results,
        "follow_up_log": follow_up_log,
    }
    total_queries = len(track_results) + len(follow_up_log)
    print(f"\n  📋 Investigation: {len(track_results)} tracks + {len(follow_up_log)} follow-ups = {total_queries} total queries")

    # Save everything — use today's date (report date), not run_date (yesterday's trading day)
    report_date = run_date + timedelta(days=1)
    today_str = report_date.strftime("%Y-%m-%d")
    briefings_dir = str(Path(__file__).resolve().parent / "briefings")
    os.makedirs(briefings_dir, exist_ok=True)

    # Markdown
    md_path = f"{briefings_dir}/{today_str}.md"
    Path(md_path).write_text(briefing + f"\n\n---\n*Generated {datetime.datetime.now().strftime('%H:%M %d %b %Y')} | Tracks: {len(track_results)} + Follow-ups: {len(follow_up_log)} | Model: {MODEL}*\n")
    Path(f"{briefings_dir}/latest.md").write_text(Path(md_path).read_text())

    # HTML Dashboard
    html = generate_dashboard_html(briefing, baseline["trading"], baseline["trend"], today_str, investigation_log=inv_log, run_date=run_date, trend_data_ly=baseline.get("trend_ly", []), driver_trends=driver_trends)
    Path(f"{briefings_dir}/{today_str}.html").write_text(html)
    Path(f"{briefings_dir}/latest.html").write_text(html)

    # Investigation log
    Path(f"{briefings_dir}/{today_str}_investigation.json").write_text(
        json.dumps({
            "analysis": analysis,
            "follow_up_results": follow_up_results,
            "follow_up_log": follow_up_log,
            "track_summary": {tid: {"name": tr["name"], "rows": tr["row_count"]} for tid, tr in track_results.items()},
        }, indent=2, default=str)
    )

    print(f"\n✅ Briefing saved:")
    print(f"   📄 {md_path}")
    print(f"   🌐 {briefings_dir}/{today_str}.html")
    print(f"   🔍 {briefings_dir}/{today_str}_investigation.json")

    # Generate archive index for the archive viewer
    _generate_archive_index(briefings_dir)

    # Open in Arc (skip in CI)
    if not os.environ.get("CI"):
        os.system(f'open -a "{BROWSER}" "{briefings_dir}/latest.html"')

    print("\n" + "=" * 60)
    print(briefing)
    print("=" * 60)


if __name__ == "__main__":
    main()
