---
# HX Trading Briefing — 26 Mar 2026

## Direct was the real problem over the last 7 days vs the same week last year: GP fell £33k, about 20%, and most of that came from weaker conversion and lower value per sale on Direct single and annual.

---

## At a Glance

- 🔴 **Total GP** — Over the last 7 days vs the same period last year, GP was £135k, down £33k or 20%, because we sold 6% fewer policies and made about 14% less on each one.
- 🔴 **Direct Single** — Over the last 7 days vs the same period last year, Direct Single GP fell £15k, with policies down 9% and average GP per policy down from £22 to £16, mainly from weaker funnel conversion and cheaper Bronze-heavy sales.
- 🔴 **Direct Annual** — Over the last 7 days vs the same period last year, Direct Annual GP fell £11k, with volume down 9% and average GP per policy down from £55 to £47; that means we are investing less into future renewal income than we want.
- 🔴 **Partner Referral** — Over the last 7 days vs the same period last year, Partner Referral GP fell about £8k across Single and Annual, mainly because partner traffic was softer, especially in cruise-heavy accounts.
- 🟡 **Aggregator economics** — Over the last 7 days vs the same period last year, Aggregator Annual still lost £4.8k on day one, but 13-month value added £3.7k and cut that to a net loss of about £1.1k, while Aggregator volume was down so future renewal intake was lighter.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same period last year, Direct Single GP fell £15k. Traffic was mixed rather than collapsing, with mobile sessions down 5% but desktop sessions up 24%, so the bigger issue was conversion and value: desktop session-to-search fell from 14% to 13%, desktop search-to-book fell from 43% to 30%, and average GP per policy dropped from £22 to £16.  
The data shows we are under-monetising demand, not missing demand altogether. This has been down on 8 of the last 10 days, with the weakest value in Bronze-heavy sales and higher underwriter cost squeezing margin.

```sql-dig
SELECT
  booking_source,
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-19' AND '2026-03-26'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1,2
```

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same period last year, Direct Annual GP fell £11k. Volume was down 9%, but the bigger drag was value per sale, down from £55 to £47, with desktop booked sessions down 21% even though desktop traffic was up.  
This clearly points to a conversion-quality problem in Direct annual rather than weak market demand. We still want annual volume because that is future renewal income, but right now we are catching less of it than last year.

```sql-dig
SELECT
  policy_type,
  distribution_channel,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-19' AND '2026-03-26'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY 1,2
```

### Partner Referral Single GP decline `RECURRING`

Over the last 7 days vs the same period last year, Partner Referral Single GP fell about £5k. This was mainly traffic-led, with policies down 37%, while average GP per policy improved, so the problem was fewer partner sales rather than weaker monetisation.  
Day-one GP was weak, but total 13-month customer value was still about £14.2k over the last 7 days, down from £20.2k last year. That means the channel still pays back, but much less strongly because volume is softer.

```sql-dig
SELECT
  insurance_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(est_13m_ins_gp AS FLOAT64)) AS est_future_ins_gp,
  SUM(CAST(est_13m_other_gp AS FLOAT64)) AS est_future_other_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-19' AND '2026-03-26'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1
```

### Partner Referral Annual GP decline `RECURRING`

Over the last 7 days vs the same period last year, Partner Referral Annual GP fell about £3k. Volume was down 19%, and margin got squeezed by higher commission and underwriter cost in cruise-heavy partners.  
Because this is annual, the lower volume matters more than the day-one loss. Total 13-month customer value was about £7.9k over the last 7 days, down from £11.2k last year, so we are bringing in less future value from this channel too.

```sql-dig
SELECT
  insurance_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) AS commission,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(est_13m_ins_gp AS FLOAT64)) AS est_future_ins_gp,
  SUM(CAST(est_13m_other_gp AS FLOAT64)) AS est_future_other_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-19' AND '2026-03-26'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
GROUP BY 1
```

### Direct new-customer GP decline `RECURRING`

Over the last 7 days vs the same period last year, Direct new-customer GP fell about £1.6k. Traffic is there, but too much of what we are winning is low-value Bronze single-trip business, especially on mobile, so future value is getting diluted.  
These are the customers that carry 13-month upside, and over the last 7 days Direct new customers added about £4.4k of future value on top of day-one GP across Single and Annual. That uplift is real, but it is smaller than it should be because mix is weak.

```sql-dig
SELECT
  policy_type,
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(est_13m_ins_gp AS FLOAT64)) AS est_future_ins_gp,
  SUM(CAST(est_13m_other_gp AS FLOAT64)) AS est_future_other_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-19' AND '2026-03-26'
  AND distribution_channel = 'Direct'
  AND customer_type = 'New'
GROUP BY 1,2
```

### Aggregator Annual GP less negative `EMERGING`

Over the last 7 days vs the same period last year, Aggregator Annual improved by about £3k. Day-one GP was still -£4.8k, but estimated 13-month customer value added about £3.7k, leaving a net loss of about £1.1k, better than last year’s net loss of about £3.5k.  
That is acceptable acquisition economics for annual, but volume was down 27% over the last 7 days vs last year, so we are investing less into future renewals than we were.

```sql-dig
SELECT
  agent_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(est_13m_ins_gp AS FLOAT64)) AS est_future_ins_gp,
  SUM(CAST(est_13m_other_gp AS FLOAT64)) AS est_future_other_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-19' AND '2026-03-26'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Annual'
GROUP BY 1
```

### Aggregator Single GP decline `EMERGING`

