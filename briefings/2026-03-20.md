---
# HX Trading Briefing — 19 Mar 2026

## Over the last 7 days vs the same period last year, GP was down £19k, with Europe mix and weaker Direct annual conversion doing most of the damage.

---

## At a Glance

- 🔴 **Overall GP** — Over the last 7 days vs the same period last year, GP was £136k — down £19k, about 12% worse, as policy volume fell 4% and we made 9% less on each policy.
- 🔴 **Europe drag** — Over the last 7 days vs the same period last year, Europe GP was £88k — down about £13k, with policy volume flat but GP per policy down 12%.
- 🔴 **Direct annual down** — Over the last 7 days vs the same period last year, Direct annual GP was £37k — down about £10k, as annual policies fell 15%; that is bad for this week, but annual volume still matters because we are investing in future renewal income.
- 🔴 **Direct single down** — Over the last 7 days vs the same period last year, Direct single GP was £31k — down about £8k, as mobile traffic fell, desktop conversion weakened, and GP per policy dropped 11%.
- 🟢 **Renewals helped** — Over the last 7 days vs the same period last year, Renewal GP was up about £6k, partly offsetting weaker new business.

---

## What's Driving This

### Europe destination GP decline `RECURRING`

Over the last 7 days vs the same period last year, Europe GP fell by about £13k even though policy volume was basically flat, so this was not a traffic story at destination level. The data shows the problem was value: GP per Europe policy fell 12%, driven by weaker Direct single and Aggregator single economics, and this has been negative on 7 of the last 10 days.

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

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same period last year, Direct annual GP fell by about £10k as policies dropped 15% and GP per policy fell 8%. Traffic was mixed — mobile sessions were down 5%, desktop sessions were up 27% but did not turn into bookings — and desktop search-to-book fell from 41% to 29%, so the issue is softer conversion plus some margin squeeze from higher underwriter cost, not price; this has been negative on 8 of the last 10 days.

```sql-dig
WITH p AS (
  SELECT
    transaction_date,
    SUM(policy_count) AS policies,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price
  FROM `hx-data-production.commercial_finance.insurance_policies_new`
  WHERE distribution_channel = 'Direct'
    AND policy_type = 'Annual'
    AND transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
  GROUP BY 1
)
SELECT * FROM p ORDER BY transaction_date;
```

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same period last year, Direct single GP fell by about £8k as policies dropped 12% and GP per policy fell 11%. Traffic and conversion both hurt: mobile sessions were softer, desktop search-to-book weakened, and because these are single-trip sales there is no later renewal payback; this has been negative on 7 of the last 10 days.

```sql-dig
WITH p AS (
  SELECT
    CAST(certificate_id AS STRING) AS certificate_id,
    SUM(policy_count) AS policies,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
  FROM `hx-data-production.commercial_finance.insurance_policies_new`
  WHERE distribution_channel = 'Direct'
    AND policy_type = 'Single'
    AND transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
  GROUP BY 1
),
w AS (
  SELECT
    certificate_id,
    ANY_VALUE(device_type) AS device_type
  FROM `hx-data-production.commercial_finance.insurance_web_utm_4`
  WHERE session_start_date BETWEEN '2026-03-12' AND '2026-03-19'
  GROUP BY 1
)
SELECT
  COALESCE(device_type, 'unknown') AS device_type,
  SUM(policies) AS policies,
  SUM(gp) AS gp,
  SUM(gp) / NULLIF(SUM(policies), 0) AS avg_gp
FROM p
LEFT JOIN w USING (certificate_id)
GROUP BY 1;
```

### Partner Referral Annual GP decline `EMERGING`

Over the last 7 days vs the same period last year, Partner Referral annual GP fell by about £5k. Volumes were down 14% and GP per policy was down 31%, which points to weaker partner demand and worse economics together, with cruise softness likely in the mix.

```sql-dig
SELECT
  insurance_group,
  agent_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_commission
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
  AND transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
GROUP BY 1,2
ORDER BY gp DESC;
```

### Bronze cover level GP decline `EMERGING`

Over the last 7 days vs the same period last year, Bronze GP fell by about £10k as policies were down 12% and GP per policy was down 15%. This looks like more sales coming through lower-value Bronze single-trip mix, especially in Direct, which pulled average value down.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE cover_level_name = 'Bronze'
  AND transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
GROUP BY 1,2
ORDER BY gp DESC;
```

### Partner Referral Single GP decline `NEW`

Over the last 7 days vs the same period last year, Partner Referral single GP fell by about £3k. This may be mostly traffic-led rather than margin-led, because volume was down 25% while GP per policy improved, which fits weaker cruise-partner demand more than an economics problem.

```sql-dig
SELECT
  CASE
    WHEN LOWER(product) LIKE '%cruise%' OR LOWER(scheme_name) LIKE '%cruise%' THEN 'Cruise'
    ELSE 'Non-Cruise'
  END AS cruise_flag,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
  AND transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
