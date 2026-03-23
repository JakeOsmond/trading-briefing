---
# HX Trading Briefing — 23 Mar 2026

## Europe drove the damage over the last 7 days vs the same week last year, with GP down about £18k as we made less on each policy, and Direct single-trip added another £14k of pressure.

---

## At a Glance

- 🔴 **Europe GP** — Over the last 7 days vs the same week last year, Europe GP fell to about £81k, down £18k, with policies only 2% lower but GP per policy down 17%, so the problem was value not demand.
- 🔴 **Direct single-trip** — Over the last 7 days vs the same week last year, Direct single-trip GP fell to about £27k, down £14k, as policies dropped 14% and GP per policy fell 23%.
- 🔴 **Desktop conversion** — Over the last 7 days vs the same week last year, Direct desktop traffic was up 18% but search-to-book fell from 44% to 31%, so more people arrived and fewer bought.
- 🔴 **Mobile quality** — Over the last 7 days vs the same week last year, Direct mobile sessions fell 7% and mobile session-to-search dropped from 19% to 15%, which hit single-trip volume and value.
- 🟢 **Annual investment** — Over the last 7 days vs the same week last year, annual growth remains good news where it appears because we’re investing in future renewal income, not chasing first-sale margin.

---

## What's Driving This

### Europe destination GP decline `RECURRING`

Over the last 7 days vs the same week last year, Europe GP dropped about £18k to £81k. Policies were only down 2%, so this was mainly about weaker value per sale, with average GP per policy down 17%.  
The data shows Europe got pulled down by lower-value single-trip mix, especially Direct and Aggregator single trips. This has been negative on 8 of the last 10 trading days.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-15' AND '2026-03-22'
  AND destination_group = 'Europe'
GROUP BY 1;
```

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, Direct single-trip GP fell about £14k to £27k. Policies were down 14%, and average GP per policy fell from about £20 to £16, so we sold fewer policies and made less on each one.  
Traffic and conversion both hurt us. Desktop sessions were up 18% but desktop search-to-book dropped from 44% to 31%, while mobile sessions fell 7% and mobile session-to-search dropped from 19% to 15%. This has been negative on 9 of the last 10 trading days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-15' AND '2026-03-22'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Bronze single-trip squeeze `RECURRING`

Over the last 7 days vs the same week last year, Bronze-led single-trip schemes were the biggest product drag inside Direct single. Bronze Main Single Med HX alone was down about £8k of GP, with policies down from 1,066 to 967 and average GP per policy down from about £17 to £10.  
That tells us the issue was not just fewer sales. We also gave up a lot of value on the sales we did win. This has been negative most days in the last 10 trading days.

```sql-dig
SELECT
  scheme_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-15' AND '2026-03-22'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1
ORDER BY gp ASC;
```

### Silver single-trip weakness `RECURRING`

Over the last 7 days vs the same week last year, Silver Main Single Med HX lost about £5k of GP, with policies down from 617 to 477 and average GP per policy down from about £23 to £19.  
This backs up the broader single-trip story. The weakness is not isolated to one tier, though Bronze is taking the biggest hit. This has been a repeat pattern over recent trading days.

```sql-dig
SELECT
  scheme_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-15' AND '2026-03-22'
  AND scheme_name = 'Silver Main Single Med HX'
GROUP BY 1;
```

### Desktop Direct conversion collapse `RECURRING`

Over the last 7 days vs the same week last year, desktop Direct traffic was up from about 26k sessions to 31k, up 18%, but booked sessions still fell about 23% because search-to-book dropped from 44% to 31%.  
The data shows traffic was not the problem here. We got the visits, but the quote-to-sale step got much worse, which points to weaker funnel performance or weaker competitiveness at the point customers saw prices. This has been persistent.

```sql-dig
SELECT
  device_type,
  COUNT(DISTINCT session_id) AS sessions
FROM `hx-data-production.commercial_finance.insurance_web_utm_4`
WHERE session_start_date BETWEEN '2026-03-15' AND '2026-03-22'
  AND device_type = 'computer'
GROUP BY 1;
```

### Mobile Direct demand and funnel decline `RECURRING`

Over the last 7 days vs the same week last year, mobile Direct sessions fell from about 27k to 25k, down 7%, and mobile session-to-search fell from 19% to 15%.  
So mobile hurt us twice: fewer people arrived, and fewer of those who did got through to a quote. That fed straight into weaker single-trip volumes and lower GP. This has also been running for most of the last 10 trading days.

```sql-dig
SELECT
  device_type,
  COUNT(DISTINCT session_id) AS sessions
FROM `hx-data-production.commercial_finance.insurance_web_utm_4`
WHERE session_start_date BETWEEN '2026-03-15' AND '2026-03-22'
  AND device_type = 'mobile'
