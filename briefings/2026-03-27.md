---
# HX Trading Briefing — 26 Mar 2026

## Over the last 7 days vs the same period last year, GP was down about £33k or 20%, with the biggest hit coming from Direct Single where weaker web conversion and lower GP per sale cost us about £15k.

---

## At a Glance

- 🔴 **Direct Single down hard** — Over the last 7 days vs the same period last year, Direct Single GP fell to about £31k, down £15k or 33%, as traffic quality worsened, conversion weakened, and GP per policy fell from £22 to £16.
- 🔴 **Europe value leak** — Over the last 7 days vs the same period last year, Europe GP fell to about £86k, down £24k or 22%, while policies were only down 3%, so we sold nearly as many policies but made much less on each one.
- 🔴 **Direct Annual softer** — Over the last 7 days vs the same period last year, Direct Annual GP fell to about £37k, down £11k or 23%, and volume fell 9%, so we are putting fewer annual customers into the future renewal book.
- 🔴 **Partner referrals weaker** — Over the last 7 days vs the same period last year, Partner Referral GP fell to about £19k, down £8k or 29%, mostly because single-trip partner volume dropped away.
- 🟡 **Desktop traffic not paying back** — Over the last 7 days vs the same period last year, desktop sessions rose 24% to 35.6k but booked sessions fell 20% to 1.3k, so extra traffic did not turn into sales.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same period last year, Direct Single GP fell £15k to £31k, down 33%. The data clearly shows a three-part problem: mobile sessions fell 5%, desktop traffic rose 24% but converted much worse, and average GP per policy dropped from £22 to £16; this has been negative on 9 of the last 10 trading days.  
This is internal, not market-wide. Google Trends demand is up, but we are getting fewer high-value deep desktop conversions and lower-value Bronze single sales, especially on mobile.

```sql-dig
SELECT
  DATE(p.looker_trans_date) AS trans_date,
  SUM(p.policy_count) AS policies,
  SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data` p
WHERE p.distribution_channel = 'Direct'
  AND p.policy_type = 'Single'
  AND DATE(p.looker_trans_date) BETWEEN '2026-03-19' AND '2026-03-26'
GROUP BY 1
ORDER BY 1;
```

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same period last year, Direct Annual GP fell £11k to £37k, down 23%, and policies fell 9%. That matters because annual volume is future renewal income, so we are investing less into the renewal book.  
Traffic was mixed, but the bigger issue was weaker desktop conversion, with search-to-book down from 43% to 30% over the last 7 days vs the same period last year. This has been a persistent drag rather than a one-day wobble.

```sql-dig
SELECT
  DATE(p.looker_trans_date) AS trans_date,
  SUM(p.policy_count) AS policies,
  SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.insurance.insurance_trading_data` p
WHERE p.distribution_channel = 'Direct'
  AND p.policy_type = 'Annual'
  AND DATE(p.looker_trans_date) BETWEEN '2026-03-19' AND '2026-03-26'
GROUP BY 1
ORDER BY 1;
```

### Europe destination mix GP decline `RECURRING`

Over the last 7 days vs the same period last year, Europe GP fell £24k to £86k, down 22%, while policies were only down 3%. That tells us this was mainly a value problem, not a collapse in demand.  
The weakness sits inside Direct Single and Direct Annual in Europe. Europe should be helping in the current market, so poor monetisation here is costing us more than the volume line suggests.

```sql-dig
SELECT
  p.destination_group,
  SUM(p.policy_count) AS policies,
  SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data` p
WHERE DATE(p.looker_trans_date) BETWEEN '2026-03-19' AND '2026-03-26'
  AND p.destination_group = 'Europe'
GROUP BY 1;
```

### Partner Referral Single volume-led decline `RECURRING`

Over the last 7 days vs the same period last year, Partner Referral Single GP fell £5k to £13k, down 29%. Policies fell 37%, while GP per policy improved from £19 to £21, so this is clearly a partner traffic problem more than a margin problem.  
This lines up with known cruise and partner softness. The good news is the unit economics still work: over the last 7 days, day-one GP was about £13k and estimated 13-month customer value lifted that to about £14k.

```sql-dig
SELECT
  p.insurance_group,
  SUM(p.policy_count) AS policies,
  SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data` p
WHERE p.distribution_channel = 'Partner Referral'
  AND p.policy_type = 'Single'
  AND DATE(p.looker_trans_date) BETWEEN '2026-03-19' AND '2026-03-26'
GROUP BY 1
ORDER BY gp DESC;
```

