#!/usr/bin/env python3
"""
HX Insurance Trading Morning Briefing
Pulls trading data, web funnel, market intelligence, and recent changes,
then uses OpenAI to produce a diagnostic trading briefing.
"""

import os
import sys
import json
import datetime
from textwrap import dedent

import openai
import markdown
from pathlib import Path
import google.auth
import google.auth.transport.requests
from google.cloud import bigquery
from googleapiclient.discovery import build

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
BQ_PROJECT = "hx-data-production"
POLICIES_TABLE = f"`{BQ_PROJECT}.commercial_finance.insurance_policies_new`"
WEB_TABLE = f"`{BQ_PROJECT}.commercial_finance.insurance_web_utm_4`"
MARKET_SHEET_ID = "1RUasLdbB9OiHPJzQClglC7aY5KMH4P-dnzk4v_h-tsg"
def _load_env():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

_load_env()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL = "gpt-4.1"
BROWSER = "Arc"

# ---------------------------------------------------------------------------
# AUTH HELPERS
# ---------------------------------------------------------------------------

def get_credentials():
    """Get Google credentials from application default credentials."""
    creds, project = google.auth.default(
        scopes=[
            "https://www.googleapis.com/auth/bigquery",
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
    )
    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)
    return creds


def get_bq_client(creds):
    return bigquery.Client(project=BQ_PROJECT, credentials=creds)


def get_sheets_service(creds):
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def get_drive_service(creds):
    return build("drive", "v3", credentials=creds, cache_discovery=False)


# ---------------------------------------------------------------------------
# 1. BIGQUERY — TRADING DATA (364-day comparison)
# ---------------------------------------------------------------------------

