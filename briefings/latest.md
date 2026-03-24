---
# HX Trading Briefing — 23 Mar 2026

## GP was soft over the last 7 days vs the same week last year: we made £136k, down £26k or 16%, with the biggest damage coming from direct annual and direct single where traffic quality, conversion and margin all got worse.

---

## At a Glance

- 🔴 **Direct annual hurt most** — over the last 7 days vs the same week last year, direct annual GP fell £13k, down 27%, as policies sold fell 12% and GP per policy dropped 16%; desktop traffic was up but desktop search-to-book got much worse.
- 🔴 **Direct single also down hard** — over the last 7 days vs the same week last year, direct single GP fell £13k, down 30%, as policies sold fell 11% and GP per policy dropped 21%; this matters because single-trip has no renewal payback.
- 🔴 **Europe mix squeezed margin** — over the last 7 days vs the same week last year, Europe GP fell £18k, down 18%, with policy volume down only 2%, so we sold about the same amount but made less on each sale.
- 🟢 **Renewals did some repair work** — over the last 7 days vs the same week last year, renewals annual GP rose about £8k, up 18%, on 15% more renewed policies.
- 🔴 **Partner referral stayed soft** — over the last 7 days vs the same week last year, partner referral GP fell about £10k across single and annual, mainly cruise-led volume weakness.

---

## What's Driving This

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct annual GP fell £13k because both traffic quality and conversion worsened. Desktop sessions were up 21%, but desktop search-to-book fell to 29% from 41%, and this has now been negative on 8 of the last 10 trading days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price,
  SUM(CAST(total_net_to_underwriter_inc_gadget AS FLOAT64)) / NULLIF(SUM(CAST(total_gross_inc_ipt AS FLOAT64)), 0) AS uw_cost_pct_of_gross
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY distribution_channel, policy_type
```

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct single GP fell £13k as both traffic quality and margin worsened. Mobile sessions were down 5%, desktop sessions were up 21%, but desktop search-to-book fell to 29% from 41% and underwriter cost rose to 50% of gross from 46%, so we sold fewer policies and made less on each one.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price,
  SUM(CAST(total_net_to_underwriter_inc_gadget AS FLOAT64)) / NULLIF(SUM(CAST(total_gross_inc_ipt AS FLOAT64)), 0) AS uw_cost_pct_of_gross
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY distribution_channel, policy_type
```

### Europe destination GP decline `EMERGING`

Over the last 7 days vs the same week last year, Europe GP fell £18k while volume was down only 2%, so the hit came from mix and margin, not demand falling away. More of the sales came from lower-value Europe business, and Europe Including could not be yielded up further after the 12 March pricing changes.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND destination_group = 'Europe'
GROUP BY destination_group
```

### Partner Referral Single GP decline `EMERGING`

Over the last 7 days vs the same week last year, partner single GP fell about £5k because policies sold dropped by roughly a third, while GP per policy improved a bit. This looks traffic-led rather than a pricing problem, and the cruise partners, especially Carnival, are the weak spot.

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
GROUP BY distribution_channel, policy_type
```

### Renewals Annual GP growth `EMERGING`

Over the last 7 days vs the same week last year, renewals annual GP rose £8k on 15% more renewed policies. That is good news and the payoff from earlier annual acquisition, even if some of the lift may be timing noise.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS renewed_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY distribution_channel, policy_type
```

### Partner Referral Annual GP decline `NEW`

Over the last 7 days vs the same week last year, partner annual GP fell about £5k on lower cruise-partner volume and weaker selling price. This is worth watching, but annual economics here are more about feeding future renewal income than day-one margin.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
GROUP BY distribution_channel, policy_type
```

### Direct new-customer GP decline `NEW`

Over the last 7 days vs the same week last year, direct new-customer day-one GP fell about £4k even though policies sold rose 16%, because GP per policy dropped 37%. The mix shifted toward cheaper mobile, single-trip and Bronze business, but 13-month value is still positive at direct channel level, so we are still buying customers profitably overall.

```sql-dig
SELECT
  distribution_channel,
  customer_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS day_one_gp,
  SUM(COALESCE(est_13m_ins_gp, 0) + COALESCE(est_13m_other_gp, 0)) AS est_13m_future_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND distribution_channel = 'Direct'
  AND customer_type = 'New'
GROUP BY distribution_channel, customer_type
```

### Aggregator Single volume growth with weaker unit GP `NEW`

