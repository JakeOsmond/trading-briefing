# BigQuery Schema Knowledge

_This is the authoritative source for table schemas. Both `agentic_briefing.py` and `functions/api/ask.js` should reflect this. If you update schema knowledge, update both._

## `hx-data-production.commercial_finance.insurance_policies_new`

The ONLY policy table. Project: hx-data-production. Dataset: commercial_finance.

### Critical Rules
- ALWAYS use the full backtick-quoted name
- Use `SUM(policy_count)` not `COUNT(*)` for policy counts
- Use `SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))` for GP — NEVER `AVG()`
- Avg GP = `SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0)`
- YoY = 364-day offset (matches day-of-week)
- `transaction_date` is DATE type — use directly, no `EXTRACT()`

### Key Columns
- `transaction_date` — when the policy was sold
- `travel_end_date` — policy expiry date (used for renewal rate calculation)
- `policy_type` — Annual or Single
- `distribution_channel` — Direct, Aggregator, Partner Referral, Renewals
- `insurance_group` — sub-channel detail (Direct - Standard, Direct - Medical, etc.)
- `cover_level_name` — Bronze, Classic, Silver, Gold, Deluxe, Elite, Adventure
- `booking_source` — Web or Phone
- `device_type` — Mobile, Desktop, Tablet
- `medical_split` — medical condition declared
- `max_medical_score_grouped` — medical risk grouping
- `customer_type` — New, Existing, Lapsed, Re-engaged
- `policy_count` — signed count (positive for new, negative for cancellations)
- `total_gross_exc_ipt_ntu_comm` — THIS IS GP (gross profit)
- `total_gross_inc_ipt` — customer price
- `total_discount_value` — discount applied
- `total_paid_commission_value` — commission paid to partner
- `total_net_to_underwriter_inc_gadget` — underwriter cost

## `hx-data-production.commercial_finance.insurance_web_utm_4`

Web analytics. Direct channel ONLY (no aggregator/renewal web data).

### Key Columns
- `session_id`, `visitor_id` — session and user identifiers
- `device_type` — Mobile, Desktop, Tablet
- `booking_flow_stage` — funnel stage (Landing, Gatekeeper, Screening, Search, etc.)
- `session_start_date` — date of session
- `page_type`, `event_name` — page and event tracking
- `customer_type` — New, Existing, Lapsed, Re-engaged

### Counting
- Sessions = `COUNT(DISTINCT session_id)`
- Users = `COUNT(DISTINCT visitor_id)`