TRADING_QUERY = f"""
WITH params AS (
  SELECT
    DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) AS yesterday,
    DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY) AS week_start,
    DATE_SUB(CURRENT_DATE(), INTERVAL 29 DAY) AS month_start
),

-- Yesterday vs 364 days ago
daily_gp AS (
  SELECT
    'yesterday' AS period,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) AS total_gross,
    COUNT(DISTINCT CASE WHEN transaction_type = 'New Issue' THEN policy_id END) AS new_policies,
    COUNT(DISTINCT CASE WHEN transaction_type = 'New Issue' AND policy_type = 'Annual' THEN policy_id END) AS annual_policies,
    COUNT(DISTINCT CASE WHEN transaction_type = 'New Issue' AND policy_type = 'Single' THEN policy_id END) AS single_policies,
    COUNT(DISTINCT CASE WHEN transaction_type = 'Cancellation' THEN policy_id END) AS cancellations,
    AVG(CASE WHEN transaction_type = 'New Issue' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) END) AS avg_gp_per_policy,
    AVG(CASE WHEN transaction_type = 'New Issue' THEN CAST(total_gross_inc_ipt AS FLOAT64) END) AS avg_customer_price
  FROM {POLICIES_TABLE}, params
  WHERE transaction_date = params.yesterday
),

daily_gp_ly AS (
  SELECT
    'yesterday_ly' AS period,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) AS total_gross,
    COUNT(DISTINCT CASE WHEN transaction_type = 'New Issue' THEN policy_id END) AS new_policies,
    COUNT(DISTINCT CASE WHEN transaction_type = 'New Issue' AND policy_type = 'Annual' THEN policy_id END) AS annual_policies,
    COUNT(DISTINCT CASE WHEN transaction_type = 'New Issue' AND policy_type = 'Single' THEN policy_id END) AS single_policies,
    COUNT(DISTINCT CASE WHEN transaction_type = 'Cancellation' THEN policy_id END) AS cancellations,
    AVG(CASE WHEN transaction_type = 'New Issue' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) END) AS avg_gp_per_policy,
    AVG(CASE WHEN transaction_type = 'New Issue' THEN CAST(total_gross_inc_ipt AS FLOAT64) END) AS avg_customer_price
  FROM {POLICIES_TABLE}, params
  WHERE transaction_date = DATE_SUB(params.yesterday, INTERVAL 364 DAY)
),

-- Trailing 7 days vs 364 days ago equivalent
weekly_gp AS (
  SELECT
    'trailing_7d' AS period,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) AS total_gross,
    COUNT(DISTINCT CASE WHEN transaction_type = 'New Issue' THEN policy_id END) AS new_policies,
    COUNT(DISTINCT CASE WHEN transaction_type = 'New Issue' AND policy_type = 'Annual' THEN policy_id END) AS annual_policies,
    COUNT(DISTINCT CASE WHEN transaction_type = 'New Issue' AND policy_type = 'Single' THEN policy_id END) AS single_policies,
    COUNT(DISTINCT CASE WHEN transaction_type = 'Cancellation' THEN policy_id END) AS cancellations,
    AVG(CASE WHEN transaction_type = 'New Issue' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) END) AS avg_gp_per_policy,
    AVG(CASE WHEN transaction_type = 'New Issue' THEN CAST(total_gross_inc_ipt AS FLOAT64) END) AS avg_customer_price
  FROM {POLICIES_TABLE}, params
  WHERE transaction_date BETWEEN params.week_start AND params.yesterday
),

weekly_gp_ly AS (
  SELECT
    'trailing_7d_ly' AS period,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) AS total_gross,
    COUNT(DISTINCT CASE WHEN transaction_type = 'New Issue' THEN policy_id END) AS new_policies,
    COUNT(DISTINCT CASE WHEN transaction_type = 'New Issue' AND policy_type = 'Annual' THEN policy_id END) AS annual_policies,
    COUNT(DISTINCT CASE WHEN transaction_type = 'New Issue' AND policy_type = 'Single' THEN policy_id END) AS single_policies,
    COUNT(DISTINCT CASE WHEN transaction_type = 'Cancellation' THEN policy_id END) AS cancellations,
    AVG(CASE WHEN transaction_type = 'New Issue' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) END) AS avg_gp_per_policy,
    AVG(CASE WHEN transaction_type = 'New Issue' THEN CAST(total_gross_inc_ipt AS FLOAT64) END) AS avg_customer_price
  FROM {POLICIES_TABLE}, params
  WHERE transaction_date BETWEEN DATE_SUB(params.week_start, INTERVAL 364 DAY) AND DATE_SUB(params.yesterday, INTERVAL 364 DAY)
),

-- Trailing 28 days vs 364 days ago equivalent
monthly_gp AS (
  SELECT
    'trailing_28d' AS period,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) AS total_gross,
    COUNT(DISTINCT CASE WHEN transaction_type = 'New Issue' THEN policy_id END) AS new_policies,
    COUNT(DISTINCT CASE WHEN transaction_type = 'New Issue' AND policy_type = 'Annual' THEN policy_id END) AS annual_policies,
    COUNT(DISTINCT CASE WHEN transaction_type = 'New Issue' AND policy_type = 'Single' THEN policy_id END) AS single_policies,
    COUNT(DISTINCT CASE WHEN transaction_type = 'Cancellation' THEN policy_id END) AS cancellations,
    AVG(CASE WHEN transaction_type = 'New Issue' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) END) AS avg_gp_per_policy,
    AVG(CASE WHEN transaction_type = 'New Issue' THEN CAST(total_gross_inc_ipt AS FLOAT64) END) AS avg_customer_price
  FROM {POLICIES_TABLE}, params
  WHERE transaction_date BETWEEN params.month_start AND params.yesterday
),

monthly_gp_ly AS (
  SELECT
    'trailing_28d_ly' AS period,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) AS total_gross,
    COUNT(DISTINCT CASE WHEN transaction_type = 'New Issue' THEN policy_id END) AS new_policies,
    COUNT(DISTINCT CASE WHEN transaction_type = 'New Issue' AND policy_type = 'Annual' THEN policy_id END) AS annual_policies,
    COUNT(DISTINCT CASE WHEN transaction_type = 'New Issue' AND policy_type = 'Single' THEN policy_id END) AS single_policies,
    COUNT(DISTINCT CASE WHEN transaction_type = 'Cancellation' THEN policy_id END) AS cancellations,
    AVG(CASE WHEN transaction_type = 'New Issue' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) END) AS avg_gp_per_policy,
    AVG(CASE WHEN transaction_type = 'New Issue' THEN CAST(total_gross_inc_ipt AS FLOAT64) END) AS avg_customer_price
  FROM {POLICIES_TABLE}, params
  WHERE transaction_date BETWEEN DATE_SUB(params.month_start, INTERVAL 364 DAY) AND DATE_SUB(params.yesterday, INTERVAL 364 DAY)
)

SELECT * FROM daily_gp
UNION ALL SELECT * FROM daily_gp_ly
UNION ALL SELECT * FROM weekly_gp
UNION ALL SELECT * FROM weekly_gp_ly
UNION ALL SELECT * FROM monthly_gp
UNION ALL SELECT * FROM monthly_gp_ly
"""

# ---------------------------------------------------------------------------
# Mix breakdown — policy type, cover level, distribution channel, medical
# ---------------------------------------------------------------------------

MIX_QUERY = f"""
WITH params AS (
  SELECT
    DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) AS yesterday,
    DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY) AS week_start
)

SELECT
  'trailing_7d' AS period,
  policy_type,
  cover_level_name,
  distribution_channel,
  CASE WHEN CAST(max_medical_score AS FLOAT64) > 0 THEN 'Medical' ELSE 'Non-Medical' END AS medical_flag,
  COUNT(DISTINCT CASE WHEN transaction_type = 'New Issue' THEN policy_id END) AS new_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
  AVG(CASE WHEN transaction_type = 'New Issue' THEN CAST(total_gross_inc_ipt AS FLOAT64) END) AS avg_customer_price,
  AVG(CASE WHEN transaction_type = 'New Issue' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) END) AS avg_gp_per_policy
FROM {POLICIES_TABLE}, params
WHERE transaction_date BETWEEN params.week_start AND params.yesterday
GROUP BY policy_type, cover_level_name, distribution_channel, medical_flag
ORDER BY total_gp DESC
"""