GROUP BY 1;
```

### Aggregator Single GP decline `NEW`

Over the last 7 days vs the same period last year, Aggregator single GP fell by about £1k even though policy volume jumped 50%. That means we sold a lot more cheap single-trip policies and GP per policy more than halved, which is a real issue because single-trip losses do not come back later.

```sql-dig
SELECT
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
  AND transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
GROUP BY 1;
```

### Renewals GP growth `NEW`

Over the last 7 days vs the same period last year, Renewal GP was up about £6k, which helped offset weaker new business. The gain came from better renewal performance and slightly better GP per renewed policy, though this looks less established than the declines above.

```sql-dig
SELECT
  booking_source,
  converted_by,
  SUM(policy_count) AS renewed,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS renewed_gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_renewed_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
  AND transaction_date BETWEEN '2026-03-12' AND '2026-03-19'
GROUP BY 1,2
ORDER BY renewed_gp DESC;
```

---

## Customer Search Intent

Travel insurance demand is still running ahead of holiday demand. [“Holiday insurance” is up 114% YoY](https://trends.google.com/explore?q=holiday%20insurance&date=2024-03-19%202026-03-19&geo=GB), ahead of [“cheap flights” up 46% YoY](https://trends.google.com/explore?q=cheap%20flights&date=2024-03-19%202026-03-19&geo=GB). The biggest moves are in [“annual travel insurance UK” up 544% YoY](https://trends.google.com/explore?q=annual%20travel%20insurance%20UK&date=2024-03-19%202026-03-19&geo=GB), [“Staysure holiday insurance” up 521% YoY](https://trends.google.com/explore?q=Staysure%20holiday%20insurance&date=2024-03-19%202026-03-19&geo=GB), [“travel insurance excess” up 220% YoY](https://trends.google.com/explore?q=travel%20insurance%20excess&date=2024-03-19%202026-03-19&geo=GB), and [“cruise holiday insurance” up 184% YoY](https://trends.google.com/explore?q=cruise%20holiday%20insurance&date=2024-03-19%202026-03-19&geo=GB). That says demand is there, but shoppers are comparing hard and looking for value. Single-trip interest is softer than annual search interest, so the market is still giving us annual demand to go after even while customers are converting less cleanly in Direct. Compare the full insurance set [here](https://trends.google.com/explore?q=travel%20insurance,holiday%20insurance,annual%20travel%20insurance,single%20trip%20travel%20insurance,travel%20insurance%20comparison&date=2024-03-19%202026-03-19&geo=GB).

---

## News & Market Context

The market does not look demand-starved: insurance search demand is up 64% YoY and holiday demand is up 51% YoY. **Source:** AI Insights — [quarterly]. British Airways is still not operating some Middle East routes and is offering flexible rebooking, which keeps disruption concerns live for travellers ([Yahoo News](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai)). War-related disruption also keeps policy wording under more scrutiny because standard cover often excludes military action or airspace closure ([The Week](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war?utm_source=openai)). Saga is publicly highlighting auto-extensions for stranded customers, which raises the service bar in market ([Saga](https://www.saga.co.uk/travel-insurance/middle-east-travel-disruption?utm_source=openai)). Carnival is still running at about 80% of last year, which fits the weaker Partner Referral annual and single numbers. **Source:** Internal — [Insurance Weekly Trading w/c 09/03/2026]. Specialist cruise product changes went live this week, so that is the main near-term offset to watch. **Source:** Internal — [Weekly Pricing Updates]. The FCA’s signposting rules for customers with medical conditions remain relevant for specialist positioning and older travellers ([FCA](https://www.fca.org.uk/publications/multi-firm-reviews/travel-insurance-signposting-rules-consumers-medical-conditions-review)).

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Pull a same-day funnel check on Direct desktop from search results to checkout for annual and single, and fix the biggest drop-off in the live flow first | Over the last 7 days vs the same period last year, extra desktop traffic did not convert, hitting about £18k of Direct GP across annual and single | ~£18k/week |
| 2 | Rework Direct annual landing and quote pages to push annual commitment harder on mobile and desktop | Over the last 7 days vs the same period last year, Direct annual lost about £10k as policies fell 15% even with annual search demand rising | ~£10k/week |
| 3 | Review Aggregator single pricing and scheme rules by age and destination, and cut the lowest-value pockets first | Over the last 7 days vs the same period last year, Aggregator single volume was up 50% but GP per policy more than halved | ~£1k/week |
| 4 | Push harder on renewal auto-renew and self-serve recovery journeys this week | Over the last 7 days vs the same period last year, Renewals added about £6k and are the cleanest profit offset in the mix | ~£6k/week |
| 5 | Review Carnival, P&O and other cruise-partner CTA placement and current offers with the partner team | Over the last 7 days vs the same period last year, Partner Referral annual and single GP were down about £8k combined, with cruise weakness likely in the mix | ~£8k/week |

---
*Generated 10:09 20 Mar 2026 | Tracks: 23 + Follow-ups: 31 | Model: gpt-5.4*
