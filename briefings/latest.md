---
# HX Trading Briefing — 18 Mar 2026

## Over the last 7 days vs the same week last year, GP fell to £138k — down £26k or 16% — as weaker direct annual and single-trip sales outweighed better renewals.

---

## At a Glance

- 🔴 **Direct annual** — Over the last 7 days vs the same week last year, direct annual GP fell £12k to £39k, with policies down 20% to 761 because fewer annual shoppers came through; that means slower investment into future renewal income.
- 🔴 **Direct single** — Over the last 7 days vs the same week last year, direct single GP fell £11k to £32k, mainly because mobile traffic fell, desktop traffic was weaker quality, session-to-search got worse, and each sale made about 15% less GP.
- 🔴 **Bronze and Silver** — Over the last 7 days vs the same week last year, Bronze GP fell £11k to £30k and Silver GP fell £10k to £52k, mostly reflecting weaker direct single and annual sales in those tiers.
- 🟢 **Renewals** — Over the last 7 days vs the same week last year, renewal annual GP rose £5k to £48k because renewed policy volume grew even though the expiry pool was smaller; that is the payoff from the annual book.
- 🟡 **Yesterday** — Yesterday vs the same day last year, GP was £19k, down £2k or 11%, on 819 policies, down 101 or 11%; average GP per policy was flat, so the miss was mostly fewer sales.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct single GP fell £11k to £32k. The data shows this was traffic quality and conversion as much as margin: mobile sessions were down 5%, desktop sessions were up 30% but converted worse, session-to-search fell from 20% to 16% on mobile and from 14% to 12% on desktop, and average GP per policy dropped 15%; this has been negative on 8 of the last 10 days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Direct'
  AND policy_type = 'Single'
  AND transaction_date BETWEEN '2026-03-11' AND '2026-03-18'
GROUP BY 1,2;
```

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct annual GP fell £12k to £39k and policies fell 20% to 761. This was mainly fewer annual shoppers, not a broken funnel: annual-intent mobile sessions fell 14%, desktop sessions fell 23%, conversion held up fairly well, and this has been negative on 7 of the last 10 days, so we are investing less into future renewal income.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Direct'
  AND policy_type = 'Annual'
  AND transaction_date BETWEEN '2026-03-11' AND '2026-03-18'
GROUP BY 1,2;
```

### Bronze cover level GP decline `RECURRING`

Over the last 7 days vs the same week last year, Bronze GP fell £11k to £30k. This mostly mirrors direct Bronze single and annual weakness rather than a Bronze-only issue, with the biggest drag coming from lower search generation and weaker single-trip unit economics.

```sql-dig
SELECT
  cover_level_name,
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE cover_level_name = 'Bronze'
  AND transaction_date BETWEEN '2026-03-11' AND '2026-03-18'
GROUP BY 1,2,3
ORDER BY gp;
```

### Silver cover level GP decline `RECURRING`

Over the last 7 days vs the same week last year, Silver GP fell £10k to £52k. This again looks like a read-through from weaker direct annual and single trading, especially Silver Main Annual Med HX and Silver Main Single Med HX, rather than a standalone Silver problem; this has been part of the same softer pattern across the last week.

```sql-dig
SELECT
  cover_level_name,
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE cover_level_name = 'Silver'
  AND transaction_date BETWEEN '2026-03-11' AND '2026-03-18'
GROUP BY 1,2,3
ORDER BY gp;
```

### Renewals Annual GP growth `EMERGING`

Over the last 7 days vs the same week last year, renewal annual GP rose £5k to £48k. Renewed policy volume was up about 10% even though the expiry pool was about 20% smaller, so renewal take-up improved and is paying back the annual acquisition strategy.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS renewed_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS renewed_gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_renewed_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
  AND transaction_date BETWEEN '2026-03-11' AND '2026-03-18'