# ---------------------------------------------------------------------------
# 2. BIGQUERY — WEB FUNNEL (364-day comparison)
# ---------------------------------------------------------------------------

FUNNEL_QUERY = f"""
WITH params AS (
  SELECT
    DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) AS yesterday,
    DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY) AS week_start
),

-- Trailing 7 days funnel
funnel_ty AS (
  SELECT
    'trailing_7d' AS period,
    booking_flow_stage,
    COUNT(DISTINCT visitor_id) AS unique_visitors,
    COUNT(DISTINCT session_id) AS unique_sessions,
    COUNT(DISTINCT CASE WHEN certificate_id IS NOT NULL THEN session_id END) AS converting_sessions,
    SUM(CAST(total_gp AS FLOAT64)) AS web_total_gp
  FROM {WEB_TABLE}, params
  WHERE session_start_date BETWEEN params.week_start AND params.yesterday
  GROUP BY booking_flow_stage
),

funnel_ly AS (
  SELECT
    'trailing_7d_ly' AS period,
    booking_flow_stage,
    COUNT(DISTINCT visitor_id) AS unique_visitors,
    COUNT(DISTINCT session_id) AS unique_sessions,
    COUNT(DISTINCT CASE WHEN certificate_id IS NOT NULL THEN session_id END) AS converting_sessions,
    SUM(CAST(total_gp AS FLOAT64)) AS web_total_gp
  FROM {WEB_TABLE}, params
  WHERE session_start_date BETWEEN DATE_SUB(params.week_start, INTERVAL 364 DAY) AND DATE_SUB(params.yesterday, INTERVAL 364 DAY)
  GROUP BY booking_flow_stage
),

-- Yesterday only
funnel_yesterday AS (
  SELECT
    'yesterday' AS period,
    booking_flow_stage,
    COUNT(DISTINCT visitor_id) AS unique_visitors,
    COUNT(DISTINCT session_id) AS unique_sessions,
    COUNT(DISTINCT CASE WHEN certificate_id IS NOT NULL THEN session_id END) AS converting_sessions,
    SUM(CAST(total_gp AS FLOAT64)) AS web_total_gp
  FROM {WEB_TABLE}, params
  WHERE session_start_date = params.yesterday
  GROUP BY booking_flow_stage
),

funnel_yesterday_ly AS (
  SELECT
    'yesterday_ly' AS period,
    booking_flow_stage,
    COUNT(DISTINCT visitor_id) AS unique_visitors,
    COUNT(DISTINCT session_id) AS unique_sessions,
    COUNT(DISTINCT CASE WHEN certificate_id IS NOT NULL THEN session_id END) AS converting_sessions,
    SUM(CAST(total_gp AS FLOAT64)) AS web_total_gp
  FROM {WEB_TABLE}, params
  WHERE session_start_date = DATE_SUB(params.yesterday, INTERVAL 364 DAY)
  GROUP BY booking_flow_stage
)

SELECT * FROM funnel_ty
UNION ALL SELECT * FROM funnel_ly
UNION ALL SELECT * FROM funnel_yesterday
UNION ALL SELECT * FROM funnel_yesterday_ly
ORDER BY period, booking_flow_stage
"""

# ---------------------------------------------------------------------------
# Daily trend (last 14 days) for spotting drift
# ---------------------------------------------------------------------------

DAILY_TREND_QUERY = f"""
SELECT
  transaction_date,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS daily_gp,
  COUNT(DISTINCT CASE WHEN transaction_type = 'New Issue' THEN policy_id END) AS new_policies,
  AVG(CASE WHEN transaction_type = 'New Issue' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) END) AS avg_gp_per_policy
FROM {POLICIES_TABLE}
WHERE transaction_date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 15 DAY) AND DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
GROUP BY transaction_date
ORDER BY transaction_date
"""


# ---------------------------------------------------------------------------
# 3. GOOGLE SHEETS — MARKET INTELLIGENCE
# ---------------------------------------------------------------------------

SHEET_RANGES = {
    "ai_insights": "AI Insights!A1:C10",
    "dashboard_metrics": "Dashboard Metrics!A1:D10",
    "dashboard_weekly": "Dashboard Weekly!A1:D200",
    "section_trends": "Dashboard Section Trends!A1:F100",
    "spike_log": "Spike Log!A1:G50",
    "insurance_intent": "Insurance Intent!A1:K500",
}


def fetch_sheets_data(sheets_service):
    """Pull market intelligence from the shared Google Sheet."""
    results = {}
    for key, range_str in SHEET_RANGES.items():
        try:
            resp = (
                sheets_service.spreadsheets()
                .values()
                .get(spreadsheetId=MARKET_SHEET_ID, range=range_str)
                .execute()
            )
            rows = resp.get("values", [])
            if rows:
                headers = rows[0]
                data = [dict(zip(headers, row)) for row in rows[1:]]
                results[key] = data
            else:
                results[key] = []
        except Exception as e:
            results[key] = f"Error: {e}"
    return results


