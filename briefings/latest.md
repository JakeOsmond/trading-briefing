---
# HX Trading Briefing — 12 Mar 2026

## Over the last 7 days GP was £147k — down £28k vs the same week last year, mainly because direct annual and direct single web journeys converted worse even though demand stayed strong.

---

## At a Glance

- 🔴 **7-day GP** — Over the last 7 days GP was £147k, down £28k vs the same week last year, about 16% worse.
- 🔴 **Direct annual miss** — Over the last 7 days direct annual GP was £43k, down about £10k vs the same week last year, because traffic was mixed but fewer people got through to quote and buy.
- 🔴 **Worldwide weakness** — Over the last 7 days worldwide GP was down about £14k vs the same week last year, mostly because we made less on each policy rather than because travellers disappeared.
- 🔴 **Direct single squeeze** — Over the last 7 days direct single GP was £35k, down about £9k vs the same week last year; policies were almost flat, so we sold about the same but made much less on each one.
- 🔴 **Partner singles down** — Over the last 7 days partner referral single GP was down about £7k vs the same week last year, mainly because fewer sales came through partner feeds.

---

## What's Driving This

### Direct Annual GP decline `RECURRING`

Over the last 7 days direct annual GP was £43k, down about £10k vs the same week last year. Desktop traffic was up 34% and mobile traffic was down 3%, so traffic was not the main issue; session-to-search got worse on both devices, annual policies sold fell 12%, and we captured less future renewal income for the seventh negative day in the last 10.

```sql-dig
SELECT
  transaction_date,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-05' AND '2026-03-12'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY transaction_date
ORDER BY transaction_date;
```

### Direct Single GP decline `RECURRING`

Over the last 7 days direct single GP was £35k, down about £9k vs the same week last year. Mobile sessions were down 3% but desktop sessions were up 34%, so this was mostly a conversion and margin problem: quote-start and buy rates worsened, policy volume was almost flat, and average GP per policy fell 20%; this has been negative on 8 of the last 10 trading days.

```sql-dig
SELECT
  transaction_date,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-05' AND '2026-03-12'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY transaction_date
ORDER BY transaction_date;
```

### Gold cover level GP decline `RECURRING`

Over the last 7 days Gold GP was down about £9k vs the same week last year. Demand was there, but fewer customers made it through higher-value Gold journeys and average GP per policy slipped about 5%; this has been negative on 7 of the last 10 trading days.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-05' AND '2026-03-12'
  AND cover_level_name = 'Gold'
GROUP BY cover_level_name;
```

### Silver Main Annual Med HX decline `RECURRING`

Over the last 7 days Silver Main Annual Med HX GP was down about £8k vs the same week last year. This was mainly a direct web capture problem: desktop traffic improved, but fewer customers reached quote and buy, and value per sale also fell; this has been negative on 8 of the last 10 trading days.

```sql-dig
SELECT
  scheme_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-05' AND '2026-03-12'
  AND scheme_name = 'Silver Main Annual Med HX'
GROUP BY scheme_name;
```

### Bronze cover level GP decline `RECURRING`

Over the last 7 days Bronze GP was down about £8k vs the same week last year. Traffic was not the main issue; we made about £16 per policy vs about £20 last year, so margin got squeezed for the seventh negative day in the last 10.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-05' AND '2026-03-12'
  AND cover_level_name = 'Bronze'
GROUP BY cover_level_name;
```

### Worldwide destination GP decline `EMERGING`

Over the last 7 days worldwide GP was down about £14k vs the same week last year, the biggest segment hit. Policies were only down about 5%, so the main issue was value per policy, down about 18%, and it lines up with weaker capture in higher-value annual and medical journeys over 6 of the last 10 trading days.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-05' AND '2026-03-12'
  AND destination_group = 'Worldwide'
GROUP BY destination_group;
```

### Renewals Annual GP decline `EMERGING`

Over the last 7 days renewals annual GP was down about £2k vs the same week last year. Volume was up 6%, so this was not a traffic problem; we renewed more people but made about 10% less on each one, especially in higher tiers.

```sql-dig
SELECT
  transaction_date,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-05' AND '2026-03-12'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY transaction_date
