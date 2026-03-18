---
# HX Trading Briefing — 17 Mar 2026

## GP was soft again over the last 7 days vs the same period last year — down about £24k, with direct single the biggest drag and renewals only partly offsetting it.

---

## At a Glance

- 🔴 **Weekly GP down** — Over the last 7 days vs the same period last year, GP was about £139k, down £24k or 15%, with direct single the biggest hit.
- 🔴 **Direct single is the main problem** — Over the last 7 days vs the same period last year, direct single GP fell about £11.7k, with policies down 8%, quote-stage sessions down 8%, and GP per policy down about £5.
- 🔴 **Partner referral weakened again** — Over the last 7 days vs the same period last year, partner referral GP fell about £11k across single and annual, mostly from lower referred volume and weaker margin after commission.
- 🟡 **Direct annual demand was softer** — Over the last 7 days vs the same period last year, direct annual GP fell about £11k as policies dropped 18%; that means less investment into future renewal income.
- 🟢 **Renewals helped** — Over the last 7 days vs the same period last year, renewal GP rose about £8k as renewed policies grew 14% and average GP improved slightly.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same period last year, direct single GP fell about £11.7k, from about £42k to £30k. Traffic into quote was weaker, with search-stage sessions down 8%, and conversion got worse at the top of funnel on both mobile and desktop, while GP per policy fell from about £22 to £17 as underwriter cost rose faster than price. This has been negative on 8 of the last 10 trading days.

```sql-dig
SELECT
  p.distribution_channel,
  p.policy_type,
  SUM(p.policy_count) AS policies,
  SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(p.total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_price,
  SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new` p
WHERE p.transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND p.distribution_channel = 'Direct'
  AND p.policy_type = 'Single'
GROUP BY 1,2;
```

### Partner Referral Single GP decline `RECURRING`

Over the last 7 days vs the same period last year, partner referral single GP fell about £5.8k, from about £19k to £13.5k. Volume was the main issue, with policies down 27%, and margin got squeezed as commission per policy rose from about £20 to £25 and underwriter cost took a bigger share of the price. This has been negative on 7 of the last 10 trading days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_commission,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Direct Annual GP decline `EMERGING`

Over the last 7 days vs the same period last year, direct annual GP fell about £11k as policies dropped 18%. Traffic and booked sessions were weaker, so this looks like softer annual demand rather than a pricing issue, which means we are investing less into future renewal income.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

### Partner Referral Annual GP decline `EMERGING`

Over the last 7 days vs the same period last year, partner referral annual GP fell about £5k, with policies down 19% and average GP down about £21. This may be older cruise-heavy partner traffic weakening, with commission also taking a bigger bite.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_commission
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

### New customer GP deterioration in Direct `EMERGING`

Over the last 7 days vs the same period last year, direct new-customer GP fell about £1k even though policies grew 20%. That says traffic from new shoppers improved, but we made less on each sale, with average GP per policy down about £8.

```sql-dig
SELECT
  customer_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Direct'
  AND customer_type = 'New'
GROUP BY 1;
```

### Aggregator Single GP decline `NEW`

Over the last 7 days vs the same period last year, aggregator single GP was down about £500. Traffic through comparison sites looks strong because policies jumped 50%, but average GP roughly halved, so we are buying volume with much weaker quality.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Destination mix shift away from Europe GP `NEW`

Over the last 7 days vs the same period last year, Europe GP fell about £20k even though policy count was only down 2%. That points to weaker quality rather than missing demand, with more price-led and single-trip weighted sales pulling average GP down.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
GROUP BY 1;
```

### Renewals Annual GP growth `NEW`

Over the last 7 days vs the same period last year, renewal GP rose about £8k, with renewed policies up 14% and average GP up about £1. This is good news and exactly the payoff we want from the annual book.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS renewed_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS renewed_gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_renewed_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

---

## Customer Search Intent

According to Google Sheets Insurance Intent and Dashboard Metrics, travel insurance search intent is running about 74% above last year, ahead of broader holiday search demand at about 51% above last year. According to AI Insights — deep_dive and divergence — “travel insurance deals” is up about 986% YoY, “cheapest” is up about 141% YoY, and comparison-led terms are up about 400% YoY, which fits the weaker direct monetisation and stronger price-led shopping. According to AI Insights — channels — Spain, Greece and Italy are the main destination winners, while GHIC/EHIC and “do I need travel insurance” searches are also rising, which suggests customers are checking rules and value before they buy. Rival brand intent is also stronger, with Staysure up about 52% YoY and AllClear up about 33% YoY, especially among older and medical shoppers. **Source:** Google Sheets — Insurance Intent tab; **Source:** Google Sheets — Dashboard Metrics tab; **Source:** AI Insights — what_matters, deep_dive, divergence, channels.

---

## News & Market Context

According to AI Insights — trend and deep_dive — this is not a weak-demand market overall; it is a more competitive, price-led market where shoppers are comparing harder before buying. British Airways is still adjusting Middle East flying and offering flexible rebooking on some routes, which keeps disruption concerns visible for travellers. **Source:** AI Insights — trend, deep_dive; **Source:** [British Airways issues update today on flights resuming from the Middle East](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai)  
According to AI Insights — news — war-risk exclusions are getting more attention, which may be pushing customers to read policy wording more closely and favour reassurance-led messaging. Saga is publicly highlighting cover extensions for stranded customers, which shows where competitor messaging is leaning. **Source:** AI Insights — news; **Source:** [How travel insurance works if your holiday is disrupted by war](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war?utm_source=openai); **Source:** [Saga Middle East travel disruption](https://www.saga.co.uk/travel-insurance/middle-east-travel-disruption?utm_source=openai)  
Cruise partner traffic is also soft, with Carnival flows down about 20% in the active market notes, which helps explain partner referral weakness. Internal market notes also show specialist cruise product changes launched on 17 Mar 2026, so partner and cruise conversion should be checked again once that beds in. **Source:** Current Market Events — Cruise Partner Dynamics; **Source:** Current Market Events — Key Pricing Changes.

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Fix direct single landing-to-search drop on mobile and desktop, starting with Bronze and Silver medical journeys | Direct single lost about £11.7k over the last 7 days vs last year, with quote-stage sessions down 8% and mobile session-to-search down 4pp | ~£12k/week |
| 2 | Reprice or rebalance the worst direct single schemes where underwriter cost has outrun customer price | Direct single GP per policy fell from about £22 to £17 over the last 7 days vs last year, with Bronze and Silver medical schemes the biggest drags | ~£8k/week |
| 3 | Push partner referral recovery with cruise partners and challenge commission on the weakest single-trip deals | Partner referral lost about £11k over the last 7 days vs last year, mostly from lower volume and weaker margin after commission | ~£11k/week |
| 4 | Lean harder into direct annual demand capture through owned channels and CRM | Direct annual policies were down 18% over the last 7 days vs last year, which means less investment into future renewal income | ~£11k/week |
| 5 | Protect renewal momentum by tightening auto-renew and renewal contact journeys now | Renewals added about £8k over the last 7 days vs last year and are offsetting roughly a third of the wider decline | ~£8k/week |

---

---
*Generated 12:20 18 Mar 2026 | Tracks: 23 + Follow-ups: 29 | Model: gpt-5.4*