Over the last 7 days vs the same week last year, aggregator single policies sold jumped 62% but GP was still down about £500 because GP per policy more than halved to under £2. That is very thin single-trip business, so it only works if the 13-month value on new customers covers the day-one weakness.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS day_one_gp,
  SUM(COALESCE(est_13m_ins_gp, 0) + COALESCE(est_13m_other_gp, 0)) AS est_13m_future_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-16' AND '2026-03-23'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
GROUP BY distribution_channel, policy_type
```

---

## Customer Search Intent

Insurance demand still looks stronger than holiday demand. Travel insurance searches are running ahead of the holiday basket ([insurance vs holiday](https://trends.google.com/explore?q=travel%20insurance,holiday%20insurance,annual%20travel%20insurance,single%20trip%20travel%20insurance,travel%20insurance%20comparison&date=2024-03-23%202026-03-23&geo=GB), [holiday basket](https://trends.google.com/explore?q=book%20holiday,cheap%20flights,package%20holiday,all%20inclusive%20holiday,summer%20holiday&date=2024-03-23%202026-03-23&geo=GB)). “Holiday insurance” is up 118% YoY ([Google Trends](https://trends.google.com/explore?q=holiday%20insurance&date=2024-03-23%202026-03-23&geo=GB)) while “book holiday” is up 42% YoY ([Google Trends](https://trends.google.com/explore?q=book%20holiday&date=2024-03-23%202026-03-23&geo=GB)). Caution-led terms are spiking too: “FCDO travel advice” is up 1367% YoY ([Google Trends](https://trends.google.com/explore?q=FCDO%20travel%20advice&date=2024-03-23%202026-03-23&geo=GB)) and “flight cancellation insurance” is up 767% YoY ([Google Trends](https://trends.google.com/explore?q=flight%20cancellation%20insurance&date=2024-03-23%202026-03-23&geo=GB)). Price shopping is still intense, with “cheap travel insurance” up 196% YoY ([Google Trends](https://trends.google.com/explore?q=cheap%20travel%20insurance&date=2024-03-23%202026-03-23&geo=GB)) and “MoneySupermarket travel insurance” up 180% YoY ([Google Trends](https://trends.google.com/explore?q=MoneySupermarket%20travel%20insurance&date=2024-03-23%202026-03-23&geo=GB)). Net: demand is there, but customers want reassurance and are comparing hard.

---

## News & Market Context

Middle East disruption is still affecting traveller behaviour. British Airways said it still could not operate several Middle East routes and was offering flexible rebooking, which keeps disruption and cover questions front of mind ([Yahoo News](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai)). Standard travel policies still often exclude war-related losses, which is pushing customers to read cover detail more closely ([The Week](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war?utm_source=openai)). Saga is publicly highlighting automatic extensions for stranded travellers, which raises the bar for reassurance messaging ([Saga](https://www.saga.co.uk/travel-insurance/middle-east-travel-disruption?utm_source=openai)). Cruise partners are still under pressure: Carnival is running at about 80% of last year’s performance. **Source:** Internal — Insurance Weekly Trading w/c 09/03/2026. HX also pushed pricing up in Europe Excluding and Worldwide Excluding on 12 March, but Europe Including was already capped, so the Europe-heavy squeeze has not been fixed. **Source:** Internal — Weekly Pricing Updates.

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Pull a same-day desktop funnel check on direct annual and direct single from Search to Just Booked, split by annual/single and desktop/mobile, and fix the worst drop step this week | Over the last 7 days vs the same week last year, direct annual and direct single lost about £26k combined, with desktop search-to-book dropping to 29% from 41% in both paths | ~£26k/week |
| 2 | Reprice or re-merchandise the worst-hit direct single schemes first, starting with Bronze Main Single Med HX and Silver Main Single Med HX | Over the last 7 days vs the same week last year, direct single lost £13k and the biggest scheme losses came from lower-tier single medical products | ~£8k-£12k/week |
| 3 | Put disruption and cancellation-cover messaging higher on direct landing pages and paid search copy | Over the last 7 days, search demand was up sharply for FCDO advice and flight cancellation insurance, but direct conversion still weakened | ~£5k-£10k/week |
| 4 | Get cruise partner reviews in with Carnival and other weak partner-referral accounts this week, focused on traffic drop and selling-price pressure | Over the last 7 days vs the same week last year, partner referral lost about £10k across single and annual, mainly cruise-led | ~£10k/week |
| 5 | Check aggregator single new-customer 13-month value by destination and medical mix before pushing more volume | Over the last 7 days vs the same week last year, aggregator single volume was up 62% but GP per policy fell to under £2, so this only works if future value pays back | ~£1k-£3k/week |

---

---
*Generated 07:32 24 Mar 2026 | Tracks: 29 + Follow-ups: 30 | Model: gpt-5.4*
