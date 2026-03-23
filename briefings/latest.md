---
# HX Trading Briefing — 22 Mar 2026

## Direct web was the big drag over the last 7 days vs the same week last year: total GP fell to about £128k, down about £28k or 18%, mostly because direct single-trip conversion and value both got worse.

---

## At a Glance

- 🔴 **Direct single** — Over the last 7 days vs the same week last year, direct single-trip GP fell about £14k to £27k, with policy volume down 14% and average GP per policy down 23%; weaker direct traffic quality and worse conversion did most of the damage.
- 🔴 **Europe mix** — Over the last 7 days vs the same week last year, Europe GP fell about £18k to £81k, with volumes broadly flat but average GP per policy down about 17%, pointing to a lower-value single-trip mix.
- 🔴 **Direct annual** — Over the last 7 days vs the same week last year, direct annual GP fell about £14k to £36k as volumes dropped; that is a capture problem because annual sales are future renewal income for us.
- 🟢 **Renewals** — Over the last 7 days vs the same week last year, renewal GP rose about £8k to £50k, with renewed policy count up about 13%, which helped offset the new-business shortfall.
- 🔴 **Partner weakness** — Over the last 7 days vs the same week last year, partner referral GP fell about £9k across single and annual, mainly because partner demand was softer rather than margins collapsing.

---

## What's Driving This

### Europe destination GP dilution `EMERGING`
Over the last 7 days vs the same week last year, Europe GP fell about £18k to £81k, with policy volume roughly flat but average GP per policy down about 17%. This looks like a mix issue more than a traffic issue: we sold more lower-value Europe single trips, and holiday timing versus last year may be exaggerating the size a bit.

```sql-dig
SELECT
  destination_group,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE (
    DATE(looker_trans_date) BETWEEN '2026-03-15' AND '2026-03-22'
    OR DATE(looker_trans_date) BETWEEN '2025-03-16' AND '2025-03-23'
  )
  AND destination_group = 'Europe'
GROUP BY 1,2;
```

### Direct Single GP decline `RECURRING`
Over the last 7 days vs the same week last year, direct single-trip GP fell about £14k to £27k. Traffic was the biggest problem: mobile sessions were down about 7%, search-producing traffic weakened on both mobile and desktop, and desktop search-to-book fell from about 44% to 31%, so we got fewer bookings and made less from each one; this has been negative on 9 of the last 10 days.

```sql-dig
SELECT
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE distribution_channel = 'Direct'
  AND policy_type = 'Single'
  AND (
    DATE(looker_trans_date) BETWEEN '2026-03-15' AND '2026-03-22'
    OR DATE(looker_trans_date) BETWEEN '2025-03-16' AND '2025-03-23'
  )
GROUP BY 1;
```

### Direct Annual GP decline `EMERGING`
Over the last 7 days vs the same week last year, direct annual GP fell about £14k to £36k and policies were down about 16%. This may partly be calendar noise, but it still points to weaker direct capture and conversion; the important bit is volume, because annual sales mean we are investing in future renewal income.

```sql-dig
SELECT
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE distribution_channel = 'Direct'
  AND policy_type = 'Annual'
  AND (
    DATE(looker_trans_date) BETWEEN '2026-03-15' AND '2026-03-22'
    OR DATE(looker_trans_date) BETWEEN '2025-03-16' AND '2025-03-23'
  )
GROUP BY 1;
```

### Renewals GP growth `EMERGING`
Over the last 7 days vs the same week last year, renewals GP rose about £8k to £50k and renewed policy count was up about 13%. Some of this may still be holiday timing, but the direction is good and the data suggests better take-up plus cleaner auto-renew processing.

```sql-dig
SELECT
  booking_source,
  renewal_journey,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
  AND (
    DATE(looker_trans_date) BETWEEN '2026-03-15' AND '2026-03-22'
    OR DATE(looker_trans_date) BETWEEN '2025-03-16' AND '2025-03-23'
  )
GROUP BY 1,2;
```

### Partner Referral Single GP decline `RECURRING`
Over the last 7 days vs the same week last year, partner referral single-trip GP fell about £5k to £12k. This is mainly a demand problem, not a margin problem: policy volume dropped about 30%, while average GP per policy actually improved slightly; this has been negative on 8 of the last 10 days.

```sql-dig
SELECT
  insurance_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
  AND (
    DATE(looker_trans_date) BETWEEN '2026-03-15' AND '2026-03-22'
    OR DATE(looker_trans_date) BETWEEN '2025-03-16' AND '2025-03-23'
  )
GROUP BY 1;
```

### Partner Referral Annual GP decline `NEW`
Over the last 7 days vs the same week last year, partner referral annual GP fell about £5k to £6k. This may be softer cruise and retail partner demand, especially from older higher-value customers, rather than anything wrong with annual economics.

```sql-dig
SELECT
  insurance_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
  AND (
    DATE(looker_trans_date) BETWEEN '2026-03-15' AND '2026-03-22'
    OR DATE(looker_trans_date) BETWEEN '2025-03-16' AND '2025-03-23'
  )
GROUP BY 1;
```