# ---------------------------------------------------------------------------
# 4. GOOGLE DRIVE — RECENT CHANGES
# ---------------------------------------------------------------------------

CHANGE_KEYWORDS = [
    "pricing", "scheme", "campaign", "release", "deploy", "launch",
    "insurance", "trading", "conversion", "test", "experiment",
    "discount", "medical", "annual", "single trip",
]


def scan_drive_changes(drive_service, days_back=7):
    """Scan Google Drive for recently modified docs that might indicate changes."""
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=days_back)).isoformat() + "Z"

    # Search for recently modified docs
    query = f"modifiedTime > '{cutoff}' and mimeType != 'application/vnd.google-apps.folder' and trashed = false"

    try:
        resp = (
            drive_service.files()
            .list(
                q=query,
                fields="files(id, name, mimeType, modifiedTime, lastModifyingUser)",
                orderBy="modifiedTime desc",
                pageSize=50,
            )
            .execute()
        )
        files = resp.get("files", [])
    except Exception as e:
        return f"Error scanning Drive: {e}"

    # Filter for potentially relevant changes
    relevant = []
    for f in files:
        name_lower = f["name"].lower()
        if any(kw in name_lower for kw in CHANGE_KEYWORDS):
            relevant.append({
                "name": f["name"],
                "modified": f["modifiedTime"],
                "modified_by": f.get("lastModifyingUser", {}).get("displayName", "Unknown"),
                "type": f["mimeType"].split(".")[-1] if "." in f["mimeType"] else f["mimeType"],
            })

    return relevant


# ---------------------------------------------------------------------------
# 5. CLAUDE ANALYSIS
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = dedent("""\
    You are an expert insurance trading analyst for Holiday Extras (HX), a UK travel
    extras company selling travel insurance direct and via aggregators/affiliates.

    Your job is to produce a MORNING TRADING BRIEFING that reads like a clear, compelling
    story — not a list of numbers. Jake reads this first thing in the morning. It should
    tell him exactly where things stand, why, and what deserves his attention today.

    KEY DOMAIN RULES:
    - GP (Gross Profit) = total_gross_exc_ipt_ntu_comm, summed across ALL transaction types
      (New Issue + Contra + MTA + Cancellation). Contras are negative. This is the true net GP.
    - Policy volume = COUNT DISTINCT policy_id WHERE transaction_type = 'New Issue'
    - Web users = COUNT DISTINCT visitor_id; sessions = COUNT DISTINCT session_id
    - "Search" stage in the web funnel = where customer SEES a price (key conversion gate)
    - All comparisons use 364 DAYS AGO (not calendar year), matching day-of-week
    - COVID years (2020-2021) are structural breaks — flag but don't compare against
    - The business is highly seasonal — emails go out on the same day each week
    - Annual policies have much higher LTV than Single Trip
    - Medical screening adds complexity and margin
    - Distribution channels: Direct, Aggregator, Partner Referral, Renewals

    FORMAT YOUR OUTPUT AS A CLEAN MARKDOWN DOCUMENT WITH THIS EXACT STRUCTURE:

    ---

    # 🟢/🟡/🔴 HX Insurance Trading Briefing — [Day Date Month Year]

    > **One-sentence summary**: e.g. "GP is down 8% despite selling more policies — margin
    > compression in aggregator annuals is the primary driver."

    ---

    ## The Headline

    A short paragraph (3-4 sentences) summarising the overall trading position. Use actual
    £ figures. Compare yesterday, trailing 7d, and trailing 28d against the 364-day-ago
    equivalent. State clearly whether the business is ahead or behind, and whether the
    trend is improving or worsening. Use a table for the key numbers:

    | Metric | Yesterday | vs LY | 7-Day | vs LY | 28-Day | vs LY |
    |--------|-----------|-------|-------|-------|--------|-------|

    ---

    ## The Story: Why Is This Happening?

    This is the most important section. Write it as a connected narrative, not bullet points.
    Walk through the logic:

    ### Volume vs Value
    Is GP moving because of how many policies you're selling, or how much each one is worth?
    Quantify both.

    ### The Customer Journey
    Where in the funnel is the change happening? Use the web data to trace:
    Arrival → Search (sees price) → Quote → Checkout → Sale.
    Call out conversion rates at each stage vs LY. Where is the biggest gap?

    ### The Mix
    Has the type of business changed? Annual vs single trip, medical vs non-medical,
    cover level, distribution channel. Which segments are growing or shrinking?
    Which are profitable and which aren't?

    ### Pricing & Margin
    What's happening to the average customer price vs the average GP per policy?
    Are customers paying more but HX keeping less? Or vice versa?

    ---

    ## The Market

    What's happening externally? Use the market intelligence data to tell Jake whether
    HX is moving with or against the market. Include search demand trends, competitor
    signals, and any notable external events.

    ---

    ## What Changed This Week

    List recently modified Google Drive documents that might explain trading movements.
    Group by theme (pricing, campaigns, site changes, strategy). Call out anything
    that could have caused the patterns you've identified.

    ---

    ## The 14-Day Picture

    Show the daily GP trend for the last 14 days. Is yesterday an anomaly or part
    of a pattern? Are things getting better or worse? Include a simple ASCII/text
    sparkline or mini table showing the trajectory.

    ---

    ## What To Do Today

    End with 2-3 specific, actionable recommendations. For each one:
    - **What**: the specific thing to investigate or do
    - **Why**: the data point that triggered this recommendation
    - **Expected impact**: what fixing this could mean for GP

    Prioritise by potential GP impact. Be specific — "review aggregator pricing" is
    too vague; "check annual Gold aggregator margin which is showing -£4.75/policy
    vs +£12/policy LY" is actionable.

    ---

    WRITING STYLE:
    - Write in plain English, like a sharp colleague talking to Jake over coffee
    - Use actual numbers everywhere — no vague "slightly up" or "broadly flat"
    - Connect the dots — don't just list facts, explain the cause and effect
    - Be honest about uncertainty — "this could be X or Y, worth checking" is fine
    - Keep it scannable — bold the key numbers, use headers to navigate
    - Total length: aim for 800-1200 words. Enough to be useful, short enough to read in 5 mins
""")


