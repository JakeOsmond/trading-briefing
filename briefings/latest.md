---
# HX Trading Briefing — 17 Mar 2026

## Direct single and direct annual drove most of the damage over the last 7 days vs the same period last year, as quote-entry weakened and single-trip value per sale fell.

---

## At a Glance

- 🔴 **Total GP down** — Yesterday GP was £19k, down £3k vs the same day last year, about 12% worse; over the last 7 days GP was £139k, down £24k vs the same period last year, about 15% worse.
- 🔴 **Direct single hurt most** — Over the last 7 days vs the same period last year, direct single GP fell £11.7k to £30.3k, mainly because fewer visitors got through to quote and average GP per policy fell to £17 from £22.
- 🔴 **Direct annual weaker** — Over the last 7 days vs the same period last year, direct annual GP fell £10.6k to £37.3k because we sold 159 fewer annuals, which means weaker acquisition into future renewal income.
- 🟢 **Renewals helped** — Over the last 7 days vs the same period last year, annual renewals GP was up £8k to £53k, which offset some of the direct weakness.
- 🔴 **Europe lost value** — Over the last 7 days vs the same period last year, Europe GP fell £20k to £89k, with volumes down only about 90 policies, so most of the hit came from weaker GP per policy.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same period last year, direct single GP fell £11.7k to £30.3k. Traffic was mixed, with mobile sessions down 2% but desktop up 34%, and the real problem was weaker quote-entry: mobile session-to-search fell to 16% from 20% and desktop fell to 12% from 15%, while average GP per policy dropped to £17 from £22; this has been negative on 8 of the last 10 trading days.

```sql-dig
SELECT
  p.distribution_channel,
  p.policy_type,
  SUM(p.policy_count) AS policies,
  SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new` p
WHERE p.transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND p.distribution_channel = 'Direct'
  AND p.policy_type = 'Single'
GROUP BY 1,2;
```

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same period last year, direct annual GP fell £10.6k to £37.3k, with volumes down 18% to 729 policies from 888. Traffic was mixed, but fewer people got through to quote on both devices and annual booked sessions fell on mobile and desktop, so we are investing less into future renewal income; this has been negative on 7 of the last 10 trading days.

```sql-dig
SELECT
  p.distribution_channel,
  p.policy_type,
  SUM(p.policy_count) AS policies,
  SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new` p
WHERE p.transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND p.distribution_channel = 'Direct'
  AND p.policy_type = 'Annual'
GROUP BY 1,2;
```

### Europe destination GP decline `EMERGING`

Over the last 7 days vs the same period last year, Europe GP fell £20k to £89k, while volumes were down only about 90 policies. The data points to weaker value per policy rather than a traffic collapse, which may mean more customers are buying cheaper Europe cover or lower tiers.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND destination_group = 'Europe'
GROUP BY 1;
```

### Gold cover level GP decline `EMERGING`

Over the last 7 days vs the same period last year, Gold GP fell £7k to £46k because we sold about 130 fewer policies, while GP per policy held broadly flat. That suggests shoppers may be trading down rather than us losing value on each sale.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND cover_level_name = 'Gold'
GROUP BY 1;
```

### Partner Referral Single GP decline `EMERGING`

Over the last 7 days vs the same period last year, partner single GP fell £6k to £13k, with volumes down about 240 policies. This looks mainly traffic-led from weaker partner demand, and cruise softness may be part of it.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Partner Referral Annual GP decline `NEW`

Over the last 7 days vs the same period last year, partner annual GP fell £5k to £8k, with volumes down about 30 and GP per policy down about £21. This may be more than traffic alone, because commission per policy also rose, but confidence is still low.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_commission,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

### Aggregator Single GP decline `NEW`

Over the last 7 days vs the same period last year, aggregator single GP was only down about £500, but volumes were up about 50% and average GP per policy fell to about £2. The traffic is clearly there through comparison sites, but we are converting a lot more low-value single-trip business.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_commission,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Renewals Annual GP growth `NEW`

Over the last 7 days vs the same period last year, renewal GP was up £8k to £53k. That is good news and likely means better retention, although the exact renewal-rate read is still lower confidence.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS renewed_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS renewed_gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_renewed_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

## Customer Search Intent

According to Google Sheets data, travel insurance search intent is up about 63% YoY, and insurance-specific searches are up about 74% YoY, so demand is there even though our GP is softer. According to AI Insights, comparison-led searches are rising much faster: “travel insurance comparison” is up 400% YoY, “travel insurance deals” is up 986% YoY, and “cheapest” terms are up 141% YoY over the latest tracked period, which fits the weaker value we are seeing in single-trip sales. According to the Insurance Intent and Dashboard Metrics tabs, Spain, Greece and Italy are leading destination demand, while ski-related searches are up 188% YoY, pointing to late winter and Easter cover demand. According to Dashboard Metrics, insurance demand is now 3 points ahead of holiday demand vs 1 point last year, which suggests customers are actively checking cover earlier in the journey. **Source:** Google Sheets — Insurance Intent tab; **Source:** Google Sheets — Dashboard Metrics tab; **Source:** AI Insights — trend, deep_dive, channels.

## News & Market Context

According to AI Insights, airline and holiday demand is still supportive, with cheap-flight and holiday-deal interest both up, especially for Spain, Greece and Italy. According to [Yahoo News](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai), British Airways is still suspending several Middle East routes, which keeps disruption and insurance questions front of mind. According to [The Week](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war?utm_source=openai), standard policies often exclude war-related losses, which makes customers more price- and wording-sensitive when they compare cover. According to [Saga](https://www.saga.co.uk/travel-insurance/middle-east-travel-disruption?utm_source=openai), rivals are leaning into disruption support, including automatic extensions for stranded travellers. According to AI Insights, Staysure search interest is up 52% YoY and AllClear is up 33% YoY, especially with older and medical customers. That lines up with what we are seeing over the last 7 days: demand is there, but more of it is comparison-led and harder to monetise. **Source:** AI Insights — what_matters, deep_dive, news.

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Check the direct quote-entry funnel by device today and fix the biggest mobile and desktop drop between landing and search on single-trip journeys | Direct single lost £11.7k over the last 7 days vs last year, and both mobile and desktop session-to-search got worse | ~£12k/week |
| 2 | Review annual direct landing pages and quote-start steps this week to recover annual conversions | Direct annual lost £10.6k over the last 7 days vs last year because fewer people reached quote and booked, which means less future renewal income | ~£11k/week |
| 3 | Rework quote-page messaging to defend Gold and higher tiers, focusing on cover value not just price | Gold GP lost £7k over the last 7 days vs last year because customers bought fewer higher-tier policies | ~£7k/week |
| 4 | Speak to the biggest partner accounts this week, especially cruise-led partners, to find where referral traffic has dropped | Partner single lost £6k over the last 7 days vs last year, and this looks mainly traffic-led | ~£6k/week |
| 5 | Review partner annual placements with rising commission per policy and pull back any that are clearly uneconomic | Partner annual lost £5k over the last 7 days vs last year, and commission per policy appears to have risen | ~£5k/week |

---

---
*Generated 15:14 18 Mar 2026 | Tracks: 23 + Follow-ups: 37 | Model: gpt-5.4*