### Direct new-customer acquisition deterioration `NEW`
Over the last 7 days vs the same week last year, direct GP from new customers fell about £4k to £9k even though policy count edged up slightly. That says traffic quality and conversion got worse: fewer high-intent shoppers reached search, and the ones we converted bought lower-value policies.

```sql-dig
SELECT
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE distribution_channel = 'Direct'
  AND customer_type = 'New'
  AND (
    DATE(looker_trans_date) BETWEEN '2026-03-15' AND '2026-03-22'
    OR DATE(looker_trans_date) BETWEEN '2025-03-16' AND '2025-03-23'
  )
GROUP BY 1;
```

### Aggregator Single GP decline despite volume growth `NEW`
Over the last 7 days vs the same week last year, aggregator single-trip GP fell by about £600 to about £2k even though policy volume jumped about 58%. That is a real issue because single trips do not renew: we sold a lot more very short, cheap trips and made about half as much on each one.

```sql-dig
SELECT
  CASE
    WHEN duration <= 3 THEN '0-3'
    WHEN duration <= 7 THEN '4-7'
    WHEN duration <= 14 THEN '8-14'
    ELSE '15+'
  END AS trip_duration_band,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
  AND (
    DATE(looker_trans_date) BETWEEN '2026-03-15' AND '2026-03-22'
    OR DATE(looker_trans_date) BETWEEN '2025-03-16' AND '2025-03-23'
  )
GROUP BY 1;
```

---

## Customer Search Intent

Search demand is strong. Insurance searches are up about 74% year on year and running ahead of holiday searches at about 51% year on year, so demand is there and insurance is keeping pace better than the wider holiday market. Shoppers are leaning into cheap, compare and specialist-cover behaviour, which says this is mainly a capture issue, not a demand issue. That fits the week: people are shopping, but our direct web funnel is not turning enough of that demand into good-value sales. It also suggests more late-booked Easter single trips, while annual demand is still there if we get in early enough. **Source:** AI Insights — [what_matters], [trend], [divergence], [quarterly]

---

## News & Market Context

The market backdrop is supportive rather than weak. Insurance search demand is up about 57% to 74% year on year, and four-week momentum is up about 39%, with compare and cheap/deals intent rising fastest. **Source:** AI Insights — [what_matters], [yoy], [channels]  
The Iran conflict is still disrupting travel plans and pushing demand toward shorter-lead, Europe-heavy trips, which fits the lower-value single-trip mix we are seeing. **Source:** Internal — [Current Market Events — Active Context], [British Airways issues update today on flights resuming from the Middle East](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai)  
War-related disruption is also making shoppers more cautious about what is and is not covered, which can slow conversion even when search demand is high. **Source:** [How travel insurance works if your holiday is disrupted by war](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war?utm_source=openai)  
Cruise demand is still mixed. Carnival-linked traffic is weaker and Carnival is running at about 80% of last year, while specialist cruise pricing changes have just gone live to improve conversion and GP with partners. **Source:** Internal — [Insurance Weekly Trading w/c 09/03/2026], [Weekly Pricing Updates]  
Easter is early this year and the summer airline schedule starts on 29 March, so short-lead travel demand should stay active over the next two weeks. **Source:** [Good Friday 2026](https://www.timeanddate.com/holidays/uk/good-friday?utm_source=openai)

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Pull a same-day fix list for direct desktop from search results to checkout, then ship the top conversion bug or friction fix this week | Over the last 7 days vs the same week last year, direct single and direct annual GP were down about £28k combined, and desktop search-to-book dropping from about 44% to 31% is the clearest funnel break | ~£28k/week |
| 2 | Put more paid and owned traffic into the best-performing direct single-trip landing pages for “cheap”, “compare” and price-led intent this week | Over the last 7 days vs the same week last year, direct new-customer GP was down about £4k even though the market is searching harder, so we are missing high-intent shoppers | ~£4k/week |
| 3 | Review aggregator single-trip pricing on 0-7 day durations and either tighten rates or cap unprofitable volume | Over the last 7 days vs the same week last year, aggregator single-trip GP fell about £600 despite 58% more policies, and single-trip losses do not come back on renewal | ~£1k/week |
| 4 | Keep renewal ops tight this week by checking auto-renew exceptions, payment token failures and manual recovery queues daily | Over the last 7 days vs the same week last year, renewals added about £8k and are doing real work to offset weaker direct new business | ~£8k/week |
| 5 | Rank partner referral sources by lost GP and meet the worst 3 partners this week to agree a traffic recovery plan | Over the last 7 days vs the same week last year, partner referral GP was down about £9k combined across single and annual, and the issue looks like softer partner demand rather than margin | ~£9k/week |

---
*Generated 15:50 23 Mar 2026 | Tracks: 28 + Follow-ups: 26 | Model: gpt-5.4*