def build_analysis_prompt(trading_data, mix_data, funnel_data, trend_data, market_data, drive_changes):
    """Assemble all data into a prompt for Claude."""
    sections = []

    sections.append("## TRADING DATA (364-day comparison)\n```json\n" + json.dumps(trading_data, indent=2, default=str) + "\n```")
    sections.append("## POLICY MIX BREAKDOWN (trailing 7 days)\n```json\n" + json.dumps(mix_data, indent=2, default=str) + "\n```")
    sections.append("## WEB FUNNEL DATA (364-day comparison)\n```json\n" + json.dumps(funnel_data, indent=2, default=str) + "\n```")
    sections.append("## 14-DAY DAILY GP TREND\n```json\n" + json.dumps(trend_data, indent=2, default=str) + "\n```")
    sections.append("## MARKET INTELLIGENCE\n```json\n" + json.dumps(market_data, indent=2, default=str) + "\n```")
    sections.append("## RECENT GOOGLE DRIVE CHANGES (last 7 days)\n```json\n" + json.dumps(drive_changes, indent=2, default=str) + "\n```")

    today = datetime.date.today().strftime("%A %d %B %Y")
    return f"Today is {today}. Produce the Morning Trading Briefing based on the following data:\n\n" + "\n\n".join(sections)


def generate_dashboard_html(briefing_md, trading_data, trend_data, today_str):
    """Generate a modern styled dashboard HTML from the briefing and raw data."""
    html_body = markdown.markdown(briefing_md, extensions=["tables", "fenced_code"])

    # Extract key metrics for the hero cards
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
        sign = "+" if val >= 0 else ""
        return f"{sign}{val:.1f}%"

    def status_color(val):
        if val >= 2: return "#10b981"
        if val >= -2: return "#f59e0b"
        return "#ef4444"

    gp_pct = pct(ty.get("total_gp", 0), ly.get("total_gp", 1))
    vol_pct = pct(ty.get("new_policies", 0), ly.get("new_policies", 1))
    gppp_pct = pct(ty.get("avg_gp_per_policy", 0), ly.get("avg_gp_per_policy", 1))
    price_pct = pct(ty.get("avg_customer_price", 0), ly.get("avg_customer_price", 1))

    w_gp_pct = pct(w_ty.get("total_gp", 0), w_ly.get("total_gp", 1))
    m_gp_pct = pct(m_ty.get("total_gp", 0), m_ly.get("total_gp", 1))

    # Status indicator
    if m_gp_pct >= 2:
        status_emoji, status_text, status_bg = "&#9679;", "ON TRACK", "#10b981"
    elif m_gp_pct >= -5:
        status_emoji, status_text, status_bg = "&#9679;", "WATCH", "#f59e0b"
    else:
        status_emoji, status_text, status_bg = "&#9679;", "ACTION NEEDED", "#ef4444"

    # Build sparkline SVG from trend data
    if trend_data:
        gp_vals = [float(r.get("daily_gp", 0)) for r in trend_data]
        max_gp = max(gp_vals) if gp_vals else 1
        min_gp = min(gp_vals) if gp_vals else 0
        rng = max_gp - min_gp if max_gp != min_gp else 1
        points = []
        bar_width = 700 / max(len(gp_vals), 1)
        for i, v in enumerate(gp_vals):
            x = i * bar_width + bar_width / 2
            h = ((v - min_gp) / rng) * 80 + 10
            color = "#10b981" if v >= (sum(gp_vals) / len(gp_vals)) else "#ef4444"
            points.append(f'<rect x="{x:.0f}" y="{100-h:.0f}" width="{bar_width*0.7:.0f}" height="{h:.0f}" rx="3" fill="{color}" opacity="0.85"/>')
        sparkline_svg = f'<svg viewBox="0 0 700 100" style="width:100%;height:120px;">{"".join(points)}</svg>'
        # Date labels
        date_labels = ""
        if len(trend_data) > 1:
            first_d = str(trend_data[0].get("transaction_date", ""))[-5:]
            last_d = str(trend_data[-1].get("transaction_date", ""))[-5:]
            date_labels = f'<div style="display:flex;justify-content:space-between;font-size:11px;color:#94a3b8;margin-top:4px;"><span>{first_d}</span><span>{last_d}</span></div>'
    else:
        sparkline_svg = ""
        date_labels = ""

    now_str = datetime.datetime.now().strftime("%H:%M %d %b %Y")
    day_name = datetime.date.today().strftime("%A %d %B %Y")

    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HX Trading Briefing — {today_str}</title>
