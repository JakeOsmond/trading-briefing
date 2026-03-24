---
# HX Trading Briefing — 23 Mar 2026

## GP was softer over the last 7 days vs the same week last year — down £26k, or 16%, because Direct annual and single both kept losing ground, while renewals only partly filled the gap.

---

## At a Glance

- 🔴 **Direct annual down** — Over the last 7 days vs the same week last year, Direct annual GP fell £13k to £37k, with policies down 12% and GP per policy down 17%, so we had both weaker conversion and worse money on each sale.
- 🔴 **Direct single down** — Over the last 7 days vs the same week last year, Direct single GP fell £13k to £29k, with policies down 11% and GP per policy down 21%, and this hurts more because single trip has no renewal payback.
- 🔴 **Europe margin squeeze** — Over the last 7 days vs the same week last year, Europe GP fell £18k to £86k, while policy volume was only down 2%, so this was mainly worse margin per sale.
- 🟢 **Renewals offset some pain** — Over the last 7 days vs the same week last year, renewal GP grew £8k to £53k, up 18%, as renewed volume rose 15%.
- 🔴 **Partner referral soft** — Over the last 7 days vs the same week last year, Partner Referral single GP fell £5k to £13k because volume dropped 33%, with Carnival the biggest drag.

---

## What's Driving This

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same week last year, Direct annual GP fell £13k to £37k because policies dropped 12% and GP per policy dropped 17%. Desktop traffic was not the issue — computer sessions were up 21% — but session-to-search slipped from 14% to 13% and search-to-book fell hard from 41% to 29%; this has been going the wrong way on 8 of the last 10 trading days, so it looks entrenched.

```sql-dig
SELECT
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY 1;
```

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, Direct single GP fell £13k to £29k because policies were down 11% and GP per policy fell 21%. Traffic was mixed rather than weak overall — computer sessions were up 21% but mobile sessions were down 5% — and the bigger problem was conversion, with computer search-to-book down from 41% to 29%; this has been negative on 9 of the last 10 trading days.

```sql-dig
SELECT
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1;
```

### Europe destination GP decline `RECURRING`

Over the last 7 days vs the same week last year, Europe GP fell £18k to £86k while policy volume was down just 2%, so the hit was mainly margin, not demand. This lines up with mix moving toward lower-value Europe sales and weaker Direct capture, and it has shown up repeatedly in the last 10 trading days rather than being a one-day wobble.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND destination_group IN ('Europe', 'Worldwide')
GROUP BY 1
ORDER BY gp DESC;
```

### Renewals GP growth `EMERGING`

Over the last 7 days vs the same week last year, renewals GP grew £8k to £53k, up 18%, with renewed volume up 15% and GP per renewal up 3%. That says the renewal engine is doing its job, even if some of the week-on-week shape may be a bit noisy because holiday timing differs vs last year.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY 1, 2;
```

### Partner Referral Single GP decline `EMERGING`

Over the last 7 days vs the same week last year, Partner Referral single GP fell £5k to £13k because policies dropped 33%, while GP per policy actually improved 8%. That points to a traffic problem more than a pricing problem, and the current read is that Carnival softness is doing most of the damage.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1, 2;
```

### Aggregator Annual loss improvement `EMERGING`

Over the last 7 days vs the same week last year, Aggregator annual GP improved by £3k, from a £7k loss to a £4k loss, mostly because we sold 27% fewer policies. Annual losses are part of the strategy because we are investing in future renewal income, but this specific new-customer cut still looks negative even after adding estimated 13-month value, so this acquisition is still not paying back.

```sql-dig
SELECT
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS day_one_gp,
  SUM(
    CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)
    + COALESCE(est_13m_ins_gp, 0)
    + COALESCE(est_13m_other_gp, 0)
  ) AS gp_13m_value
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Annual'
  AND customer_type = 'New'
GROUP BY 1;
```

### Partner Referral Annual GP decline `NEW`

Over the last 7 days vs the same week last year, Partner Referral annual GP fell £5k to £7k, with policies down 16% and GP per policy down 28%. Because this is annual, the margin line on day one is less important than the volume, but the mix still looks weaker and the segment probably needs a partner-level check rather than a pricing reaction.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
GROUP BY 1, 2;
```

### Aggregator Single GP decline `NEW`

Over the last 7 days vs the same week last year, Aggregator single GP slipped by about £500 to about £2k even though policies jumped 62%, because GP per policy fell from about £3 to about £2. That is worth watching because single trip has no renewal pathway, so we need the 13-month cross-sell value to do the work if day-one GP stays this thin.

