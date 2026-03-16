---
# HX Trading Briefing — 15 Mar 2026

## Over the last 7 days vs the same week last year, GP was down about £25k, led by a £19k hit in Europe and a £12k drop in direct single-trip, even though market demand is up.

---

## At a Glance

- 🔴 **Europe GP down** — Over the last 7 days vs the same week last year, Europe GP was about £90k, down £19k, about 17% worse, mostly because we made less on each policy rather than because demand disappeared.
- 🔴 **Direct single-trip drag** — Over the last 7 days vs the same week last year, direct single-trip GP was about £31k, down £12k, about 28% worse, with policies down 8% and average GP per policy down 21% as fewer sessions reached search.
- 🔴 **7-day GP down** — Over the last 7 days vs the same week last year, total GP was about £140k, down £25k, about 15% worse, with average GP per policy down to about £22 from about £24.
- 🔴 **Partner single-trip down** — Over the last 7 days vs the same week last year, partner referral single-trip GP was down about £6.5k, about 33% worse, mostly because policies fell 28% with a smaller margin squeeze on top.
- 🟢 **Renewals helped a little** — Over the last 7 days vs the same week last year, renewals GP was up about £600 because stronger take-up more than offset a smaller expiry pool.

---

## What's Driving This

### Europe destination weakness `RECURRING`

Over the last 7 days vs the same week last year, Europe GP fell £19k, from about £109k to £90k. Volume was only down 4%, but average GP per policy fell 14%, and the wider evidence says traffic in market is still there, so this is mainly weaker monetisation on short-haul business; it has been negative on 8 of the last 10 trading days.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND destination_group = 'Europe'
GROUP BY destination_group
```

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct single-trip GP fell £12k, from about £43k to £31k. Traffic was mixed rather than collapsing, but fewer sessions got through to search on both mobile and desktop, policies fell 8%, and average GP per policy fell 21%; this has been negative on 9 of the last 10 trading days, so the data shows a real recurring problem.

```sql-dig
SELECT
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY booking_source
ORDER BY gp DESC
```

### Bronze cover level margin erosion `EMERGING`

Over the last 7 days vs the same week last year, Bronze GP fell about £7.7k. Policies were only down about 5%, but average GP per policy fell 18%, which says we are still selling Bronze but making less on it, especially inside direct single-trip mobile journeys.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND cover_level_name = 'Bronze'
GROUP BY distribution_channel, policy_type
ORDER BY gp DESC
```

### Silver cover level softness `EMERGING`

Over the last 7 days vs the same week last year, Silver GP fell about £7.7k. Most of that came from policies down 11%, with only a smaller drop in average GP per policy, so this looks like weaker mainstream single-trip demand capture rather than a pure pricing issue.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND cover_level_name = 'Silver'
GROUP BY distribution_channel, policy_type
```

### Partner Referral Single volume loss `EMERGING`

Over the last 7 days vs the same week last year, partner referral single-trip GP fell £6.5k. Policies dropped 28% and average GP per policy slipped from about £22 to about £20, so volume is the bigger problem and this may be broad referral weakness rather than one bad partner.

```sql-dig
SELECT
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY booking_source
```

### Direct Annual volume decline `NEW`

Over the last 7 days vs the same week last year, direct annual GP fell £6.2k because policies were down 13% while average GP per policy was basically flat. This is not a margin problem; it means we are investing less in future renewal income because fewer annual customers are getting through to quote and book.

```sql-dig
SELECT
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY booking_source
```

### Aggregator Single margin squeeze `NEW`

Over the last 7 days vs the same week last year, aggregator single-trip GP was down only about £300, but that hides weak quality. We sold 44% more policies but average GP per policy fell from about £2.80 to about £1.70, so volume grew because of traffic on price comparison sites, but the value of each sale got much thinner.

```sql-dig
SELECT
  insurance_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
GROUP BY insurance_group
ORDER BY gp DESC
```

### Renewals GP uplift `NEW`

Over the last 7 days vs the same week last year, renewals GP was up about £600. Renewed policies were up by about 100 because take-up improved from 32% to 42%, even though fewer annual policies were expiring, so the volume win more than offset average GP per renewed policy being down 8%.

```sql-dig
SELECT
  policy_renewal_year,
  SUM(policy_count) AS renewed_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS renewed_gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_renewed_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Renewals'
