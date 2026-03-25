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
import statistics
import time
import traceback

import openai
import anthropic
import markdown
import google.auth
import google.auth.transport.requests
from google.cloud import bigquery
from googleapiclient.discovery import build

# ---------------------------------------------------------------------------
# CONFIG [DOMAIN-AGNOSTIC — except BQ_PROJECT and MARKET_SHEET_ID]
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

# Load trading context (business knowledge for AI prompts)
# Reads from context/ folder if present, falls back to trading_context.md
def _load_trading_context():
    ctx_dir = Path(__file__).parent / "context"
    if ctx_dir.is_dir():
        # Load all markdown files from context/ in order: universal → domain → operational
        parts = []
        for subdir in ["universal", "insurance", "operational"]:
            sub_path = ctx_dir / subdir
            if sub_path.is_dir():
                for f in sorted(sub_path.glob("*.md")):
                    parts.append(f.read_text())
        if parts:
            return "\n\n---\n\n".join(parts)
    # Fallback to single file
    ctx_path = Path(__file__).parent / "trading_context.md"
    if ctx_path.exists():
        return ctx_path.read_text()
    return ""

TRADING_CONTEXT = _load_trading_context()

# ---------------------------------------------------------------------------
# DOMAIN CONFIG — load from domains/{domain}/config.yaml or use defaults
# ---------------------------------------------------------------------------
def _load_domain_config(domain="insurance"):
    """Load domain config. Falls back to hardcoded defaults if config file or yaml missing."""
    config_path = Path(__file__).parent / "domains" / domain / "config.yaml"
    if config_path.exists():
        try:
            import yaml
            return yaml.safe_load(config_path.read_text())
        except ImportError:
            print("⚠ pyyaml not installed — using default config. pip install pyyaml to enable domain config.")
    return {}

_DOMAIN_CONFIG = _load_domain_config()

BQ_PROJECT = _DOMAIN_CONFIG.get("bq_project", "hx-data-production")
MARKET_SHEET_ID = _DOMAIN_CONFIG.get("market_sheet_id", "1RUasLdbB9OiHPJzQClglC7aY5KMH4P-dnzk4v_h-tsg")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
# Model configuration — roles map to specific models.
# Change model assignments here or in domains/{domain}/config.yaml.
_model_defaults = {
    "analyst": "gpt-5.4",
    "verifier": "claude-sonnet-4-20250514",
    "lightweight": "gpt-5-mini",
}
MODELS = {**_model_defaults, **_DOMAIN_CONFIG.get("models", {})}
MODEL = MODELS["analyst"]
VERIFY_MODEL = MODELS["verifier"]
LIGHTWEIGHT_MODEL = MODELS["lightweight"]
BROWSER = "Arc"
MAX_INVESTIGATION_LOOPS = _DOMAIN_CONFIG.get("max_investigation_loops", 10)

# ---------------------------------------------------------------------------
# UK HOLIDAYS [DOMAIN-AGNOSTIC — UK-wide, applies to all HX products]
# ---------------------------------------------------------------------------

# Fallback bank holidays if gov.uk API unavailable
_FALLBACK_BANK_HOLIDAYS = {
    "2024-01-01", "2024-03-29", "2024-04-01", "2024-05-06", "2024-05-27",
    "2024-08-26", "2024-12-25", "2024-12-26",
    "2025-01-01", "2025-04-18", "2025-04-21", "2025-05-05", "2025-05-26",
    "2025-08-25", "2025-12-25", "2025-12-26",
    "2026-01-01", "2026-04-03", "2026-04-06", "2026-05-04", "2026-05-25",
    "2026-08-31", "2026-12-25", "2026-12-28",
    "2027-01-01", "2027-03-26", "2027-03-29", "2027-05-03", "2027-05-31",
    "2027-08-30", "2027-12-27", "2027-12-28",
}

