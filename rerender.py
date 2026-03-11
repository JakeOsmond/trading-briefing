#!/usr/bin/env python3
"""Re-render latest.html with real BigQuery data but existing markdown briefing."""
import sys, os, datetime, json, re
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
    BQ_CLIENT, _infer_segment_filter, _compute_persistence
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

# ── Collect driver trend data from BigQuery ──
driver_trends = {}
analysis_data = inv_log.get("analysis", {})
movers = analysis_data.get("material_movers", [])

# Parse movers from raw_analysis if needed (same logic as generate_dashboard_html)
if not movers and "raw_analysis" in analysis_data:
    raw_str = analysis_data["raw_analysis"]
    def _fix_json(s):
        s = re.sub(r'(?<=\d),(?=\d{3})', '', s)
        s = re.sub(r'(?<=\d)_(?=\d)', '', s)
        s = re.sub(r',\s*([}\]])', r'\1', s)
        return s
    try:
        parsed = json.loads(_fix_json(raw_str))
        movers = parsed.get("material_movers", [])
    except (json.JSONDecodeError, ValueError):
        mm_match = re.search(r'"material_movers"\s*:\s*\[', _fix_json(raw_str))
        if mm_match:
            fixed = _fix_json(raw_str)
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

if movers:
    start_date = yesterday - datetime.timedelta(days=13)
    ly_start = start_date - datetime.timedelta(days=364)
    ly_end = yesterday - datetime.timedelta(days=364)

    print(f"\n📈 Fetching trend data for {len(movers)} movers...")
    for i, mover in enumerate(movers):
        driver_name = mover.get("driver", f"Mover {i+1}")
        seg_filter = mover.get("segment_filter", "") or _infer_segment_filter(mover)
        if not seg_filter:
            print(f"  ⚠ No segment_filter for '{driver_name}' — skipping")
            continue

        metric_expr = "SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))"
        metric_label = "GP"

        sql_ty = f"""SELECT transaction_date AS dt, {metric_expr} AS val
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '{start_date}' AND '{yesterday}' AND {seg_filter}
GROUP BY transaction_date ORDER BY transaction_date"""

        sql_ly = f"""SELECT transaction_date AS dt, {metric_expr} AS val
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '{ly_start}' AND '{ly_end}' AND {seg_filter}
GROUP BY transaction_date ORDER BY transaction_date"""

        try:
            ty_rows = [dict(r) for r in BQ_CLIENT.query(sql_ty).result()]
            ly_rows = [dict(r) for r in BQ_CLIENT.query(sql_ly).result()]
            ty_parsed = [{"dt": str(r["dt"]), "val": float(r["val"])} for r in ty_rows]
            ly_parsed = [{"dt": str(r["dt"]), "val": float(r["val"])} for r in ly_rows]

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
            print(f"  ✓ {driver_name}: {label} ({consistent}/{total} days)")
        except Exception as e:
            print(f"  ⚠ Failed for '{driver_name}': {e}")

    print(f"  ✓ Collected trends for {len(driver_trends)} drivers")

html = generate_dashboard_html(
    md, trading, trend, run_date.strftime("%Y-%m-%d"),
    investigation_log=inv_log, run_date=run_date,
    trend_data_ly=trend_ly, driver_trends=driver_trends
)

out_path = briefings_dir / "latest.html"
out_path.write_text(html)
print(f"\n✓ Re-rendered {out_path} ({len(html):,} bytes)")
print(f"  Refresh http://localhost:8788/latest.html")