GROUP BY 1,2;
```

### Partner Referral Annual GP decline `EMERGING`

Over the last 7 days vs the same week last year, partner annual GP fell £6k to £8k. This may be mostly cruise-partner softness rather than an HX-only problem, with volumes down 18% and partner traffic weaker in market; annual margin is not the issue here, volume is.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  insurance_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) AS commission,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
  AND transaction_date BETWEEN '2026-03-11' AND '2026-03-18'
GROUP BY 1,2,3
ORDER BY gp;
```

### Partner Referral Single GP decline `NEW`

Over the last 7 days vs the same week last year, partner single GP fell £3k to £14k. This may be mostly lost cruise traffic and fewer new customers rather than a pricing issue, because average GP per policy improved.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  customer_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
  AND transaction_date BETWEEN '2026-03-11' AND '2026-03-18'
GROUP BY 1,2,3
ORDER BY 3;
```

### Aggregator Single GP decline `NEW`

Over the last 7 days vs the same week last year, aggregator single GP fell about £500 to £2k even though policies were up 49%. That is the wrong kind of growth for single trip: we sold more, but made about half as much on each policy, so this needs tighter trading before it scales.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  insurance_group,
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
  AND transaction_date BETWEEN '2026-03-11' AND '2026-03-18'
GROUP BY 1,2,3,4
ORDER BY gp;
```

---

## Customer Search Intent

Search demand still looks supportive. Insurance searches are growing faster than holiday searches, with the market demand index showing insurance up 74% YoY versus holiday terms up 51% YoY. That says people are still shopping for cover, but our trading says too much of that demand is turning into weak-quality traffic rather than clean profitable sales. In plain English: the market is there, but over the last 7 days vs the same week last year we did a worse job turning that interest into quotes and profitable direct single sales.

---

## News & Market Context

The Iran conflict remains the main backdrop for travel demand and is still pushing some customers away from annual cover and towards single trip and Europe instead. **Source:** AI Insights — [Current Market Events — Active Context]. That fits the weaker direct annual acquisition over the last 7 days vs the same week last year, but it does not explain the direct single margin squeeze, which looks more HX-specific. Cruise partners also remain soft, with Carnival running at about 80% of last year. **Source:** Internal — [Insurance Weekly Trading w/c 09/03/2026]. Competitor shopping remains comparison-heavy, with aggregators still dominating finance search visibility, which supports the softer-quality demand we are seeing in single trip ([Adthena UK finance aggregator market share](https://www.adthena.com/market-share/uk-finance-aggregators/)). War-disruption and exclusion questions are keeping insurance research high and may be pushing customers toward cheaper or more cautious choices ([The Week — How travel insurance works if your holiday is disrupted by war](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war), [Saga — Middle East travel disruption](https://www.saga.co.uk/travel-insurance/middle-east-travel-disruption)). FCA medical signposting changes remain a structural support for specialist medical demand, not a drag on this week’s numbers ([FCA instrument](https://api-handbook.fca.org.uk/files/instrument/ICOBS/FCA%202025/45-2026-01-01.pdf)).

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Fix the direct landing-to-search drop on mobile and desktop for single trip this week, starting with the search form and quote-entry pages | Direct single is down about £11k/week and the clearest break is fewer sessions reaching a quote, especially mobile and desktop | ~£11k/week |
| 2 | Review single-trip underwriter-cost and pricing by Bronze and Silver direct schemes now | Direct single GP per policy is down 15% over the last 7 days vs the same week last year, and Bronze and Silver are carrying most of the loss | ~£11k/week |
| 3 | Push harder on high-intent direct annual acquisition through CRM, cross-sell and direct mailings, not broad discounting | Direct annual is down about £12k/week mainly because fewer annual shoppers are arriving; this is slower investment into future renewal income | ~£12k/week |
| 4 | Get partner managers onto Carnival and the other cruise partners this week to recover referral traffic | Partner annual and single are down about £9k/week combined and market context shows cruise demand is still soft | ~£9k/week |
| 5 | Tighten aggregator single-trip trading rules by partner and booking source now | Aggregator single is only down about £500/week today, but volume is up 49% while unit GP has roughly halved | ~£1k/week |

---

---
*Generated 17:14 19 Mar 2026 | Tracks: 23 + Follow-ups: 31 | Model: gpt-5.4*