ORDER BY transaction_date;
```

### Partner Referral Single GP decline `NEW`

Over the last 7 days partner referral single GP was down about £7k vs the same week last year. We do not have session data here, but policies sold fell 29%, so this looks like weaker partner traffic or feed quality first, with a smaller margin squeeze on top.

```sql-dig
SELECT
  transaction_date,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-05' AND '2026-03-12'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY transaction_date
ORDER BY transaction_date;
```

---

## Customer Search Intent

According to Google Sheets Dashboard Metrics, overall market demand was up 62% YoY and 4-week momentum was up 38%, so customers were searching hard over the last week. According to the same source, insurance searches were 11.5 vs 6.6 last year, up 74% YoY, while holiday searches were up 48% YoY, so insurance intent was growing faster than general trip planning. According to AI Insights, the strongest themes over the last week were annual multi-trip, pre-existing medical, comparison and GHIC-related searches, which fits where we should be winning more. According to AI Insights, Spain, Greece and Italy were the strongest destination themes, helped by early Easter timing and airline seat sales pulling demand forward. **Source:** Google Sheets — Dashboard Metrics tab. **Source:** Google Sheets — Insurance Intent tab. **Source:** AI Insights — what_matters, trend, divergence, seasonal.

---

## News & Market Context

According to AI Insights, easyJet, Jet2, BA and Ryanair all added or promoted 2026 capacity, which supports more travel demand and more insurance shopping. According to [Yahoo Finance](https://uk.finance.yahoo.com/news/easyjet-releases-25-million-budget-162457150.html?utm_source=openai), easyJet launched a 2.5 million seat sale, which helps explain why demand stayed hot over the last week. According to [MoneyWeek](https://moneyweek.com/spending-it/travel-holidays/new-spanish-travel-insurance-rule?utm_source=openai), confusion around Spain health cover rules is pushing more travellers to think about medical cover. According to [AP News](https://apnews.com/article/95179f730223cf9bb5184e650d33a515?utm_source=openai) and the [Met Office](https://weather.metoffice.gov.uk/binaries/content/assets/metofficegovuk/pdf/weather/learn-about/uk-past-events/interesting/2026/2026_03_storm_chandra.pdf?utm_source=openai), strikes, storms and passport-rule noise kept disruption risk visible, which usually supports travel insurance demand. According to [MoneySuperMarket travel insurance statistics](https://www.moneysupermarket.com/travel-insurance/travel-insurance-statistics/), average single-trip cover is about £25 and annual multi-trip about £61, so market pricing still looks sharp. That makes the direct single margin squeeze believable market-wide, but the direct web conversion miss is still our problem. **Source:** AI Insights — deep_dive, trend, news.

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Fix the direct web quote-start drop on mobile and desktop in the annual and single journeys this week | Over the last 7 days desktop traffic was up 34% but session-to-search got worse on both devices, driving about £19k of lost GP across direct annual and direct single | ~£19k/week |
| 2 | Review direct single pricing and underwriter cost changes in Bronze and Silver since 9 Mar | Over the last 7 days direct single GP was down about £9k vs last year and average GP per policy fell 20% while price was flat | ~£9k/week |
| 3 | Push paid search harder on annual, medical and GHIC terms this week | Over the last 7 days insurance search intent was up 74% YoY but direct annual sales were down 12%, so we are missing future renewal income | ~£10k/week |
| 4 | Get partner managers onto the biggest single-trip referral feeds today and check feed quality and volume by partner | Over the last 7 days partner referral single GP was down about £7k vs last year, mostly because policy volume fell 29% | ~£7k/week |
| 5 | Review renewal pricing and offer strength in higher tiers for year-1 auto-renew cohorts this week | Over the last 7 days renewals annual GP was down about £2k vs last year despite 6% higher volume, so value per renewal is slipping | ~£2k/week |

---

_Generated 06:50 13 Mar 2026 | 23 investigation tracks | gpt-5_

---
*Generated 13:30 13 Mar 2026 | Tracks: 23 + Follow-ups: 34 | Model: gpt-5.4*
