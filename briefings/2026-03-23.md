---
# HX Trading Briefing — 22 Mar 2026

## Over the last 7 days vs the same week last year, GP was down £28k and most of the damage came from Direct single and annual, where traffic softened a bit but the bigger problem was fewer people getting through to a quote.

---

## At a Glance

- 🔴 **Weekly GP down** — Over the last 7 days GP was £128k, down £28k vs the same week last year, about 18% worse, with policy sales down 6% and average GP per policy also lower.
- 🔴 **Direct was the main drag** — Over the last 7 days Direct single GP was down £14k and Direct annual GP was down £14k vs the same week last year, together wiping out about £28k, mainly because fewer visitors reached search and each sale was worth less.
- 🔴 **Europe quality slipped** — Over the last 7 days Europe GP was down £18k vs the same week last year, with policy count only 2% lower, so the bigger issue was weaker GP per sale rather than demand falling away.
- 🟢 **Renewals kept paying back** — Over the last 7 days renewal annual GP was £50k, up £8k vs the same week last year, about 20% better, because more customers renewed despite fewer policies expiring.
- 🔴 **Yesterday was soft too** — Yesterday GP was £15k, down £6k vs the same day last year, about 29% worse, with 884 policies sold, down 11%, and average GP per policy down from about £22 to £17.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, Direct single GP fell £14k to £27k. Sessions were down about 4%, but conversion did most of the damage: mobile session-to-search fell from 19% to 15% and desktop from 14% to 13%, while policy sales fell 14% and average GP per policy fell from about £20 to £16.  
The data shows this is not just weaker demand. Underwriter cost rose from 46% to 50% of gross while price stayed flat, so we sold fewer policies and made less on each one. This has been negative on 9 of the last 10 trading days.

```sql-dig
SELECT scheme_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-15' AND '2026-03-22'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY scheme_name
ORDER BY gp DESC;
```

### Europe destination GP decline `RECURRING`

Over the last 7 days vs the same week last year, Europe GP fell £18k to £81k. Policies were only down 2%, so this was mostly weaker value per sale rather than a traffic collapse.  
This looks like mix and margin pressure inside Europe, not demand disappearing. Customers still bought, but more of the mix appears to have shifted into lower-value cover, while costs stayed heavy. This has been a persistent drag across the week.

```sql-dig
SELECT distribution_channel, policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-15' AND '2026-03-22'
  AND destination_group = 'Europe'
GROUP BY distribution_channel, policy_type
ORDER BY gp DESC;
```

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same week last year, Direct annual GP fell £14k to £36k, with policies down 16%. For annuals, the volume line matters most because this is future renewal income, and right now we are not getting enough customers through the funnel.  
Traffic was mixed, but the bigger issue was fewer visitors getting to search and weaker GP on the sales we did win. This has run for 9 of the last 10 trading days. Annual margin on day one is strategic, so the problem here is lost volume, not the fact annuals are thinner-margin.

```sql-dig
SELECT cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-15' AND '2026-03-22'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY cover_level_name
ORDER BY gp DESC;
```

### Partner Referral Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, Partner Referral single GP fell £5k to £12k. Policies were down 30%, while average GP per policy actually improved slightly, so this was mainly a volume problem.  
Carnival looks to be the main drag, which fits the softer cruise market. This has been weak on 8 of the last 10 trading days, so it is not just a one-day wobble.

```sql-dig
SELECT insurance_group, agent_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_commission
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-15' AND '2026-03-22'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY insurance_group, agent_name
ORDER BY gp DESC;
```

### Worldwide destination GP decline `EMERGING`

Over the last 7 days vs the same week last year, Worldwide GP fell £9k to £47k, with policies down 14%. This looks mainly like fewer long-haul sales rather than a major quality issue.  
That fits the Iran conflict pushing people away from long-haul and toward Europe. Pricing changes may have stopped this getting worse, but they have not replaced the missing volume.

```sql-dig
SELECT distribution_channel, policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-15' AND '2026-03-22'
  AND destination_group = 'Worldwide'
GROUP BY distribution_channel, policy_type
ORDER BY gp DESC;
```

### Renewals Annual GP growth `EMERGING`

Over the last 7 days vs the same week last year, renewal annual GP rose £8k to £50k, about 20% better. That happened even though expiries were down 21%, which means the renewal machine worked harder.  
More customers renewed, and they renewed at slightly better value. This is the clearest sign that earlier annual acquisition is still paying back.

```sql-dig
SELECT booking_source, converted_by,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-15' AND '2026-03-22'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY booking_source, converted_by
ORDER BY policies DESC;
```

### Partner Referral Annual GP decline `NEW`

