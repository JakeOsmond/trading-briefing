---
# HX Trading Briefing — 12 Mar 2026

## Over the last 7 days vs the same period last year, GP fell £28k to £147k even though travel insurance demand is up, so this looks like us missing traffic quality, conversion and margin capture rather than a soft market.

---

## At a Glance

- 🔴 **7-day GP** — Over the last 7 days vs the same period last year, GP was £147k, down £28k or 16%, with 180 fewer policies sold and average GP down to £22 from £25, so we sold less and made less on each sale.
- 🔴 **Worldwide & Europe** — Over the last 7 days vs the same period last year, Worldwide GP fell £14k and Europe GP fell £14k, mostly because average GP per policy dropped, not because volume collapsed.
- 🔴 **Direct web singles** — Over the last 7 days vs the same period last year, Direct single-trip GP fell £9k, with sessions flat overall but search sessions down 16% and average GP per policy down 20%, so quote entry and margin both got worse.
- 🔴 **Direct annuals** — Over the last 7 days vs the same period last year, Direct annual GP fell £10k, with policies down 12%, so we under-captured demand in a part of the market where annual intent is strong.
- 🔴 **Core tiers & partners** — Over the last 7 days vs the same period last year, Gold GP fell £9k, Silver fell £8k and Partner Referral single-trip GP fell £7k, showing weakness across our core products and partner-fed single-trip business.

---

## What's Driving This

### Worldwide destination GP decline `RECURRING`

Over the last 7 days vs the same period last year, Worldwide GP fell £14k to £49k, down 22%. Policies were only down 5%, so most of the damage came from lower value per sale, with average GP down 18%; this has been negative on 8 of the last 10 days and points to weaker capture in higher-value medical and premium journeys rather than a demand drop.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-05' AND '2026-03-12'
  AND destination_group = 'Worldwide'
GROUP BY 1;
```

### Europe destination GP decline `RECURRING`

Over the last 7 days vs the same period last year, Europe GP fell £14k to about £98k, down 13%. Policies were almost flat, down 2%, so this is mainly a margin and mix problem, with average GP per policy down 12%; this has been running through direct single, direct annual and partner single-trip rather than one isolated segment.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-05' AND '2026-03-12'
  AND destination_group = 'Europe'
GROUP BY 1;
```

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same period last year, Direct annual GP fell £10k to about £43k, down 19%, with policies down 12%. Annual growth is still strategically good because it builds future renewal income, so the issue here is not annual margin itself; it is that we are missing conversion and traffic quality in a market where annual search demand is hot, and this has now been weak for multiple days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-05' AND '2026-03-12'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY 1, 2;
```

### Direct Single GP deterioration `RECURRING`

Over the last 7 days vs the same period last year, Direct single-trip GP fell £9k to £35k, down 21%. Sessions were flat overall, but search sessions fell 16%, session-to-search weakened and desktop search-to-book also got worse, while average GP per policy dropped 20%; this has been negative on 9 of the last 10 days, so it looks persistent.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-05' AND '2026-03-12'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1, 2;
```

### Gold cover level GP decline `RECURRING`

Over the last 7 days vs the same period last year, Gold GP fell £9k to £55k, down 14%. Sales were down 10% and average GP slipped 5%, with the sharpest weakness in Direct single and Partner Referral single-trip, so both traffic capture and sale quality are hurting a key premium tier; this has been weak on 8 of the last 10 days.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-05' AND '2026-03-12'
  AND cover_level_name = 'Gold'
GROUP BY 1;
```

### Silver cover level GP decline `RECURRING`

Over the last 7 days vs the same period last year, Silver GP fell £8k to £56k, down 13%. Volume was down 8% and average GP was down 5%, with the biggest drag in Direct annual and Direct single web journeys, so this is broad under-performance in a core tier rather than one-off channel noise; this has also been weak on 8 of the last 10 days.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-05' AND '2026-03-12'
  AND cover_level_name = 'Silver'
GROUP BY 1;
```

### Partner Referral Single GP decline `NEW`