Over the last 7 days vs the same period last year, Aggregator Single GP fell about £500 even though policies were up 50%. We sold more, but made much less on each one, with average GP roughly halving, so this was a quality problem not a traffic problem.  
Day-one GP was still positive at about £2.1k over the last 7 days, and 13-month customer value lifted that to about £3.1k. That keeps the segment worthwhile, but for single trip the weak margin still matters because there is no renewal payoff.

```sql-dig
SELECT
  product,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(est_13m_ins_gp AS FLOAT64)) AS est_future_ins_gp,
  SUM(CAST(est_13m_other_gp AS FLOAT64)) AS est_future_other_gp,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-19' AND '2026-03-26'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
GROUP BY 1
```

### Renewals GP decline `EMERGING`

Over the last 7 days vs the same period last year, Renewals GP fell about £1.5k. Policies were up 7% and renewal rate improved, but we made less on each renewed policy and had fewer expiries to work from.  
This may be mix and holiday timing rather than a retention problem. It is worth watching, but the data does not yet say we have a structural renewal issue.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS renewed_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS renewed_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-19' AND '2026-03-26'
  AND distribution_channel = 'Renewals'
GROUP BY 1
```

---

## Customer Search Intent

Insurance demand is still running ahead of holiday demand. “Holiday insurance” is up 132% YoY ([Google Trends](https://trends.google.com/explore?q=holiday%20insurance&date=2024-03-26%202026-03-26&geo=GB)) versus “book holiday” up 42% YoY ([Google Trends](https://trends.google.com/explore?q=book%20holiday&date=2024-03-26%202026-03-26&geo=GB)), and the broader insurance basket is still ahead of holiday terms ([insurance comparison](https://trends.google.com/explore?q=travel%20insurance,holiday%20insurance,annual%20travel%20insurance,single%20trip%20travel%20insurance,travel%20insurance%20comparison&date=2024-03-26%202026-03-26&geo=GB)).  
Risk and value are driving search behaviour. “FCDO travel advice” is up 1,262% ([Google Trends](https://trends.google.com/explore?q=FCDO%20travel%20advice&date=2024-03-26%202026-03-26&geo=GB)), “cheap holiday insurance” is up 529% ([Google Trends](https://trends.google.com/explore?q=cheap%20holiday%20insurance&date=2024-03-26%202026-03-26&geo=GB)), and “travel insurance claims” is up 231% ([Google Trends](https://trends.google.com/explore?q=travel%20insurance%20claims&date=2024-03-26%202026-03-26&geo=GB)).  
Family and cruise intent are also strong, with “family holiday insurance” up 204% ([Google Trends](https://trends.google.com/explore?q=family%20holiday%20insurance&date=2024-03-26%202026-03-26&geo=GB)) and “cruise travel insurance” up 144% ([Google Trends](https://trends.google.com/explore?q=cruise%20travel%20insurance&date=2024-03-26%202026-03-26&geo=GB)). That fits the trading picture: demand is there, but we are not converting or monetising it well enough in Direct.

---

## News & Market Context

Price comparison sites are still keeping the market very price-led. MoneySuperMarket says average February prices were £25 for single trip and £61 for annual multi-trip, which fits the weaker money per sale we are seeing in aggregator and lower-tier Direct business ([MoneySuperMarket travel insurance statistics](https://www.moneysupermarket.com/travel-insurance/travel-insurance-statistics/)).  
Middle East disruption is still shaping customer behaviour. GOV.UK travel advice says travelling against FCDO advice can invalidate cover in some cases, which helps explain why risk-related searches have jumped ([GOV.UK UAE advice](https://www.gov.uk/foreign-travel-advice/united-arab-emirates)). Trade press has also reported that standard policies may not cover war-related disruption, pushing customers to read cover details more closely and shop around harder ([Insurance Journal](https://www.insurancejournal.com/news/international/2026/03/05/860552.htm)).  
Cruise weakness still looks market-wide, not just us. Internal trading notes say Carnival traffic is down about 20% and key cruise partners remain soft. **Source:** Internal — Insurance Weekly Trading w/c 09/03/2026.  
Pricing changes are also in flight. Specialist Cruise changes went live on 23 Mar 2026, and Direct Travel and Cruise discount changes are due on 28 Mar 2026. **Source:** Internal — Weekly Pricing Updates.

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Fix Direct desktop quote-to-book on Single and Annual, starting with Bronze and Silver search results and the screening-to-results step | Direct Single and Direct Annual cost about £26k over the last 7 days vs last year, and desktop conversion is the clearest controllable leak | ~£19k/week |
| 2 | Push Direct mix away from low-value Bronze into Silver and Gold with stronger results-page merchandising before the 28 Mar rate changes | Over the last 7 days vs last year, too much Direct loss came from cheaper Bronze-heavy sales and lower GP per policy, especially in Single | ~£8k/week |
| 3 | Get account plans in front of Carnival, TTNG, Advantage and Althams now, with partner-specific recovery asks on traffic and placement | Partner Referral Single and Annual were down about £8k combined over the last 7 days vs last year, mainly from softer partner traffic in cruise-heavy accounts | ~£8k/week |
| 4 | Keep Aggregator Annual acquisition live, but set a weekly volume floor by partner so we do not starve future renewals | Over the last 7 days vs last year, Aggregator Annual economics improved, but volume was down 27%, so future renewal intake is getting lighter | ~£3k/week |
| 5 | Tighten Aggregator Single pricing or commission where we can on short-lead solo and couple trips | Over the last 7 days vs last year, Aggregator Single policies were up 50% but GP fell about £500 because margin roughly halved | ~£1k/week |

---
*Generated 07:55 27 Mar 2026 | Tracks: 29 + Follow-ups: 29 | Model: gpt-5.4*