def _fetch_uk_bank_holidays():
    """Fetch UK bank holidays from gov.uk API. Returns set of YYYY-MM-DD strings."""
    import urllib.request
    try:
        req = urllib.request.Request(
            "https://www.gov.uk/bank-holidays.json",
            headers={"User-Agent": "TradingCovered/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        dates = set()
        for division in data.values():
            for event in division.get("events", []):
                dates.add(event["date"])
        print(f"  ✓ Fetched {len(dates)} bank holidays from gov.uk")
        return dates
    except Exception as e:
        print(f"  ⚠ Could not fetch bank holidays from gov.uk ({e}), using fallback")
        return _FALLBACK_BANK_HOLIDAYS

# Initialised at pipeline start (lazy — populated on first use)
UK_BANK_HOLIDAYS = None

def _get_bank_holidays():
    global UK_BANK_HOLIDAYS
    if UK_BANK_HOLIDAYS is None:
        UK_BANK_HOLIDAYS = _fetch_uk_bank_holidays()
    return UK_BANK_HOLIDAYS


def _easter_date(year):
    """Compute Easter Sunday for a given year using the Anonymous Gregorian algorithm."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _generate_school_holidays(year):
    """Generate approximate English school holiday periods for the academic year
    starting in September of `year`. Returns list of (start, end) date string tuples.

    Based on typical English state school term patterns:
    - October half term: last full week of October
    - Christmas: ~2 weeks from ~22 Dec
    - February half term: 3rd full week of February
    - Easter: 2 weeks around Easter (starts ~Fri before Good Friday week)
    - May half term: week containing late May bank holiday
    - Summer: ~late July to late August
    """
    holidays = []
    from datetime import date as _d

    # October half term (last full Mon-Fri of October)
    oct_31 = _d(year, 10, 31)
    # Find last Monday on or before Oct 31
    last_mon = oct_31 - timedelta(days=(oct_31.weekday()))
    if last_mon.month == 11:
        last_mon -= timedelta(days=7)
    holidays.append((last_mon.isoformat(), (last_mon + timedelta(days=4)).isoformat()))

    # Christmas (~22 Dec to ~2 Jan)
    holidays.append((_d(year, 12, 22).isoformat(), _d(year + 1, 1, 2).isoformat()))

    # February half term (3rd full week of Feb, year+1)
    feb_1 = _d(year + 1, 2, 1)
    first_mon = feb_1 + timedelta(days=(7 - feb_1.weekday()) % 7)
    third_mon = first_mon + timedelta(weeks=2)
    holidays.append((third_mon.isoformat(), (third_mon + timedelta(days=4)).isoformat()))

    # Easter (2 weeks: week before and week of Easter Monday, year+1)
    easter = _easter_date(year + 1)
    good_friday = easter - timedelta(days=2)
    easter_start = good_friday - timedelta(days=6)  # Saturday before Good Friday week
    easter_end = easter + timedelta(days=8)  # Friday after Easter Monday week
    holidays.append((easter_start.isoformat(), easter_end.isoformat()))

    # May half term (week containing the Spring bank holiday, year+1)
    # Spring bank holiday is last Monday of May
    may_31 = _d(year + 1, 5, 31)
    spring_bh = may_31 - timedelta(days=(may_31.weekday()))
    if spring_bh.month == 6:
        spring_bh -= timedelta(days=7)
    ht_mon = spring_bh
    holidays.append((ht_mon.isoformat(), (ht_mon + timedelta(days=4)).isoformat()))

    # Summer (~3rd week of July to last week of August, year+1)
    jul_21 = _d(year + 1, 7, 21)
    summer_start = jul_21 - timedelta(days=jul_21.weekday())  # Monday on or before 21 Jul
    aug_31 = _d(year + 1, 8, 31)
    summer_end = aug_31 - timedelta(days=(aug_31.weekday() + 3) % 7)  # ~last Friday of Aug
    holidays.append((summer_start.isoformat(), summer_end.isoformat()))

    return holidays


def _build_school_holidays():
    """Generate school holiday periods covering the current and surrounding academic years."""
    current_year = date.today().year
    all_holidays = []
    for y in range(current_year - 2, current_year + 2):
        all_holidays.extend(_generate_school_holidays(y))
    return all_holidays

UK_SCHOOL_HOLIDAYS = _build_school_holidays()


def _date_in_school_holiday(d_str):
    """Check if a date string (YYYY-MM-DD) falls within a UK school holiday period."""
    for start, end in UK_SCHOOL_HOLIDAYS:
        if start <= d_str <= end:
            return True
    return False

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
# TOOL IMPLEMENTATIONS [DOMAIN-AGNOSTIC — SQL runner, market data, web search, drive scanner]
# ---------------------------------------------------------------------------

def _autocorrect_sql(sql: str) -> tuple[str, list[str]]:
    """Fix common SQL mistakes instead of rejecting. Returns (corrected_sql, warnings)."""
    import re, calendar
    warnings = []
    corrected = sql
    upper = corrected.upper()

    if "INSURANCE_TRADING_DATA" in upper or "INSURANCE_POLICIES_NEW" in upper:
        # Redirect old table name to new table
        if "INSURANCE_POLICIES_NEW" in upper:
            corrected = re.sub(r'`[^`]*insurance_policies_new[^`]*`', '`hx-data-production.insurance.insurance_trading_data`', corrected, flags=re.IGNORECASE)
            corrected = re.sub(r'\binsurance_policies_new\b', 'insurance_trading_data', corrected, flags=re.IGNORECASE)
            corrected = re.sub(r'commercial_finance\.insurance_trading_data', 'insurance.insurance_trading_data', corrected, flags=re.IGNORECASE)
            warnings.append("Auto-corrected old table insurance_policies_new → insurance_trading_data")
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
        # Fix EXTRACT(DATE FROM transaction_date) or bare transaction_date → DATE(looker_trans_date)
        if re.search(r'EXTRACT\s*\(\s*DATE\s+FROM\s+transaction_date\s*\)', corrected, re.IGNORECASE):
            corrected = re.sub(r'EXTRACT\s*\(\s*DATE\s+FROM\s+transaction_date\s*\)', 'DATE(looker_trans_date)', corrected, flags=re.IGNORECASE)
            warnings.append("Auto-corrected EXTRACT(DATE FROM transaction_date) → DATE(looker_trans_date)")

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
    import re
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
            model=LIGHTWEIGHT_MODEL,
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
                model=LIGHTWEIGHT_MODEL,
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
    """Scan Google Drive for recently modified docs matching keywords (owned OR shared)."""
    try:
        print(f"    📂 Scanning Drive for: {keywords}")
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=days_back)).isoformat() + "Z"
        # Include files owned by me AND shared with me
        query = f"modifiedTime > '{cutoff}' and trashed = false"
        resp = DRIVE_SVC.files().list(
            q=query,
            fields="files(id, name, mimeType, modifiedTime, lastModifyingUser)",
            orderBy="modifiedTime desc",
            pageSize=100,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
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
                    "id": f["id"],
                    "name": f["name"],
                    "mimeType": f.get("mimeType", ""),
                    "modified": f["modifiedTime"],
                    "modified_by": f.get("lastModifyingUser", {}).get("displayName", "Unknown"),
                })
        return json.dumps(relevant[:30], indent=2)
    except Exception as e:
        return f"Drive error: {e}"


def tool_read_drive_doc(file_id: str, max_chars: int = 100000) -> str:
    """Read the text content of a Google Drive document (Doc, Sheet, or text file)."""
    import io
    from googleapiclient.http import MediaIoBaseDownload

    try:
        # Get file metadata to determine type
        meta = DRIVE_SVC.files().get(fileId=file_id, fields="mimeType,name").execute()
        mime = meta.get("mimeType", "")
        name = meta.get("name", "unknown")

        text = ""

        if "spreadsheet" in mime:
            # Google Sheet — use Sheets API
            try:
                result = SHEETS_SVC.spreadsheets().values().get(
                    spreadsheetId=file_id, range="A1:Z30"
                ).execute()
                rows = result.get("values", [])
                text = "\n".join(["\t".join(row) for row in rows[:30]])
            except Exception as sheet_err:
                return f"Could not read sheet '{name}': {sheet_err}"

        elif "document" in mime or "presentation" in mime:
            # Google Doc/Slides — export as plain text using media download
            try:
                request = DRIVE_SVC.files().export_media(fileId=file_id, mimeType="text/plain")
                buf = io.BytesIO()
                downloader = MediaIoBaseDownload(buf, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                text = buf.getvalue().decode("utf-8")
            except Exception:
                # Fallback: try simple export (works for smaller files)
                try:
                    content = DRIVE_SVC.files().export(fileId=file_id, mimeType="text/plain").execute()
                    if isinstance(content, bytes):
                        text = content.decode("utf-8")
                    else:
                        text = str(content)
                except Exception as e2:
                    return f"Could not read '{name}': {e2}"

        elif "pdf" in mime:
            return f"Could not read doc: PDF not supported ({name})"

        else:
            # Other file types — download raw bytes
            try:
                request = DRIVE_SVC.files().get_media(fileId=file_id)
                buf = io.BytesIO()
                downloader = MediaIoBaseDownload(buf, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                text = buf.getvalue().decode("utf-8", errors="replace")
            except Exception as dl_err:
                return f"Could not read '{name}': {dl_err}"

        return text[:max_chars] if text.strip() else f"Could not read doc: empty content ({name})"
    except Exception as e:
        return f"Could not read doc: {e}"


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
            "description": "Execute a SQL query against Google BigQuery. CRITICAL RULES for insurance_trading_data: (1) NEVER use COUNT(*) or COUNT(DISTINCT policy_id) — always SUM(policy_count), (2) NEVER use AVG() on financial columns — always SUM(col)/NULLIF(SUM(policy_count),0), (3) use DATE(looker_trans_date) for date filtering and grouping — never bare transaction_date. For web table: use COUNT(DISTINCT visitor_id) for users, COUNT(DISTINCT session_id) for sessions. Always use project-qualified table names.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "The BigQuery SQL query to execute. Must use fully qualified table names like `hx-data-production.insurance.insurance_trading_data`."
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

# Follow-up tools — only SQL and web search.  Drive context and market
# intelligence are already loaded in the prompt so re-fetching wastes time.
FOLLOW_UP_TOOLS = [t for t in TOOLS if t["function"]["name"] in ("run_sql", "web_search")]


# ---------------------------------------------------------------------------
# DOMAIN-SPECIFIC PROMPTS — loaded from domains/insurance/prompts.py
# ---------------------------------------------------------------------------

from domains.insurance.prompts import build_prompts as _build_prompts
_PROMPTS = _build_prompts(TRADING_CONTEXT)
SCHEMA_KNOWLEDGE = _PROMPTS["schema"]



# ---------------------------------------------------------------------------
# BASELINE DATA QUERIES — loaded from domains/insurance/baselines.py
# ---------------------------------------------------------------------------

from domains.insurance.baselines import init_tables, get_date_params
from domains.insurance.baselines import build_baseline_trading_sql, build_baseline_trend_sql
from domains.insurance.baselines import build_baseline_trend_ly_sql, build_baseline_funnel_sql
from domains.insurance.baselines import build_baseline_web_engagement_sql
POLICIES_TABLE, WEB_TABLE = init_tables(BQ_PROJECT)



# ---------------------------------------------------------------------------
# INVESTIGATION TRACKS [INSURANCE-SPECIFIC — replace entirely for new domains]
# ---------------------------------------------------------------------------

def build_investigation_tracks(dp):
    """Build all investigation track SQL queries — delegates to domains/insurance/tracks.py."""
    from domains.insurance.tracks import build_investigation_tracks as _build_tracks
    return _build_tracks(dp, POLICIES_TABLE, WEB_TABLE)



# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# DOMAIN-SPECIFIC ANALYSIS PROMPTS — loaded from domains/insurance/prompts.py
# ---------------------------------------------------------------------------

ANALYSIS_SYSTEM = _PROMPTS["analysis"]
FOLLOW_UP_SYSTEM = _PROMPTS["follow_up"]
SYNTHESIS_SYSTEM = _PROMPTS["synthesis"]



# ---------------------------------------------------------------------------
# GOOGLE TRENDS — direct fetch for Customer Search Intent
# ---------------------------------------------------------------------------

INSURANCE_INTENT_TERMS = [
    "travel insurance",
    "holiday insurance",
    "annual travel insurance",
    "single trip travel insurance",
    "travel insurance comparison",
]
HOLIDAY_INTENT_TERMS = [
    "book holiday",
    "cheap flights",
    "package holiday",
    "all inclusive holiday",
    "summer holiday",
    "winter sun",
]

_TRENDS_CACHE_DIR = Path(__file__).parent / ".trends_cache"


def _google_trends_deep_link(term, start_date, end_date, geo="GB"):
    """Generate a Google Trends explore URL for a search term."""
    from urllib.parse import quote
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    return f"https://trends.google.com/explore?q={quote(term)}&date={start_str}%20{end_str}&geo={geo}"


def _google_trends_compare_link(terms, start_date, end_date, geo="GB"):
    """Generate a Google Trends compare URL for multiple terms."""
    from urllib.parse import quote
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    q = ",".join(quote(t) for t in terms[:5])  # GT max 5 terms
    return f"https://trends.google.com/explore?q={q}&date={start_str}%20{end_str}&geo={geo}"


def _fetch_trends_batch(pytrends, terms, timeframe, max_retries=3):
    """Fetch a single batch of up to 5 terms from Google Trends with retry on 429."""
    backoff = 30
    for attempt in range(max_retries):
        try:
            pytrends.build_payload(terms, cat=0, timeframe=timeframe, geo="GB")
            df = pytrends.interest_over_time()
            if df.empty:
                return {}, []
            if "isPartial" in df.columns:
                df = df.drop(columns=["isPartial"])
            dates = [d.isoformat() for d in df.index]
            data = {}
            for col in df.columns:
                data[col] = df[col].tolist()
            return data, dates
        except Exception as e:
            err = str(e)
            if "429" in err and attempt < max_retries - 1:
                print(f"    ⚠ Rate limited (attempt {attempt + 1}/{max_retries}), waiting {backoff}s...")
                time.sleep(backoff)
                backoff *= 2
                continue
            print(f"    ⚠ Google Trends batch failed: {e}")
            return {}, []
    return {}, []


def _compute_yoy(values, n):
    """Compute YoY change from a weekly time series: recent 4 weeks vs same 4 weeks a year ago."""
    recent_4w = max(0, n - 4)
    ly_4w_start = max(0, n - 56)
    ly_4w_end = max(0, n - 52)
    recent_avg = sum(values[recent_4w:]) / max(1, n - recent_4w) if recent_4w < n else 0
    ly_avg = sum(values[ly_4w_start:ly_4w_end]) / max(1, ly_4w_end - ly_4w_start) if ly_4w_end > ly_4w_start else 0
    yoy = ((recent_avg - ly_avg) / ly_avg * 100) if ly_avg > 0 else 0
    return round(recent_avg, 1), round(ly_avg, 1), round(yoy, 1)


def _ai_suggest_deep_dive_terms(base_terms_summary):
    """Ask AI to suggest follow-up Google Trends terms based on the biggest movers."""
    if not OPENAI_API_KEY:
        return []

    # Pick top 3 insurance + top 3 holiday by absolute YoY variance
    insurance = [(t, d) for t, d in base_terms_summary.items() if d["category"] == "insurance"]
    holiday = [(t, d) for t, d in base_terms_summary.items() if d["category"] == "holiday"]
    top_insurance = sorted(insurance, key=lambda x: abs(x[1]["yoy_change_pct"]), reverse=True)[:3]
    top_holiday = sorted(holiday, key=lambda x: abs(x[1]["yoy_change_pct"]), reverse=True)[:3]

    movers_text = "TOP INSURANCE MOVERS:\n"
    for term, d in top_insurance:
        movers_text += f"- \"{term}\": {d['yoy_change_pct']:+.1f}% YoY (recent avg {d['recent_avg']}, LY avg {d['ly_avg']})\n"
    movers_text += "\nTOP HOLIDAY MOVERS:\n"
    for term, d in top_holiday:
        movers_text += f"- \"{term}\": {d['yoy_change_pct']:+.1f}% YoY (recent avg {d['recent_avg']}, LY avg {d['ly_avg']})\n"

    prompt = f"""You are analysing UK Google Trends search data for an insurance trading team.

{movers_text}

For EACH of the 6 terms above, suggest 5 related Google Trends search terms that might EXPLAIN
why that term is moving up or down. Think about:
- Competitor brands (e.g. "Staysure travel insurance", "Post Office travel insurance")
- Specific products or covers (e.g. "cruise travel insurance", "medical travel insurance")
- External factors (e.g. "FCDO travel advice", "flight cancellation", "travel warning")
- Seasonal/destination terms (e.g. "Spain holiday", "Turkey holiday")
- Price/channel terms (e.g. "cheap travel insurance", "MoneySupermarket travel insurance")

Return JSON: {{"deep_dive_terms": ["term1", "term2", ...]}}

Rules:
- Return exactly 30 terms (5 per mover)
- Each term should be a realistic Google Trends search query (1-4 words, UK English)
- Don't repeat any of the 11 base terms
- Focus on terms that would EXPLAIN the movements, not just related terms"""

    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            max_completion_tokens=2000,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You suggest Google Trends search terms. Return JSON only."},
                {"role": "user", "content": prompt},
            ],
        )
        result = _parse_llm_json(resp.choices[0].message.content)
        terms = result.get("deep_dive_terms", []) if isinstance(result, dict) else []
        # Dedupe against base terms
        base_set = {t.lower() for t in INSURANCE_INTENT_TERMS + HOLIDAY_INTENT_TERMS}
        terms = [t for t in terms if isinstance(t, str) and t.lower() not in base_set]
        return terms[:30]
    except Exception as e:
        print(f"    ⚠ AI term suggestion failed: {e}")
        return []


def fetch_google_trends(run_date):
    """Fetch Google Trends data for insurance + holiday terms, then AI-suggested deep-dive terms.

    Flow:
    1. Fetch 11 base terms (5 insurance + 6 holiday), compute YoY
    2. AI picks top 3 insurance + top 3 holiday by variance, suggests 60 follow-up terms
    3. Fetch follow-up terms from Google Trends, compute YoY
    4. Return everything with deep links

    Returns dict with base terms, deep-dive terms, and compare links.
    Falls back gracefully if pytrends or AI fails.
    """
    try:
        from pytrends.request import TrendReq
    except ImportError:
        print("  ⚠ pytrends not installed — skipping Google Trends")
        return None

    end_date = run_date
    start_date = date(end_date.year - 2, end_date.month, end_date.day)
    timeframe = f"{start_date.isoformat()} {end_date.isoformat()}"

    # Check cache (24h TTL)
    _TRENDS_CACHE_DIR.mkdir(exist_ok=True)
    cache_file = _TRENDS_CACHE_DIR / f"trends_{run_date.isoformat()}.json"
    if cache_file.exists():
        try:
            cached = json.loads(cache_file.read_text())
            print(f"  📊 Google Trends: loaded from cache ({len(cached.get('terms', {}))} base + {len(cached.get('deep_dive_terms', {}))} deep-dive terms)")
            return cached
        except Exception:
            pass

    print("  📊 Google Trends: fetching live data (2-year window)...")
    pytrends = TrendReq(hl="en-GB", tz=0)

    # --- STAGE 1: Base terms ---
    all_base = INSURANCE_INTENT_TERMS + HOLIDAY_INTENT_TERMS
    anchor = "travel insurance"
    other = [t for t in all_base if t != anchor]
    batches = [[anchor] + other[i:i + 4] for i in range(0, len(other), 4)]

    all_data = {}
    all_dates = []
    for batch in batches:
        data, dates = _fetch_trends_batch(pytrends, batch, timeframe)
        if data:
            all_data.update(data)
            if not all_dates and dates:
                all_dates = dates
            print(f"    ✓ Base: {', '.join(batch)}")
        time.sleep(30)

    if not all_data or not all_dates:
        print("  ⚠ Google Trends: no data retrieved")
        return None

    n = len(all_dates)
    terms_summary = {}
    for term, values in all_data.items():
        if len(values) != n:
            continue
        recent_avg, ly_avg, yoy = _compute_yoy(values, n)
        category = "insurance" if term in INSURANCE_INTENT_TERMS else "holiday"
        terms_summary[term] = {
            "category": category,
            "recent_avg": recent_avg,
            "ly_avg": ly_avg,
            "yoy_change_pct": yoy,
            "direction": "up" if yoy > 2 else ("down" if yoy < -2 else "flat"),
            "deep_link": _google_trends_deep_link(term, start_date, end_date),
        }

    print(f"  📊 Base terms: {len(terms_summary)} analysed")

    # --- STAGE 2: AI suggests deep-dive terms ---
    print("  🤖 Asking AI to suggest deep-dive search terms...")
    suggested_terms = _ai_suggest_deep_dive_terms(terms_summary)
    print(f"  🤖 AI suggested {len(suggested_terms)} deep-dive terms")

    # --- STAGE 3: Fetch deep-dive terms ---
    deep_dive_summary = {}
    if suggested_terms:
        print(f"  📊 Fetching {len(suggested_terms)} deep-dive terms from Google Trends...")
        # Batch in groups of 5 (no anchor needed — each batch is independent)
        dd_batches = [suggested_terms[i:i + 5] for i in range(0, len(suggested_terms), 5)]
        fetched = 0
        for batch in dd_batches:
            data, dates = _fetch_trends_batch(pytrends, batch, timeframe)
            if data and dates:
                batch_n = len(dates)
                for term, values in data.items():
                    if len(values) != batch_n:
                        continue
                    recent_avg, ly_avg, yoy = _compute_yoy(values, batch_n)
                    deep_dive_summary[term] = {
                        "category": "deep_dive",
                        "recent_avg": recent_avg,
                        "ly_avg": ly_avg,
                        "yoy_change_pct": yoy,
                        "direction": "up" if yoy > 2 else ("down" if yoy < -2 else "flat"),
                        "deep_link": _google_trends_deep_link(term, start_date, end_date),
                    }
                    fetched += 1
                print(f"    ✓ Deep-dive: {', '.join(batch[:3])}{'...' if len(batch) > 3 else ''}")
            time.sleep(30)
        print(f"  📊 Deep-dive: {fetched} terms analysed")

    # Build compare links
    insurance_compare = _google_trends_compare_link(INSURANCE_INTENT_TERMS, start_date, end_date)
    holiday_compare = _google_trends_compare_link(HOLIDAY_INTENT_TERMS, start_date, end_date)

    # --- STAGE 4: AI narrative — synthesise all trends into a daily context summary ---
    narrative = ""
    if OPENAI_API_KEY and (terms_summary or deep_dive_summary):
        print("  🤖 Generating Google Trends narrative...")
        try:
            # Build a concise data summary — only include terms with meaningful movement
            base_lines = []
            for term, d in sorted(terms_summary.items(), key=lambda x: abs(x[1]["yoy_change_pct"]), reverse=True):
                base_lines.append(f"- {term} ({d['category']}): {d['yoy_change_pct']:+.1f}% YoY")
            # Only include deep-dive terms with >10% absolute YoY change
            dd_meaningful = [(t, d) for t, d in deep_dive_summary.items() if abs(d["yoy_change_pct"]) > 10]
            dd_lines = []
            for term, d in sorted(dd_meaningful, key=lambda x: abs(x[1]["yoy_change_pct"]), reverse=True)[:15]:
                dd_lines.append(f"- {term}: {d['yoy_change_pct']:+.1f}% YoY")

            narrative_prompt = f"""You are writing a daily Google Trends intelligence summary for an insurance trading team at Holiday Extras (HX).

BASE SEARCH TERMS (insurance vs holiday demand):
{chr(10).join(base_lines)}

DEEP-DIVE TERMS WITH MEANINGFUL MOVEMENT (>10% YoY change):
{chr(10).join(dd_lines) if dd_lines else '(none had >10% movement)'}

Date range: {start_date.isoformat()} to {end_date.isoformat()} (UK, Google Trends)

Write a 4-8 sentence narrative that:
1. Summarises the overall picture: is insurance search demand keeping pace with holiday demand?
2. Highlights the biggest movers and what the deep-dive terms suggest about WHY
3. Calls out any competitor or destination terms that are surging or declining
4. Notes any divergences between insurance and holiday intent
5. Ends with 1-2 implications for trading

Only mention deep-dive terms that have meaningful movement — don't pad with flat terms.
Be specific with numbers. Write in plain English for a trading team — no jargon.
This will appear on the daily trading briefing as the Customer Search Intent section."""

            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            resp = client.chat.completions.create(
                model="gpt-4.1-mini",
                max_completion_tokens=500,
                messages=[
                    {"role": "system", "content": "You write concise daily market intelligence summaries based on Google Trends data. Be specific, use numbers, write for traders."},
                    {"role": "user", "content": narrative_prompt},
                ],
            )
            narrative = resp.choices[0].message.content.strip()
            print(f"  ✓ Trends narrative: {len(narrative)} chars")
        except Exception as e:
            print(f"  ⚠ Trends narrative failed (non-fatal): {e}")

    result = {
        "terms": terms_summary,
        "deep_dive_terms": deep_dive_summary,
        "deep_dive_suggested_by": "gpt-4.1-mini",
        "narrative": narrative,
        "insurance_compare_link": insurance_compare,
        "holiday_compare_link": holiday_compare,
        "date_range": f"{start_date.isoformat()} to {end_date.isoformat()}",
        "fetched_at": datetime.datetime.now().isoformat(),
    }

    # Cache
    try:
        cache_file.write_text(json.dumps(result, indent=2))
    except Exception:
        pass

    total = len(terms_summary) + len(deep_dive_summary)
    print(f"  📊 Google Trends complete: {total} terms ({len(terms_summary)} base + {len(deep_dive_summary)} deep-dive)")
    return result


# ---------------------------------------------------------------------------
# PHASE 0: CONTEXT INTELLIGENCE — scan Drive, classify, surface in briefing
# ---------------------------------------------------------------------------

# Title whitelist — only scan Drive docs whose title contains one of these words.
# This prevents scanning sensitive files. Content is read, but only from known-safe doc types.
CONTEXT_TITLE_WHITELIST = ["trading", "pricing", "price", "circle", "marketing"]
TRAVEL_EVENTS_SHEET_ID = "1lqLYxLTnfFyBSsIPRyPr8vpr25S7Fhz3p-nlWNToZpU"


def _load_kv_json(filename):
    """Load a JSON file populated by the CI KV fetch step."""
    path = Path(__file__).parent / "context" / "operational" / filename
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        path.write_text("[]")  # consume
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _process_context_removals():
    """Process context removal requests from KV (via CI wrangler step)."""
    context_dir = Path(__file__).parent / "context"
    removals_raw = _load_kv_json("context-removals.json")
    removals = []
    for r in removals_raw:
        filed_info = r.get("filed_info", r)  # support both nested and flat format
        if filed_info.get("filed_to") and filed_info.get("filed_text"):
            removals.append(filed_info)

    removed = 0
    for removal in removals:
        filed_to = removal.get("filed_to", "")
        filed_text = removal.get("filed_text", "")
        if not filed_to or not filed_text:
            continue
        target = context_dir / filed_to
        if target.exists():
            content = target.read_text()
            if filed_text.strip() in content:
                content = content.replace(filed_text.strip(), "").replace("\n\n\n", "\n\n")
                target.write_text(content)
                removed += 1
                print(f"  🗑 Removed context from {filed_to}: {filed_text[:50]}")
    return removed


def _process_context_additions():
    """Load pending manual context additions from KV (via CI wrangler step)."""
    additions = _load_kv_json("context-additions.json")
    processed = []
    for addition in additions:
        raw_text = addition.get("raw_text", "")
        if not raw_text:
            continue
        processed.append({
            "source": f"Manual entry by {addition.get('added_by', 'user')}",
            "modified_by": addition.get("added_by", "user"),
            "modified": addition.get("timestamp", ""),
            "content_preview": raw_text,
        })
        print(f"  ➕ Manual context to process: {raw_text[:60]}")
    return processed


def run_context_refresh(run_date):
    """Phase 0: Scan Drive + Travel Events for new context. Cross-model classify."""
    print("\n📋 Phase 0: Context intelligence refresh...")

    # 0. Process any pending context removals
    removed = _process_context_removals()
    if removed:
        print(f"  🗑 Processed {removed} context removal(s)")

    items = []

    # 0b. Process any pending manual context additions
    manual_items = _process_context_additions()
    items.extend(manual_items)

    # 1. Scan Drive for recently modified docs (owned + shared)
    try:
        drive_results_json = tool_scan_drive(",".join(CONTEXT_TITLE_WHITELIST), days_back=7)
        drive_results = json.loads(drive_results_json) if not drive_results_json.startswith("Drive error") else []
        print(f"  📂 Found {len(drive_results)} relevant Drive docs modified in last 7 days")

        # Read content of top 10 docs
        for doc in drive_results:
            content = tool_read_drive_doc(doc["id"])
            if content and not content.startswith("Could not read"):
                print(f"    ✓ Read: {doc['name']} ({len(content)} chars)")
                items.append({
                    "source": f"Drive: '{doc['name']}'",
                    "modified_by": doc.get("modified_by", "Unknown"),
                    "modified": doc.get("modified", ""),
                    "content_preview": content[:1500],
                })
            else:
                # Fallback: use file name + metadata as context (name can be informative)
                print(f"    ⚠ Could not read content of: {doc['name']} — using metadata only")
                items.append({
                    "source": f"Drive: '{doc['name']}'",
                    "modified_by": doc.get("modified_by", "Unknown"),
                    "modified": doc.get("modified", ""),
                    "content_preview": f"Document: {doc['name']}. Modified by {doc.get('modified_by', 'Unknown')} on {doc.get('modified', 'Unknown')}. (Content not accessible — classify based on document title only.)",
                })
    except Exception as e:
        print(f"  ⚠ Drive scan failed (non-fatal): {e}")

    # 2. Check Travel Events Log sheet for new entries
    try:
        print(f"  📊 Checking Travel Events Log...")
        resp = SHEETS_SVC.spreadsheets().values().get(
            spreadsheetId=TRAVEL_EVENTS_SHEET_ID, range="A1:Z20"
        ).execute()
        rows = resp.get("values", [])
        if rows:
            # Look for rows with recent dates
            cutoff = (run_date - timedelta(days=7)).isoformat()
            for row in rows[1:]:  # skip header
                if row and row[0] >= cutoff:
                    items.append({
                        "source": "Travel Events Log",
                        "modified_by": "Shared Sheet",
                        "modified": row[0],
                        "content_preview": " | ".join(row[:5]),
                    })
            print(f"  📊 Found {sum(1 for i in items if i['source'] == 'Travel Events Log')} recent travel events")
    except Exception as e:
        err_str = str(e)
        if "permission" in err_str.lower():
            print(f"  ⚠ Travel Events sheet not accessible — share sheet {TRAVEL_EVENTS_SHEET_ID} with the GCP service account email")
        else:
            print(f"  ⚠ Travel Events check failed (non-fatal): {e}")

    print(f"  📋 Total items to classify: {len(items)}")
    if not items:
        print("  ℹ No new context found")
        return {"temporary": [], "permanent": [], "section_html": ""}

    # 3. Two-stage: EXTRACT facts from each doc, then CLASSIFY each fact
    print(f"  🧠 Stage 1: Extracting facts from {len(items)} items (GPT)...")

    extract_prompt = """You are reading a document related to HX insurance trading.
Extract ONLY facts that could MATERIALLY IMPACT future trading decisions or explain a change in trading performance.

Return JSON: {"facts": ["fact 1", "fact 2", ...], "skip_reason": null}

THE MATERIAL IMPACT TEST — every fact you extract MUST pass this test:
"Could this fact CHANGE how we trade, EXPLAIN a movement in trading performance, or DRIVE a future decision?"
If the answer is no, do NOT extract it.

EXTRACT (these CAUSE or EXPLAIN trading impact):
- Pricing changes: "EU Exc yielding margins were increased on 12/03/2026"
- Product launches/changes: "Specialist cruise product launched with flexible excess options"
- Competitor actions: "Carnival launched £850 onboard spend offer to combat slow trading"
- Partner dynamics: "On the Beach partnership worth approximately £150k/year"
- Market events: "Iran conflict causing aggregator quote surge"
- UW rule changes: "Max age limit for single trip policies changed to 85 years"
- Promotional campaigns: "HX Insurance Competition runs April-September 2026 with £10k prize"
- Conversion/funnel changes: "Payment process optimisation with WorldPay to address low start purchase conversion"
- Strategy decisions: "AMT discounts cannot go live until RNWL rates received — compliance constraint"

DO NOT EXTRACT (these are trading OUTPUTS, not causes):
- Historical data points: "The Combined Demand Index was 88.6 in 2015Q4" — this is a result, not a driver
- Periodic metrics/figures: "H1 FY26 delivered 180k policies" — this is what happened, not why
- Per-month booking statistics: "P&O Cruises had 38,067 total bookings in April 2025"
- Generic definitions: "CTR is defined as the percentage of impressions that were clicked"
- Operational process details: "A rota is used to assign agents to payment-taking"
- Tool/vendor descriptions: "The WeDiscover website is www.we-discover.com"
- Document metadata: "The document is dated January 2026"
- Conversion rates without context: "Start Purchase was 92.2% over the last 7 days" — a snapshot metric, not actionable
- Weekly trading figures that just state what happened: "Policy volume increased by 4.6% last week"

ALSO SKIP:
- Raw data tables (CSV/spreadsheet dumps with no narrative)
- Sensitive personal data (individual names, salaries, addresses)
- Summaries/max/min of historical time series

Travel Events Log entries are ALWAYS worth extracting — they describe external events that drive trading.

Each fact should be a single sentence that a trader could ACT on or use to EXPLAIN a movement."""

    classify_prompt = """Classify this fact for a trading briefing context system. Return JSON only.

{"classification": "<PERMANENT|TEMPORARY|SKIP>", "category": "<insurance|operational|universal>", "reasoning": "<why, max 30 chars>"}

PERMANENT = structural facts that won't revert week to week. Use PERMANENT for:
  - Product changes going live or in production (e.g. "Medical amends are moving to production")
  - New product features or cover types (e.g. "Flexible excess options launched for cruise")
  - Product rule changes (e.g. "Maximum age for annual multi-trip increasing to 85")
  - Market structure facts (e.g. "All Clear market size estimated at £150m-£200m")
  - Strategic directions (e.g. "Strategy is to build a repeat direct customer base")
  - New distribution partners or scheme changes
  - Underwriter threshold or business logic changes
  - New KPIs or measurement approaches
  - Dataset/schema knowledge (e.g. "Insurance group identifies return customer behaviour")
TEMPORARY = current/recent changes that will evolve:
  - Active promotions, recent pricing discount changes, competitor offers
  - Market events, funnel experiments, campaign launches
  - Tactical pricing adjustments that may be reversed
SKIP = not useful for trading decisions. ALWAYS skip these:
  - Historical metrics/figures (e.g. "H1 FY26 was 180k policies")
  - Periodic booking stats (e.g. "P&O had 38,067 bookings in April")
  - Generic definitions (e.g. "CTR is the percentage of impressions clicked")
  - Operational processes (e.g. "A rota is used to assign agents")
  - Document metadata (e.g. "The document is dated November 2025")
  - Tool/vendor contact info
  - Data that describes WHAT HAPPENED rather than WHY or WHAT CHANGED

CATEGORY (where to file this fact):
  - insurance = specific to insurance products, pricing, partners, schemes, cover levels
  - operational = market events, competitor actions, promotions, funnel changes, campaigns
  - universal = macro factors (economy, regulation, travel demand, geopolitics)"""

    client_oai = openai.OpenAI(api_key=OPENAI_API_KEY)
    gpt_items = []

    for item in items:
        try:
            item_text = f"Source: {item['source']}\nContent:\n{item['content_preview'][:3000]}"
            # Stage 1: Extract facts
            extract_resp = client_oai.chat.completions.create(
                model=MODEL,
                max_completion_tokens=2000,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": extract_prompt},
                    {"role": "user", "content": item_text},
                ],
            )
            extract_raw = extract_resp.choices[0].message.content
            extracted = _parse_llm_json(extract_raw)
            facts = extracted.get("facts", []) if isinstance(extracted, dict) else []
            skip = extracted.get("skip_reason") if isinstance(extracted, dict) else None

            if skip or not facts:
                print(f"    ⏭ {item['source']}: {skip or 'no extractable facts'}")
                continue

            print(f"    📄 {item['source']}: {len(facts)} facts extracted")

            # Stage 2: Classify each fact
            for fact in facts:
                try:
                    cls_resp = client_oai.chat.completions.create(
                        model=LIGHTWEIGHT_MODEL,
                        max_completion_tokens=100,
                        response_format={"type": "json_object"},
                        messages=[
                            {"role": "system", "content": classify_prompt},
                            {"role": "user", "content": fact},
                        ],
                    )
                    cls_parsed = _parse_llm_json(cls_resp.choices[0].message.content)
                    cls = cls_parsed.get("classification", "TEMPORARY") if isinstance(cls_parsed, dict) else "TEMPORARY"
                    gpt_items.append({
                        "summary": fact,
                        "classification": cls,
                        "source": item["source"],
                        "reasoning": cls_parsed.get("reasoning", "") if isinstance(cls_parsed, dict) else "",
                    })
                    print(f"      {cls}: {fact[:70]}")
                except Exception as e:
                    print(f"      ⚠ Classify failed for fact: {e}")
        except Exception as e:
            print(f"    ⚠ Extraction failed for {item['source']}: {e}")

    print(f"  📝 Extracted and classified {len(gpt_items)} facts from {len(items)} docs")

    if not gpt_items:
        print("  ℹ No useful facts extracted")
        return {"temporary": [], "permanent": [], "section_html": ""}

    # 4. Cross-verify: gpt-5-mini vs gpt-4o-mini — two fast models compete, consensus wins
    # Each fact gets classified by both. If they agree, that's the answer.
    # If they disagree, the more conservative one wins (TEMPORARY > PERMANENT, SKIP > TEMPORARY).
    verified_items = gpt_items
    VERIFY_MODELS = ["gpt-5-mini", "gpt-4o-mini"]
    CONSERVATISM = {"SKIP": 0, "TEMPORARY": 1, "PERMANENT": 2}  # lower = more conservative

    if gpt_items:
        print(f"  🔍 Cross-verifying {len(gpt_items)} facts ({VERIFY_MODELS[0]} vs {VERIFY_MODELS[1]})...")
        verify_prompt = """Classify each fact for a trading briefing. Return JSON: {"items": [{"classification": "PERMANENT|TEMPORARY|SKIP"}, ...]}
PERMANENT = structural rule, UW threshold, new product/partner — won't change week-to-week
TEMPORARY = active promotion, recent pricing change, current market event, competitor action
SKIP = not useful for trading DECISIONS. Always skip: historical figures, periodic stats,
generic definitions, operational processes, document metadata, booking volume snapshots.
Ask: "Could a trader ACT on this or use it to EXPLAIN a movement?" If no → SKIP."""

        # Build character-length batches (~4000 chars each)
        batches = []
        current_batch = []
        current_chars = 0
        for item in gpt_items:
            s = len(item.get("summary", "")[:100])
            if current_chars + s > 3500 and current_batch:
                batches.append(current_batch)
                current_batch = []
                current_chars = 0
            current_batch.append(item)
            current_chars += s
        if current_batch:
            batches.append(current_batch)

        agreements = 0
        disagreements = 0
        for batch_idx, batch in enumerate(batches):
            summaries = [i.get("summary", "")[:100] for i in batch]
            results_by_model = {}

            for model_name in VERIFY_MODELS:
                try:
                    resp = client_oai.chat.completions.create(
                        model=model_name,
                        max_completion_tokens=1500,
                        response_format={"type": "json_object"},
                        messages=[
                            {"role": "system", "content": verify_prompt},
                            {"role": "user", "content": json.dumps(summaries)},
                        ],
                    )
                    result = _parse_llm_json(resp.choices[0].message.content)
                    items_list = result.get("items", result) if isinstance(result, dict) else result
                    if isinstance(items_list, list) and len(items_list) == len(batch):
                        results_by_model[model_name] = [i.get("classification", "TEMPORARY") if isinstance(i, dict) else "TEMPORARY" for i in items_list]
                    else:
                        results_by_model[model_name] = [i.get("classification", "TEMPORARY") for i in batch]
                except Exception:
                    results_by_model[model_name] = [i.get("classification", "TEMPORARY") for i in batch]

            # Consensus: if both agree, use that. If they disagree, use the more conservative one.
            if len(results_by_model) == 2:
                m1, m2 = VERIFY_MODELS
                for i, item in enumerate(batch):
                    cls1 = results_by_model.get(m1, ["TEMPORARY"] * len(batch))[i]
                    cls2 = results_by_model.get(m2, ["TEMPORARY"] * len(batch))[i]
                    if cls1 == cls2:
                        item["classification"] = cls1
                        agreements += 1
                    else:
                        # If EITHER model says PERMANENT, use PERMANENT (rare, valuable)
                        if cls1 == "PERMANENT" or cls2 == "PERMANENT":
                            item["classification"] = "PERMANENT"
                        else:
                            # For SKIP vs TEMPORARY, more conservative wins
                            item["classification"] = cls1 if CONSERVATISM.get(cls1, 1) <= CONSERVATISM.get(cls2, 1) else cls2
                        disagreements += 1

        total = agreements + disagreements
        print(f"  ✓ Cross-verified {total} facts: {agreements} agreed, {disagreements} disagreed (conservative wins)")

    # 5. Split into permanent, temporary, and skip
    temporary = [i for i in verified_items if i.get("classification") == "TEMPORARY"]
    permanent = [i for i in verified_items if i.get("classification") == "PERMANENT"]
    skipped = [i for i in verified_items if i.get("classification") == "SKIP"]
    print(f"  📋 Result: {len(temporary)} temporary, {len(permanent)} permanent, {len(skipped)} skipped")

    # 5b. Write temporary facts to temporary-context.md with expiry dates
    if temporary:
        context_dir_tmp = Path(__file__).parent / "context" / "operational"
        temp_path = context_dir_tmp / "temporary-context.md"
        today_iso = run_date.isoformat()
        expiry_iso = (run_date + timedelta(days=7)).isoformat()

        # First, prune expired entries from the file
        if temp_path.exists():
            lines = temp_path.read_text().strip().split("\n")
            kept = [lines[0]] if lines else ["# Temporary Context — Auto-Expires After 7 Days"]  # keep header
            for line in lines[1:]:
                if "expires:" in line:
                    try:
                        exp_date = line.split("expires:")[1].strip().rstrip(")")
                        if exp_date >= today_iso:
                            kept.append(line)
                        else:
                            print(f"  🗑 Expired: {line[:60]}")
                    except Exception:
                        kept.append(line)
                elif line.strip():
                    kept.append(line)
            temp_path.write_text("\n".join(kept) + "\n")
        else:
            temp_path.write_text("# Temporary Context — Auto-Expires After 7 Days\n\n_Facts below are used in briefings but expire automatically. Do not edit manually._\n\n")

        # Dedup temporary facts against existing temp file
        # Extract existing fact cores (text before " — Source:") for comparison
        existing_facts = set()
        if temp_path.exists():
            for line in temp_path.read_text().split("\n"):
                if line.startswith("- "):
                    core = line.split(" — Source:")[0].strip("- ").lower().strip()
                    # Store a set of the significant words (>4 chars) as a frozenset
                    words = frozenset(w for w in core.split() if len(w) > 4)
                    if len(words) >= 3:
                        existing_facts.add(words)

        new_temp = []
        for item in temporary:
            fact = item.get("summary", "").replace("\n", " ")
            fact_words = frozenset(w for w in fact.lower().split() if len(w) > 4)
            # Check if any existing fact shares >60% of its significant words with this one
            is_dup = False
            for existing in existing_facts:
                if not existing or not fact_words:
                    continue
                overlap = len(fact_words & existing) / min(len(fact_words), len(existing))
                if overlap > 0.6:
                    is_dup = True
                    break
            if not is_dup:
                new_temp.append(item)
                # Add to existing set so we don't duplicate within this batch either
                if len(fact_words) >= 3:
                    existing_facts.add(fact_words)

        if new_temp:
            with open(temp_path, "a") as f:
                for item in new_temp:
                    fact = item.get("summary", "").replace("\n", " ")
                    source = item.get("source", "")
                    f.write(f"- {fact} — Source: {source}, {today_iso} (expires: {expiry_iso})\n")
        print(f"  📝 {len(new_temp)} new temporary facts written ({len(temporary) - len(new_temp)} already in temp file)")
        temporary = new_temp

    # 5c. AI dedup pass — send the full temp file to a fast model to clean up
    temp_path_cleanup = Path(__file__).parent / "context" / "operational" / "temporary-context.md"
    if temp_path_cleanup.exists():
        temp_lines = [l for l in temp_path_cleanup.read_text().split("\n") if l.startswith("- ")]
        if len(temp_lines) > 20:
            print(f"  🧹 AI dedup: cleaning {len(temp_lines)} temp facts...")
            try:
                cleanup_resp = client_oai.chat.completions.create(
                    model="gpt-4.1-mini",
                    max_completion_tokens=8000,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": """You are deduplicating a list of trading context facts using SEMANTIC matching, not word matching.

Return JSON: {"facts": ["- fact 1 — Source: ...", "- fact 2 — Source: ...", ...]}

PROCESS:
1. Group facts by TOPIC or EVENT (e.g. all facts about "Ergo AMT pricing changes" are one group,
   all facts about "Carnival cruise promotions" are another group)
2. Within each group, keep ONLY the single most informative and complete version
3. Two facts describe the SAME thing if they're about the same event, change, or action — even if
   they use completely different words. E.g. "Ergo AMT discounts go live on 25/03" and
   "Aggregator pricing changes targeting 20% of market on 25 March" = SAME event, keep the more detailed one
4. Remove any fact that is fully covered by another more detailed fact

ALSO REMOVE:
- Historical data points and time-series values
- Periodic booking statistics
- Generic definitions
- Document metadata
- Operational process descriptions
- Weekly trading output snapshots that just report WHAT HAPPENED
- Vague facts with no actionable content

KEEP only facts a trader could ACT on or use to EXPLAIN a movement:
- Pricing changes, product launches, competitor actions, promotions, UW rules, strategy decisions, market events

Preserve the FULL line exactly as-is including "— Source: ..." and "(expires: YYYY-MM-DD)"
Do NOT rewrite or rephrase — only remove redundant lines."""},
                        {"role": "user", "content": "\n".join(temp_lines)},
                    ],
                )
                result = _parse_llm_json(cleanup_resp.choices[0].message.content)
                cleaned = result.get("facts", []) if isinstance(result, dict) else []
                if cleaned and len(cleaned) < len(temp_lines):
                    header = "# Temporary Context — Auto-Expires After 7 Days\n\n_Facts below are used in briefings but expire automatically. Do not edit manually._\n\n"
                    temp_path_cleanup.write_text(header + "\n".join(cleaned) + "\n")
                    print(f"  🧹 AI dedup: {len(temp_lines)} → {len(cleaned)} facts ({len(temp_lines) - len(cleaned)} removed)")
                else:
                    print(f"  🧹 AI dedup: no reduction (returned {len(cleaned)} items)")
            except Exception as e:
                print(f"  ⚠ AI dedup failed (non-fatal): {e}")

    # 6. Dedup + auto-file permanent items into the correct context file
    if permanent:
        context_dir = Path(__file__).parent / "context"

        # Load all existing context for dedup — extract fact-level word sets
        existing_perm_facts = set()
        context_file_index = {}
        for md_file in context_dir.rglob("*.md"):
            try:
                text = md_file.read_text()
                rel = str(md_file.relative_to(context_dir))
                first_line = text.strip().split("\n")[0].replace("#", "").strip()
                context_file_index[rel] = first_line
                # Extract per-line word sets for precise dedup
                for line in text.split("\n"):
                    line_stripped = line.strip().lstrip("- ").split(" — Source:")[0].lower().strip()
                    words = frozenset(w for w in line_stripped.split() if len(w) > 4)
                    if len(words) >= 3:
                        existing_perm_facts.add(words)
            except Exception:
                pass

        # Dedup: compare word sets, not individual words against full text
        new_permanent = []
        for item in permanent:
            summary_lower = item.get("summary", "").lower().strip()
            if not summary_lower:
                continue
            fact_words = frozenset(w for w in summary_lower.split() if len(w) > 4)
            is_dup = False
            for existing in existing_perm_facts:
                if not existing or not fact_words:
                    continue
                overlap = len(fact_words & existing) / min(len(fact_words), len(existing))
                if overlap > 0.6:
                    is_dup = True
                    break
            if is_dup:
                print(f"  ⏭ Skipping (already known): {item.get('summary', '')[:60]}")
            else:
                new_permanent.append(item)

        # Route each new item to the correct file using GPT
        if new_permanent:
            file_index_str = "\n".join([f"- {k}: {v}" for k, v in context_file_index.items()])
            route_prompt = f"""You are filing new context items into the correct markdown file.

Available context files:
{file_index_str}

For each item, return a JSON array with:
- "summary": the item summary (pass through)
- "target_file": which file path to append to (from the list above)
- "text_to_add": one bullet point to append (format: "- <fact> — Source: <source>, <date>")

If no file is appropriate, use "operational/current-market-events.md" as default.
Return ONLY valid JSON array."""

            items_for_routing = json.dumps([{"summary": i.get("summary"), "source": i.get("source")} for i in new_permanent])
            try:
                client_oai = openai.OpenAI(api_key=OPENAI_API_KEY)
                route_resp = client_oai.chat.completions.create(
                    model=LIGHTWEIGHT_MODEL,
                    max_completion_tokens=1500,
                    messages=[
                        {"role": "system", "content": route_prompt},
                        {"role": "user", "content": items_for_routing},
                    ],
                )
                routed = _parse_llm_json(route_resp.choices[0].message.content)
                if not isinstance(routed, list):
                    routed = []
            except Exception as e:
                print(f"  ⚠ Routing failed, using default file: {e}")
                routed = [{"summary": i.get("summary"), "target_file": "operational/current-market-events.md",
                           "text_to_add": f"- {i.get('summary', 'Unknown')} — Source: {i.get('source', 'Unknown')}, {run_date.isoformat()}"}
                          for i in new_permanent]

            # Write each item to its target file and record the reference for removal
            for ri, route in enumerate(routed):
                target = route.get("target_file", "operational/current-market-events.md")
                text = route.get("text_to_add", "")
                if not text:
                    continue
                target_path = context_dir / target
                if not target_path.exists():
                    target_path = context_dir / "operational" / "current-market-events.md"
                try:
                    with open(target_path, "a") as f:
                        f.write(f"\n{text}\n")
                    # Store reference on the item for the remove button
                    if ri < len(new_permanent):
                        new_permanent[ri]["_filed_to"] = str(target_path.relative_to(context_dir))
                        new_permanent[ri]["_filed_text"] = text
                    print(f"  📝 Filed to {target}: {route.get('summary', '')[:50]}")
                except Exception as e:
                    print(f"  ⚠ Failed to write to {target}: {e}")

            print(f"  ✅ {len(routed)} permanent items auto-filed ({len(permanent) - len(new_permanent)} already known)")
        else:
            print(f"  ℹ All {len(permanent)} permanent items already exist in context")

        permanent = new_permanent

    # 7. Build collapsible HTML section — permanent on top, temporary below, both expandable
    if not temporary and not permanent:
        return {"temporary": temporary, "permanent": permanent, "section_html": ""}

    def _escape(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")

    def _build_items(items, badge_cls, badge_text, start_idx=0):
        html = ""
        for i, item in enumerate(items):
            idx = start_idx + i
            summary = _escape(item.get("summary", "Unknown"))
            source = _escape(item.get("source", ""))
            remove_btn = ""
            if item.get("_filed_to"):
                filed_to = item.get("_filed_to", "").replace("'", "").replace('"', "")
                filed_text = item.get("_filed_text", "").replace("'", "").replace('"', "").replace("\n", " ")[:200]
                remove_btn = (
                    f' <button class="context-remove-btn" '
                    f'onclick="removeContext(&quot;ctx-{idx}&quot;,&quot;{filed_to}&quot;,&quot;{filed_text}&quot;)"'
                    f'>✕ Remove</button>'
                )
            # Build source line — hyperlink to GitHub if filed_to is available
            source_html = ""
            if source:
                filed_to_path = item.get("_filed_to", "")
                if filed_to_path:
                    gh_url = f"https://github.com/JakeOsmond/trading-briefing/blob/main/context/{filed_to_path}"
                    source_html = f'<a class="context-source" href="{gh_url}" target="_blank" rel="noopener">{source}</a>'
                else:
                    source_html = f'<span class="context-source">{source}</span>'
            html += (
                f'<div class="context-item" id="ctx-{idx}">'
                f'<span class="{badge_cls}">{badge_text}</span> '
                f'{summary}{remove_btn}'
                f'{source_html}'
                f'</div>\n'
            )
        return html

    perm_count = len(permanent)
    temp_count = len(temporary)
    subtitle = []
    if perm_count:
        subtitle.append(f"{perm_count} new fact{'s' if perm_count != 1 else ''} stored permanently")
    if temp_count:
        subtitle.append(f"{temp_count} temporary insight{'s' if temp_count != 1 else ''} (7-day expiry)")
    subtitle_text = " &middot; ".join(subtitle)

    # Build permanent subsection
    perm_html = ""
    if permanent:
        perm_items = _build_items(permanent, "context-badge-perm", "Learned", 0)
        perm_html = (
            f'<div class="context-subsection">'
            f'<div class="context-sub-header" onclick="var b=this.nextElementSibling;b.style.display=b.style.display===\'none\'?\'block\':\'none\'">'
            f'<strong>Permanently learned ({perm_count})</strong> — stored in context files'
            f'<span class="context-sub-toggle">&#9660;</span></div>'
            f'<div class="context-sub-body">{perm_items}</div>'
            f'</div>\n'
        )

    # Build temporary subsection
    temp_html = ""
    if temporary:
        temp_items = _build_items(temporary, "context-badge-temp", "This week", perm_count)
        temp_html = (
            f'<div class="context-subsection">'
            f'<div class="context-sub-header" onclick="var b=this.nextElementSibling;b.style.display=b.style.display===\'none\'?\'block\':\'none\'">'
            f'<strong>This week ({temp_count})</strong> — temporary, expires in 7 days'
            f'<span class="context-sub-toggle">&#9660;</span></div>'
            f'<div class="context-sub-body" style="display:none">{temp_items}</div>'
            f'</div>\n'
        )

    section_html = (
        '<div class="section-gap" data-animate="reveal">\n'
        '<div class="section-title">What Trading Covered Learned Today</div>\n'
        '<div class="context-update glass-card">\n'
        f'<p class="context-intro">Auto-learned from Drive and team docs. '
        f'<strong>{subtitle_text}.</strong></p>\n'
        f'<button class="trail-toggle" onclick="this.nextElementSibling.style.display=this.nextElementSibling.style.display===\'none\'?\'block\':\'none\';this.querySelector(\'span\').textContent=this.nextElementSibling.style.display===\'none\'?\'Show\':\'Hide\'">'
        f'<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M4 6l4 4 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
        f' <span>Show</span> what was learned</button>\n'
        f'<div class="context-items-body" style="display:none">\n'
        f'{perm_html}{temp_html}'
        f'</div>\n</div>\n</div>\n'
    )

    return {"temporary": temporary, "permanent": permanent, "section_html": section_html}


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

    # Data freshness gate — check that BigQuery has data for the expected date
    expected_date = date_params["yesterday"]
    freshness_sql = f"""
    SELECT MAX(DATE(looker_trans_date)) AS latest_date,
           SUM(policy_count) AS row_count
    FROM `{BQ_PROJECT}.insurance.insurance_trading_data`
    WHERE DATE(looker_trans_date) = '{expected_date}'
    """
    try:
        freshness = [dict(r) for r in BQ_CLIENT.query(freshness_sql).result()]
        if freshness and freshness[0].get("row_count", 0) and freshness[0]["row_count"] > 0:
            print(f"  ✓ Data freshness check: {freshness[0]['row_count']} policies for {expected_date}")
        else:
            print(f"  ⚠ WARNING: No data found for {expected_date} in BigQuery!")
            print(f"    The upstream data load may not have completed yet.")
            print(f"    Proceeding anyway — briefing may contain incomplete data.")
    except Exception as e:
        print(f"  ⚠ Freshness check failed (non-fatal): {e}")

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

    # Google Trends — fetch directly instead of via Google Sheet
    run_date_obj = date.fromisoformat(date_params["yesterday"])
    google_trends = fetch_google_trends(run_date_obj)

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
        "google_trends": google_trends,
        "spike_log": spike_log,
    }


def run_investigation_tracks(date_params):
    """Phase 2: Run ALL investigation tracks deterministically via BigQuery."""
    print("\n🔬 Phase 2: Running 23 investigation tracks...")
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
                    'sql': sql,
                    'data': rows[:300],
                    'row_count': len(rows),
                }
                print(f"     ✓ {len(rows)} rows")
                # Run additional SQL parts (sql_2, sql_3, etc.) if present
                for extra_key in sorted(k for k in track if k.startswith('sql_') and k != 'sql'):
                    try:
                        extra_rows = [dict(r) for r in BQ_CLIENT.query(track[extra_key]).result()]
                        results[track_id][f'data_{extra_key}'] = extra_rows[:300]
                        print(f"     ✓ {extra_key}: {len(extra_rows)} rows")
                    except Exception as ex:
                        print(f"     ⚠ {extra_key} failed: {str(ex)[:120]}")
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
### Google Trends — Search Intent (live data, 2-year window)
```json
{json.dumps(baseline_data.get('google_trends', {}), indent=2, default=str)}
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

## INVESTIGATION TRACK RESULTS (23 tracks, each comparing TY vs LY)
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

    # Try parsing as a JSON array first (GPT often returns [...] for lists)
    arr_start = cleaned.find("[")
    arr_end = cleaned.rfind("]") + 1
    if arr_start >= 0 and arr_end > arr_start:
        # Only try if [ comes before { (it's an array, not an object with arrays inside)
        obj_start = cleaned.find("{")
        if obj_start < 0 or arr_start < obj_start:
            arr_str = _fix_common_issues(cleaned[arr_start:arr_end])
            try:
                result = json.loads(arr_str)
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                # Try repair
                try:
                    result = json.loads(_try_repair(arr_str))
                    if isinstance(result, list):
                        return result
                except json.JSONDecodeError:
                    pass

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

    # Pre-load context so the AI doesn't need to re-fetch Drive/Sheets
    # Google Trends narrative
    gt_narrative = ""
    gt = baseline_data.get("google_trends")
    if isinstance(gt, dict):
        gt_narrative = gt.get("narrative", "")
    # AI Insights from market intelligence sheet
    ai_insights = json.dumps(baseline_data.get("ai_insights", [])[:30], indent=2, default=str)

    # Build initial messages with follow-up questions and tools
    analysis_date = run_date.strftime("%A %d %B %Y")
    messages = [
        {"role": "system", "content": FOLLOW_UP_SYSTEM},
        {"role": "user", "content": f"""Date: {analysis_date}. run_date = {run_date}.

{working_memory}

## CONTEXT ALREADY LOADED (do NOT re-fetch — use this directly)

### Google Trends Narrative
{gt_narrative if gt_narrative else '(not available)'}

### Market Intelligence — AI Insights
{ai_insights}

## FOLLOW-UP QUESTIONS TO INVESTIGATE
{json.dumps(follow_up_questions, indent=2, default=str)}

Use the context above alongside your SQL investigations. You have run_sql and web_search
available. Drive context and market intelligence sheets are already loaded above — use them
directly, do not try to re-fetch them.

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
            tools=FOLLOW_UP_TOOLS,
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


def run_synthesis(baseline_data, analysis, follow_up_results, track_results, run_date, driver_trends=None):
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

    # Inject finding IDs into each mover so the LLM can tag headings
    for i, mover in enumerate(merged_findings.get("material_movers", [])):
        mover["finding_id"] = f"finding-{i}"
        if fu_context:
            merged_findings["market_context"] = str(merged_findings.get("market_context", "")) + " " + str(fu_context)
        # Merge recent changes
        fu_changes = follow_up_results.get("recent_changes", "")
        if fu_changes:
            merged_findings["recent_changes"] = str(merged_findings.get("recent_changes", "")) + " " + str(fu_changes)

    prompt = f"""The date being analysed is {analysis_date}.
run_date = {run_date}

USE THESE DATE LITERALS in all sql-dig blocks (do NOT use a 'period' column — it doesn't exist):
- Yesterday: DATE(looker_trans_date) = '{yesterday}'
- Trailing 7d: DATE(looker_trans_date) BETWEEN '{week_start}' AND '{yesterday}'
- Trailing 7d LY: DATE(looker_trans_date) BETWEEN '{week_start_ly}' AND '{yesterday_ly}'

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

## CUSTOMER SEARCH INTENT — Google Trends (live data with deep links)
Each term has a `deep_link` field — use these as markdown source links in the briefing.
The `insurance_compare_link` and `holiday_compare_link` fields compare all terms in each category.
The `deep_dive_terms` section contains AI-suggested follow-up terms that explain WHY base terms are moving.
The `narrative` field is a pre-written daily intelligence summary — use it as context for the Customer Search Intent
section AND for the wider trading analysis (it explains search demand dynamics that may drive trading movements).

### Google Trends Daily Narrative
{baseline_data.get('google_trends', {}).get('narrative', '(not available)') if isinstance(baseline_data.get('google_trends'), dict) else '(not available)'}

### Full Google Trends Data
```json
{json.dumps(baseline_data.get('google_trends', {}), indent=2, default=str)}
```

## DASHBOARD METRICS (search volume, demand signals)
```json
{json.dumps(baseline_data.get('dashboard_metrics', [])[:20], indent=2, default=str)}
```

## INVESTIGATED FINDINGS (from 23 tracks + AI analysis + follow-ups)
```json
{json.dumps(merged_findings, indent=2, default=str)}
```

## TRACK COVERAGE SUMMARY
{json.dumps({tid: tr['name'] + ': ' + str(tr['row_count']) + ' rows' for tid, tr in track_results.items()}, indent=2)}

## STATISTICAL CONFIDENCE (from 90-day + seasonal analysis)
```json
{json.dumps({k: {"confidence": v.get("confidence", "Low"), "explanation": v.get("confidence_explanation", ""), "bank_holiday_note": v.get("bank_holiday_note")} for k, v in (driver_trends or {}).items()}, indent=2, default=str)}
```

Now produce the final briefing following the 3-tier format exactly:
1. Headline (one sentence, like a newspaper)
2. At a Glance (5 traffic light bullets, biggest £ first)
3. What's Driving This (ALL 8 movers, ordered by CONFIDENCE: VERY HIGH first, then HIGH, MEDIUM, LOW, VERY LOW. Within each confidence tier, order by absolute £ impact. Do NOT put confidence tags in headings — they are injected automatically by the dashboard. 2 sentences + sql-dig)
   IMPORTANT: Each mover has a `finding_id` field (e.g. "finding-0"). You MUST include it at the END of each ### heading as a hidden span: `### Driver heading <span data-fid="finding-0"></span>`. This links each driver to its verification result.
4. Customer Search Intent (Google Trends / search behaviour data)
5. News & Market Context (AI Insights, competitor activity, external factors)
6. Actions table (max 5, with £ values)

**CONFIDENCE-AWARE LANGUAGE:**
- For VERY HIGH confidence movers: Use strongest language ("this is definitively...", "the data conclusively shows...")
- For HIGH confidence movers: Use definitive language ("this is clearly...", "the data shows...")
- For MEDIUM confidence movers: Use moderate language ("this appears to be...", "early signs suggest...")
- For LOW confidence movers: Use hedged language ("this may be noise...", "too early to tell if...")
- For VERY LOW confidence movers: Use cautious language ("this is likely noise...", "insufficient evidence to conclude...")
- If a mover has a bank_holiday_note, mention the holiday effect briefly in the narrative

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
10. Deep dives are ordered by confidence: VERY HIGH first, then HIGH, MEDIUM, LOW, VERY LOW
11. Language is hedged appropriately for low/very low confidence movers ("may be...", "too early to tell...")
12. High/very high confidence movers use definitive language ("clearly...", "the data shows...")

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
# DRIVER TREND DATA [DOMAIN-AGNOSTIC — statistical confidence system works for any metric]
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


def _compute_confidence(observed, ty_90d_vals, ly_seasonal_vals, persistence_label,
                         consistent_days, total_days, direction,
                         ty_start, ty_end, ly_start, ly_end):
    """Compute statistical confidence by combining persistence with z-score analysis.

    Returns dict with confidence level, z-scores, sample sizes, and natural language explanation.
    """
    result = {
        "confidence": "Low",
        "z_recent": 0.0,
        "z_seasonal": 0.0,
        "sample_size_recent": len(ty_90d_vals),
        "sample_size_seasonal": len(ly_seasonal_vals),
        "explanation": "",
        "bank_holiday_note": None,
    }

    # ── Bank holiday & school holiday detection ─────────────────────────────
    _bank_hols = _get_bank_holidays()
    ty_holidays = [h for h in _bank_hols
                   if ty_start <= h <= ty_end]
    ly_holidays = [h for h in _bank_hols
                   if ly_start <= h <= ly_end]
    bank_hol_mismatch = len(ty_holidays) != len(ly_holidays)

    # Check if the analysis week overlaps school holidays differently TY vs LY
    from datetime import date as _date
    _ty_end_dt = _date.fromisoformat(ty_end)
    _ty_week_start = (_ty_end_dt - timedelta(days=6)).isoformat()
    _ly_end_dt = _date.fromisoformat(ly_end) if ly_end <= ty_end else _date.fromisoformat(ly_end)
    _ly_week_start = (_ly_end_dt - timedelta(days=6)).isoformat()
    ty_in_school_hol = any(_date_in_school_holiday(d) for d in [_ty_week_start, ty_end])
    ly_in_school_hol = any(_date_in_school_holiday(d) for d in [_ly_week_start, ly_end])
    school_hol_mismatch = ty_in_school_hol != ly_in_school_hol

    holiday_mismatch = bank_hol_mismatch or school_hol_mismatch
    notes = []
    if bank_hol_mismatch:
        notes.append(
            f"There are {len(ty_holidays)} bank holiday(s) in the current window "
            f"but {len(ly_holidays)} at the same point last year."
        )
    if school_hol_mismatch:
        ty_label = "falls during school holidays" if ty_in_school_hol else "is outside school holidays"
        ly_label = "fell during school holidays" if ly_in_school_hol else "was outside school holidays"
        notes.append(f"This period {ty_label}, but last year it {ly_label}.")
    if notes:
        result["bank_holiday_note"] = " ".join(notes)

    # ── Guard: insufficient data ───────────────────────────────────────────
    if len(ty_90d_vals) < 7:
        result["explanation"] = (
            "There isn't enough historical data for this segment to assess "
            "whether this movement is meaningful or just normal variation."
        )
        return result

    # ── Recent baseline (90-day same-day-of-week) ──────────────────────────
    mean_recent = statistics.mean(ty_90d_vals)
    stdev_recent = statistics.pstdev(ty_90d_vals)
    z_recent = (observed - mean_recent) / stdev_recent if stdev_recent > 0 else 0.0
    result["z_recent"] = round(z_recent, 2)

    # ── Seasonal baseline (LY equivalent ±3 weeks, same-day-of-week) ──────
    z_seasonal = 0.0
    if len(ly_seasonal_vals) >= 4:
        mean_seasonal = statistics.mean(ly_seasonal_vals)
        stdev_seasonal = statistics.pstdev(ly_seasonal_vals)
        z_seasonal = (observed - mean_seasonal) / stdev_seasonal if stdev_seasonal > 0 else 0.0
        result["z_seasonal"] = round(z_seasonal, 2)
    has_seasonal = len(ly_seasonal_vals) >= 4

    # ── Confidence matrix ──────────────────────────────────────────────────
    recent_sig = abs(z_recent) > 2.0
    seasonal_sig = has_seasonal and abs(z_seasonal) > 2.0
    both_sig = recent_sig and seasonal_sig
    either_sig = recent_sig or seasonal_sig

    if persistence_label == "recurring":
        confidence = "Very High" if both_sig else ("High" if either_sig else "Medium")
    elif persistence_label == "emerging":
        confidence = "High" if both_sig else ("Medium" if either_sig else "Low")
    else:  # new
        confidence = "Medium" if both_sig else ("Low" if either_sig else "Very Low")

    # Holiday mismatch downgrade (bank holidays or school holidays)
    if holiday_mismatch:
        _downgrade = {"Very High": "High", "High": "Medium", "Medium": "Low", "Low": "Very Low"}
        confidence = _downgrade.get(confidence, confidence)

    result["confidence"] = confidence

    # ── Natural language explanation (plain English, no jargon) ─────────────
    parts = []

    # How consistent the pattern is
    if persistence_label == "recurring":
        parts.append(f"This has been happening consistently — {consistent_days} out of "
                      f"the last {total_days} trading days showed the same trend.")
    elif persistence_label == "emerging":
        parts.append(f"This is starting to form a pattern — {consistent_days} out of "
                      f"the last {total_days} trading days, but it's not yet established.")
    else:
        parts.append(f"This is a recent change — only {consistent_days} out of the "
                      f"last {total_days} trading days showed this.")

    # How unusual it is vs recent history
    if stdev_recent > 0:
        if recent_sig:
            parts.append(f"Compared to the last 90 days, this level of movement is unusual "
                          f"and stands out from what we'd normally expect to see.")
        else:
            parts.append(f"Compared to the last 90 days, this is within the normal range "
                          f"of day-to-day variation we typically see.")

    # How unusual it is vs this time last year
    if has_seasonal:
        if seasonal_sig:
            parts.append(f"It's also unusual compared to this time last year, suggesting "
                          f"something has genuinely changed rather than it being seasonal.")
        else:
            parts.append(f"However, it's in line with what we saw at this time last year, "
                          f"so seasonality could be a factor.")

    # Holiday context
    if holiday_mismatch:
        if bank_hol_mismatch and school_hol_mismatch:
            parts.append("Both bank holidays and school holidays fall differently this year vs last year, "
                          "making the year-on-year comparison less reliable.")
        elif bank_hol_mismatch:
            parts.append("Bank holidays fall differently this year vs last year, "
                          "which makes the year-on-year comparison less reliable.")
        elif school_hol_mismatch:
            parts.append("School holidays fall differently this year vs last year, "
                          "which could be influencing this movement.")
        parts.append("This has reduced the confidence rating by one level.")

    # Small sample warning
    if len(ty_90d_vals) < 20:
        parts.append("Note: this is a smaller segment with limited data, "
                      "so the analysis is less reliable than for larger segments.")

    result["explanation"] = " ".join(parts)
    return result


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
            metric_expr = "SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(CAST(ppc_cost_per_policy AS FLOAT64), 0))"
            metric_label = "GP"

        # If no segment_filter, skip — we can't generate a meaningful trend
        if not seg_filter:
            print(f"  ⚠ No segment_filter for mover '{driver_name}' — skipping trend")
            continue

        sql = f"""
SELECT
  DATE(looker_trans_date) AS transaction_date,
  {metric_expr} AS val
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{yesterday.strftime('%Y-%m-%d')}'
  AND {seg_filter}
GROUP BY transaction_date
ORDER BY transaction_date
"""
        sql_ly = f"""
SELECT
  DATE(looker_trans_date) AS transaction_date,
  {metric_expr} AS val
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '{ly_start.strftime('%Y-%m-%d')}' AND '{ly_end.strftime('%Y-%m-%d')}'
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
            ty_parsed = [{"dt": str(r.get("transaction_date", r.get("dt", ""))), "val": float(r.get("val", 0))} for r in ty_rows]
            ly_parsed = [{"dt": str(r.get("transaction_date", r.get("dt", ""))), "val": float(r.get("val", 0))} for r in ly_rows]
            direction = mover.get("direction", "down")
            consistent, total, label = _compute_persistence(
                [d["val"] for d in ty_parsed],
                [d["val"] for d in ly_parsed],
                direction
            )

            # ── 90-day statistical confidence ──────────────────────────
            confidence_data = {
                "confidence": "Medium" if label == "recurring" else "Low",
                "z_recent": 0.0, "z_seasonal": 0.0,
                "sample_size_recent": 0, "sample_size_seasonal": 0,
                "explanation": "Statistical analysis not available.",
                "bank_holiday_note": None,
            }
            try:
                ty_90d_start = (yesterday - datetime.timedelta(days=89)).strftime('%Y-%m-%d')
                ly_seasonal_start = (yesterday - datetime.timedelta(days=364 + 21)).strftime('%Y-%m-%d')
                ly_seasonal_end = (yesterday - datetime.timedelta(days=364 - 21)).strftime('%Y-%m-%d')

                sql_90d = f"""
SELECT 'TY' AS period, DATE(looker_trans_date) AS transaction_date,
  {metric_expr} AS val
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '{ty_90d_start}' AND '{yesterday.strftime('%Y-%m-%d')}'
  AND {seg_filter}
GROUP BY period, transaction_date
UNION ALL
SELECT 'LY' AS period, DATE(looker_trans_date) AS transaction_date,
  {metric_expr} AS val
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '{ly_seasonal_start}' AND '{ly_seasonal_end}'
  AND {seg_filter}
GROUP BY period, transaction_date
ORDER BY period, dt
"""
                stat_result = tool_run_sql(sql_90d)
                stat_rows = json.loads(stat_result.split("\n\n")[-1]) if "auto-corrected" in stat_result or "AI-corrected" in stat_result else json.loads(stat_result)

                # Split into TY 90d and LY seasonal, filter to same day-of-week
                target_dow = yesterday.weekday()
                ty_90d_vals = [float(r.get("val", 0)) for r in stat_rows
                               if r.get("period") == "TY"
                               and datetime.date.fromisoformat(str(r.get("transaction_date", r.get("dt", "")))[:10]).weekday() == target_dow]
                ly_seasonal_vals = [float(r.get("val", 0)) for r in stat_rows
                                     if r.get("period") == "LY"
                                     and datetime.date.fromisoformat(str(r.get("transaction_date", r.get("dt", "")))[:10]).weekday() == target_dow]

                # Observed value = most recent TY data point (last day of 14-day series)
                observed = ty_parsed[-1]["val"] if ty_parsed else 0.0

                confidence_data = _compute_confidence(
                    observed, ty_90d_vals, ly_seasonal_vals,
                    label, consistent, total, direction,
                    ty_90d_start, yesterday.strftime('%Y-%m-%d'),
                    ly_seasonal_start, ly_seasonal_end
                )
                print(f"     📊 Confidence: {confidence_data['confidence']} (z_recent={confidence_data['z_recent']}, z_seasonal={confidence_data['z_seasonal']})")
            except Exception as stat_err:
                print(f"     ⚠ Statistical confidence failed: {stat_err}")

            trend_entry = {
                "ty": ty_parsed,
                "ly": ly_parsed,
                "metric_label": metric_label,
                "direction": direction,
                "persistence": label,
                "consistent_days": consistent,
                "total_days": total,
                "confidence": confidence_data["confidence"],
                "z_recent": confidence_data["z_recent"],
                "z_seasonal": confidence_data["z_seasonal"],
                "sample_size_recent": confidence_data["sample_size_recent"],
                "sample_size_seasonal": confidence_data["sample_size_seasonal"],
                "confidence_explanation": confidence_data["explanation"],
                "bank_holiday_note": confidence_data.get("bank_holiday_note"),
            }
            driver_trends[driver_name] = trend_entry
            # Also key by finding_id for direct matching via data-fid span
            finding_id = mover.get("finding_id", f"finding-{i}")
            driver_trends[finding_id] = trend_entry
        except Exception as e:
            print(f"  ⚠ Trend query failed for '{driver_name}': {e}")
            continue

    print(f"  ✓ Collected trends for {len(driver_trends)} drivers")
    return driver_trends


# ---------------------------------------------------------------------------
# CROSS-MODEL VERIFICATION [DOMAIN-AGNOSTIC — verifies any finding against SQL evidence]
# ---------------------------------------------------------------------------

def verify_findings(analysis, track_results, follow_up_results):
    """Phase 4c: Cross-verify each material mover using Claude as independent verifier."""
    if not ANTHROPIC_API_KEY:
        print("  ⚠ ANTHROPIC_API_KEY not set — skipping verification")
        return {}

    movers = analysis.get("material_movers", [])
    if not movers:
        print("  ⚠ No material movers to verify")
        return {}

    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    verification_results = {}

    for i, mover in enumerate(movers):
        driver_name = mover.get("driver", f"Driver {i+1}")
        finding_id = f"finding-{i}"
        print(f"  🔍 Verifying: {driver_name}...")

        # Gather the SQL evidence for this mover
        segment_filter = mover.get("segment_filter", "")
        evidence_tracks = mover.get("evidence", "")
        sql_evidence = []
        for tid, tr in track_results.items():
            if tid in str(evidence_tracks) or tr["name"].lower() in driver_name.lower():
                sql_evidence.append({
                    "track": tr["name"],
                    "sql": tr.get("sql", "N/A"),
                    "row_count": tr["row_count"],
                    "sample_data": tr["data"][:10] if tr["data"] else [],
                })

        # Also check follow-up results
        follow_up_evidence = []
        if isinstance(follow_up_results, dict):
            for fk, fv in follow_up_results.items():
                if isinstance(fv, dict) and (driver_name.lower() in str(fv).lower()):
                    follow_up_evidence.append({
                        "question": fv.get("question", fk),
                        "sql": fv.get("sql", "N/A"),
                        "result_summary": str(fv.get("data", []))[:500],
                    })

        verification_prompt = f"""You are an independent data analyst verifying a trading analysis finding.

## THE FINDING (generated by OpenAI GPT)
- Driver: {driver_name}
- Weekly GP Impact: £{mover.get('impact_gbp_weekly', 'unknown'):,}
- Direction: {mover.get('direction', 'unknown')}
- Detail: {mover.get('detail', 'No detail provided')}
- Evidence cited: {evidence_tracks}
- Segment filter: {segment_filter}

## RAW SQL EVIDENCE
### Investigation Tracks
{json.dumps(sql_evidence, indent=2, default=str)}

### Follow-up Investigations
{json.dumps(follow_up_evidence, indent=2, default=str)}

## YOUR TASK
Based ONLY on the raw SQL evidence provided:
1. Does the stated £ impact direction (up/down) match the data?
2. Does the stated magnitude seem reasonable given the numbers?
3. Does the driver label accurately describe what the SQL measured?
4. Are there obvious alternative explanations the analysis missed?

Output ONLY raw JSON (no markdown fences):
{{
  "verdict": "agree" | "partially_agree" | "disagree",
  "reasoning": "2-3 sentence explanation of your verdict",
  "concern": "If partially_agree or disagree, what specifically is wrong or uncertain"
}}"""

        try:
            response = client.messages.create(
                model=VERIFY_MODEL,
                max_tokens=512,
                messages=[{"role": "user", "content": verification_prompt}],
            )
            result_text = response.content[0].text if response.content else "{}"
            result = _parse_llm_json(result_text)
            verdict = result.get("verdict", "unverified")
            reasoning = result.get("reasoning", "")
            concern = result.get("concern", "")
            print(f"    → {verdict}: {reasoning[:80]}...")
        except Exception as e:
            print(f"    ⚠ Verification failed for {driver_name}: {e}")
            verdict = "unverified"
            reasoning = f"Verification unavailable: {str(e)[:100]}"
            concern = ""

        verification_results[finding_id] = {
            "driver": driver_name,
            "verdict": verdict,
            "reasoning": reasoning,
            "concern": concern,
            "sql_evidence": sql_evidence[:3],  # Keep top 3 for HTML display
        }

    return verification_results


# ---------------------------------------------------------------------------
# HTML DASHBOARD [DOMAIN-AGNOSTIC — layout, CSS, JS, charts, verification UI. Only the banner image is insurance-branded]
# ---------------------------------------------------------------------------

def generate_dashboard_html(briefing_md, trading_data, trend_data, today_str, investigation_log=None, run_date=None, trend_data_ly=None, driver_trends=None, verification=None, context_updates=None):
    """Generate styled dark-mode dashboard with interactive charts and SQL dig buttons."""
    import re

    # Load extracted CSS/JS templates (un-escaped, lintable files)
    _tpl_dir = Path(__file__).parent / "templates"
    css_content = (_tpl_dir / "dashboard.css").read_text()
    js_content = (_tpl_dir / "dashboard.js").read_text()
    js_verify_content = (_tpl_dir / "dashboard-verify.js").read_text()

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
        r'\n+_Generated \d.*$',  # Catch AI-generated footer without --- separator
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

    # Replace confidence/persistence text tags with styled badges in driver headings
    # New confidence tags (from updated synthesis)
    for _conf_tag, _conf_class in [
        ('VERY HIGH CONFIDENCE', 'badge-confidence-very-high'),
        ('HIGH CONFIDENCE', 'badge-confidence-high'),
        ('MEDIUM CONFIDENCE', 'badge-confidence-medium'),
        ('LOW CONFIDENCE', 'badge-confidence-low'),
        ('VERY LOW CONFIDENCE', 'badge-confidence-very-low'),
    ]:
        html_body = re.sub(
            rf'<code>{_conf_tag}</code>',
            f'<span class="{_conf_class}">{_conf_tag.title()}</span>',
            html_body
        )
        html_body = re.sub(
            rf'\s*{_conf_tag}\s*</h3>',
            f' <span class="{_conf_class}">{_conf_tag.title()}</span></h3>',
            html_body
        )
        html_body = re.sub(
            rf'(?<=</h3>)\s*{_conf_tag}\b',
            f' <span class="{_conf_class}">{_conf_tag.title()}</span>',
            html_body
        )
    # Legacy persistence tags (backwards compat with older briefings)
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

    # Build verification lookup — keyed by finding ID and by driver name for fuzzy matching
    _verification_results = verification or {}
    _verification_by_name = {}
    for fid, vdata in _verification_results.items():
        driver = vdata.get("driver", "")
        if driver:
            _verification_by_name[driver.lower().strip()] = {**vdata, "_original_id": fid}

    def _find_verification(heading_text):
        """Match a heading to its verification result by driver name similarity."""
        h_lower = heading_text.lower().strip()
        h_words = set(w for w in re.sub(r'[^a-z0-9\s]', '', h_lower).split() if len(w) > 2)
        if not h_words:
            return {}
        best_match = None
        best_score = 0
        best_pct = 0
        for driver_name, vdata in _verification_by_name.items():
            d_words = set(w for w in re.sub(r'[^a-z0-9\s]', '', driver_name).split() if len(w) > 2)
            if not d_words:
                continue
            shared = h_words & d_words
            score = len(shared)
            # Percentage of smaller set that matches
            pct = score / min(len(h_words), len(d_words)) if min(len(h_words), len(d_words)) > 0 else 0
            if score > best_score or (score == best_score and pct > best_pct):
                best_score = score
                best_pct = pct
                best_match = vdata
        # Accept if ≥2 matching words, OR ≥1 word matching ≥50% of the shorter set
        if best_score >= 2 or (best_score >= 1 and best_pct >= 0.5):
            return best_match
        return {}

    _used_verification = set()  # track which verifications have been assigned

    def _add_driver_id(match):
        heading_html = match.group(1)
        heading_text = re.sub(r'<[^>]+>', '', heading_html)
        slug = re.sub(r'[^a-z0-9]+', '-', heading_text.lower().strip()).strip('-')
        idx = _driver_idx[0]
        _driver_idx[0] += 1
        tid = f'trend-{idx}'

        # Match verification using multiple strategies (in priority order)
        vr = {}
        finding_id = f"finding-{idx}"

        # Strategy 1: data-fid span from synthesis LLM
        fid_match = re.search(r'data-fid="(finding-\d+)"', heading_html)
        if fid_match:
            fid = fid_match.group(1)
            if fid in _verification_results and fid not in _used_verification:
                finding_id = fid
                vr = _verification_results[fid]
                _used_verification.add(fid)

        # Strategy 2: fuzzy name matching
        if not vr:
            vr_candidate = _find_verification(heading_text)
            cand_id = vr_candidate.get("_original_id", "")
            if vr_candidate and cand_id and cand_id not in _used_verification:
                finding_id = cand_id
                vr = vr_candidate
                _used_verification.add(cand_id)

        # Strategy 3: grab the next unassigned verification result (all drivers should be verified)
        if not vr:
            for fid, vdata in _verification_results.items():
                if fid not in _used_verification:
                    finding_id = fid
                    vr = vdata
                    _used_verification.add(fid)
                    break

        # Embed matched trend key directly as data attribute
        # Try finding_id first (direct match), then fall back to fuzzy h_to_k
        trend_key = ''
        if finding_id and _all_trends_for_js and finding_id in _all_trends_for_js:
            trend_key = finding_id
        if not trend_key:
            trend_key = _h_to_k.get(idx, '')
        trend_attr = f' data-trend-key="{trend_key}"' if trend_key else ''
        # Strip the data-fid span and stray confidence code tags from heading text
        clean_heading = re.sub(r'\s*<span\s+data-fid="[^"]*"\s*>\s*</span>\s*', '', match.group(1))
        clean_heading = re.sub(r'\s*<code>\s*(?:VERY\s+)?(?:HIGH|MEDIUM|LOW)\s*(?:CONFIDENCE)?\s*</code>\s*', '', clean_heading)
        # Title on its own line — pills go below
        h3_tag = f'<h3 id="driver-{slug}" data-driver-idx="{idx}" data-finding-id="{finding_id}"{trend_attr}>{clean_heading}</h3>'
        # Pills line: persistence dots + confidence injected by initDriverTrends, verification pill here
        # Trend button is now created by JS in the .dig-buttons row
        pills_line = f'<div class="driver-pills">'
        verdict = vr.get("verdict", "")
        reasoning = (vr.get("reasoning") or "").replace('"', '&quot;').replace("'", "&#39;")
        concern = (vr.get("concern") or "").replace('"', '&quot;').replace("'", "&#39;")
        sql_ev = vr.get("sql_evidence", [])
        # Format SQL evidence: clean, copy-pastable SQL for BigQuery
        sql_blocks = []
        for ev in sql_ev:
            track_name = ev.get('track', 'Unknown track')
            row_count = ev.get('row_count', '?')
            raw_sql = ev.get("sql", "").strip()
            if raw_sql and raw_sql != "N/A":
                sql_blocks.append(f"-- Track: {track_name} ({row_count} rows returned)\n{raw_sql};")
        sql_preview = ("\n\n".join(sql_blocks) if sql_blocks else "No SQL evidence available").replace('<', '&lt;').replace('>', '&gt;')

        if verdict == "agree":
            pill = f'<span class="verify-pill verify-pill-agreed" data-finding-id="{finding_id}">&#10003; VERIFIED'
            pill += f'<span class="verify-tip">Independently verified by both OpenAI and Claude. Both models agree this finding is supported by the SQL evidence. {reasoning}</span>'
            pill += '</span>'
            pills_line += f' {pill}'
        elif verdict in ("partially_agree", "disagree"):
            label = "DISPUTED" if verdict == "disagree" else "REVIEW"
            pill = f'<span class="verify-pill verify-pill-contested" data-finding-id="{finding_id}">&#9888; {label}'
            pill += f'<span class="verify-tip">OpenAI and Claude disagree on this finding. {concern}. Please speak with Commercial Finance to verify.</span>'
            pill += '</span>'
            pills_line += f' {pill}'
        # else: no pill shown — only VERIFIED or CONTESTED appear on the dashboard

        pills_line += '</div>'  # close .driver-pills
        h3_tag += pills_line

        # Contested detail block with actions (below pills line)
        if verdict in ("partially_agree", "disagree"):
            h3_tag += f'<div class="verify-contested-detail" data-finding-id="{finding_id}">'
            h3_tag += f'&#9888; {concern}<br>'
            h3_tag += '<span class="verify-cf-note">Please speak with Commercial Finance to verify this finding.</span><br>'
            h3_tag += f'<button class="verify-action-btn" onclick="verifyFinding(\'{finding_id}\',\'verify\')">&#10003; Verify</button> '
            h3_tag += f'<button class="verify-action-btn verify-remove-btn" onclick="verifyFinding(\'{finding_id}\',\'remove\')">&#10007; Remove</button> '
            h3_tag += f'<button class="verify-action-btn" onclick="toggleSqlEvidence(this)">&#128269; View SQL</button>'
            h3_tag += f'<div class="verify-sql-wrap" style="display:none"><button class="verify-action-btn" onclick="copySqlEvidence(this)" style="margin-bottom:4px">&#128203; Copy SQL</button><pre class="verify-sql-evidence">{sql_preview}</pre></div>'
            h3_tag += '</div>'

        h3_tag += f'<div id="{tid}" class="yoy-trend-container"></div>'
        return h3_tag
    html_body = re.sub(r'<h3>(.*?)</h3>', _add_driver_id, html_body)

    # ── Reorder deep dive sections by confidence (High → Medium → Low) ────
    if _all_trends_for_js and _h_to_k:
        try:
            # Split HTML into h3 sections within "What's Driving This"
            h3_pattern = re.compile(r'(<h3\s[^>]*data-driver-idx="(\d+)"[^>]*>.*?)(?=<h3\s|<h2\s|$)', re.DOTALL)
            h3_sections = list(h3_pattern.finditer(html_body))
            if h3_sections:
                first_start = h3_sections[0].start()
                last_end = h3_sections[-1].end()
                before = html_body[:first_start]
                after = html_body[last_end:]
                conf_priority = {"Very High": 0, "High": 1, "Medium": 2, "Low": 3, "Very Low": 4}
                section_list = []
                for m in h3_sections:
                    idx = int(m.group(2))
                    trend_key = _h_to_k.get(idx, '')
                    td = _all_trends_for_js.get(trend_key, {})
                    conf = td.get("confidence", "Low")
                    section_list.append((conf_priority.get(conf, 2), m.group(0)))
                section_list.sort(key=lambda x: x[0])
                html_body = before + ''.join(s[1] for s in section_list) + after
        except Exception as e:
            print(f"  ⚠ Section reorder failed (non-fatal): {e}")

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
        FROM `hx-data-production.insurance.insurance_trading_data`
        WHERE DATE(looker_trans_date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
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
    generated_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

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
{f'<div class="hl-also" style="margin-top:6px;font-size:11px;opacity:0.75">Jump to: {" &middot; ".join(section_links)}</div>' if section_links else ''}
</div>
</div>"""

    return f"""<!DOCTYPE html>
<html lang="en" data-generated-utc="{generated_utc}"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trading Covered</title>
<link rel="icon" type="image/png" href="https://dmy0b9oeprz0f.cloudfront.net/holidayextras.co.uk/brand-guidelines/logo-tags/png/better-future.png">
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
{css_content}
</style>
<script src="https://dbq5t2jl0vcpj.cloudfront.net/hx-tracker/tracker-v5-latest.min.js"></script>
<script>tracker.initialise({{env:'production',service:'trading-covered',organisation:'Holiday Extras Limited',lb:false}});</script>
</head><body>
<div id="staging-banner" style="display:none;background:linear-gradient(90deg,#f59e0b,#f97316);color:#000;text-align:center;padding:6px 12px;font-size:12px;font-weight:700;letter-spacing:1px;text-transform:uppercase;position:sticky;top:0;z-index:9999;">&#9888; Staging Environment &mdash; Changes here are not live</div>
<script>if(location.hostname.includes('staging'))document.getElementById('staging-banner').style.display='block';</script>
<div id="stale-banner" style="display:none;background:linear-gradient(90deg,#dc2626,#ef4444);color:#fff;text-align:center;padding:8px 12px;font-size:13px;font-weight:600;position:sticky;top:0;z-index:9998;">&#9888; This briefing may be stale &mdash; generated <span id="stale-age"></span> ago. <a href="https://github.com/JakeOsmond/trading-briefing/actions/workflows/daily-briefing.yml" target="_blank" style="color:#fde68a;text-decoration:underline;margin-left:8px;">Re-run pipeline</a></div>
<script>
(function(){{
  var utc=document.documentElement.getAttribute('data-generated-utc');
  if(!utc)return;
  var gen=new Date(utc);
  var now=new Date();
  var hrs=Math.round((now-gen)/3600000);
  if(hrs>=20){{
    var d=Math.floor(hrs/24),h=hrs%24;
    document.getElementById('stale-age').textContent=d>0?(d+'d '+h+'h'):(h+'h');
    document.getElementById('stale-banner').style.display='block';
  }}
}})();
</script>
<div class="c">

<!-- Banner -->
<div class="banner-wrap">
<img src="tradingCoveredBanner.png" alt="Trading Covered by Holiday Extras" class="banner-img">
<div class="banner-date" id="banner-date"></div>
<script>!function(){{var d=new Date(),days=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'],months=['January','February','March','April','May','June','July','August','September','October','November','December'];document.getElementById('banner-date').textContent=days[d.getDay()]+' '+d.getDate()+' '+months[d.getMonth()]+' '+d.getFullYear()}}()</script>
</div>

<!-- Sticky toolbar — buttons only -->
<div class="hdr">
<div style="display:flex;align-items:center;gap:8px;width:100%;justify-content:flex-end"><button class="refresh-btn" onclick="triggerRefresh()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>Refresh</button><button class="archive-btn" onclick="toggleArchive()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px"><path d="M21 8v13H3V8"/><path d="M1 3h22v5H1z"/><path d="M10 12h4"/></svg>Archive</button><a href="context-manager.html" class="archive-btn" style="text-decoration:none"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>Context</a>{"<span class='inv-badge' onclick='openInvestigations()'>" + str(inv_count) + " investigations<span class='inv-tooltip'>Trading Covered ran <strong>" + str(inv_count) + " automated checks</strong> across trading data, web analytics, market intelligence, and internal documents before writing this briefing.<br><br><strong>Click to see exactly what was investigated.</strong></span></span>" if inv_count else ""}</div>
</div>

<!-- Headline Tile — one-sentence takeaway -->
{headline_tile_html}

<!-- Key Metrics — cards animate individually, parent wrapper does NOT -->
<div class="section-gap">
<div class="section-title">Key Metrics &mdash; Yesterday vs Last Year</div>
<div class="grid4">
<div class="card glass-card" data-animate="card" style="transition-delay:0ms"><div class="lbl">Yesterday's GP (Post PPC)</div><div class="val" data-countup data-target="{ty.get('total_gp',0):.0f}" data-prefix="&pound;">&pound;{ty.get('total_gp',0):,.0f}</div><div class="chg {"chg-up" if gp_pct>=0 else "chg-dn"}" data-metric>{fmt_pct(gp_pct)} vs same day LY</div><div class="sub">Same day LY: &pound;{ly.get('total_gp',0):,.0f}</div></div>
<div class="card glass-card" data-animate="card" style="transition-delay:80ms"><div class="lbl">Yesterday's Policies</div><div class="val" data-countup data-target="{ty.get('new_policies',0)}" data-prefix="">{ty.get('new_policies',0):,}</div><div class="chg {"chg-up" if vol_pct>=0 else "chg-dn"}" data-metric>{fmt_pct(vol_pct)} vs same day LY</div><div class="sub">Same day LY: {ly.get('new_policies',0):,}</div></div>
<div class="card glass-card" data-animate="card" style="transition-delay:160ms"><div class="lbl">Yesterday's GP / Policy (Post PPC)</div><div class="val" data-countup data-target="{ty.get('avg_gp_per_policy',0):.2f}" data-prefix="&pound;" data-decimals="2">&pound;{ty.get('avg_gp_per_policy',0):.2f}</div><div class="chg {"chg-up" if gppp_pct>=0 else "chg-dn"}" data-metric>{fmt_pct(gppp_pct)} vs same day LY</div><div class="sub">Same day LY: &pound;{ly.get('avg_gp_per_policy',0):.2f}</div></div>
<div class="card glass-card" data-animate="card" style="transition-delay:240ms"><div class="lbl">Yesterday's Avg Price</div><div class="val" data-countup data-target="{ty.get('avg_customer_price',0):.0f}" data-prefix="&pound;">&pound;{ty.get('avg_customer_price',0):.0f}</div><div class="chg {"chg-fl" if abs(price_pct)<2 else ("chg-up" if price_pct>=0 else "chg-dn")}" data-metric>{fmt_pct(price_pct)} vs same day LY</div><div class="sub">Same day LY: &pound;{ly.get('avg_customer_price',0):.0f}</div></div>
</div>
</div>

<!-- Period Comparison — cards animate individually -->
<div class="section-gap">
<div class="section-title">Period Comparison &mdash; GP vs Last Year</div>
<div class="grid3">
<div class="pcard glass-card" data-animate="card" style="transition-delay:0ms"><div class="pl">Yesterday</div><div class="pv" data-countup data-target="{ty.get('total_gp',0):.0f}" data-prefix="&pound;">&pound;{ty.get('total_gp',0):,.0f}</div><div style="color:{status_color(gp_pct)};font-size:14px;font-weight:700" data-metric class="chg {"chg-up" if gp_pct>=0 else "chg-dn"}">{fmt_pct(gp_pct)} YoY</div></div>
<div class="pcard glass-card" data-animate="card" style="transition-delay:80ms"><div class="pl">Trailing 7 Days GP (Post PPC)</div><div class="pv" data-countup data-target="{w_ty.get('total_gp',0):.0f}" data-prefix="&pound;">&pound;{w_ty.get('total_gp',0):,.0f}</div><div style="color:{status_color(w_gp_pct)};font-size:14px;font-weight:700" data-metric class="chg {"chg-up" if w_gp_pct>=0 else "chg-dn"}">{fmt_pct(w_gp_pct)} vs same 7d LY</div></div>
<div class="pcard glass-card" data-animate="card" style="transition-delay:160ms"><div class="pl">Trailing 28 Days GP (Post PPC)</div><div class="pv" data-countup data-target="{m_ty.get('total_gp',0):.0f}" data-prefix="&pound;">&pound;{m_ty.get('total_gp',0):,.0f}</div><div style="color:{status_color(m_gp_pct)};font-size:14px;font-weight:700" data-metric class="chg {"chg-up" if m_gp_pct>=0 else "chg-dn"}">{fmt_pct(m_gp_pct)} vs same 28d LY</div></div>
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

<!-- Context Update (Phase 0) -->
{context_updates.get("section_html", "") if context_updates else ""}

<!-- Investigation Trail -->
{inv_trail_section}

<!-- Footer -->
<div class="foot">
<div>Generated {now_str} (UTC: {generated_utc}) &middot; {inv_count} investigations ({len(track_results) if track_results else 0} tracks + {len(follow_up_log) if follow_up_log else 0} follow-ups) via {MODEL} &middot; Data: BigQuery + Sheets + Drive + Web</div>
<div class="foot-brand">Trading Covered &mdash; Powered by AI for Holiday Extras</div>
</div>

</div><!-- /.c -->

<script>
{js_content.replace("__DRIVER_TRENDS_JSON__", driver_trends_json).replace("__FIELD_DISCOVERY_JSON__", field_discovery_json).replace("__CHART_DATA_JSON__", chart_data_json)}
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
  <div class="chat-resize-handle" id="chatResizeHandle"></div>
  <div class="chat-header">
    <span class="chat-title">Ask Trading Covered</span>
    <button class="chat-close" onclick="toggleChat()">&times;</button>
  </div>
  <div class="chat-messages" id="chatMessages">
    <div class="chat-welcome" id="chatWelcome">
      <strong>Ask Trading Covered</strong><br>
      Ask anything about today's data. Try:<br>
      "What drove the GP decline yesterday?"<br>
      "Show me renewal rate trend for March"<br>
      "Compare direct vs aggregator this week"
    </div>
  </div>
  <div class="chat-input-wrap">
    <input type="text" id="chatInput" class="chat-input" placeholder="Ask anything about today's trading data..."
           onkeydown="if(event.key==='Enter')submitChat()">
    <button class="chat-send" onclick="submitChat()">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:16px;height:16px"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
    </button>
  </div>
</div>

<!-- Chat FAB — always-visible floating button -->
<button class="chat-fab" onclick="toggleChat()" id="chatFab" aria-label="Ask Trading Covered">
  <svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
</button>
<div class="chat-fab-label">Ask Trading Covered</div>

<script>
{js_verify_content}
</script>
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
    parser = argparse.ArgumentParser(description="Trading Covered — Agentic Daily Briefing")
    parser.add_argument("--date", type=str, default=None,
                        help="Run for a specific date (YYYY-MM-DD). Defaults to yesterday.")
    parser.add_argument("--from", dest="from_date", type=str, default=None,
                        help="Start of date range (YYYY-MM-DD). Use with --to.")
    parser.add_argument("--to", dest="to_date", type=str, default=None,
                        help="End of date range (YYYY-MM-DD). Use with --from.")
    parser.add_argument("--domain", type=str, default="insurance",
                        help="Domain to run (default: insurance). Must have domains/{domain}/ folder.")
    args = parser.parse_args()

    # Determine run_date (the "yesterday" equivalent — the most recent trading day to analyse)
    if args.date:
        run_date = date.fromisoformat(args.date)
    elif args.from_date and args.to_date:
        # When a range is given, run_date is the end of the range (most recent day)
        run_date = date.fromisoformat(args.to_date)
    else:
        run_date = date.today() - timedelta(days=1)

    # Log domain selection
    print(f"🏷️  Domain: {args.domain}")

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

    _pipeline_start = time.time()

    def _log_phase(name, start):
        elapsed = time.time() - start
        print(f"  ⏱  {name} completed in {elapsed:.1f}s")
        return time.time()

    print("\n🔐 Authenticating...")
    init_services()

    # Phase 0: Context intelligence refresh
    _phase_start = time.time()
    try:
        context_updates = run_context_refresh(run_date)
    except Exception as e:
        print(f"  ⚠ Context refresh failed (non-fatal): {e}")
        context_updates = {"temporary": [], "permanent": [], "section_html": ""}
    _phase_start = _log_phase("Phase 0: Context refresh", _phase_start)

    # Phase 1: Baseline
    _phase_start = time.time()
    baseline = run_baseline_queries(dp)

    for row in baseline["trading"]:
        if row.get("period") == "yesterday_ly":
            print(f"  LY equiv GP:  £{row['total_gp']:,.2f} | Policies: {row['new_policies']}")
        elif row.get("period") == "yesterday":
            print(f"\n  Yesterday GP: £{row['total_gp']:,.2f} | Policies: {row['new_policies']}")

    _phase_start = _log_phase("Phase 1: Baseline queries", _phase_start)

    # Phase 2: Deterministic investigation tracks
    track_results = run_investigation_tracks(dp)
    _phase_start = _log_phase("Phase 2: Investigation tracks", _phase_start)

    # Phase 3: AI analysis of track results
    analysis = run_ai_analysis(baseline, track_results, run_date)
    _phase_start = _log_phase("Phase 3: AI analysis", _phase_start)

    # Phase 4: AI-driven follow-up investigations
    follow_up_results, follow_up_log = run_ai_follow_ups(analysis, baseline, run_date)
    _phase_start = _log_phase("Phase 4: AI follow-ups", _phase_start)

    # Phase 4b: Collect per-driver trend data + statistical confidence
    print("\n📈 Phase 4b: Collecting driver trends & statistical confidence...")
    try:
        driver_trends = collect_driver_trends(analysis, run_date)
    except Exception as e:
        print(f"  ⚠ Driver trend collection failed: {e}")
        driver_trends = {}

    _phase_start = _log_phase("Phase 4b: Driver trends & confidence", _phase_start)

    # Phase 4c: Cross-model verification
    print("\n🔍 Phase 4c: Cross-model verification (Claude vs OpenAI)...")
    try:
        verification = verify_findings(analysis, track_results, follow_up_results)
        agreed = sum(1 for v in verification.values() if v.get("verdict") == "agree")
        contested = sum(1 for v in verification.values() if v.get("verdict") in ("partially_agree", "disagree"))
        print(f"  ✓ Verification: {agreed} agreed, {contested} contested, {len(verification) - agreed - contested} unverified")
    except Exception as e:
        print(f"  ⚠ Verification failed (non-fatal): {e}")
        verification = {}
    _phase_start = _log_phase("Phase 4c: Cross-model verification", _phase_start)

    # Phase 5: Two-pass synthesis (with confidence data)
    briefing = run_synthesis(baseline, analysis, follow_up_results, track_results, run_date, driver_trends)
    _phase_start = _log_phase("Phase 5: Synthesis", _phase_start)

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
    html = generate_dashboard_html(briefing, baseline["trading"], baseline["trend"], today_str, investigation_log=inv_log, run_date=run_date, trend_data_ly=baseline.get("trend_ly", []), driver_trends=driver_trends, verification=verification, context_updates=context_updates)
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

    # Confidence calibration log — tracks confidence vs verification for future analysis
    calibration_path = Path(__file__).resolve().parent / "calibration.jsonl"
    movers = analysis.get("material_movers", [])
    for i, mover in enumerate(movers):
        finding_id = f"finding-{i}"
        trend_key = mover.get("driver", "")
        td = driver_trends.get(trend_key, {}) if driver_trends else {}
        # Find matching trend data by partial name match if exact key fails
        if not td:
            for tk, tv in (driver_trends or {}).items():
                if any(w in tk.lower() for w in trend_key.lower().split()[:3] if len(w) > 3):
                    td = tv
                    break
        vr = verification.get(finding_id, {})
        entry = {
            "date": today_str,
            "finding_id": finding_id,
            "driver": mover.get("driver", ""),
            "impact_gbp": mover.get("impact_gbp_weekly", 0),
            "direction": mover.get("direction", ""),
            "confidence": td.get("confidence", "Unknown"),
            "z_recent": td.get("z_recent", None),
            "z_seasonal": td.get("z_seasonal", None),
            "persistence": td.get("persistence", ""),
            "verification_verdict": vr.get("verdict", "none"),
            "verification_concern": vr.get("concern", None),
        }
        with open(calibration_path, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    if movers:
        print(f"   📊 Calibration log: {len(movers)} entries → calibration.jsonl")

    print(f"\n✅ Briefing saved:")
    print(f"   📄 {md_path}")
    print(f"   🌐 {briefings_dir}/{today_str}.html")
    print(f"   🔍 {briefings_dir}/{today_str}_investigation.json")

    # Generate archive index for the archive viewer
    _generate_archive_index(briefings_dir)

    # Generate context manager page (using standalone script)
    try:
        import subprocess
        subprocess.run([sys.executable, str(Path(__file__).parent / "scripts" / "generate-context-manager.py"), f"{briefings_dir}/context-manager.html"], check=True)
    except Exception as e:
        print(f"   ⚠ Context manager generation failed (non-fatal): {e}")

    # Open in Arc (skip in CI)
    if not os.environ.get("CI"):
        os.system(f'open -a "{BROWSER}" "{briefings_dir}/latest.html"')

    _total_elapsed = time.time() - _pipeline_start
    _mins, _secs = divmod(int(_total_elapsed), 60)
    print(f"\n⏱  Total pipeline time: {_mins}m {_secs}s")
    print("\n" + "=" * 60)
    print(briefing)
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ PIPELINE FAILED: {e}")
        traceback.print_exc()
        sys.exit(1)