Over the last 7 days vs the same period last year, Partner Referral single-trip GP fell £7k to £15k, down 33%. Policies were down 29% and average GP also weakened, so this is both a feed problem and a margin problem in single-trip business where there is no renewal upside.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-05' AND '2026-03-12'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1, 2;
```

### Renewals annual GP decline `NEW`

Over the last 7 days vs the same period last year, Renewals annual GP fell £2k to £49k, down 4%. Policies were up 6%, so the renewal book is still coming through, but average GP per renewal was down 10%, which points to weaker cohort value rather than a retention problem.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-05' AND '2026-03-12'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY 1, 2;
```

---

## Customer Search Intent

According to Google Sheets Dashboard Metrics, over the latest tracked period vs last year, travel insurance search intent is up 74%, with the insurance index at 11.5 versus 6.6 last year, while holiday search intent is up 48%, so insurance demand is growing faster than travel planning. According to the same Dashboard Metrics data, the gap between insurance and holiday intent widened to 3.1 from 1.0 last year, which usually means people are closer to buying and more focused on risk and cover, not just browsing. According to Google Sheets AI Insights, “travel insurance comparison” is up 816%, “travel insurance price” is up 274%, and “travel insurance over 70” is up 301%, which points to heavier price-shopping and stronger older and medical demand. According to Google Sheets Insurance Intent and AI Insights, annual multi-trip, pre-existing medical, Spain and USA terms are all running stronger, so the market backdrop looks supportive for both annual and medical-led products. **Source:** Google Sheets — Insurance Intent tab. **Source:** Google Sheets — Dashboard Metrics tab. **Source:** AI Insights — deep_dive.

---

## News & Market Context

According to AI Insights and recent airline reporting, easyJet, Ryanair and Jet2 seat sales are pulling travel planning forward, which should be helping insurance demand rather than hurting it. **Source:** AI Insights — what_matters; [easyJet sale update](https://uk.finance.yahoo.com/news/easyjet-releases-25-million-budget-162457150.html?utm_source=openai). According to the FCA, the travel insurance signposting rules for customers with medical conditions remain in focus, which fits the rise in medical and comparison-led searches. **Source:** [FCA review](https://www.fca.org.uk/publications/multi-firm-reviews/travel-insurance-signposting-rules-consumers-medical-conditions-review). According to MoneyWeek and AI Insights, confusion around Spain entry rules, GHIC limits and wider cover questions is pushing more travellers to check insurance earlier in the journey. **Source:** [MoneyWeek](https://moneyweek.com/spending-it/travel-holidays/new-spanish-travel-insurance-rule?utm_source=openai); **Source:** AI Insights — deep_dive. According to British Airways coverage and consumer press, Middle East disruption is still keeping cancellation and disruption cover relevant, even if standard war exclusions still need clear wording. **Source:** [Yahoo News / BA update](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai); [The Week](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war?utm_source=openai). Net: external demand looks active, so this week’s weakness looks more like HX under-capturing demand than the market going quiet.

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Fix the direct single-trip web funnel at the top of funnel, starting with desktop session-to-search and desktop search-to-book, then check the mobile Bronze and Silver quote paths | Over the last 7 days vs the same period last year, Direct single GP is down £9k, search sessions are down 16%, and average GP per policy is down 20% | ~£9k/week |
| 2 | Review direct single-trip underwriting margin on Europe and Worldwide products, especially Bronze, Silver and Gold | Over the last 7 days vs the same period last year, Europe GP is down £14k, Worldwide is down £14k, and average GP per policy fell sharply in both | ~£14k/week |
| 3 | Put more paid search and landing-page focus behind annual multi-trip and medical terms, and send traffic to faster annual-first pages | Over the last 7 days vs the same period last year, Direct annual GP is down £10k while annual intent is strong, so we are missing demand we should be converting into future renewal income | ~£10k/week |
| 4 | Review partner single-trip feed quality, partner pricing and contact-centre handling on Gold-heavy and cruise-linked schemes | Over the last 7 days vs the same period last year, Partner Referral single GP is down £7k and Gold GP is down £9k, with both volume and value weaker | ~£7k/week |
| 5 | Reprice weaker renewal cohorts and check year-1 opt-in mix on higher-tier annual renewals | Over the last 7 days vs the same period last year, Renewals annual GP is down £2k even though policies are up 6%, so value per renewal is slipping | ~£2k/week |

---

_Generated 06:50 13 Mar 2026 | 23 investigation tracks | gpt-5_

---
*Generated 11:47 13 Mar 2026 | Tracks: 23 + Follow-ups: 39 | Model: gpt-5.4*
