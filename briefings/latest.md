---
# HX Trading Briefing — 26 Mar 2026

## Over the last 7 days vs the same week last year, GP was down hard again, and the biggest damage came from Direct Single where weaker quote reach, worse desktop conversion, and lower-value Bronze/Silver sales all hit at once.

---

## At a Glance

- 🔴 **7-day GP down** — Over the last 7 days GP was £135k, down £33k vs the same week last year, about 20% worse, with average GP per policy down from £23 to £20.
- 🔴 **Yesterday was weak too** — Yesterday GP was £17k, down £10k vs the same day last year, about 37% worse, as we sold 880 policies vs 1,030 last year and made about £19 each vs £26.
- 🔴 **Direct is doing most of the damage** — Over the last 7 days vs the same week last year, Direct Single GP fell £15k and Direct Annual GP fell £11k, driven by weaker quote reach and much worse desktop conversion.
- 🔴 **Europe mix is dragging value** — Over the last 7 days vs the same week last year, Europe GP fell £24k on only 3% fewer policies, so we are still selling but making less on each sale.
- 🟡 **Aggregator annual is still an investment** — Over the last 7 days vs the same week last year, Aggregator Annual day-one GP was a £4.8k loss, improved from an £8.0k loss last year, but Track 29 shows total 13-month customer value still stayed at about -£4.8k.

---

## What's Driving This

### Desktop direct web conversion deterioration `RECURRING`

Over the last 7 days vs the same week last year, desktop Direct sessions were up 24%, but session-to-search fell from 14% to 13% and search-to-book fell from 43% to 30%, so extra traffic did not turn into sales. This is clearly a conversion problem, not a demand problem, and the findings show it has been negative on 10 of the last 10 trading days.

```sql-dig
SELECT
  device_type,
  COUNT(DISTINCT CASE WHEN session_start_date BETWEEN '2026-03-19' AND '2026-03-26' THEN session_id END) AS ty_sessions,
  COUNT(DISTINCT CASE WHEN session_start_date BETWEEN '2026-03-19' AND '2026-03-26' AND page_type = 'search_results' THEN session_id END) AS ty_search_sessions,
  COUNT(DISTINCT CASE WHEN session_start_date BETWEEN '2026-03-19' AND '2026-03-26' AND booking_flow_stage = 'Just_Booked' THEN session_id END) AS ty_booked_sessions,
  COUNT(DISTINCT CASE WHEN session_start_date BETWEEN '2025-03-20' AND '2025-03-27' THEN session_id END) AS ly_sessions,
  COUNT(DISTINCT CASE WHEN session_start_date BETWEEN '2025-03-20' AND '2025-03-27' AND page_type = 'search_results' THEN session_id END) AS ly_search_sessions,
  COUNT(DISTINCT CASE WHEN session_start_date BETWEEN '2025-03-20' AND '2025-03-27' AND booking_flow_stage = 'Just_Booked' THEN session_id END) AS ly_booked_sessions
FROM `hx-data-production.commercial_finance.insurance_web_utm_4`
WHERE channel = 'Direct'
GROUP BY 1;
```

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, Direct Single GP fell £15k to £31k. Policies were down 9% from 2,081 to 1,893, and average GP per policy fell from £22 to £16 because mobile and tablet traffic fell, desktop mix grew, quote reach weakened, and underwriter cost and discounts ate more of the sale value. This is clearly structural rather than a one-off, with the findings showing it was negative on 9 of the last 10 trading days.

```sql-dig
SELECT
  DATE(looker_trans_date) AS trans_date,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE distribution_channel = 'Direct'
  AND policy_type = 'Single'
  AND DATE(looker_trans_date) BETWEEN '2026-03-19' AND '2026-03-26'
GROUP BY 1
ORDER BY 1;
```

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same week last year, Direct Annual GP fell £11k to £37k. Policies were down 9% from 861 to 784, and average GP per policy fell from £55 to £47 as quote reach weakened and desktop booked sessions fell despite more desktop traffic. Annual is still a strategic acquisition route, so the issue here is not the annual strategy itself. The issue is weaker direct conversion and lower yield on core Bronze and Silver annual products.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE distribution_channel = 'Direct'
  AND policy_type = 'Annual'
  AND DATE(looker_trans_date) BETWEEN '2026-03-19' AND '2026-03-26'
GROUP BY 1
ORDER BY gp DESC;
```

### Europe destination GP decline `RECURRING`

Over the last 7 days vs the same week last year, Europe GP fell £24k to £86k on 4,884 policies vs 5,021 last year, only 3% lower. That tells us demand held up better than value, and the drag came from lower-margin product mix and weaker GP per sale rather than traffic disappearing.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-19' AND '2026-03-26'
GROUP BY 1
ORDER BY gp DESC;
```

### Bronze cover-level GP decline `RECURRING`

Over the last 7 days vs the same week last year, Bronze GP fell £19k to £28k. Policies were down from 2,170 to 1,777, and average GP per policy fell from £22 to £16, so this is both fewer sales and weaker sale quality. The findings show this is a major part of the Direct Single problem, especially in core mobile single-trip schemes.

```sql-dig
SELECT
  scheme_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE cover_level_name = 'Bronze'
  AND DATE(looker_trans_date) BETWEEN '2026-03-19' AND '2026-03-26'
GROUP BY 1
ORDER BY gp DESC;
```

### Partner Referral Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, Partner Referral Single GP fell £5k to £13k. Policies dropped from 931 to 591, while GP per policy improved from £19 to £21, so this is a traffic and partner-demand problem rather than a pricing problem. The likely read-through is weaker cruise partner traffic and CTA placement, which fits current Carnival and P&O softness.

