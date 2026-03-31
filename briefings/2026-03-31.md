---
# HX Trading Briefing — 30 Mar 2026

## Direct was the problem over the last 7 days vs the same week last year: GP was about £150k, down £19k or 11%, because we got more traffic but fewer people reached quotes and each direct sale made less.

---

## At a Glance

- 🔴 **Direct Single dragged hardest** — Over the last 7 days vs the same week last year, Direct Single GP fell about £13k, with policies up 6% but average GP down from about £23 to £16 as quote reach weakened and margins got squeezed.
- 🔴 **Direct Annual also slipped** — Over the last 7 days vs the same week last year, Direct Annual GP fell about £10k and policies fell 11%, even though search demand stayed healthy, so we are missing demand rather than lacking it.
- 🟢 **Renewals helped** — Over the last 7 days vs the same week last year, Renewals added about £9k of GP from 32% more renewed policies, but average GP per renewal dropped from about £41 to £37.
- 🔴 **Bronze mix hurt** — Over the last 7 days vs the same week last year, Bronze GP fell about £17k, mostly because more sales came through lower-value direct single journeys.
- 🔴 **Partners stayed weak** — Over the last 7 days vs the same week last year, Partner Referral lost about £7k of GP, split between weaker Single traffic and lower Annual value per sale.

---

## What's Driving This

### Direct Single GP deterioration `RECURRING`

Over the last 7 days vs the same week last year, Direct Single lost about £13k of GP. Traffic was not the issue on its own: desktop sessions were up 38% and mobile sessions were up 5%, but fewer visitors reached quotes and average GP per policy fell from about £23 to £16.  
The data shows this is a value problem as much as a funnel problem. Prices were about 10% lower, underwriter cost rose from 45% to 50% of gross, discounting deepened, and this has been negative on 9 of the last 10 days.

```sql-dig
SELECT
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_gp_per_policy,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_price
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-23' AND '2026-03-30'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single';
```

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same week last year, Direct Annual GP fell about £10k and policy volume fell 11%. Traffic rose, but fewer annual sessions made it through to booked policies, so the issue is conversion and capture, not lack of interest.  
This is strategically bad because annual growth is how we invest in future renewal income. The data shows this has been negative on 8 of the last 10 days, with average GP per policy down from about £50 to £45 as underwriter cost and discounting both rose.

```sql-dig
SELECT
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_gp_per_policy,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_price
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-23' AND '2026-03-30'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual';
```

### Bronze cover level GP compression `RECURRING`

Over the last 7 days vs the same week last year, Bronze GP fell about £17k, the biggest cover-level drag in the book. This was mostly a direct single issue, where we sold a cheaper mix and average GP dropped from about £22 to £16.  
The data shows customers are buying down into cheaper cover while price-sensitive demand stays high. That fits the wider search picture, with cheap insurance terms rising sharply.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_gp_per_policy,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_price
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-23' AND '2026-03-30'
  AND cover_level_name = 'Bronze'
GROUP BY 1,2
ORDER BY gp DESC;
```

### Renewals GP growth `EMERGING`

Over the last 7 days vs the same week last year, Renewals added about £9k of GP, rising from about £51k to £60k. That came from 32% more renewed policies, which is good news.  
The watch-out is value per renewal. Over the last 7 days vs the same week last year, average GP per renewed policy fell from about £41 to £37, so we offset weakness elsewhere with more renewals but made less on each one.

```sql-dig
SELECT
  booking_source,
  SUM(policy_count) AS renewed_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-23' AND '2026-03-30'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY 1
ORDER BY gp DESC;
```

### Renewed policy average GP erosion `EMERGING`

Over the last 7 days vs the same week last year, renewed policies made about £37 each versus £41 last year, leaking about £7k of GP even while total renewal GP rose.  
This looks like lower renewal value rather than weaker demand. Journey reporting on renewals is still being fixed internally, so the direction is clear but the exact operational cause needs care.

```sql-dig
SELECT
  SUM(policy_count) AS renewed_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_gp_per_policy,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_price
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-23' AND '2026-03-30'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual';
```

### Partner Referral Annual GP decline `EMERGING`

Over the last 7 days vs the same week last year, Partner Referral Annual lost about £4k of GP. Volume was down about 10% and average GP per policy fell from about £74 to £51.  
Because this is annual business, lower volume matters more than the day-one margin. We are missing acquisition into future renewals here, and each sale is also worth less today.

```sql-dig
SELECT
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_gp_per_policy,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_price,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_commission
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-23' AND '2026-03-30'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual';
```

### Partner Referral Single volume-led GP decline `NEW`

Over the last 7 days vs the same week last year, Partner Referral Single lost about £3k of GP because policy volume fell 35%. Value per sale improved, so this looks like a traffic problem more than a pricing problem.  
That lines up with weaker cruise and partner demand in the market. This one looks newer and less entrenched than the direct issues.

```sql-dig
SELECT
  product,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-23' AND '2026-03-30'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1
