# Insurance Data Quirks

## Policy Counting
- The policy table has **multiple rows per booking** (New Issue, Contra, MTA Debit, Cancellation, Client Details Update, UnCancel).
- Never use COUNT(*) or COUNT(DISTINCT policy_id) for policy counts — this gives inflated figures.
- Always use **SUM(policy_count)** — the `policy_count` column is signed (positive for new, negative for cancellations), so SUM gives the correct net count.

## Financial Aggregation
- Financial columns are stored as BIGNUMERIC and must be cast to FLOAT64 for aggregation.
- Never use AVG() on financial columns — because rows are not one-per-policy, AVG() is meaningless.
- Correct average GP per policy: `SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0)`.

## Web Data
- The web table (`insurance_web_utm_4`) is **web-only** — it does not include call centre or offline data.
- Use `booking_source` in the policies table to distinguish web vs phone sales.
- For unique users: `COUNT(DISTINCT visitor_id)`. For unique sessions: `COUNT(DISTINCT session_id)`.

## Session Flags
- **used_syd** — customer used the "Screen Your Destinations" tool (about 0.3% of sessions)
- **med_session** — session involved medical screening (about 12% of sessions)
- **Multiple_search** — customer did multiple quote searches in one session (about 3.5%; values are 'Yes'/'No')