### Partner Referral Annual decline `RECURRING`

Over the last 7 days vs the same period last year, Partner Referral Annual GP fell £3k to £7k, down 32%, and policies fell 19%. That means fewer partner-sourced annual customers are entering the renewal book.  
This looks like weaker partner demand first, with some extra pressure from commission. It has been persistent enough to treat as a real channel issue, not just noise.

```sql-dig
SELECT
  p.insurance_group,
  SUM(p.policy_count) AS policies,
  SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.insurance.insurance_trading_data` p
WHERE p.distribution_channel = 'Partner Referral'
  AND p.policy_type = 'Annual'
  AND DATE(p.looker_trans_date) BETWEEN '2026-03-19' AND '2026-03-26'
GROUP BY 1
ORDER BY gp DESC;
```

### Desktop web conversion deterioration `RECURRING`

Over the last 7 days vs the same period last year, desktop sessions rose to 35.6k, up 24%, but booked sessions fell to 1.3k, down 20%. Session-to-search slipped from 14% to 13%, and search-to-book fell sharply from 43% to 30%, so the extra traffic was much lower quality.  
The data clearly shows this is the main web conversion problem behind both Direct Single and Direct Annual weakness. Deep sessions still convert, but we are getting too many shallow desktop visits that do not make it through the funnel.

```sql-dig
SELECT
  COUNT(DISTINCT session_id) AS sessions,
  COUNT(DISTINCT CASE WHEN page_type = 'search_results' THEN session_id END) AS search_sessions,
  COUNT(DISTINCT CASE WHEN page_type = 'just_booked' THEN session_id END) AS booked_sessions
FROM `hx-data-production.commercial_finance.insurance_web_utm_4`
WHERE session_start_date BETWEEN '2026-03-19' AND '2026-03-26'
  AND device_type = 'computer';
```

### PPC efficiency deterioration `EMERGING`

Over the last 7 days vs the same period last year, PPC policies almost tripled from 176 to 507, but GP after PPC costs fell by about £0.3k to £3.7k. PPC cost per policy rose from about £10 to £13, so we bought a lot more volume without getting more profit.  
This may still be fine where new-customer value is strong, but the weak pocket is Bronze-heavy Direct Travel Single. That is where we should pull back first and keep the better-converting tiers running.

```sql-dig
SELECT
  p.campaign_name,
  SUM(p.policy_count) AS policies,
  SUM(COALESCE(p.ppc_cost_per_policy, 0) * p.policy_count) AS ppc_cost,
  SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(p.ppc_cost_per_policy, 0) * p.policy_count) AS gp_post_ppc
FROM `hx-data-production.insurance.insurance_trading_data` p
WHERE p.insurance_group = 'Web Advertising PPC'
  AND DATE(p.looker_trans_date) BETWEEN '2026-03-19' AND '2026-03-26'
GROUP BY 1
ORDER BY gp_post_ppc DESC;
```

### Renewals GP decline despite stronger rate `EMERGING`

Over the last 7 days vs the same period last year, Renewals GP fell £2k to £51k, down 3%, even though renewed policies rose 7%. The issue was a much smaller expiry pool, down 25%, and lower GP per renewed policy, down 10%.  
This looks lower confidence than the direct and partner issues. The renewal rate improved, so the renewal engine itself still looks healthy and this may be more about mix than demand.

```sql-dig
SELECT
  SUM(p.policy_count) AS renewed_policies,
  SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS renewed_gp
FROM `hx-data-production.insurance.insurance_trading_data` p
WHERE p.distribution_channel = 'Renewals'
  AND p.policy_type = 'Annual'
  AND DATE(p.looker_trans_date) BETWEEN '2026-03-19' AND '2026-03-26';
