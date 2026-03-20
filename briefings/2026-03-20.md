---
# HX Trading Briefing — 19 Mar 2026

## Over the last 7 days vs the same period last year, GP fell by about £19k because direct annual and direct single both weakened, mostly from fewer people reaching prices and fewer desktop users finishing.

---

## At a Glance

- 🔴 **Direct annual down** — Over the last 7 days vs the same period last year, direct annual GP fell about £10k to £37k as annual-converting sessions dropped 18% and fewer visitors got through to prices.
- 🔴 **Europe margin squeeze** — Over the last 7 days vs the same period last year, Europe GP fell about £13k to £88k with policy volume roughly flat, so we’re still selling the trips but making less on them.
- 🔴 **Direct single down** — Over the last 7 days vs the same period last year, direct single GP fell about £8k to £31k, with weaker top-of-funnel conversion and about 11% less GP per sale on single trip, which is a real problem because there’s no renewal payback.
- 🟢 **Renewals helping** — Over the last 7 days vs the same period last year, renewal GP rose about £6k to £49k as more expiring customers renewed and renewed GP per policy edged up.
- 🔴 **Partner cruise softness** — Over the last 7 days vs the same period last year, partner annual GP fell about £5k and partner single GP fell about £3k, mostly tied to weaker cruise-partner demand.

---

## What's Driving This

### Direct Annual GP down `RECURRING`

Over the last 7 days vs the same period last year, direct annual GP fell about £10k to £37k. Traffic was mixed rather than weak overall, with mobile sessions down 5% but desktop sessions up 27%, yet annual-converting booked sessions still fell 18% because fewer people got to Search on both mobile and desktop.  
The data shows this is mainly a conversion problem, not a traffic problem, and it has been negative on 8 of the last 10 trading days. Average GP per annual policy also fell about 8%, but annual volume still matters most here because we’re investing in future renewal income.

```sql-dig
SELECT
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual';
```

### Europe destination GP down `RECURRING`

Over the last 7 days vs the same period last year, Europe GP fell about £13k to £88k while policy volume was roughly flat. That means demand held up, but the money we kept on each sale got worse.  
This looks like a mix and margin issue more than a traffic issue, with shorter-lead and lower-value Europe business diluting GP. It has been a persistent drag rather than a one-day wobble.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
  AND destination_group = 'Europe'
GROUP BY 1;
```

### Direct Single GP down `RECURRING`

Over the last 7 days vs the same period last year, direct single GP fell about £8k to £31k. Traffic was not the main problem, but fewer people reached Search and desktop users were much less likely to finish, while average GP per policy fell about 11%.  
The data shows a real single-trip margin squeeze on top of weaker conversion, especially in Bronze and Silver. This has also been persistent, and unlike annuals there is no renewal payback to rescue weak first-sale economics.

```sql-dig
SELECT
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single';
```

### Partner Referral Annual GP down `EMERGING`

Over the last 7 days vs the same period last year, partner annual GP fell about £5k to £8k as volume dropped 14% and GP per policy fell about 31%. We do not have web traffic for this channel, so this points to weaker partner demand and worse mix rather than a site funnel issue.  
This looks mostly cruise-led, especially around Carnival-linked traffic softness. It is building, but not yet as entrenched as the direct-channel problems.

```sql-dig
SELECT
  agent_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
GROUP BY 1
ORDER BY gp DESC;
```

### Renewals GP up `EMERGING`

Over the last 7 days vs the same period last year, renewals GP rose about £6k to £49k. There is no web traffic read here, but more expiring customers are renewing and renewed GP per policy is slightly better too.  
This looks helpful and likely real, but it has not run long enough to call fully locked in yet. It is the main offset to weaker new business right now.

```sql-dig
SELECT
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
  AND distribution_channel = 'Renewals';
```

### Partner Referral Single GP down `NEW`

Over the last 7 days vs the same period last year, partner single GP fell about £3k to £14k, mostly because policy volume dropped about 25%. Again, there is no web traffic view here, so this is likely partner demand softness rather than a checkout issue.  
This may be mostly cruise-partner weakness, especially P&O and Carnival-linked flows. The signal is smaller and newer than the main direct-channel issues.

```sql-dig
SELECT
  agent_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1
ORDER BY gp DESC;
```

### Aggregator Single GP down `NEW`

Over the last 7 days vs the same period last year, aggregator single GP fell by about £1k to about £2k even though policies jumped about 50%. We do not have traffic data for aggregators, but the outcome is clear: we sold more and made almost nothing on each one.  
This may be cheap compare-site mix, with lower-value products doing most of the damage. The move is real enough to watch, but the exact cause still needs proving.

```sql-dig
SELECT
  scheme_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
