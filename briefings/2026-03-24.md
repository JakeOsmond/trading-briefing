---
# HX Trading Briefing — 23 Mar 2026

## GP was soft over the last 7 days vs the same week last year: we made £136k, down £26k or about 16%, mainly because both Direct Annual and Direct Single converted worse even though demand was still there.

---

## At a Glance

- 🔴 **Direct annual down** — Over the last 7 days vs the same week last year, Direct Annual GP fell £13k to £37k, about 27% worse, with desktop traffic up 21% but desktop conversion and value both worse.
- 🔴 **Direct single squeezed** — Over the last 7 days vs the same week last year, Direct Single GP fell £13k to £29k, about 30% worse, because mobile quote reach fell and average GP per policy dropped 21%.
- 🟢 **Renewals paying back** — Over the last 7 days vs the same week last year, Renewals GP rose £8k to £53k, up 18%, driven by a much better renewal rate.
- 🔴 **Partner cruise softer** — Over the last 7 days vs the same week last year, Partner Referral Single GP fell £5k to £13k, down 28%, mostly from weaker Carnival-linked cruise volume.
- 🟡 **Aggregator mix got cheaper** — Over the last 7 days vs the same week last year, Aggregator Single GP fell about £500 to £2k despite 62% more policies, because we sold far more low-value Europe singles.

---

## What's Driving This

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same week last year, Direct Annual GP fell £13k to £37k. Traffic was not the issue: desktop sessions were up 21%, but desktop booked sessions fell 24% and GP per booked desktop session dropped 23%, so this is a conversion and value leak.  
The data shows weaker desktop annual journeys, especially Bronze and Silver, plus worse cost mix with underwriter cost rising from 47% to 51% of gross. This has been negative on 8 of the last 10 days.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY 1
ORDER BY gp DESC;
```

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, Direct Single GP fell £13k to £29k. Traffic was mixed, but the bigger problem was weaker mobile quote reach and much worse desktop conversion, with average GP per policy down 21% even though customer price was broadly flat.  
This is margin erosion, not pricing weakness: underwriter cost rose from 46% to 50% of gross and lower-tier single policies got squeezed hardest, especially Bronze. This has been negative on 9 of the last 10 days, and single trip has no renewal payback.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1
ORDER BY policies DESC;
```

### Renewals Annual GP growth `EMERGING`

Over the last 7 days vs the same week last year, Renewals GP rose £8k to £53k, up 18%. Fewer policies were due to expire, but renewal rate improved from 32% to 47%, which more than covered that.  
This may be a real process improvement from recent auto-renew changes, but holiday timing versus last year means keep some caution on the exact size.

```sql-dig
SELECT
  previous_cover_level_name,
  SUM(policy_count) AS renewed_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS renewed_gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND distribution_channel = 'Renewals'
GROUP BY 1
ORDER BY renewed_gp DESC;
```

### Partner Referral Single GP decline `EMERGING`

Over the last 7 days vs the same week last year, Partner Referral Single GP fell £5k to £13k, down 28%. This was mainly a volume hit, with policies down 33%, while average GP improved a little.  
The early read is weaker Carnival-linked cruise demand rather than an HX margin issue, which matches the wider cruise traffic softness in partner channels.

```sql-dig
SELECT
  CASE WHEN product LIKE '%Cruise%' OR scheme_name LIKE '%Cruise%' THEN 'Cruise' ELSE 'Non-Cruise' END AS cruise_flag,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1;
```

### Partner Referral Annual GP decline `NEW`

Over the last 7 days vs the same week last year, Partner Referral Annual GP fell £5k to £7k. We sold fewer policies and made less on each one, especially in cruise annual.  
This may be partner mix noise, but the direction fits the same softer cruise traffic seen in single trip partner sales.

```sql-dig
SELECT
  scheme_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
GROUP BY 1
ORDER BY gp DESC;
```

### Aggregator Annual volume decline reducing investment `NEW`

Over the last 7 days vs the same week last year, Aggregator Annual GP improved by £3k, but only because we sold 27% fewer annual policies at a planned loss. We are investing less in future renewal income.  
That is not a margin problem. It is a volume problem, and on new customers this cut is still negative even after adding estimated 13-month value, so this acquisition is not paying back yet.

```sql-dig
SELECT
  customer_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(COALESCE(est_13m_ins_gp, 0) + COALESCE(est_13m_other_gp, 0)) AS future_value
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Annual'
GROUP BY 1;
```

### Aggregator Single GP decline `NEW`