```

---

## Customer Search Intent

Insurance demand is running ahead of holiday demand. [Holiday insurance](https://trends.google.com/explore?q=holiday%20insurance&date=2024-03-26%202026-03-26&geo=GB) is up 121% YoY, versus [book holiday](https://trends.google.com/explore?q=book%20holiday&date=2024-03-26%202026-03-26&geo=GB) up 42% and [package holiday](https://trends.google.com/explore?q=package%20holiday&date=2024-03-26%202026-03-26&geo=GB) up 27% ([Google Trends](https://trends.google.com/explore?q=travel%20insurance,holiday%20insurance,annual%20travel%20insurance,single%20trip%20travel%20insurance,travel%20insurance%20comparison&date=2024-03-26%202026-03-26&geo=GB)).  
Risk-led searches are spiking too: [FCDO travel advice](https://trends.google.com/explore?q=FCDO%20travel%20advice&date=2024-03-26%202026-03-26&geo=GB) is up 1367% YoY, [flight cancellation insurance](https://trends.google.com/explore?q=flight%20cancellation%20insurance&date=2024-03-26%202026-03-26&geo=GB) up 1100%, and [cheap holiday insurance](https://trends.google.com/explore?q=cheap%20holiday%20insurance&date=2024-03-26%202026-03-26&geo=GB) up 574%.  
People are shopping around harder as well: [MoneySupermarket travel insurance](https://trends.google.com/explore?q=MoneySupermarket%20travel%20insurance&date=2024-03-26%202026-03-26&geo=GB) is up 201% YoY, [Staysure holiday insurance](https://trends.google.com/explore?q=Staysure%20holiday%20insurance&date=2024-03-26%202026-03-26&geo=GB) up 173%, and [Allianz travel insurance](https://trends.google.com/explore?q=Allianz%20travel%20insurance&date=2024-03-26%202026-03-26&geo=GB) up 82%.  
Bottom line: over the last 7 days, demand looks healthy, but customers are more cautious, more price-sensitive, and more comparison-led.

---

## News & Market Context

Middle East disruption is still the main market backdrop, and standard cover can be affected when customers travel against official advice, which helps explain the jump in risk-led insurance searches. **Source:** [FCDO Israel travel advice](https://www.gov.uk/foreign-travel-advice/israel)  
The current internal market view is that the conflict is pushing some customers away from annual cover and toward single-trip bookings, while Europe is picking up share from more disrupted destinations. **Source:** AI Insights — Iran Conflict (Active since 28 Feb 2026)  
Key partners are still seeing weaker traffic, and Carnival traffic is down about 20%, which fits the referral weakness in cruise-linked partner sales. **Source:** Internal — Insurance Weekly Trading w/c 09/03/2026  
Direct yielding changes went live on 12 March, specialist cruise price changes went live on 23 March, and direct rate relief is due on 28 March, so pricing competitiveness is still moving underneath this week’s numbers. **Source:** Internal — Weekly Pricing Updates  
The FCA’s medical signposting threshold moved to £200 from 1 January 2026, which may have slightly changed shopping behaviour for higher-premium medical cases. **Source:** [FCA Handbook Notice 133](https://www.fca.org.uk/publication/handbook/handbook-notice-133.pdf)  
Comparison shopping also looks elevated in the market, which matches the rise in brand and aggregator search terms. **Source:** [Compare the Market travel insurance](https://www.comparethemarket.com/travel-insurance/)

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Audit and cut the weakest desktop direct traffic sources today, especially any unattributed or low-engagement campaigns feeding shallow sessions. | Over the last 7 days vs the same period last year, desktop sessions were up 24% but booked sessions fell 20%, and this is feeding both Direct Single and Direct Annual weakness. | ~£9k/week |
| 2 | Reprice or reduce discount depth on Direct Single Bronze web journeys before the weekend, starting with the lowest-GP mobile paths. | Over the last 7 days vs the same period last year, Direct Single lost £15k, and the findings show lower-value Bronze single sales are a major leak. | ~£15k/week |
| 3 | Pull back PPC spend on Bronze-heavy Direct Travel Single campaigns and keep spend on stronger tiers only. | Over the last 7 days vs the same period last year, PPC volume nearly tripled but GP after PPC still fell by about £0.3k, so not all growth is paying back. | ~£1k/week |
| 4 | Push named partner recovery plans with cruise-led referrers, especially Carnival-linked and weaker groups like Althams, TTNG and Advantage. | Over the last 7 days vs the same period last year, Partner Referral Single lost £5k mainly from volume, not margin, so we need traffic back. | ~£5k/week |
| 5 | Protect Direct Annual desktop conversion through the 28 March rate-relief rollout and a funnel QA check on search-to-book. | Over the last 7 days vs the same period last year, Direct Annual lost £11k and desktop search-to-book fell from 43% to 30%, which means fewer future renewers entering the book. | ~£11k/week |

---

---
*Generated 12:09 27 Mar 2026 | Tracks: 29 + Follow-ups: 29 | Model: gpt-5.4*