Over the last 7 days vs the same week last year, Partner Referral annual GP fell £5k to about £6k, with policies down 25%. Because these are annuals, thinner day-one margin is not the issue on its own. The issue is that we lost volume and average GP also slipped.  
Cruise partner annual business appears to be doing most of the damage. This may be market-led, so the right response is to fix partner demand first, not chase annual margin.

```sql-dig
SELECT insurance_group, agent_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_commission
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-15' AND '2026-03-22'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
GROUP BY insurance_group, agent_name
ORDER BY gp DESC;
```

### Aggregator Single GP decline `NEW`

Over the last 7 days vs the same week last year, Aggregator single GP was down only about £1k, but the shape worsened: policies were up 58% while average GP per policy fell from about £3.40 to £1.60. We sold more, but made a lot less on each sale.  
Because this is single-trip, thin day-one GP only works if 13-month customer value covers it. We need to check whether new-customer future value still pays back the weaker margin before we lean further into this mix.

```sql-dig
SELECT insurance_group, agent_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_commission,
  SUM(COALESCE(est_13m_ins_gp,0) + COALESCE(est_13m_other_gp,0)) AS est_13m_uplift
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-15' AND '2026-03-22'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
  AND customer_type = 'New'
GROUP BY insurance_group, agent_name
ORDER BY gp ASC;
```

---

## Customer Search Intent

Search demand still looks healthy. Google Trends narrative shows travel insurance demand is running ahead of holiday demand, and comparison shopping is especially strong, with terms like travel insurance comparison, cheap travel insurance, and annual travel insurance all elevated ([travel insurance](https://trends.google.com/trends/explore?q=travel%20insurance), [travel insurance comparison](https://trends.google.com/trends/explore?q=travel%20insurance%20comparison), [annual travel insurance](https://trends.google.com/trends/explore?q=annual%20travel%20insurance), [cheap travel insurance](https://trends.google.com/trends/explore?q=cheap%20travel%20insurance)).  
That points to a market where customers are in-market but price-sensitive. For us, that matches Direct under-capturing demand and Aggregator single winning volume at much thinner value, so the trading job is to improve quote reach and defend value once shoppers do engage.

---

## News & Market Context

The Iran conflict is still shifting travel demand away from long-haul and toward Europe, which matches our weaker Worldwide mix and softer long-haul sales. **Source:** AI Insights — [deep_dive]  
British Airways is still adjusting some Middle East flying and offering flexibility on affected routes, which keeps disruption risk high for travellers and tends to increase insurance research before purchase. [British Airways issues update today on flights resuming from the Middle East](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai)  
War-related exclusions are also getting more attention, which can slow conversion because customers read more and compare more before buying. [How travel insurance works if your holiday is disrupted by war](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war?utm_source=openai)  
Saga is using reassurance messaging and says it will auto-extend cover for stranded customers, which is a good example of competitor messaging in a nervous market. [Middle East Travel Disruption | Saga Insurance](https://www.saga.co.uk/travel-insurance/middle-east-travel-disruption?utm_source=openai)  
Cruise demand still looks mixed. Carnival is soft while Fred Olsen is firmer, which lines up with our weaker Partner Referral performance. **Source:** AI Insights — [channels]  
Specialist cruise product updates went live on 17 March 2026, including flexible excess options and increased cover. **Source:** Internal — [Weekly Pricing Updates]

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Fix Direct quote reach on mobile and desktop by checking the gatekeeper-to-search and screening-to-search steps, then ship the highest-volume fix this week | Over the last 7 days vs last year, Direct single and Direct annual lost about £28k combined, and the clearest common issue is fewer visitors getting through to a quote | ~£28k/week |
| 2 | Reprice or re-yield the worst-hit Direct single schemes first, starting with Bronze Main Single Med HX and Silver Main Single Med HX | Over the last 7 days vs last year, Direct single lost £14k and the biggest scheme losses sit in Bronze and Silver while underwriter cost rose sharply | ~£13k/week |
| 3 | Put Europe traffic into stronger-value journeys, with annual and higher-tier cover shown earlier on Direct landing and search pages | Over the last 7 days vs last year, Europe lost £18k with volume nearly flat, so the issue is sale quality not lack of demand | ~£18k/week |
| 4 | Ask the partner team to review Carnival and other cruise partner traffic plans, promotions and placement this week | Over the last 7 days vs last year, Partner Referral single and annual lost about £10k combined, mainly from weaker cruise partner volume | ~£10k/week |
| 5 | Run a 13-month value check on new Aggregator single customers by partner before scaling volume further | Over the last 7 days vs last year, Aggregator single volume was up 58% but average GP per policy halved, so day-one economics are too thin to trust without future value | ~£1k/week |

---
*Generated 17:16 23 Mar 2026 | Tracks: 29 + Follow-ups: 36 | Model: gpt-5.4*