Over the last 7 days vs the same week last year, Aggregator Single GP fell about £500 to £2k even though policies were up 62%. We sold a lot more, but made about half as much on each sale.  
This looks like cheaper Europe-heavy mix rather than a traffic problem, and it may reflect more price-shopping in the market. Check whether the extra new-customer 13-month value is enough to justify the thinner day-one margin.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
GROUP BY 1;
```

### PPC Direct Web Advertising GP deterioration `NEW`

Over the last 7 days vs the same week last year, PPC looks weaker on day-one GP, especially in Bronze single, while traffic is up. More of that traffic is landing in lower-value Bronze, mainly on mobile.  
This is still low confidence this week, but the broad picture is that existing-customer PPC looks unattractive while the overall PPC machine can still work when new-customer 13-month value is included.

```sql-dig
SELECT
  customer_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(ppc_cost_per_policy, 0) * policy_count) AS gp_post_ppc,
  SUM(COALESCE(est_13m_ins_gp, 0) + COALESCE(est_13m_other_gp, 0)) AS future_value
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND distribution_channel = 'Direct'
  AND insurance_group = 'Web Advertising PPC'
GROUP BY 1;
```

---

## Customer Search Intent

Insurance search demand is still outpacing holiday demand. [Holiday insurance](https://trends.google.com/explore?q=holiday%20insurance&date=2024-03-23%202026-03-23&geo=GB) is up 114% YoY, versus [book holiday](https://trends.google.com/explore?q=book%20holiday&date=2024-03-23%202026-03-23&geo=GB) up 42% YoY.  
The biggest spikes are price-led and disruption-led: [flight cancellation insurance](https://trends.google.com/explore?q=flight%20cancellation%20insurance&date=2024-03-23%202026-03-23&geo=GB) up 767%, [cheap holiday insurance](https://trends.google.com/explore?q=cheap%20holiday%20insurance&date=2024-03-23%202026-03-23&geo=GB) up 368%, and [annual travel cover](https://trends.google.com/explore?q=annual%20travel%20cover&date=2024-03-23%202026-03-23&geo=GB) up 348%.  
Competitor interest is up too, including [Staysure travel insurance](https://trends.google.com/explore?q=Staysure%20travel%20insurance&date=2024-03-23%202026-03-23&geo=GB) and [Post Office travel insurance](https://trends.google.com/explore?q=Post%20Office%20travel%20insurance&date=2024-03-23%202026-03-23&geo=GB). Net: demand is there, but shoppers look more price-led and comparison-led, so this is mostly a capture problem, not a demand problem. Compare [insurance searches](https://trends.google.com/explore?q=travel%20insurance,holiday%20insurance,annual%20travel%20insurance,single%20trip%20travel%20insurance,travel%20insurance%20comparison&date=2024-03-23%202026-03-23&geo=GB) with [holiday searches](https://trends.google.com/explore?q=book%20holiday,cheap%20flights,package%20holiday,all%20inclusive%20holiday,summer%20holiday&date=2024-03-23%202026-03-23&geo=GB).

---

## News & Market Context

British Airways is still not operating several Middle East routes and is offering flexible rebooking, which is likely keeping disruption-related insurance shopping high. **Source:** AI Insights — [news].  
War-related disruption is pushing more people to shop around, but standard policies often exclude war losses, which raises comparison behaviour more than it kills demand. [The Week](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war?utm_source=openai), [Insurance Times](https://www.insurancetimes.co.uk/analysis/briefing-what-does-the-q1-2026-middle-east-conflict-mean-for-travel-insurance/1457907.article).  
That fits our mix: annual commitment looks softer while single-trip demand is still there. **Source:** Internal — Current Market Events — Iran Conflict.  
Cruise is still softer in partner channels. Carnival traffic is down about 20% in our internal context, and specialist cruise product updates only went live on 17 March, so partner cruise weakness is more likely demand-led than product-led right now. **Source:** Internal — [Weekly Pricing Updates]; **Source:** Internal — Current Market Events — Cruise Partner Dynamics.  
Renewals may be getting help from recent auto-renew process changes. **Source:** Internal — [Daily Auto Renewals Tracker].

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Fix desktop Direct Annual checkout and search-to-book on Bronze and Silver | Direct Annual lost £13k/week while desktop sessions were up 21%, so the leak is conversion and value, not traffic | ~£13k/week |
| 2 | Review Direct Single Bronze cost and price setup, then tighten mobile quote-to-search leaks | Direct Single lost £13k/week, average GP per policy fell 21%, and single trip has no renewal payback | ~£13k/week |
| 3 | Push a Carnival recovery plan across cruise partners and online check-in CTA placements | Partner Referral Single is down £5k/week and the weakness looks mostly cruise-volume driven | ~£5k/week |
| 4 | Protect Aggregator Annual volume, but only in cuts that can get back to positive 13-month value | We sold 27% fewer aggregator annuals, and this segment is still negative even after estimated future value | ~£3k/week future book |
| 5 | Pull back PPC on weaker existing-customer Bronze traffic and keep funding new-customer PPC | PPC day-one GP looks weak, but new-customer lifetime value still makes the overall machine work better than existing-customer PPC | ~£2k/week |

---
*Generated 12:39 24 Mar 2026 | Tracks: 29 + Follow-ups: 33 | Model: gpt-5.4*