```sql-dig
SELECT
  agent_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
  AND DATE(looker_trans_date) BETWEEN '2026-03-19' AND '2026-03-26'
GROUP BY 1
ORDER BY gp DESC
LIMIT 20;
```

### Silver cover-level GP decline `RECURRING`

Over the last 7 days vs the same week last year, Silver GP fell £9k to £50k. Policies were down 8%, and average GP per policy fell from £37 to £33, which points to the same mainstream Direct weakness seen in Bronze, just with a smaller hit.

```sql-dig
SELECT
  scheme_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE cover_level_name = 'Silver'
  AND DATE(looker_trans_date) BETWEEN '2026-03-19' AND '2026-03-26'
GROUP BY 1
ORDER BY gp DESC;
```

### Renewals GP decline `EMERGING`

Over the last 7 days vs the same week last year, Renewals GP was down about £2k at £51k. This looks smaller and lower-confidence than the other movers, and current renewal journey data caveats mean we should treat it as emerging rather than call it a real retention issue yet.

```sql-dig
SELECT
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
  AND DATE(looker_trans_date) BETWEEN '2026-03-19' AND '2026-03-26'
GROUP BY 1;
```

---

## Customer Search Intent

Insurance search demand still looks healthy, which matters because it says the market is there and our weakness is more about conversion and competitiveness. [Holiday insurance](https://trends.google.com/explore?q=travel%20insurance,holiday%20insurance,annual%20travel%20insurance,single%20trip%20travel%20insurance,travel%20insurance%20comparison&date=2024-03-26%202026-03-26&geo=GB) searches were up about 125% YoY, while [book holiday](https://trends.google.com/explore?q=book%20holiday&date=2024-03-26%202026-03-26&geo=GB) was up about 42%, and [travel insurance](https://trends.google.com/explore?q=travel%20insurance&date=2024-03-26%202026-03-26&geo=GB) was up about 61%. Concern-led demand is especially strong: [travel insurance cancellation cover](https://trends.google.com/explore?q=travel%20insurance%20cancellation%20cover&date=2024-03-26%202026-03-26&geo=GB) was up about 1,160% YoY. Competitor interest was strong too, with [MoneySuperMarket travel insurance](https://trends.google.com/explore?q=MoneySupermarket%20travel%20insurance&date=2024-03-26%202026-03-26&geo=GB) up about 203%, [Staysure holiday insurance](https://trends.google.com/explore?q=Staysure%20holiday%20insurance&date=2024-03-26%202026-03-26&geo=GB) up about 158%, and [Post Office holiday insurance](https://trends.google.com/explore?q=Post%20Office%20holiday%20insurance&date=2024-03-26%202026-03-26&geo=GB) up about 43%.

---

## News & Market Context

The Iran conflict is still disrupting travel confidence and pushing people toward single-trip buying and shorter lead times rather than annual commitment. **Source:** Internal — Travel Events Log; **Source:** Internal — Current Market Events — Active Context. Carnival partner demand is soft, with Carnival running at about 80% of last year and partner traffic down about 20%, which fits the Partner Referral Single weakness. **Source:** Internal — Insurance Weekly Trading w/c 09/03/2026; **Source:** Internal — Current Market Events — Active Context. Direct pricing should get a bit of help soon, with Ergo rate relief due on 28 March after earlier direct yielding changes on 12 March. **Source:** Internal — Weekly Pricing Updates; **Source:** Drive: 'Insurance Trading - Insights, Product & Pricing Mar26'. Search clickthrough in Direct Travel and Cruise has stayed strong since the Iran conflict started, so the market backdrop is not the main reason Direct is down. **Source:** Drive: 'Weekly Pricing Updates', 2026-03-25. Competition is still intense, and bigger players have strengthened their market position, including All Clear and Post Office. **Source:** Drive: 'Insurance Circle - Nov 2025'.

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Run a desktop Direct funnel check today on quote-to-book drop, starting with search results to checkout on Bronze and Silver | Over the last 7 days vs the same week last year, desktop sessions were up 24% but search-to-book fell from 43% to 30%, which is the clearest fixable loss | ~£8k/week |
| 2 | Rework Direct Single Bronze pricing and quote visibility first, then retest on the biggest mobile single schemes | Over the last 7 days vs the same week last year, Direct Single GP fell £15k and Bronze GP fell £19k, with core Bronze single GP per session roughly halving in the findings | ~£8k/week |
| 3 | Keep Aggregator Annual volume, but stop any deeper drift in the genuinely negative cohorts and review new-customer mix | Over the last 7 days vs the same week last year, Aggregator Annual improved its day-one loss to -£4.8k, but Track 29 still shows total 13-month customer value at about -£4.8k, so this acquisition is still not paying back | ~£3k/week |
| 4 | Escalate Carnival and P&O CTA placement and traffic with partner managers this week | Over the last 7 days vs the same week last year, Partner Referral Single GP fell £5k almost entirely because policies dropped from 931 to 591 while GP per policy improved | ~£5k/week |
| 5 | Add stronger cancellation-cover messaging into Direct landing pages and paid search copy | Search demand for cancellation cover was up about 1,160% YoY, so clearer reassurance should help quote reach and conversion in a disruption-led market | ~£2k/week |

---
*Generated 14:22 27 Mar 2026 | Tracks: 29 + Follow-ups: 29 | Model: gpt-5.4*