ORDER BY policies DESC;
```

### Aggregator Single GP erosion despite volume growth `NEW`

Over the last 7 days vs the same week last year, Aggregator Single GP fell about £900 even though policies rose 26%. We sold more, but average GP per policy almost halved from about £3.30 to £1.90.  
This is single-trip business, so thin day-one margin matters. Over the last 7 days vs the same week last year, day-one GP after PPC was about £2.4k, estimated future insurance GP was about £0, estimated other HX GP was about £0, and total 13-month customer value stayed about £2.4k, so there is no extra future value bailing this out.

```sql-dig
SELECT
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_gp_per_policy,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_price,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_commission
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-23' AND '2026-03-30'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single';
```

---

## Customer Search Intent

Insurance demand is still outpacing holiday demand. “Holiday insurance” is up 121% YoY ([Google Trends](https://trends.google.com/explore?q=holiday%20insurance&date=2024-03-30%202026-03-30&geo=GB)) versus “book holiday” up 42% YoY ([Google Trends](https://trends.google.com/explore?q=book%20holiday&date=2024-03-30%202026-03-30&geo=GB)), and annual demand is still healthy with “annual travel insurance” up 25% YoY ([Google Trends](https://trends.google.com/explore?q=annual%20travel%20insurance&date=2024-03-30%202026-03-30&geo=GB)).  
The big signal is price sensitivity. “Cheap holiday insurance” is up 746% YoY ([Google Trends](https://trends.google.com/explore?q=cheap%20holiday%20insurance&date=2024-03-30%202026-03-30&geo=GB)), “credit card travel insurance” is up 496% YoY ([Google Trends](https://trends.google.com/explore?q=credit%20card%20travel%20insurance&date=2024-03-30%202026-03-30&geo=GB)), and comparison shopping is active through terms like “MoneySupermarket travel insurance” up 195% YoY ([Google Trends](https://trends.google.com/explore?q=MoneySupermarket%20travel%20insurance&date=2024-03-30%202026-03-30&geo=GB)).  
Safety concern is elevated too, with “travel advice FCDO” up 608% YoY ([Google Trends](https://trends.google.com/explore?q=travel%20advice%20FCDO&date=2024-03-30%202026-03-30&geo=GB)). Net: demand is there, but customers want cheaper cover and are shopping harder.

---

## News & Market Context

The Iran conflict is still pushing customers toward shorter-lead trips and away from committing to annual cover. **Source:** AI Insights — current market events context.  
Search CTRs for Direct Travel and Cruise have stayed strong since the conflict started, so weak direct GP looks more like HX funnel and value capture than a category demand problem. **Source:** Internal — Weekly Pricing Updates, 2026-03-25.  
Summer demand is still softer than short-lead demand, with bookings inside 21 days holding up better. **Source:** Internal — UKD Trading 51: WC 16th Mar 26, 2026-03-29.  
Partner demand also looks weak, with Carnival still running at about 80% of last year and key partners seeing lower website traffic. **Source:** Internal — Insurance Weekly Trading w/c 09/03/2026, 2026-03-26; 2026-03-25.  
Late-March pricing changes are live across direct, aggregator and cruise products, so some of this week’s margin movement may reflect active repricing and discounting. **Source:** Internal — Weekly Pricing Updates, 2026-03-25.  
Renewals journey reporting is still being fixed, so be careful pinning renewal value changes on one exact operational cause. **Source:** Internal — WIP: Trading Dataset for Renewals — Amendments, 2026-03-30.

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Audit the direct mobile and desktop funnel from landing to search results today, and roll back any growth tests hurting quote reach if they are suppressing session-to-search | Over the last 7 days vs the same week last year, Direct Single lost about £13k and Direct Annual lost about £10k while traffic rose but fewer users reached quotes | ~£23k/week |
| 2 | Reprice or cut discount depth on Direct Bronze Single journeys first, especially mobile, where value per converted session has dropped hardest | Over the last 7 days vs the same week last year, Bronze GP fell about £17k and Direct Single average GP fell from about £23 to £16 | ~£13k/week |
| 3 | Protect Direct Annual conversion even if day-one margin stays thin, by fixing annual quote capture rather than pushing price up | Over the last 7 days vs the same week last year, Direct Annual volume was down 11% in a category where annual search demand was still up 25% YoY | ~£10k/week |
| 4 | Review renewal pricing and discount depth on this week’s annual renewal batches, split by booking source, before weaker value per policy beds in | Over the last 7 days vs the same week last year, renewal GP per policy fell from about £41 to £37, worth about £7k | ~£7k/week |
| 5 | Set a firmer pricing floor on Aggregator Single, especially low-value classic and bronze quotes, unless we can prove extra future value from new customers | Over the last 7 days vs the same week last year, Aggregator Single lost about £900 of GP and total 13-month customer value was only about £2.4k, the same as day-one GP | ~£1k/week |

---
*Generated 09:26 31 Mar 2026 | Tracks: 29 + Follow-ups: 27 | Model: gpt-5.4*
