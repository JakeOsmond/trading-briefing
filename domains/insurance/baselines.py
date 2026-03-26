"""Insurance baseline SQL queries — Phase 1 data extraction.

Each new domain needs its own baselines.py with the same function signatures.
"""
from datetime import timedelta


def get_tables(bq_project):
    """Return fully qualified table names for this domain."""
    return {
        "policies": f"`{bq_project}.insurance.insurance_trading_data`",
        "web": f"`{bq_project}.commercial_finance.insurance_web_utm_4`",
    }


# Module-level aliases set by init_tables()
POLICIES_TABLE = None
WEB_TABLE = None


def init_tables(bq_project):
    """Initialize module-level table constants."""
    global POLICIES_TABLE, WEB_TABLE
    tables = get_tables(bq_project)
    POLICIES_TABLE = tables["policies"]
    WEB_TABLE = tables["web"]
    return POLICIES_TABLE, WEB_TABLE


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
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(CAST(ppc_cost_per_policy AS FLOAT64), 0)) AS total_gp,
    SUM(policy_count) AS new_policies,
    SUM(CASE WHEN policy_type='Annual' THEN policy_count ELSE 0 END) AS annual_policies,
    SUM(CASE WHEN policy_type='Single' THEN policy_count ELSE 0 END) AS single_policies,
    SUM(CASE WHEN transaction_type='Cancellation' THEN policy_count ELSE 0 END) AS cancellations,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(CAST(ppc_cost_per_policy AS FLOAT64), 0)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_customer_price
  FROM {POLICIES_TABLE} WHERE DATE(looker_trans_date) = DATE('{dp["yesterday"]}')
),
daily_ly AS (
  SELECT 'yesterday_ly' AS period,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(CAST(ppc_cost_per_policy AS FLOAT64), 0)) AS total_gp,
    SUM(policy_count) AS new_policies,
    SUM(CASE WHEN policy_type='Annual' THEN policy_count ELSE 0 END) AS annual_policies,
    SUM(CASE WHEN policy_type='Single' THEN policy_count ELSE 0 END) AS single_policies,
    SUM(CASE WHEN transaction_type='Cancellation' THEN policy_count ELSE 0 END) AS cancellations,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(CAST(ppc_cost_per_policy AS FLOAT64), 0)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_customer_price
  FROM {POLICIES_TABLE} WHERE DATE(looker_trans_date) = DATE('{dp["yesterday_ly"]}')
),
weekly AS (
  SELECT 'trailing_7d' AS period,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(CAST(ppc_cost_per_policy AS FLOAT64), 0)) AS total_gp,
    SUM(policy_count) AS new_policies,
    SUM(CASE WHEN policy_type='Annual' THEN policy_count ELSE 0 END) AS annual_policies,
    SUM(CASE WHEN policy_type='Single' THEN policy_count ELSE 0 END) AS single_policies,
    SUM(CASE WHEN transaction_type='Cancellation' THEN policy_count ELSE 0 END) AS cancellations,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(CAST(ppc_cost_per_policy AS FLOAT64), 0)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_customer_price
  FROM {POLICIES_TABLE} WHERE DATE(looker_trans_date) BETWEEN DATE('{dp["week_start"]}') AND DATE('{dp["yesterday"]}')
),
weekly_ly AS (
  SELECT 'trailing_7d_ly' AS period,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(CAST(ppc_cost_per_policy AS FLOAT64), 0)) AS total_gp,
    SUM(policy_count) AS new_policies,
    SUM(CASE WHEN policy_type='Annual' THEN policy_count ELSE 0 END) AS annual_policies,
    SUM(CASE WHEN policy_type='Single' THEN policy_count ELSE 0 END) AS single_policies,
    SUM(CASE WHEN transaction_type='Cancellation' THEN policy_count ELSE 0 END) AS cancellations,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(CAST(ppc_cost_per_policy AS FLOAT64), 0)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_customer_price
  FROM {POLICIES_TABLE} WHERE DATE(looker_trans_date) BETWEEN DATE('{dp["week_start_ly"]}') AND DATE('{dp["yesterday_ly"]}')
),
monthly AS (
  SELECT 'trailing_28d' AS period,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(CAST(ppc_cost_per_policy AS FLOAT64), 0)) AS total_gp,
    SUM(policy_count) AS new_policies,
    SUM(CASE WHEN policy_type='Annual' THEN policy_count ELSE 0 END) AS annual_policies,
    SUM(CASE WHEN policy_type='Single' THEN policy_count ELSE 0 END) AS single_policies,
    SUM(CASE WHEN transaction_type='Cancellation' THEN policy_count ELSE 0 END) AS cancellations,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(CAST(ppc_cost_per_policy AS FLOAT64), 0)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_customer_price
  FROM {POLICIES_TABLE} WHERE DATE(looker_trans_date) BETWEEN DATE('{dp["month_start"]}') AND DATE('{dp["yesterday"]}')
),
monthly_ly AS (
  SELECT 'trailing_28d_ly' AS period,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(CAST(ppc_cost_per_policy AS FLOAT64), 0)) AS total_gp,
    SUM(policy_count) AS new_policies,
    SUM(CASE WHEN policy_type='Annual' THEN policy_count ELSE 0 END) AS annual_policies,
    SUM(CASE WHEN policy_type='Single' THEN policy_count ELSE 0 END) AS single_policies,
    SUM(CASE WHEN transaction_type='Cancellation' THEN policy_count ELSE 0 END) AS cancellations,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(CAST(ppc_cost_per_policy AS FLOAT64), 0)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_customer_price
  FROM {POLICIES_TABLE} WHERE DATE(looker_trans_date) BETWEEN DATE('{dp["month_start_ly"]}') AND DATE('{dp["yesterday_ly"]}')
)
SELECT * FROM daily UNION ALL SELECT * FROM daily_ly
UNION ALL SELECT * FROM weekly UNION ALL SELECT * FROM weekly_ly
UNION ALL SELECT * FROM monthly UNION ALL SELECT * FROM monthly_ly
"""


def build_baseline_trend_sql(dp):
    """Build the 14-day trend SQL with explicit date literals."""
    return f"""
