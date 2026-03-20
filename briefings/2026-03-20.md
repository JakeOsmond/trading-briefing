---
# HX Trading Briefing — 19 Mar 2026

## Over the last 7 days vs the same week last year, GP was down £19k and the biggest drag was weaker Direct web conversion, especially desktop annual and single-trip journeys.

---

## At a Glance

- 🔴 **Overall GP** — Over the last 7 days vs the same week last year, GP was £136k — down £19k, about 12% worse, from 4% fewer policies and about 9% less GP per policy.
- 🔴 **Direct annual** — Over the last 7 days vs the same week last year, Direct annual GP fell £10k, about 22% worse, because annual volume dropped 15% even though desktop traffic was up; we are investing less into future renewal income than we should be.
- 🔴 **Direct single** — Over the last 7 days vs the same week last year, Direct single-trip GP fell £8k, about 22% worse, with fewer sales and about 11% less GP per policy on a product that has no renewal payback.
- 🔴 **Direct existing customers** — Over the last 7 days vs the same week last year, Direct GP from existing customers fell £15k, about 23% worse, because fewer sessions turned into quotes and bookings.
- 🟢 **Renewals** — Over the last 7 days vs the same week last year, renewal GP rose £6k, about 15% better, giving us the main offset to weaker new business.
- 🔴 **Partner referrals** — Over the last 7 days vs the same week last year, partner GP was down about £8k combined across annual and single-trip, with softer referral demand the main issue.

---

## What's Driving This

### Direct Annual GP down `RECURRING`

Over the last 7 days vs the same week last year, Direct annual GP fell to £37k from £47k — down £10k. Desktop sessions were up 27% but desktop session-to-search slipped from 14% to 13% and desktop search-to-book fell hard from 41% to 29%, so more traffic did not turn into sales; this has been weak on 8 of the last 10 trading days.

```sql-dig
SELECT
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY 1;
```

### Direct Single GP down `RECURRING`

Over the last 7 days vs the same week last year, Direct single-trip GP fell to £31k from £39k — down £8k. Mobile sessions were down 5%, desktop sessions were up 27%, but mobile session-to-search fell from 20% to 16% and desktop search-to-book fell from 41% to 29%; on top of that, average GP per policy dropped about 11% as underwriter costs took a bigger share, and this has been weak on 9 of the last 10 trading days.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1
ORDER BY gp DESC;
```

### Direct existing customers GP down `RECURRING`

Over the last 7 days vs the same week last year, Direct GP from existing customers fell to £52k from £67k — down £15k. Existing-user sessions were down 10% and fewer of those users reached a quote, so this looks like a traffic-and-funnel problem rather than a demand problem; this has now been weak for 10 straight trading days.

```sql-dig
SELECT
  customer_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
  AND distribution_channel = 'Direct'
  AND customer_type = 'Existing'
GROUP BY 1;
```

### Partner Referral Annual GP down `RECURRING`

Over the last 7 days vs the same week last year, partner annual GP fell to about £8k from about £13k — down £5k. Volume was down 14% and GP per policy fell 31%, which lines up with softer cruise partner demand and weaker referral traffic; this has been weak on 8 of the last 10 trading days.

```sql-dig
SELECT
  agent_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_commission
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
GROUP BY 1
ORDER BY gp DESC;
```

### Partner Referral Single GP down `EMERGING`

Over the last 7 days vs the same week last year, partner single-trip GP fell to £14k from £16k — down £3k. Volume fell 25% while GP per policy rose 12%, so this looks like weaker partner traffic rather than a pricing problem.

```sql-dig
SELECT
  insurance_group,
  agent_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1,2
ORDER BY policies DESC;
```

### Aggregator Single GP down `EMERGING`

Over the last 7 days vs the same week last year, aggregator single-trip GP fell by about £800 even though volume rose 50%. That means the issue is value, not traffic: average GP per policy more than halved to about £1.50, which matters because single-trip losses do not come back on renewal.

```sql-dig
SELECT
  agent_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) AS gross,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) AS commission,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
GROUP BY 1
ORDER BY commission DESC;
```

### Aggregator Annual volume down despite better GP `EMERGING`

Over the last 7 days vs the same week last year, aggregator annual losses improved by about £1k, which is fine, but annual volume fell 14%. The bigger point is strategic: we are putting fewer annual policies into the future renewal book.

```sql-dig
SELECT
  campaign_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Annual'
GROUP BY 1
ORDER BY policies DESC;
```

### Renewals GP up `NEW`

Over the last 7 days vs the same week last year, renewals GP rose to £49k from £43k — up £6k. More expiring customers renewed and each renewal made slightly more GP, so this is the clearest bright spot in the week.

```sql-dig
SELECT
  booking_source,
  converted_by,
  SUM(policy_count) AS renewed_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS renewed_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY 1,2