GROUP BY 1
ORDER BY gp DESC;
```

### Aggregator Annual losses improved `NEW`

Over the last 7 days vs the same period last year, aggregator annual losses improved by about £1k, from roughly a £6k loss to roughly a £4k loss. We do not have traffic data for aggregators, and Idol quote distortion means the volume signal is noisy.  
This is still good news because annual volume is us investing in future renewal income. The right read here is not “fix the loss” but “keep building the renewal book and treat the exact level with care.”

```sql-dig
SELECT
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Annual';
```

---

## Customer Search Intent

Insurance demand still looks stronger than holiday demand. [Holiday insurance searches are up 118% YoY](https://trends.google.com/explore?q=holiday%20insurance&date=2024-03-19%202026-03-19&geo=GB), ahead of [cheap flights at 44%](https://trends.google.com/explore?q=cheap%20flights&date=2024-03-19%202026-03-19&geo=GB) and [winter sun at 40%](https://trends.google.com/explore?q=winter%20sun&date=2024-03-19%202026-03-19&geo=GB).  
The interest is also getting more price-led and detail-led, with [cheap travel insurance UK up 1200%](https://trends.google.com/explore?q=cheap%20travel%20insurance%20UK&date=2024-03-19%202026-03-19&geo=GB), [travel insurance excess up 224%](https://trends.google.com/explore?q=travel%20insurance%20excess&date=2024-03-19%202026-03-19&geo=GB), and [holiday insurance claim up 682%](https://trends.google.com/explore?q=holiday%20insurance%20claim&date=2024-03-19%202026-03-19&geo=GB).  
That says demand is there, but shoppers are comparing hard and looking for value and cover detail before they buy. Compare the full [insurance set](https://trends.google.com/explore?q=travel%20insurance,holiday%20insurance,annual%20travel%20insurance,single%20trip%20travel%20insurance,travel%20insurance%20comparison&date=2024-03-19%202026-03-19&geo=GB) against [holiday terms](https://trends.google.com/explore?q=book%20holiday,cheap%20flights,package%20holiday,all%20inclusive%20holiday,summer%20holiday&date=2024-03-19%202026-03-19&geo=GB).

---

## News & Market Context

The market backdrop still looks better than our trading. Insurance search demand is up faster than holiday demand, which points to a capture problem more than a demand problem. **Source:** AI Insights — quarterly.  
The Iran conflict is still pushing customers toward shorter-lead and single-trip behaviour, which helps explain softer annual take-up and more Europe-heavy demand. **Source:** Internal — Current Market Events — Active Context.  
Cruise partners remain under pressure, with Carnival still running at about 80% of last year. **Source:** Internal — Insurance Weekly Trading w/c 09/03/2026.  
The FCA’s medical signposting rules are still in force, so any clunky medical journey helps specialist brands more than us. [FCA review](https://www.fca.org.uk/publications/multi-firm-reviews/travel-insurance-signposting-rules-consumers-medical-conditions-review).  
Recent internal notes also say the new destination flow is going live in beta with tracking gaps and missing validation, which fits the weaker early-funnel conversion in direct web. **Source:** Internal — Insurance Data & Commercial Insights – Monthly Review – 2026/03/19 12:15 GMT – Notes by Gemini.  
Middle East disruption is also driving more cover and claims-related searches, not just buying intent. [ABTA advice](https://www.abta.com/news/advice-travel-disruption-due-middle-east-crisis), [The Week](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war).

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Fix the direct web leak before Search on annual and single journeys, starting with the mobile and desktop steps that feed quote volume | Over the last 7 days vs the same period last year, direct annual and direct single together lost about £19k, and both were hit by fewer visitors reaching prices | ~£19k/week |
| 2 | Check desktop direct checkout and search-to-book performance on single-trip journeys, especially Bronze and Silver | Over the last 7 days vs the same period last year, direct single lost about £8k and desktop completion weakened sharply after Search | ~£8k/week |
| 3 | Review Europe single-trip pricing and underwriter cost on lower-tier products, especially short-lead Bronze and Silver | Over the last 7 days vs the same period last year, Europe lost about £13k with volume flat, so margin quality got worse rather than demand | ~£8k/week |
| 4 | Push Carnival and P&O partners for CTA and traffic recovery, and shift effort toward stronger cruise partners where possible | Over the last 7 days vs the same period last year, partner annual and partner single together lost about £8k, mostly on cruise-led weakness | ~£8k/week |
| 5 | Keep renewal ops clean and protect the recent uplift in retained policies | Over the last 7 days vs the same period last year, renewals added about £6k and are the main offset to weak new business | ~£6k/week |

---

---
*Generated 13:15 20 Mar 2026 | Tracks: 23 + Follow-ups: 35 | Model: gpt-5.4*
