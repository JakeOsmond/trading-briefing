---
# HX Trading Briefing — 16 Mar 2026

## Over the last 7 days vs the same period last year, GP fell about £27k even though travel insurance demand is sharply up, so the biggest issue is our own conversion and single-trip margin capture.

---

## At a Glance

- 🔴 **Weekly GP down** — Over the last 7 days vs the same period last year, GP was about £143k — down about £27k, around 16% worse, as we sold fewer policies and made less on each single-trip sale.
- 🔴 **Direct single hurt most** — Over the last 7 days vs the same period last year, direct single GP fell about £12k, around 28% worse, because traffic was mixed but far fewer visitors reached a quote and GP per policy dropped from £22 to £17.
- 🔴 **Direct annual softer** — Over the last 7 days vs the same period last year, direct annual GP fell about £8k, around 17% worse, mainly because we sold 150 fewer annuals, which means less investment into future renewal income.
- 🔴 **Bronze and Silver dragged** — Over the last 7 days vs the same period last year, Bronze GP fell about £9k and Silver GP fell about £9k, showing the direct web weakness is concentrated in lower-tier products.
- 🟢 **Renewals helped a bit** — Over the last 7 days vs the same period last year, renewal GP rose about £3k, around 5% better, with renewed volume up 11% and blended renewal rate up from 32% to 42%.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same period last year, direct single GP fell about £12k to £31k. The data shows this is mainly a funnel and margin problem, not weak demand: traffic was mixed by device, but session-to-search fell to 14% from 18%, and average GP per policy dropped from £22 to £17; this has been negative on 8 of the last 10 trading days.

Underwriter cost rose faster than price on single-trip business, so even when we sold a policy we kept less. Bronze and Silver were the biggest drags, especially on mobile direct web journeys.

```sql-dig
SELECT
  transaction_date,
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1,2,3
ORDER BY transaction_date;
```

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same period last year, direct annual GP fell about £8k to £41k. This is mostly a volume and conversion issue: we sold 787 annuals vs 934 last year, down 16%, because fewer users got through to search and booked; this has been negative on 7 of the last 10 trading days.

This matters because we are investing less into future renewal income. Average GP per annual only slipped from £52 to £51, so the bigger issue is fewer people getting through the funnel.

```sql-dig
SELECT
  transaction_date,
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY 1,2,3
ORDER BY transaction_date;
```

### Bronze cover GP decline `RECURRING`

Over the last 7 days vs the same period last year, Bronze GP fell about £9k to £28k. Traffic is still coming through, but lower quote reach and weaker margin meant average GP fell from about £20 to £17, and this lines up with the direct single web issue rather than a demand problem.

This is the same problem showing up in the cheapest cover. We are still attracting shoppers, but low-tier sales are worth less when they convert.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND cover_level_name = 'Bronze'
GROUP BY 1;
```

### Partner Referral Single GP decline `EMERGING`

Over the last 7 days vs the same period last year, partner referral single GP fell about £6k to £14k. This looks like a volume problem first: policies dropped from 920 to 670, down 27%, while average GP stayed broadly flat.

The weakness appears concentrated in web-based partner sales, with cruise a likely factor. Too early to call this structural, but the short-term hit is clear.

```sql-dig
SELECT
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1;
```

### Silver cover GP decline `EMERGING`

Over the last 7 days vs the same period last year, Silver GP fell about £9k to £54k. The data points to the same direct web issue: fewer customers reached a quote and bought, while average GP per policy slipped only slightly from £37 to £36.

So this looks more like a funnel problem than a major pricing mistake. Direct web Silver is the biggest pool here, so small conversion losses hit hard.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND cover_level_name = 'Silver'
GROUP BY 1,2
ORDER BY gp ASC;
```

### Worldwide destination GP decline `NEW`

Over the last 7 days vs the same period last year, worldwide GP fell about £7k to £51k. Too early to call this a market problem because external intent for long-haul cover is still up, so this looks more like us failing to convert higher-value shoppers.