```sql-dig
SELECT
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS day_one_gp,
  SUM(
    CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)
    + COALESCE(est_13m_ins_gp, 0)
    + COALESCE(est_13m_other_gp, 0)
  ) AS gp_13m_value,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
  AND customer_type = 'New'
GROUP BY 1;
```

---

## Customer Search Intent

Holiday insurance searches are outpacing holiday booking intent, with [“holiday insurance” up 118% YoY](https://trends.google.com/explore?q=holiday%20insurance&date=2024-03-23%202026-03-23&geo=GB) versus [“book holiday” up 42%](https://trends.google.com/explore?q=book%20holiday&date=2024-03-23%202026-03-23&geo=GB). The biggest jumps are around reassurance and price clarity: [“flight cancellation insurance” up 750% YoY](https://trends.google.com/explore?q=flight%20cancellation%20insurance&date=2024-03-23%202026-03-23&geo=GB), [“travel insurance policy UK” up 588% YoY](https://trends.google.com/explore?q=travel%20insurance%20policy%20UK&date=2024-03-23%202026-03-23&geo=GB), [“cheap holiday insurance” up 356% YoY](https://trends.google.com/explore?q=cheap%20holiday%20insurance&date=2024-03-23%202026-03-23&geo=GB), [“travel insurance excess” up 193% YoY](https://trends.google.com/explore?q=travel%20insurance%20excess&date=2024-03-23%202026-03-23&geo=GB), and [“holiday cancellation policy” up 125% YoY](https://trends.google.com/explore?q=holiday%20cancellation%20policy&date=2024-03-23%202026-03-23&geo=GB). Meanwhile [“Turkey holiday packages” are down 26% YoY](https://trends.google.com/explore?q=Turkey%20holiday%20packages&date=2024-03-23%202026-03-23&geo=GB), which fits the weaker Europe mix. Overall, insurance demand is still ahead of holiday demand ([insurance terms](https://trends.google.com/explore?q=travel%20insurance,holiday%20insurance,annual%20travel%20insurance,single%20trip%20travel%20insurance,travel%20insurance%20comparison&date=2024-03-23%202026-03-23&geo=GB) vs [holiday terms](https://trends.google.com/explore?q=book%20holiday,cheap%20flights,package%20holiday,all%20inclusive%20holiday,summer%20holiday&date=2024-03-23%202026-03-23&geo=GB)), so the market is there if we can convert it better.

---

## News & Market Context

The market does not look weak on demand. Insurance search demand is running ahead of last year, especially on cancellation, price and policy-wording terms. **Source:** AI Insights — [what_matters]. British Airways is still suspending some Middle East routes and offering flexible rebooking, which keeps disruption in the news and pushes customers toward cancellation-focused cover rather than broad annual confidence [British Airways update](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai). Consumer guidance is also reminding people that standard policies may not cover every war-related disruption, which helps explain the jump in searches around cancellation, excess and wording [The Week](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war?utm_source=openai). Saga is publicly promising automatic cover extensions for stranded customers, which raises the bar on reassurance and service messaging [Saga](https://www.saga.co.uk/travel-insurance/middle-east-travel-disruption?utm_source=openai). Cruise is still mixed: internal market notes say Fred Olsen is holding up better, while Carnival remains softer. **Source:** AI Insights — [channels]. That fits what we are seeing in Partner Referral, where the issue looks more like weaker partner demand than our own pricing.

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Fix Direct desktop funnel from search to booking on annual and single this week | Over the last 7 days vs the same week last year, Direct annual and single lost about £26k combined, and desktop search-to-book fell from 41% to 29% in both | ~£15k/week |
| 2 | Review Direct single Europe Bronze pricing and underwriter cost load now | Over the last 7 days vs the same week last year, Direct single lost £13k and Europe lost £18k, with most of the pain coming from worse GP per sale, especially in lower-tier mix | ~£10k/week |
| 3 | Put cancellation and disruption messaging into PPC and landing pages this week | Search demand is surging on cancellation, excess and cheap-cover terms, but our Direct conversion is not keeping up | ~£5k/week |
| 4 | Get a Carnival recovery plan in front of Partnerships now | Over the last 7 days vs the same week last year, Partner Referral single lost £5k and volume was down 33%, with Carnival the main drag | ~£4k/week |
| 5 | Review Aggregator new-customer annual segments cut by cut for 13-month payback | Annual acquisition is strategic, but this cut is still negative even after estimated 13-month value, so some volume is not earning its keep | ~£3k/week |

---

---
*Generated 10:24 24 Mar 2026 | Tracks: 29 + Follow-ups: 39 | Model: gpt-5.4*