ORDER BY renewed_gp DESC;
```

---

## Customer Search Intent

Insurance demand is clearly ahead of holiday demand right now ([insurance vs holiday](https://trends.google.com/explore?q=travel%20insurance,holiday%20insurance,annual%20travel%20insurance,single%20trip%20travel%20insurance,travel%20insurance%20comparison&date=2024-03-19%202026-03-19&geo=GB); [holiday terms](https://trends.google.com/explore?q=book%20holiday,cheap%20flights,package%20holiday,all%20inclusive%20holiday,summer%20holiday&date=2024-03-19%202026-03-19&geo=GB)). Over the last 7 days vs the same week last year, “holiday insurance” searches were up 118% ([Google Trends](https://trends.google.com/explore?q=holiday%20insurance&date=2024-03-19%202026-03-19&geo=GB)), “travel insurance” was up 68% ([Google Trends](https://trends.google.com/explore?q=travel%20insurance&date=2024-03-19%202026-03-19&geo=GB)), and “annual travel insurance” was up 50% ([Google Trends](https://trends.google.com/explore?q=annual%20travel%20insurance&date=2024-03-19%202026-03-19&geo=GB)). Price-shopping is the bigger clue: over the last 7 days vs the same week last year, “cheap holiday insurance” was up 296% ([Google Trends](https://trends.google.com/explore?q=cheap%20holiday%20insurance&date=2024-03-19%202026-03-19&geo=GB)) and “travel insurance excess” was up 227% ([Google Trends](https://trends.google.com/explore?q=travel%20insurance%20excess&date=2024-03-19%202026-03-19&geo=GB)). “Staysure holiday insurance” was up 488% ([Google Trends](https://trends.google.com/explore?q=Staysure%20holiday%20insurance&date=2024-03-19%202026-03-19&geo=GB)), which says branded competitors are catching attention while shoppers look hard at value.

---

## News & Market Context

British Airways is still not operating some Middle East routes and has offered flexible rebooking, which keeps disruption and insurance need elevated. [British Airways issues update](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai) Consumer coverage is also reinforcing policy-exclusion questions, with reporting that standard travel insurance often will not cover war-related losses. [How travel insurance works if your holiday is disrupted by war](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war?utm_source=openai) Saga is leaning into reassurance with stranded-customer extension messaging, which is a useful competitor cue on copy and trust. [Saga Middle East travel disruption guidance](https://www.saga.co.uk/travel-insurance/middle-east-travel-disruption?utm_source=openai) Internal market notes say cruise partner demand is softer, with Carnival at about 80% of last year and partners using stronger offers to stimulate bookings. **Source:** Internal — [Insurance Weekly Trading w/c 09/03/2026]. AI Insights says insurance search demand is still up 57% to 74% year on year, so the market is there and our issue is capture, not lack of shoppers. **Source:** AI Insights — [what_matters]. EES and ETIAS admin changes are also keeping travel-admin and insurance-related searches elevated. [EU Entry/Exit System explainer](https://moneyweek.com/spending-it/travel-holidays/eu-entry-exit-system-ees?utm_source=openai)

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Check the Direct desktop annual funnel today. Pull step-by-step drop-off for gatekeeper, search and checkout for annual desktop sessions, then compare changes made in the last 14 days. | Over the last 7 days vs the same week last year, Direct annual GP is down £10k and desktop search-to-book fell from 41% to 29% despite 27% more desktop sessions. | ~£10k/week |
| 2 | Rework Direct single-trip pricing and underwriter-cost hotspots on mobile Bronze and Silver journeys. | Over the last 7 days vs the same week last year, Direct single GP is down £8k, GP per policy is down about 11%, and underwriter cost share rose from 46% to 51% on a product with no renewal payoff. | ~£8k/week |
| 3 | Build a recovery plan with the weakest referral partners, starting with cruise-led accounts. | Over the last 7 days vs the same week last year, partner annual and single-trip GP are down about £8k combined, and the main issue looks like softer referral traffic. | ~£8k/week |
| 4 | Push landing pages and paid search copy harder on cheap, compare and excess terms, but route traffic into the strongest-converting direct paths. | Over the last 7 days vs the same week last year, insurance search demand is up sharply, but weaker Direct conversion means we are not capturing enough of it. | ~£8k/week |
| 5 | Extend the current renewal playbook into the next expiring cohorts and protect the winning journey settings. | Over the last 7 days vs the same week last year, renewals are up £6k and are the clearest offset to weaker new business. | ~£6k/week |

---
*Generated 12:15 20 Mar 2026 | Tracks: 23 + Follow-ups: 34 | Model: gpt-5.4*
