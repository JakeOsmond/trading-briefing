---
# HX Trading Briefing — 10 Mar 2026

## GP takes a £13k hit over the last week, led by Single Trip losses in Partner and Direct channels; renewal annual growth cushions the fall.

---

## At a Glance

- 🔴 **Partner Single Trip GP down** — Lost £6.1k over the last 7 days vs last year (down 26%); sharp drop in volume, margins flat.
- 🔴 **Direct Single Trip GP down** — Dropped £3.8k (down 9%) over the last 7 days; conversion and average GP per policy both fell hard, traffic flat.
- 🔴 **Aggregator Single Trip GP down** — Lost £600 this week vs last year, despite 44% more volume; unit margin halved as policy mix shifted downmarket.
- 🟢 **Renewal Annual GP up** — Up £1.4k (up 3%) this week vs last year, with annual renewal volume rising 12% even as per-renewal GP dipped.
- 🟢 **Partner Annual GP up** — Added £1.1k (up 10%) this week, volume up while margins held steady.

---

## What's Driving This

### Partner Referral Single Trip GP `RECURRING`

GP from Partner-sold single trips is down £6.1k this week vs last year, driven by a steep 27% volume drop (240 fewer sales) across partner agents and cover levels, with average GP per policy flat. This is the seventh decline in ten days, entirely about less partner traffic.

```sql-dig
SELECT agent_code, SUM(policy_count) policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) gp
FROM hx-data-production.commercial_finance.insurance_policies_new
WHERE distribution_channel='Partner Referral' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
GROUP BY agent_code
```

### Direct Single Trip GP `RECURRING`

We lost £3.8k of Direct single trip GP this week vs last year (down 9%), as average GP per policy fell 16% and volume was down 8% (-158 policies). Conversion at the "get a quote" stage dropped sharply (down 15–23% by device); with traffic unchanged, this is now the eighth time in ten days we've seen this pattern and Google search intent for insurance is strong—so the leak is at our conversion funnel.

```sql-dig
SELECT device_type, SUM(policy_count) policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) gp
FROM hx-data-production.commercial_finance.insurance_policies_new
JOIN hx-data-production.commercial_finance.insurance_web_utm_4
USING (policy_id)
WHERE distribution_channel='Direct' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
GROUP BY device_type
```

### Aggregator Single Trip GP `RECURRING`

GP from Aggregator single trips is down £600 this week vs last year; volume surged 44% (up 331 sales) but almost all growth is in ultra-low-value products, with unit GP per policy dropping to £1.70 (off by 48%). Price competition is still hammering returns—this is a recurring seven-in-ten-days squeeze.

```sql-dig
SELECT scheme_name, SUM(policy_count) policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) gp
FROM hx-data-production.commercial_finance.insurance_policies_new
WHERE distribution_channel='Aggregator' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
GROUP BY scheme_name
```

### Direct Annual GP `RECURRING`

Direct Annual GP fell £6.2k this week vs last year, on flat volumes; average GP per policy dropped 12% as customers shifted to lower-tier (Bronze/Silver) plans and took advantage of deeper discounting. This is a deliberate move as we invest in new customers, and has now persisted for seven of the last ten days.

```sql-dig
SELECT cover_level_name, SUM(policy_count) policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) gp
FROM hx-data-production.commercial_finance.insurance_policies_new
WHERE distribution_channel='Direct' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
GROUP BY cover_level_name
```

### Renewals Annual GP `RECURRING`

Renewal annual GP rose £1.4k (up 3%) over the last 7 days vs last year, as renewal volume increased 12%—average GP per policy slid slightly due to modestly higher discounting. This is the ninth week running for positive renewal flow.

```sql-dig
SELECT customer_type, SUM(policy_count) policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) gp
FROM hx-data-production.commercial_finance.insurance_policies_new
WHERE distribution_channel='Renewals' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
GROUP BY customer_type
```

### Partner Referral Annual GP `RECURRING`