GROUP BY policy_renewal_year
ORDER BY policy_renewal_year
```

---

## Customer Search Intent

According to Google Sheets dashboard data, over the last week vs last year, overall travel demand is up 65%, insurance searches are up 74%, and holiday searches are up 53%. That tells us the market is growing, so our weakness is more about traffic capture and monetisation than demand. **Source:** Google Sheets — Dashboard Metrics tab.  
According to Google Sheets Insurance Intent data and AI Insights, “travel insurance comparison” is up 375% vs last year and “do I need travel insurance” is up 31% vs last year. That fits a market where shoppers are highly price-sensitive and need more reassurance before they buy. **Source:** Google Sheets — Insurance Intent tab; AI Insights — divergence.  
According to AI Insights, Spain, the Canaries and Algarve are seeing strong planning demand, which lines up with the broader Europe search strength but also with heavier short-haul price shopping. **Source:** AI Insights — deep_dive; Google Sheets — Dashboard Metrics tab.  
According to Google Sheets Insurance Intent history, March is usually a strong travel insurance month outside the COVID break years, so the softer performance over the last 7 days is not because the market has gone quiet. **Source:** Google Sheets — Insurance Intent tab.

---

## News & Market Context

Jet2 says it has launched its biggest ever Summer 2026 programme, including a new Gatwick base and more Spain, Canaries and Algarve capacity. That supports the view that short-haul travel demand is healthy and should be feeding insurance traffic. **Source:** [Jet2 Summer 2026 announcement](https://www.jet2.com/news/2024/09/Jet2_com_and_Jet2holidays_launch_biggest_ever_Summer_programme_for_2026?utm_source=openai)  
AI Insights also says easyJet and TUI are adding capacity, which fits the rise in holiday and insurance search demand and the pressure on Europe pricing. **Source:** AI Insights — deep_dive.  
Millions of EHIC and GHIC cards are expiring, while the NHS says they are not a replacement for travel insurance. That should support intent, especially for customers searching for simple cover guidance. **Source:** [ITIJ on expiring EHIC/GHIC cards](https://www.itij.com/latest/news/millions-uk-ehicghic-cards-set-expire-2025-raising-insurance-concerns?utm_source=openai)  
BA is still dealing with some Middle East route disruption and offering flexibility on affected routes. That is more relevant to service messaging than to the main commercial miss over the last 7 days. **Source:** [Yahoo / BA update](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai)  
Internal change logs matter here too: recent landing-page, direct marketing and rebuild changes line up with the drop in sessions reaching search in direct web journeys. **Source:** Internal — Landing Page Changes 13th Feb 2026; Insurance Direct Marketing; Insurance Rebuild Notes.

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Run a 48-hour rollback or A/B test on the recent direct landing-page and quote-flow changes for single-trip mobile, measured on session-to-search and booked GP | Over the last 7 days vs last year, direct single-trip GP is down about £12k and session-to-search has fallen sharply despite traffic holding up overall | ~£12k/week |
| 2 | Review Europe single-trip pricing and underwriter cost by Bronze and Silver, then retest value messaging on results pages for short-haul trips | Over the last 7 days vs last year, Europe is down £19k and Bronze and Silver together are down about £15k, mostly because we are making less on each policy | ~£19k/week |
| 3 | Shift paid search and onsite messaging harder into annual, medical, EHIC/GHIC and comparison-intent terms | Over the last 7 days vs last year, direct annual policies are down 13%, so we are missing future renewal income while insurance intent is up 74% in market | ~£6k/week |
| 4 | Pull partner-level cuts for referral single-trip, starting with Europe-heavy web sales, and fix or pause the weakest sources | Over the last 7 days vs last year, partner referral single-trip is down about £6.5k, mostly from volume loss rather than margin alone | ~£7k/week |
| 5 | Put guardrails on aggregator single-trip for very short trips and low-value quotes instead of chasing extra volume | Over the last 7 days vs last year, aggregator single-trip volume is up 44% but average GP per policy is down about 41%, so some of that growth is barely worth having | ~£1k/week |

---

_Generated 07:22 16 Mar 2026 | 23 investigation tracks | gpt-5_

---
*Generated 12:00 16 Mar 2026 | Tracks: 23 + Follow-ups: 29 | Model: gpt-5.4*