SELECT DATE(looker_trans_date) AS transaction_date,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(CAST(ppc_cost_per_policy AS FLOAT64), 0)) AS daily_gp,
  SUM(policy_count) AS new_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(CAST(ppc_cost_per_policy AS FLOAT64), 0)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM {POLICIES_TABLE}
WHERE DATE(looker_trans_date) BETWEEN DATE('{dp["trend_start"]}') AND DATE('{dp["yesterday"]}')
GROUP BY DATE(looker_trans_date) ORDER BY DATE(looker_trans_date)
"""


def build_baseline_trend_ly_sql(dp):
    """Build the 14-day LY trend SQL (364-day offset) for YoY chart comparison."""
    return f"""
SELECT DATE(looker_trans_date) AS transaction_date,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(CAST(ppc_cost_per_policy AS FLOAT64), 0)) AS daily_gp,
  SUM(policy_count) AS new_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(CAST(ppc_cost_per_policy AS FLOAT64), 0)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM {POLICIES_TABLE}
WHERE DATE(looker_trans_date) BETWEEN DATE('{dp["trend_start_ly"]}') AND DATE('{dp["yesterday_ly"]}')
GROUP BY DATE(looker_trans_date) ORDER BY DATE(looker_trans_date)
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
  COUNT(DISTINCT CASE WHEN page_type = 'search_results' THEN session_id END) AS search_results_sessions,
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
  COUNT(DISTINCT CASE WHEN page_type = 'search_results' THEN session_id END),
  COUNT(DISTINCT CASE WHEN event_type = 'click' AND event_name = 'book-button' THEN session_id END),
  COUNT(DISTINCT CASE WHEN med_session = TRUE THEN session_id END),
  COUNT(DISTINCT CASE WHEN Multiple_search = 'Yes' THEN session_id END)
FROM {WEB_TABLE}
WHERE session_start_date BETWEEN DATE('{dp["week_start_ly"]}') AND DATE('{dp["yesterday_ly"]}')
  AND device_type IN ('mobile', 'computer', 'tablet')
GROUP BY device_type
"""