The likely mix issue is in direct annual and medical journeys, where high-GP customers are getting through the funnel less often. This needs checking, but it does not yet look like demand weakness.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND destination_group = 'Worldwide'
GROUP BY 1,2
ORDER BY gp ASC;
```

### Aggregator Single GP decline `NEW`

Over the last 7 days vs the same period last year, aggregator single GP was only down about £500 to about £2k, but the underlying economics worsened. We sold 1,100 policies vs 730 last year, up 49%, yet average GP per policy fell from about £3 to £2, so we are winning more comparison-site single-trip volume and keeping much less on each sale.

This matters because single-trip losses do not renew. Too early to call it a major profit issue on the total £ line, but it is worth fixing before volume grows further.

```sql-dig
SELECT
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
GROUP BY 1;
```

### Renewal GP improvement `NEW`

Over the last 7 days vs the same period last year, renewal GP rose about £3k to £52k. Renewed volume increased from 1,130 to 1,260, up 11%, and blended renewal rate improved from 32% to 42%, which helped offset weaker new business.

This is good news, but the movement is still less certain than the direct declines because expiry mix can move around week to week. Even so, the direction is clearly helpful.

```sql-dig
SELECT
  booking_source,
  SUM(policy_count) AS renewed_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS renewed_gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY 1;
```

---

## Customer Search Intent

According to Google Sheets Dashboard Metrics, over the last 4 weeks vs last year, overall travel insurance demand is up 66% and travel insurance searches are up 75%, while holiday searches are up 56%. According to Google Sheets Insurance Intent and AI Insights, annual, medical and cruise terms are leading the growth, with Spain, USA and Turkey called out as strong destinations, so demand is there and shoppers are active. According to AI Insights — seasonal, January saw a spike tied to airline seat releases, and the sheet expects another lift into Easter from mid-March. That makes this look much more like a share-capture and conversion problem than a market demand problem. **Source:** Google Sheets — Insurance Intent tab. **Source:** Google Sheets — Dashboard Metrics tab. **Source:** AI Insights — what_matters, channels, seasonal.

---

## News & Market Context

According to AI Insights, airline seat releases and route launches are pulling summer demand forward, which fits the stronger insurance search pattern. [The Independent](https://www.the-independent.com/travel/news-and-advice/easyjet-2026-flight-sale-prices-b2793536.html?utm_source=openai) reports easyJet seat releases and new route activity, which supports stronger shopping now. The ABI is also pushing travel insurance reminders, including high US medical cost examples and repatriation risk, which should support medical cover demand rather than weaken it. **Source:** [ABI](https://www.abi.org.uk/news/news-articles/2025/8/eight-to-embark-travel-insurance-tips/?utm_source=openai)

Comparison sites still matter. According to AI Insights — channels, aggregator discovery remains strong, which helps explain why aggregator single volume is up while direct is softer. Middle East disruption is still affecting some routes, with BA offering flexibility on impacted journeys, which can lift cover-related searches but also create confusion about what standard policies include. **Source:** AI Insights — channels. **Source:** [Yahoo News / BA update](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai)

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Fix the direct web drop before Search on mobile and desktop, starting with screening and the steps that lead into quote results | Over the last 7 days vs last year, direct single and direct annual together lost about £20k, while session-to-search fell from 18% to 14% | ~£20k/week |
| 2 | Reprice or reset underwriter economics on direct Bronze and Silver single-trip products, especially mobile non-medical journeys | Over the last 7 days vs last year, direct single GP per policy fell from £22 to £17, and Bronze and Silver were the biggest drags | ~£12k/week |
| 3 | Push more paid search and faster landing pages into annual, medical and cruise demand | Over the last 7 days vs last year, direct annual volume was down 16% even though external insurance demand is up 66% and insurance searches are up 75% | ~£8k/week |
| 4 | Review partner web cruise journeys and placement on the weakest schemes, and move volume to stronger phone or higher-GP routes where possible | Over the last 7 days vs last year, partner single GP fell about £6k and the weakness appears concentrated in web partner sales | ~£6k/week |
| 5 | Remove or reprice the worst aggregator single comparison-site cells where GP per policy has collapsed | Over the last 7 days vs last year, aggregator single volume was up 49% but GP per policy fell from about £3 to £2, and single-trip losses have no renewal value | ~£1k/week |

---

---
*Generated 14:38 17 Mar 2026 | Tracks: 23 + Follow-ups: 41 | Model: gpt-5.4*
