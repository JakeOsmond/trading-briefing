---
# HX Trading Briefing — 24 Mar 2026

## Direct sales were the story over the last 7 days vs the same period last year: GP was down about £26k, with Direct Single and Direct Annual doing nearly all the damage while Renewals helped cushion it.

---

## At a Glance

- 🔴 **Weekly GP down** — Over the last 7 days vs the same period last year, GP was about £133k, down about £26k or 16%, because we sold 6% fewer policies and made about £2.50 less on each one.
- 🔴 **Direct Single was the biggest drag** — Over the last 7 days vs the same period last year, Direct Single GP fell about £13k, with policies down 12% and average GP per policy down 23% as conversion and margin both weakened.
- 🔴 **Direct Annual also hurt** — Over the last 7 days vs the same period last year, Direct Annual GP fell about £12k, mostly from weaker desktop conversion into higher-value annual schemes, while average GP per policy fell 18%.
- 🔴 **Partners were soft** — Over the last 7 days vs the same period last year, Partner Referral GP fell about £9k across Single and Annual, mainly because cruise-linked traffic was weaker.
- 🟢 **Renewals kept paying back** — Over the last 7 days vs the same period last year, Renewals Annual GP added about £6k, up 14%, because retention improved from 31% to 47%.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same period last year, Direct Single GP fell about £13k. Traffic was mixed rather than collapsing — desktop sessions were up 24%, mobile sessions were down 6% — but conversion clearly got worse, with mobile session-to-search down from 19% to 15% and desktop search-to-book down from 42% to 30%.  
We also made less on each sale, with average GP per policy down from about £21 to £16 as underwriter cost rose faster than price. This has been weak on 9 of the last 10 trading days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same period last year, Direct Annual GP fell about £12k. This is not a problem with the annual strategy itself — we are still investing in future renewal income — but desktop annual conversion was clearly weaker, with booked desktop annual sessions down 22% and average GP per policy down from about £59 to £48.  
The data shows the weakness was concentrated in higher-value medical annual schemes on desktop, where screening completion softened. This has been weak on 8 of the last 10 trading days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

### Partner Referral Single GP decline `RECURRING`

Over the last 7 days vs the same period last year, Partner Referral Single GP fell about £5.5k. This was mainly traffic-led rather than a pricing issue, with policies down 35% while average GP per policy edged up from about £19 to £20.  
The weakness looks concentrated in cruise-linked partners, which fits the softer Carnival and partner market backdrop. This has been weak on 8 of the last 10 trading days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  insurance_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1,2,3
ORDER BY gp DESC;
```

### Renewals Annual GP growth `RECURRING`

Over the last 7 days vs the same period last year, Renewals Annual GP grew about £6k. Expiries were lower, but retention improved from 31% to 47%, which more than offset that and shows the annual acquisition strategy is still paying back.  
This has been one of the few steady positives, up on 8 of the last 10 trading days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS renewed_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

### Aggregator Single GP decline despite volume growth `RECURRING`

Over the last 7 days vs the same period last year, Aggregator Single GP was only down about £300, but the quality got worse. Policies were up 57%, yet average GP per policy nearly halved from about £3.20 to £1.80.  
This matters because single-trip has no renewal pathway, so day-one thin margins need the 13-month value to justify them. Over the last 7 days vs the same period last year, Aggregator Single made about £1.8k after PPC and the estimated 13-month value added about £1.1k future insurance plus about £400 from other HX, leaving about £3.3k total — still positive, but with much less headroom.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(ppc_cost_per_policy,0)) AS gp_post_ppc,
  SUM(COALESCE(est_13m_ins_gp,0)) AS est_future_ins_gp,
  SUM(COALESCE(est_13m_other_gp,0)) AS est_future_other_gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(ppc_cost_per_policy,0) + COALESCE(est_13m_ins_gp,0) + COALESCE(est_13m_other_gp,0)) AS total_13m_customer_value
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Partner Referral Annual GP decline `EMERGING`

Over the last 7 days vs the same period last year, Partner Referral Annual GP fell about £4k. Volume did most of the damage, down 17%, and average GP per policy also slipped from about £76 to £58.  
Because this is annual, some day-one pain is fine if it buys future renewal income. The bigger issue here looks like softer partner traffic, especially in cruise, rather than a bad acquisition strategy.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  insurance_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(ppc_cost_per_policy,0)) AS gp_post_ppc,
  SUM(COALESCE(est_13m_ins_gp,0)) AS est_future_ins_gp,
  SUM(COALESCE(est_13m_other_gp,0)) AS est_future_other_gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(ppc_cost_per_policy,0) + COALESCE(est_13m_ins_gp,0) + COALESCE(est_13m_other_gp,0)) AS total_13m_customer_value
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
GROUP BY 1,2,3
ORDER BY gp DESC;
```

### Europe destination GP decline `EMERGING`

Over the last 7 days vs the same period last year, Europe GP fell about £18k. Policies were only down 3%, so most of the damage came from making less on each sale, with average GP per policy down from about £22 to £19.  
This looks like mix shifting towards lower-value short-lead single-trip business rather than demand disappearing. That fits the current market, where customers are still travelling but are leaning shorter lead and closer-to-home.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
  AND destination_group = 'Europe'
