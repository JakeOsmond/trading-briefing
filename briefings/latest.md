---
# HX Trading Briefing — 11 Mar 2026

## GP is down hard yesterday and over the last 7 days vs last year because we’re getting plenty of demand but too many visitors still aren’t reaching a quote, while single-trip margins keep getting squeezed.

---

## At a Glance

- 🔴 **Overall GP** — Yesterday GP was £16k, down £10k vs the same day last year, about 39% worse; over the last 7 days GP was £154k, down £26k vs the same period last year, about 14% worse.
- 🔴 **Europe weaker** — Over the last 7 days Europe GP was £102k, down £13k vs last year, about 12% worse, with policy count flat so we made less on each sale.
- 🔴 **Worldwide weaker** — Over the last 7 days Worldwide GP was £52k, down £12k vs last year, about 19% worse, again mostly margin not volume.
- 🔴 **Direct single-trip** — Over the last 7 days direct single-trip GP was £38k, down £7k vs last year, about 15% worse; traffic rose overall but fewer people got through to a quote and single-trip margin got squeezed.
- 🔴 **Partner single-trip** — Over the last 7 days partner single-trip GP was £14k, down £8k vs last year, about 36% worse, with both referral volume and margin per policy down.

---

## What's Driving This

### Europe destination GP decline `RECURRING`

Over the last 7 days Europe GP was down £13k vs last year, with policy count basically flat at 5,005 vs 4,992. This is mostly margin squeeze, not demand loss, and it matches a market where cheap-flight traffic is up but customers are buying more price-led cover.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND destination_group = 'Europe'
GROUP BY 1
UNION ALL
SELECT
  destination_group,
  SUM(policy_count),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2025-03-05' AND '2025-03-12'
  AND destination_group = 'Europe'
GROUP BY 1
```

### Worldwide destination GP decline `RECURRING`

Over the last 7 days Worldwide GP was down £12k vs last year, with policies only down 3%, so the real hit is average GP per policy down 17%. This has been negative on 8 of the last 10 days and lines up with weaker pricing power on expensive long-haul cover.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND destination_group = 'Worldwide'
GROUP BY 1
UNION ALL
SELECT
  destination_group,
  SUM(policy_count),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2025-03-05' AND '2025-03-12'
  AND destination_group = 'Worldwide'
GROUP BY 1
```

### Partner referral single-trip GP decline `RECURRING`

Over the last 7 days partner single-trip GP was down £8k vs last year, about 36% worse, with policies down 28% and average GP down 10%. This is a double hit: less partner traffic coming through and worse economics on each single-trip sale.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1,2
UNION ALL
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2025-03-05' AND '2025-03-12'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1,2
```

### Silver Main Annual Med HX scheme decline `RECURRING`

Over the last 7 days this scheme was down £8k vs last year, with volume down 16% and average GP down 21%. Traffic and conversion both weakened here, especially quote reach on web, so we lost profitable annual sales we do want.

```sql-dig
SELECT
  scheme_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND scheme_name = 'Silver Main Annual Med HX'
GROUP BY 1
UNION ALL
SELECT
  scheme_name,
  SUM(policy_count),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2025-03-05' AND '2025-03-12'
  AND scheme_name = 'Silver Main Annual Med HX'
GROUP BY 1
```

### Direct single-trip GP decline `RECURRING`

Over the last 7 days direct single-trip GP was down £7k vs last year, even though policies were up slightly. Traffic rose because desktop sessions were up, but quote reach got worse on both mobile and desktop, and average GP per policy fell 18%, so this is now 8 bad days in the last 10.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1,2
UNION ALL
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2025-03-05' AND '2025-03-12'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1,2
```

### Renewals annual GP decline `RECURRING`