Partner-sold annuals are up £1.1k (10%) this week, with volume growth and steady per-policy margin. Gains are spread widely across agents and products.

```sql-dig
SELECT cover_level_name, SUM(policy_count) policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) gp
FROM hx-data-production.commercial_finance.insurance_policies_new
WHERE distribution_channel='Partner Referral' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
GROUP BY cover_level_name
```

### Aggregator Annual GP `RECURRING`

Aggregator annual GP is still negative but less so than last year (improved by £1.1k), as mix shifted slightly up market; policy volume dipped, with most improvement from classic and elite plans. This is a deliberate renewal pipeline investment.

```sql-dig
SELECT scheme_name, SUM(policy_count) policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) gp
FROM hx-data-production.commercial_finance.insurance_policies_new
WHERE distribution_channel='Aggregator' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
GROUP BY scheme_name
```

### Direct Single Trip Volume `RECURRING`

Direct single trip policy volume fell 8% (down 158) this week, nearly all from lower conversion at the "get a quote" step; traffic held flat. This has recurred seven of the last ten days.

```sql-dig
SELECT booking_source, SUM(policy_count) policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) gp
FROM hx-data-production.commercial_finance.insurance_policies_new
WHERE distribution_channel='Direct' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
GROUP BY booking_source
```

---

## Customer Search Intent

According to Google Trends and Insurance Intent data, travel insurance search interest is up 63–74% over last year—the highest ever. Insurance queries now outpace holiday planning searches, with sharp demand for Spain, Greece, and Italy, and hot terms like “pre-existing medical” and “annual multi-trip”. There’s been a notable spike tied to new airline seat releases and EU border checks. Opportunity is real: strong shopping intent, but our web funnel isn’t capturing it as competitors move faster.  
**Source:** [Google Trends](https://trends.google.com), Dashboard Metrics, Insurance Intent tab

---

## News & Market Context

Insurance demand is at a record high, fueled by major airlines (easyJet, Ryanair, Jet2) launching 2026 ticket sales and customers worried by Mediterranean storms, airport strikes, and complex new EU border policies. Medical and cancellation cover is hot, especially for Spain and Mediterranean trips. FCA’s new signposting rules are making aggregator competition fiercer, but extra cost pressure hasn’t hit yet. Saga’s automatic cover extensions for stranded travelers and ongoing British Airways Middle East cancellations are driving more emergency cover purchases. No material internal pricing or tech changes—competitive intensity is externally driven and high.  
**Source:** [AI Insights](https://moneyweek.com/spending-it/travel-holidays/new-spanish-travel-insurance-rule?utm_source=openai), [easyJet sale](https://uk.finance.yahoo.com/news/easyjet-releases-25-million-budget-162457150.html?utm_source=openai), [FCA signposting news](https://www.itij.com/latest/news/amendments-rules-travel-insurance-signposting-system-uk-consumers?utm_source=openai)

---

## Actions

| Priority | What to do                                                          | Why                                      | Worth  |
|----------|---------------------------------------------------------------------|------------------------------------------|--------|
| 1        | Fix session-to-search drop on Direct; run root-cause UX and messaging A/B tests, especially mobile | Funnel block is killing up to £3.8k/week in GP | ~£3.8k/week |
| 2        | Push Paid Search/Google Ads toward Direct Single Trip deep funnel, targeting “quote now” intent | Demand is there (+63–74% YoY) but we’re losing out on conversion | ~£3.0k/week |
| 3        | Tighten aggregator pricing just at the lowest-value single trip tiers | Margin on these policies halved; protect against further race-to-bottom | ~£0.6k/week |
| 4        | Engage top partner agents who fell away—proactively recover lost single trip volume | Partner volume down 27% YoY, worth £6.1k/week | ~£6.1k/week |

---

_Generated 07:11 11 Mar 2026 | 22 investigation tracks | gpt-4_1106_vision_oa_

---

---
*Generated 16:25 11 Mar 2026 | Tracks: 22 + Follow-ups: 31 | Model: gpt-4.1*
