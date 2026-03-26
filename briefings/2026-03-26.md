---
# HX Trading Briefing — 25 Mar 2026

## GP stayed under pressure over the last 7 days vs the same week last year, down about £25k, with Direct Single and Direct Annual driving almost all of the miss.

---

## At a Glance

- 🔴 **Direct did most of the damage** — Over the last 7 days vs the same week last year, Direct Single GP fell about £13k and Direct Annual fell about £11k, as quote-reaching traffic dropped and we made less on each sale.
- 🔴 **Bronze was the biggest product drag** — Over the last 7 days vs the same week last year, Bronze GP fell about £20k, with fewer sales and much weaker value per policy, mainly in Direct Single.
- 🟢 **Renewals helped offset the loss** — Over the last 7 days vs the same week last year, Renewals added about £4k because renewal rate improved from 30% to 47%, even though GP per renewed policy was about 8% lower.
- 🔴 **Partner Single was light** — Over the last 7 days vs the same week last year, Partner Referral Single GP fell about £5k, mostly because policy volume dropped 36%, especially in cruise-led partners.
- 🟡 **Aggregator mix needs watching** — Over the last 7 days vs the same week last year, Aggregator Single sold 53% more policies but GP still slipped by about £400 because GP per policy fell from about £3 to under £2, while Aggregator Annual losses improved by about £3k only because annual volume fell 28%.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, Direct Single GP fell about £13k. Traffic softened where it matters, with Search-stage sessions down 15%, and conversion also weakened, so policies fell 12% and GP per policy fell 19% to about £17.  
The data shows this is structural, not a blip. Mobile session-to-search fell from 20% to 15%, search-to-book fell from 89% to 77%, and this has been negative on 9 of the last 10 trading days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-18' AND '2026-03-25'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same week last year, Direct Annual GP fell about £11k. Volume was down 9%, but the bigger hit was value per sale, with GP per policy down 14% to about £48 while selling price was basically flat.  
Annual losses are part of the strategy, so lower margin is not the issue on its own. The real problem is weaker annual volume into next year’s renewal book, with desktop booked sessions down 21% and underwriter cost rising from 47% to 51% of gross.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-18' AND '2026-03-25'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

### Bronze cover-level GP collapse `RECURRING`

Over the last 7 days vs the same week last year, Bronze GP fell about £20k, the biggest product-level drag in the book. We sold 20% fewer Bronze policies and made 26% less on each one.  
This is mostly the Direct Single problem concentrated in one product. Bronze Main Single Med HX was hit hardest, where GP fell from about £20k to £11k over the last 7 days vs the same week last year.

```sql-dig
SELECT
  cover_level_name,
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-18' AND '2026-03-25'
  AND cover_level_name = 'Bronze'
GROUP BY 1,2,3
ORDER BY gp ASC;
```

### Renewals GP growth `RECURRING`

Over the last 7 days vs the same week last year, Renewals added about £4k of GP. That came from renewal rate improving from 30% to 47%, which more than offset fewer expiring policies.  
This is exactly the payoff we want from the annual acquisition strategy. GP per renewed policy fell about 8% over the last 7 days vs the same week last year, so the gain came from better retention rather than richer pricing.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-18' AND '2026-03-25'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY 1,2,3;
```

### Partner Referral Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, Partner Referral Single GP fell about £5k. This was mostly a traffic problem, with policy volume down 36%, while GP per policy improved.  
There is no usable web funnel here, so policy count is our best traffic read. The weakness lines up with softer cruise partner demand, especially Carnival, which is still trading at about 80% of last year according to internal partner reporting.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  agent_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-18' AND '2026-03-25'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1,2,3
ORDER BY gp ASC;
```

### Aggregator Annual losses reduced via lower volume `RECURRING`

Over the last 7 days vs the same week last year, Aggregator Annual day-one GP improved by about £3k, but only because annual policy volume fell 28%. That is weaker acquisition into the renewal book, not better trading.  
Annual losses here are deliberate because we are investing in future renewal income. The channel needs protecting if 13-month value still pays back, so lower annual volume is the thing to worry about.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  customer_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(COALESCE(est_13m_ins_gp,0) + COALESCE(est_13m_other_gp,0)) AS est_future_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-18' AND '2026-03-25'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Annual'
GROUP BY 1,2,3;
```

### Partner Referral Annual GP decline `EMERGING`

Over the last 7 days vs the same week last year, Partner Referral Annual GP fell about £3k. Volumes were down 17% and GP per policy was down 15%, with cruise-heavy web referrals doing most of the damage.  
This may improve as the specialist cruise changes bed in, because those changes only went live on 23 Mar 2026. Phone remains materially richer than web in this channel over the last 7 days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  booking_source,
  agent_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-18' AND '2026-03-25'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
GROUP BY 1,2,3,4
ORDER BY gp ASC;
```

### Aggregator Single GP decline despite higher volume `EMERGING`

