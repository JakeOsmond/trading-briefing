#!/usr/bin/env python3
"""Re-render latest.html with real BigQuery data but existing markdown briefing."""
import sys, os, datetime, json
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path

# Set credentials before importing
os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS",
    os.path.expanduser("~/.config/gcloud/application_default_credentials.json"))

# Import what we need from the main module
import agentic_briefing
agentic_briefing.init_services()
from agentic_briefing import (
    generate_dashboard_html, build_baseline_trading_sql,
    build_baseline_trend_sql, build_baseline_trend_ly_sql,
    BQ_CLIENT
)

briefings_dir = Path(__file__).parent / "briefings"
md = (briefings_dir / "latest.md").read_text()

# Use today's date for fresh data
run_date = datetime.date.today()
yesterday = run_date - datetime.timedelta(days=1)
dp = {
    "yesterday": yesterday.strftime("%Y-%m-%d"),
    "yesterday_ly": (yesterday - datetime.timedelta(days=364)).strftime("%Y-%m-%d"),
    "week_start": (yesterday - datetime.timedelta(days=6)).strftime("%Y-%m-%d"),
    "week_start_ly": (yesterday - datetime.timedelta(days=6+364)).strftime("%Y-%m-%d"),
    "week_end": yesterday.strftime("%Y-%m-%d"),
    "week_end_ly": (yesterday - datetime.timedelta(days=364)).strftime("%Y-%m-%d"),
    "month_start": (yesterday - datetime.timedelta(days=27)).strftime("%Y-%m-%d"),
    "month_start_ly": (yesterday - datetime.timedelta(days=27+364)).strftime("%Y-%m-%d"),
    "month_end": yesterday.strftime("%Y-%m-%d"),
    "month_end_ly": (yesterday - datetime.timedelta(days=364)).strftime("%Y-%m-%d"),
    "trend_start": (yesterday - datetime.timedelta(days=13)).strftime("%Y-%m-%d"),
    "trend_end": yesterday.strftime("%Y-%m-%d"),
    "trend_start_ly": (yesterday - datetime.timedelta(days=13+364)).strftime("%Y-%m-%d"),
    "trend_end_ly": (yesterday - datetime.timedelta(days=364)).strftime("%Y-%m-%d"),
}

print("📊 Fetching real data from BigQuery...")
trading = [dict(r) for r in BQ_CLIENT.query(build_baseline_trading_sql(dp)).result()]
print(f"  ✓ Trading: {len(trading)} rows")
trend = [dict(r) for r in BQ_CLIENT.query(build_baseline_trend_sql(dp)).result()]
print(f"  ✓ Trend: {len(trend)} rows")
trend_ly = [dict(r) for r in BQ_CLIENT.query(build_baseline_trend_ly_sql(dp)).result()]
print(f"  ✓ Trend LY: {len(trend_ly)} rows")

# Load investigation log — try today first, then fall back to most recent
inv_path = briefings_dir / f"{run_date.strftime('%Y-%m-%d')}_investigation.json"
if not inv_path.exists():
    # Find most recent investigation log
    inv_files = sorted(briefings_dir.glob("*_investigation.json"), reverse=True)
    if inv_files:
        inv_path = inv_files[0]

if inv_path.exists():
    inv_log = json.loads(inv_path.read_text())
    print(f"  ✓ Investigation log loaded from {inv_path.name}")
else:
    inv_log = {
        "track_results": {f"track_{i}": {"name": f"Track {i}", "row_count": 10} for i in range(22)},
        "analysis": {"material_movers": []},
        "follow_up_results": {},
        "follow_up_log": [{"round": i} for i in range(15)],
    }
    print(f"  ⚠ No investigation log found, using stub")

html = generate_dashboard_html(
    md, trading, trend, run_date.strftime("%Y-%m-%d"),
    investigation_log=inv_log, run_date=run_date,
    trend_data_ly=trend_ly, driver_trends={}
)

out_path = briefings_dir / "latest.html"
out_path.write_text(html)
print(f"\n✓ Re-rendered {out_path} ({len(html):,} bytes)")
print(f"  Refresh http://localhost:8788/latest.html")