Over the last 7 days renewals annual GP was down £1k vs last year, even though policy count was up 9%, which is good for the book. The issue is lower value per renewal, with average GP down 10% and heavier discounting, so we’re keeping the customer but earning less this cycle.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY 1,2
UNION ALL
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2025-03-05' AND '2025-03-12'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY 1,2
```

### Aggregator single-trip GP decline despite volume growth `EMERGING`

Over the last 7 days aggregator single-trip GP was down only about £500 vs last year, but policies jumped 42%, so we’re clearly winning traffic there. The problem is those extra sales are low-value: average GP per policy nearly halved, which fits a comparison market getting more price-led.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
GROUP BY 1,2
UNION ALL
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2025-03-05' AND '2025-03-12'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
GROUP BY 1,2
```

### Silver cover level GP decline `EMERGING`

Over the last 7 days Silver GP was down £4k vs last year, with volume only down 3%, so this is mainly weaker value inside the tier. It looks like a mix problem rather than a Silver problem on its own, driven by weaker annual medical and single-trip journeys inside the tier.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND cover_level_name = 'Silver'
GROUP BY 1
UNION ALL
SELECT
  cover_level_name,
  SUM(policy_count),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2025-03-05' AND '2025-03-12'
  AND cover_level_name = 'Silver'
GROUP BY 1
```

---

## Customer Search Intent

According to Google Sheets dashboard metrics, insurance search intent is up 74% vs last year, ahead of holiday search growth at 50%, so the market is there. According to AI Insights, “travel insurance comparison” is up 826%, “compare travel insurance” is up 31%, and “travel insurance over 70” is up 216%, which tells us shoppers are both more price-led and more medical-led. According to AI Insights, HX brand search is down 9%, so stronger market demand is not automatically flowing to us. According to Dashboard Metrics, insurance search index is 11.5 now vs 6.6 last year, with 4-week momentum up 38%, which supports the view that this is still building into Easter. **Source:** Google Sheets — Insurance Intent tab. **Source:** Google Sheets — Dashboard Metrics tab. **Source:** AI Insights — what_matters, trend, yoy.

---

## News & Market Context

According to AI Insights, cheap-flight search is up 135%, which helps explain why Europe volumes are holding up even while margin falls. According to AP, Spain has hit record visitor numbers, and AI Insights say easyJet and Jet2 are adding Med capacity, which keeps travel demand strong but price-sensitive. **Source:** [AP News](https://apnews.com/article/5aad69a1bab3ebcbe1bb56d07e19d17b?utm_source=openai)  
According to AI Insights, Staysure and AllClear are growing fast in older and medical-led searches, which fits our weaker direct capture in valuable segments. **Source:** AI Insights — channels, deep_dive.  
According to WTW, healthcare cost inflation is staying in double digits into 2026, which raises the cost of cover and makes margin discipline harder on long-haul and medical trips. **Source:** [WTW](https://www.wtwco.com/en-gb/news/2025/11/double-digit-healthcare-cost-increases-projected-to-persist-into-2026-and-beyond?utm_source=openai)  
According to BA and ABI-linked reporting, Middle East disruption is still active and standard war exclusions still apply, so customer questions may rise even if that is not yet a trading driver. **Source:** [Yahoo/BA update](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai), [The Week](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war?utm_source=openai)

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Fix direct quote-entry on mobile and desktop for single-trip pages this week | Direct single-trip lost about £7k/week and session-to-search is the main break | ~£7k/week |
| 2 | Push price-led PPC and landing pages for compare/cheap/over-70 terms into direct annual and medical journeys | Search demand is up 74% YoY but HX brand capture is soft | ~£8k/week |
| 3 | Review partner single-trip deals by referral source and cut back weak commission-heavy traffic | Partner single-trip lost about £8k/week on lower volume and worse margin | ~£8k/week |
| 4 | Rework Silver Main Annual Med HX quote path and pricing proof points | This scheme alone is down about £8k/week from weaker traffic, conversion and yield | ~£8k/week |
| 5 | Tighten aggregator single-trip floor economics, not volume | We sold 42% more policies but made about £500 less GP over the last 7 days | ~£1k/week |

---

_Generated 06:57 12 Mar 2026 | 22 investigation tracks | gpt-5_

---
*Generated 16:48 12 Mar 2026 | Tracks: 22 + Follow-ups: 29 | Model: gpt-5.4*