GROUP BY 1;
```

### Direct single-trip margin squeeze `RECURRING`

Over the last 7 days vs the same week last year, Direct single-trip margin rate fell from 36% to 28% while average selling price stayed broadly flat at about £57.  
That means price did not rescue us. Costs or mix moved against us, and fewer people were adding enough higher-value cover or extras to protect GP. This is a recurring issue alongside the conversion drop.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(CAST(total_gross_exc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price_exc_ipt,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(CAST(total_gross_exc_ipt AS FLOAT64)), 0) AS gp_margin_rate
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-15' AND '2026-03-22'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Aggregator single-trip Europe value drop `EMERGING`

Over the last 7 days vs the same week last year, aggregator single-trip Europe average GP per policy fell from about £3.40 to £1.60.  
This matters because Europe volume held up, but the sales were worth much less. This looks like mix and economics getting worse rather than a traffic issue, and it is early enough that we should treat it as building rather than fully entrenched.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-15' AND '2026-03-22'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
  AND destination_group = 'Europe'
GROUP BY 1,2,3;
```

---

## Customer Search Intent

Google Trends still shows healthy demand in market. Travel insurance searches are up year on year, and comparison behaviour is strong, which fits what we’re seeing in trading: customers are shopping around more, not disappearing.  
“Travel insurance” demand remains elevated ([Google Trends](https://trends.google.com/trends/explore?q=travel%20insurance&geo=GB)). “Annual travel insurance” also remains active ([Google Trends](https://trends.google.com/trends/explore?q=annual%20travel%20insurance&geo=GB)), but conflict-driven uncertainty is likely keeping some customers in single-trip rather than committing for the year.  
“Single trip travel insurance” interest is also strong ([Google Trends](https://trends.google.com/trends/explore?q=single%20trip%20travel%20insurance&geo=GB)). “Travel insurance comparison” is up too ([Google Trends](https://trends.google.com/trends/explore?q=travel%20insurance%20comparison&geo=GB)), which matches the weaker Direct desktop conversion once customers hit the quote stage.  
Holiday demand terms like “cheap flights” ([Google Trends](https://trends.google.com/trends/explore?q=cheap%20flights&geo=GB)) and “summer holiday” ([Google Trends](https://trends.google.com/trends/explore?q=summer%20holiday&geo=GB)) are still supportive, so demand is there. We need to win the sale better, not wait for the market to fix this.

---

## News & Market Context

The Iran conflict is still a live drag on travel confidence and destination choice, and HX already notes that it is pushing some customers away from annual cover and toward single trip and Europe-heavy choices. **Source:** AI Insights — [Current Market Events — Active Context].  
HX pricing notes say Europe Including and Worldwide Excluding were yielded up in Direct on 12 Mar 2026, and early readout showed GP per policy improved in the targeted segments. That means today’s weakness is more concentrated in the still-softer single-trip and Europe mix outside those gains. **Source:** Internal — [Weekly Pricing Updates].  
HX also notes aggregator quote volumes have normalised after the early conflict surge and are now about 20% down year on year, which helps explain why Europe volume held up better than value. **Source:** Internal — [Weekly Pricing Updates].  
Cruise partners remain softer, with Carnival trading at about 80% of last year and partners using offers to stimulate demand. That is a market headwind rather than an HX-only issue. **Source:** Internal — [Insurance Weekly Trading w/c 09/03/2026].  
Search demand itself is not the issue. Google Trends still shows strong insurance and holiday interest, especially for comparison-led terms, which suggests the market is shopping actively but is more price-sensitive at decision point. **Source:** Google Trends links above.

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Pull a same-day funnel check on Direct desktop single-trip from search results to payment, split by Bronze and Silver, and fix the biggest drop step before noon. | Over the last 7 days vs the same week last year, desktop sessions were up 18% but search-to-book fell from 44% to 31%, costing roughly the £14k/week Direct single-trip miss. | ~£14k/week |
| 2 | Review Direct single-trip Europe pricing and product mix on Bronze and Silver, especially where GP per policy has fallen hardest, and push any safe yield or merchandising fixes today. | Over the last 7 days vs the same week last year, Europe GP is down about £18k with GP per policy down 17%, and Bronze plus Silver schemes are the clearest drag. | ~£18k/week |
| 3 | Audit mobile single-trip quote-start and screening journeys for Direct, especially no-screening and medical sessions, and remove friction on the worst-performing step. | Over the last 7 days vs the same week last year, mobile sessions were down 7% and mobile session-to-search fell from 19% to 15%, dragging volume and GP. | ~£7k/week |
| 4 | Check aggregator single-trip Europe economics by partner and cover tier, and cut back exposure where GP per policy is now too thin to be worth the sale. | Over the last 7 days vs the same week last year, aggregator single-trip Europe GP per policy fell from about £3.40 to £1.60. | ~£4k/week |
| 5 | Keep backing annual volume where it is growing, especially in channels that feed renewals, and do not chase first-sale margin there. | Annual growth is strategic because we’re investing in future renewal income. | ~£longer-term renewal upside |

---

---
*Generated 15:17 23 Mar 2026 | Tracks: 28 + Follow-ups: 33 | Model: gpt-5.4*