GROUP BY 1;
```

### Direct PPC web economics deterioration `NEW`

Over the last 7 days vs the same period last year, paid direct web volume was up, but quality is still mixed. Direct PPC made about £2.0k after PPC and the 13-month value added about £1.6k, taking the total to about £3.6k, so the channel still looks investable overall.  
The weaker pocket is Single PPC: it lost about £600 after PPC, but the estimated 13-month value added about £700 future insurance plus about £400 from other HX, taking it to about £600 positive. This is early-stage, so treat it as one to steer rather than one to shut off.

```sql-dig
SELECT
  insurance_group,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(ppc_cost_per_policy,0)) AS gp_post_ppc,
  SUM(COALESCE(est_13m_ins_gp,0)) AS est_future_ins_gp,
  SUM(COALESCE(est_13m_other_gp,0)) AS est_future_other_gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(ppc_cost_per_policy,0) + COALESCE(est_13m_ins_gp,0) + COALESCE(est_13m_other_gp,0)) AS total_13m_customer_value
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
  AND distribution_channel = 'Direct'
  AND insurance_group = 'Web Advertising PPC'
GROUP BY 1,2;
```

---

## Customer Search Intent

Insurance demand is running ahead of holiday demand in Google. “Holiday insurance” is up 118% YoY ([Google Trends](https://trends.google.com/explore?q=holiday%20insurance&date=2024-03-24%202026-03-24&geo=GB)) versus “book holiday” up 42% ([Google Trends](https://trends.google.com/explore?q=book%20holiday&date=2024-03-24%202026-03-24&geo=GB)) and “package holiday” up 27% ([Google Trends](https://trends.google.com/explore?q=package%20holiday&date=2024-03-24%202026-03-24&geo=GB)).  
Risk and price terms are surging too: “travel insurance claims” is up 600% ([Google Trends](https://trends.google.com/explore?q=travel%20insurance%20claims&date=2024-03-24%202026-03-24&geo=GB)), “flight cancellation insurance” is up 513% ([Google Trends](https://trends.google.com/explore?q=flight%20cancellation%20insurance&date=2024-03-24%202026-03-24&geo=GB)), and “cheap holiday insurance” is up 415% ([Google Trends](https://trends.google.com/explore?q=cheap%20holiday%20insurance&date=2024-03-24%202026-03-24&geo=GB)).  
Competitor searches are also up, especially “MoneySupermarket travel insurance” up 190% ([Google Trends](https://trends.google.com/explore?q=MoneySupermarket%20travel%20insurance&date=2024-03-24%202026-03-24&geo=GB)) and “Staysure travel insurance” up 33% ([Google Trends](https://trends.google.com/explore?q=Staysure%20travel%20insurance&date=2024-03-24%202026-03-24&geo=GB)). Net: demand is there, but it is price-led and comparison-led rather than brand-led ([insurance vs holiday comparison](https://trends.google.com/explore?q=travel%20insurance,holiday%20insurance,annual%20travel%20insurance,single%20trip%20travel%20insurance,travel%20insurance%20comparison&date=2024-03-24%202026-03-24&geo=GB)).

---

## News & Market Context

UK aviation is still growing, which supports the view that demand is there and our softness is more about capture than the market disappearing. [CAA update](https://www.caa.co.uk/newsroom/news/new-caa-data-suggests-2026-will-be-another-year-of-growth-for-the-aviation-sector/)  
International passenger demand is still rising too, according to IATA. [IATA release](https://www.iata.org/en/pressroom/2026-releases/2026-03-02-02/)  
Comparison pressure is real: Staysure has moved onto aggregators, which makes price comparison tougher where we are already seeing thinner Aggregator Single margins. [Insurance Age](https://www.insuranceage.co.uk/insight/7956783/staysure-moves-onto-aggregators)  
The Middle East disruption is still shaping booking behaviour, and BA has kept flexible rebooking in place on affected routes. [Yahoo / BA coverage](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai)  
That helps explain why claims and cancellation-related searches are spiking. [The Week](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war?utm_source=openai)  
Internally, direct yielding changes went live on 12 March and specialist cruise pricing changes went live on 23 March, so some mix movement in direct and cruise-linked partner business is expected this week. **Source:** Internal — Weekly Pricing Updates.  
Carnival partner traffic is still running at about 80% of last year, which lines up with the weaker Partner Referral picture. **Source:** Internal — Insurance Weekly Trading w/c 09/03/2026.

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Fix Direct Single search drop-off on mobile and desktop, starting with Bronze single journeys and desktop search-to-book | Over the last 7 days vs the same period last year, Direct Single lost about £13k, with mobile session-to-search down from 19% to 15% and desktop search-to-book down from 42% to 30% | ~£13k/week |
| 2 | Review desktop annual medical screening and quote flow before doing more price work | Over the last 7 days vs the same period last year, Direct Annual lost about £12k, and the weakness is in desktop conversion into higher-value medical annual schemes | ~£12k/week |
| 3 | Get with Carnival and other cruise partners to recover referral traffic and CTA visibility | Over the last 7 days vs the same period last year, Partner Referral Single and Annual were down about £9k combined, mainly volume-led | ~£9k/week |
| 4 | Keep pushing renewal retention mechanics and fix any journey issues blocking take-up | Over the last 7 days vs the same period last year, Renewals Annual added about £6k and retention improved from 31% to 47% | ~£6k/week |
| 5 | Push PPC mix away from low-value Single traffic and towards Annual and stronger-value segments | Over the last 7 days vs the same period last year, Direct PPC stayed positive on a 13-month view, but Single PPC only worked because future value bailed out a day-one loss of about £600 | ~£1k/week |

---
*Generated 10:11 25 Mar 2026 | Tracks: 29 + Follow-ups: 35 | Model: gpt-5.4*