Over the last 7 days vs the same week last year, Aggregator Single GP slipped by about £400 even though policy volume jumped 53%. We sold more, but made much less on each sale, with GP per policy dropping from about £3 to under £2.  
Single-trip losses matter because there is no renewal path, so this only works if 13-month value covers it. The data in this draft does not yet state the actual 13-month payback number, so that needs confirming before we call this healthy growth.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  agent_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(COALESCE(est_13m_ins_gp,0) + COALESCE(est_13m_other_gp,0)) AS est_future_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-18' AND '2026-03-25'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
GROUP BY 1,2,3
ORDER BY gp ASC;
```

---

## Customer Search Intent

Insurance demand is still running ahead of holiday demand. [Holiday insurance](https://trends.google.com/explore?q=holiday%20insurance&date=2024-03-25%202026-03-25&geo=GB) is up 129% YoY and [travel insurance](https://trends.google.com/explore?q=travel%20insurance&date=2024-03-25%202026-03-25&geo=GB) is up 61%, versus [book holiday](https://trends.google.com/explore?q=book%20holiday&date=2024-03-25%202026-03-25&geo=GB) up 42% ([insurance comparison view](https://trends.google.com/explore?q=travel%20insurance,holiday%20insurance,annual%20travel%20insurance,single%20trip%20travel%20insurance,travel%20insurance%20comparison&date=2024-03-25%202026-03-25&geo=GB)).  

The big message is price sensitivity. [Holiday insurance cheapest](https://trends.google.com/explore?q=holiday%20insurance%20cheapest&date=2024-03-25%202026-03-25&geo=GB) is up 1,338% and [cheap travel insurance UK](https://trends.google.com/explore?q=cheap%20travel%20insurance%20UK&date=2024-03-25%202026-03-25&geo=GB) is up 1,200% YoY.  

Concern-led demand is rising too. [Travel insurance claims](https://trends.google.com/explore?q=travel%20insurance%20claims&date=2024-03-25%202026-03-25&geo=GB) is up 350% and [holiday cancellation insurance](https://trends.google.com/explore?q=holiday%20cancellation%20insurance&date=2024-03-25%202026-03-25&geo=GB) is up 85% YoY.  

Competitor shopping is hotter as well, with [MoneySupermarket travel insurance](https://trends.google.com/explore?q=MoneySupermarket%20travel%20insurance&date=2024-03-25%202026-03-25&geo=GB) up 189% YoY. Annual intent is stronger than single, with [annual travel cover](https://trends.google.com/explore?q=annual%20travel%20cover&date=2024-03-25%202026-03-25&geo=GB) up 250% while [single trip travel insurance](https://trends.google.com/explore?q=single%20trip%20travel%20insurance&date=2024-03-25%202026-03-25&geo=GB) is flat.

---

## News & Market Context

Comparison pricing is still aggressive. MoneySuperMarket says average single-trip prices were about £25 in February 2026 and annual multi-trip prices were about £61, which fits the weaker lower-tier yield we are seeing in Direct and Aggregator Single ([MoneySuperMarket travel insurance statistics](https://www.moneysupermarket.com/travel-insurance/travel-insurance-statistics/)).  

Compare the Market is still advertising very low entry prices, including Europe single-trip cover from about £7, which keeps pressure on Bronze and Classic products ([Compare the Market travel insurance](https://www.comparethemarket.com/travel-insurance/)).  

Middle East disruption is still feeding travel caution and cover questions. The ABI has published conflict-specific insurance guidance, and FCDO advice pages remain active for affected destinations ([ABI Middle East conflict FAQs](https://www.abi.org.uk/products-and-issues/choosing-the-right-insurance/travel-guide/travel-insurance-faqs-for-middle-east-conflict/), [FCDO UAE advice](https://www.gov.uk/foreign-travel-advice/united-arab-emirates)).  

Cruise softness also looks real. Carnival is currently trading at about 80% of last year according to internal partner reporting, and cruise disruption linked to Gulf port issues has been reported externally ([Euronews cruise disruption](https://www.euronews.com/travel/2026/03/10/european-cruises-cancelled-due-to-ships-being-stuck-in-gulf-ports); **Source:** Internal — Insurance Weekly Trading w/c 09/03/2026).  

Internally, specialist cruise price changes went live on 23 Mar 2026, renewal discount parity went live on 25 Mar 2026, and direct Ergo rate relief is due on 28 Mar 2026, so most of this week is still pre-fix trading (**Source:** Internal — Weekly Pricing Updates; **Source:** Internal — Insurance Trading - Insights, Product & Pricing Mar26).

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Reprice and review underwriting on Direct Bronze Single, starting with Bronze Main Single Med HX | Over the last 7 days vs the same week last year, Direct Single lost about £13k and Bronze lost about £20k, with underwriter cost up and GP per policy badly down | ~£13k/week |
| 2 | Fix the Direct mobile quote journey from landing to search | Over the last 7 days vs the same week last year, Search-stage sessions fell 15% and mobile session-to-search dropped from 20% to 15% in the biggest loss-making segment | ~£8k/week |
| 3 | Keep renewal conversion pressure high while rates are elevated | Over the last 7 days vs the same week last year, Renewals added about £4k from a 17-point better renewal rate | ~£4k/week |
| 4 | Put Carnival and other cruise-led partners on a recovery plan with channel owners this week | Over the last 7 days vs the same week last year, Partner Referral Single lost about £5k, mostly from 36% lower volume | ~£5k/week |
| 5 | Protect Aggregator Annual volume even if day-one margin stays negative | Over the last 7 days vs the same week last year, Aggregator Annual looked £3k better only because annual volume fell 28%, which means less future renewal income | ~£3k/week |

---
*Generated 09:13 26 Mar 2026 | Tracks: 29 + Follow-ups: 31 | Model: gpt-5.4*