<style>
  :root {{
    --bg: #0f172a;
    --surface: #1e293b;
    --surface2: #334155;
    --border: #475569;
    --text: #f1f5f9;
    --text-muted: #94a3b8;
    --accent: #3b82f6;
    --green: #10b981;
    --red: #ef4444;
    --amber: #f59e0b;
    --radius: 12px;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
  }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 24px 20px; }}

  /* Header */
  .header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--surface2);
  }}
  .header h1 {{
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.5px;
  }}
  .header h1 span {{ color: var(--accent); }}
  .header .date {{ color: var(--text-muted); font-size: 13px; }}
  .status-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.5px;
    background: {status_bg}20;
    color: {status_bg};
    border: 1px solid {status_bg}40;
  }}
  .status-dot {{ font-size: 10px; }}

  /* Hero cards */
  .hero-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 24px;
  }}
  .hero-card {{
    background: var(--surface);
    border-radius: var(--radius);
    padding: 18px;
    border: 1px solid var(--surface2);
  }}
  .hero-card .label {{ font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px; }}
  .hero-card .value {{ font-size: 26px; font-weight: 700; letter-spacing: -1px; }}
  .hero-card .change {{
    display: inline-block;
    font-size: 13px;
    font-weight: 600;
    margin-top: 4px;
    padding: 2px 8px;
    border-radius: 6px;
  }}
  .change-up {{ background: #10b98120; color: #10b981; }}
  .change-down {{ background: #ef444420; color: #ef4444; }}
  .change-flat {{ background: #f59e0b20; color: #f59e0b; }}
  .hero-card .sub {{ font-size: 11px; color: var(--text-muted); margin-top: 6px; }}

  /* Sparkline section */
  .spark-section {{
    background: var(--surface);
    border-radius: var(--radius);
    padding: 20px;
    border: 1px solid var(--surface2);
    margin-bottom: 24px;
  }}
  .spark-section .title {{ font-size: 13px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; }}

  /* Period comparison row */
  .period-row {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin-bottom: 24px;
  }}
  .period-card {{
    background: var(--surface);
    border-radius: var(--radius);
    padding: 16px;
    border: 1px solid var(--surface2);
    text-align: center;
  }}
  .period-card .period-label {{ font-size: 12px; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
  .period-card .period-gp {{ font-size: 22px; font-weight: 700; margin: 6px 0 2px; }}
  .period-card .period-change {{ font-size: 13px; font-weight: 600; }}

  /* Narrative section */
  .narrative {{
    background: var(--surface);
    border-radius: var(--radius);
    padding: 28px 32px;
    border: 1px solid var(--surface2);
    margin-bottom: 24px;
  }}
  .narrative h1 {{
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 6px;
    color: var(--text);
    display: none;
  }}
  .narrative h2 {{
    font-size: 17px;
    font-weight: 700;
    color: var(--accent);
    margin: 28px 0 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--surface2);
  }}
  .narrative h2:first-of-type {{ margin-top: 0; }}
  .narrative h3 {{
    font-size: 14px;
    font-weight: 700;
    color: var(--text);
    margin: 20px 0 8px;
  }}
  .narrative p {{
    font-size: 14px;
    color: #cbd5e1;
    margin-bottom: 12px;
    line-height: 1.75;
  }}
  .narrative blockquote {{
    border-left: 3px solid var(--accent);
    padding: 12px 16px;
    margin: 16px 0;
    background: var(--accent)10;
    border-radius: 0 8px 8px 0;
    font-weight: 600;
    font-size: 14px;
    color: var(--text);
  }}
  .narrative ul, .narrative ol {{
    padding-left: 20px;
    margin-bottom: 12px;
  }}
  .narrative li {{
    font-size: 14px;
    color: #cbd5e1;
    margin-bottom: 6px;
    line-height: 1.7;
  }}
  .narrative strong {{ color: var(--text); }}
  .narrative em {{ color: var(--text-muted); }}
  .narrative table {{
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 13px;
  }}
  .narrative th {{
    background: var(--surface2);
    color: var(--text);
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .narrative td {{
    padding: 10px 14px;
    border-bottom: 1px solid var(--surface2);
    color: #cbd5e1;
  }}
  .narrative tr:hover td {{ background: var(--surface2)40; }}
  .narrative code {{
    background: var(--surface2);
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 12px;
    color: var(--green);
  }}
  .narrative pre {{
    background: #0f172a;
    padding: 16px;
    border-radius: 8px;
    overflow-x: auto;
    border: 1px solid var(--surface2);
    margin: 12px 0;
  }}
  .narrative pre code {{
    background: none;
    padding: 0;
    color: var(--text-muted);
    font-size: 12px;
    line-height: 1.8;
  }}
  .narrative hr {{ border: none; border-top: 1px solid var(--surface2); margin: 24px 0; }}

  /* Footer */
  .footer {{
    text-align: center;
    padding: 16px;
    color: var(--text-muted);
    font-size: 11px;
    border-top: 1px solid var(--surface2);
    margin-top: 12px;
  }}

  @media (max-width: 768px) {{
    .hero-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .period-row {{ grid-template-columns: 1fr; }}
    .narrative {{ padding: 20px; }}
  }}
</style>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
<div class="container">

  <div class="header">
    <div>
      <h1><span>HX</span> Insurance Trading Briefing</h1>
      <div class="date">{day_name}</div>
    </div>
    <div class="status-badge">
      <span class="status-dot">{status_emoji}</span> {status_text}
    </div>
  </div>

  <div class="hero-grid">
    <div class="hero-card">
      <div class="label">Yesterday GP</div>
      <div class="value">&pound;{ty.get('total_gp', 0):,.0f}</div>
      <div class="change {"change-up" if gp_pct >= 0 else "change-down"}">{fmt_pct(gp_pct)} vs LY</div>
      <div class="sub">LY: &pound;{ly.get('total_gp', 0):,.0f}</div>
    </div>
    <div class="hero-card">
      <div class="label">Policies Sold</div>
      <div class="value">{ty.get('new_policies', 0):,}</div>
      <div class="change {"change-up" if vol_pct >= 0 else "change-down"}">{fmt_pct(vol_pct)} vs LY</div>
      <div class="sub">LY: {ly.get('new_policies', 0):,}</div>
    </div>
    <div class="hero-card">
      <div class="label">GP / Policy</div>
      <div class="value">&pound;{ty.get('avg_gp_per_policy', 0):.2f}</div>
      <div class="change {"change-up" if gppp_pct >= 0 else "change-down"}">{fmt_pct(gppp_pct)} vs LY</div>
      <div class="sub">LY: &pound;{ly.get('avg_gp_per_policy', 0):.2f}</div>
    </div>
    <div class="hero-card">
      <div class="label">Avg Price</div>
      <div class="value">&pound;{ty.get('avg_customer_price', 0):.2f}</div>
      <div class="change {"change-flat" if abs(price_pct) < 2 else ("change-up" if price_pct >= 0 else "change-down")}">{fmt_pct(price_pct)} vs LY</div>
      <div class="sub">LY: &pound;{ly.get('avg_customer_price', 0):.2f}</div>
    </div>
  </div>

  <div class="period-row">
    <div class="period-card">
      <div class="period-label">Yesterday</div>
      <div class="period-gp">&pound;{ty.get('total_gp', 0):,.0f}</div>
      <div class="period-change" style="color:{status_color(gp_pct)}">{fmt_pct(gp_pct)} vs LY</div>
    </div>
    <div class="period-card">
      <div class="period-label">Trailing 7 Days</div>
      <div class="period-gp">&pound;{w_ty.get('total_gp', 0):,.0f}</div>
      <div class="period-change" style="color:{status_color(w_gp_pct)}">{fmt_pct(w_gp_pct)} vs LY</div>
    </div>
    <div class="period-card">
      <div class="period-label">Trailing 28 Days</div>
      <div class="period-gp">&pound;{m_ty.get('total_gp', 0):,.0f}</div>
      <div class="period-change" style="color:{status_color(m_gp_pct)}">{fmt_pct(m_gp_pct)} vs LY</div>
    </div>
  </div>

  <div class="spark-section">
    <div class="title">14-Day GP Trend</div>
    {sparkline_svg}
    {date_labels}
  </div>

  <div class="narrative">
    {html_body}
  </div>

  <div class="footer">
    Generated {now_str} &middot; Data: BigQuery + Google Sheets + Drive &middot; Model: {MODEL}
  </div>

</div>
</body></html>"""


def run_ai_analysis(prompt):
    """Send data to OpenAI and get the briefing."""
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=MODEL,
        max_completion_tokens=8192,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# 6. MAIN
# ---------------------------------------------------------------------------

def run_bq_query(client, query, label=""):
    """Run a BQ query and return results as list of dicts."""
    print(f"  Querying BQ: {label}...")
    job = client.query(query)
    rows = list(job.result())
    return [dict(row) for row in rows]


def main():
    print("=" * 60)
    print("  HX INSURANCE TRADING — MORNING BRIEFING")
    print(f"  {datetime.date.today().strftime('%A %d %B %Y')}")
    print("=" * 60)

    if not OPENAI_API_KEY:
        print("\n⚠️  Set OPENAI_API_KEY environment variable to enable AI analysis.")
        print("   export OPENAI_API_KEY='your-key-here'")
        print("   Running data collection only...\n")

    # Auth
    print("\n🔐 Authenticating...")
    creds = get_credentials()
    bq_client = get_bq_client(creds)
    sheets_svc = get_sheets_service(creds)
    drive_svc = get_drive_service(creds)

    # Collect data
    print("\n📊 Collecting trading data...")
    trading_data = run_bq_query(bq_client, TRADING_QUERY, "GP summary (364-day)")
    mix_data = run_bq_query(bq_client, MIX_QUERY, "Policy mix breakdown")
    trend_data = run_bq_query(bq_client, DAILY_TREND_QUERY, "14-day trend")

    print("\n🌐 Collecting web funnel data...")
    funnel_data = run_bq_query(bq_client, FUNNEL_QUERY, "Web funnel (364-day)")

    print("\n📈 Collecting market intelligence...")
    market_data = fetch_sheets_data(sheets_svc)

    print("\n📂 Scanning Google Drive for recent changes...")
    drive_changes = scan_drive_changes(drive_svc)

    # Output raw data summary
    print("\n" + "-" * 60)
    print("DATA COLLECTION COMPLETE")
    print("-" * 60)

    for row in trading_data:
        if row.get("period") == "yesterday":
            print(f"  Yesterday GP: £{row['total_gp']:,.2f} | Policies: {row['new_policies']}")
        elif row.get("period") == "yesterday_ly":
            print(f"  LY equiv GP:  £{row['total_gp']:,.2f} | Policies: {row['new_policies']}")

    if drive_changes and isinstance(drive_changes, list):
        print(f"\n  Recent Drive changes: {len(drive_changes)} relevant docs modified")
    print("-" * 60)

    if not OPENAI_API_KEY:
        # Dump raw data for inspection
        output_path = "/Users/jake.osmond/tradingTeam/trading-briefing/raw_data.json"
        with open(output_path, "w") as f:
            json.dump({
                "trading": trading_data,
                "mix": mix_data,
                "funnel": funnel_data,
                "trend": trend_data,
                "market": market_data,
                "drive_changes": drive_changes,
            }, f, indent=2, default=str)
        print(f"\n📁 Raw data saved to {output_path}")
        print("   Add OPENAI_API_KEY to generate AI briefing.")
        return

    # AI analysis
    print("\n🤖 Generating AI briefing...")
    prompt = build_analysis_prompt(trading_data, mix_data, funnel_data, trend_data, market_data, drive_changes)
    briefing = run_ai_analysis(prompt)

    # Save briefing
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    briefings_dir = "/Users/jake.osmond/tradingTeam/trading-briefing/briefings"
    os.makedirs(briefings_dir, exist_ok=True)
    output_path = f"{briefings_dir}/{today_str}.md"
    with open(output_path, "w") as f:
        f.write(briefing)
        f.write("\n\n---\n\n")
        f.write(f"*Generated {datetime.datetime.now().strftime('%H:%M %d %b %Y')} | ")
        f.write(f"Data: BigQuery + Google Sheets + Drive | Model: {MODEL}*\n")

    # Also save as "latest" for easy access
    latest_path = f"{briefings_dir}/latest.md"
    with open(latest_path, "w") as f:
        f.write(briefing)
        f.write("\n\n---\n\n")
        f.write(f"*Generated {datetime.datetime.now().strftime('%H:%M %d %b %Y')} | ")
        f.write(f"Data: BigQuery + Google Sheets + Drive | Model: {MODEL}*\n")

    # Generate HTML dashboard version
    html = generate_dashboard_html(briefing, trading_data, trend_data, today_str)
    html_path = f"{briefings_dir}/{today_str}.html"
    latest_html = f"{briefings_dir}/latest.html"
    Path(html_path).write_text(html)
    Path(latest_html).write_text(html)

    # Also save raw data alongside for reference
    raw_path = f"{briefings_dir}/{today_str}_data.json"
    with open(raw_path, "w") as f:
        json.dump({
            "trading": trading_data,
            "mix": mix_data,
            "funnel": funnel_data,
            "trend": trend_data,
            "market": market_data,
            "drive_changes": drive_changes,
        }, f, indent=2, default=str)

    print(f"\n✅ Briefing saved to {output_path}")
    print(f"   Also available at {latest_path}")
    print(f"   Raw data at {raw_path}")

    # Output to terminal too
    print("\n" + "=" * 60)
    print(briefing)
    print("=" * 60)


if __name__ == "__main__":
    main()
