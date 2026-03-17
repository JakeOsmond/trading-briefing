---
# HX Trading Briefing — 16 Mar 2026

## GP weakened again over the last 7 days vs the same week last year, with £143k GP down £27k or 16%, mainly because Direct single-trip and annual sales missed a strong market.

---

## At a Glance

- 🔴 **Overall GP** — Over the last 7 days vs the same week last year, GP was £143k — down £27k, about 16% worse.
- 🔴 **Direct Single** — Over the last 7 days vs the same week last year, Direct single-trip GP fell £12k, down 28%, with softer traffic, weaker conversion, and average GP per policy down from £22 to £17.
- 🔴 **Direct Annual** — Over the last 7 days vs the same week last year, Direct annual GP fell £8k, down 17%, mostly because we sold 16% fewer policies in a market where demand is up.
- 🔴 **Direct Existing** — Over the last 7 days vs the same week last year, Direct GP from existing customers fell £18k, down 25%, with sessions down 4% and session-to-search down from 23% to 19%.
- 🟢 **Renewals offset** — Over the last 7 days vs the same week last year, renewal GP rose £3k, up 5%, because more expiring annual customers kept their cover.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, Direct single-trip GP fell to £31k from £43k — down £12k or 28%. Traffic softened and conversion got worse: mobile sessions were down 2%, tablet down 19%, session-to-search fell from 17% to 14%, search-to-book fell from 58% to 54%, and average GP per policy dropped from £22 to £17; this has been negative on 8 of the last 10 trading days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY distribution_channel, policy_type;
```

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same week last year, Direct annual GP fell to £41k from £49k — down £8k or 17%. This is mainly a volume miss, not an annual margin problem: we sold 16% fewer policies, booked sessions fell on mobile and desktop, and weaker session-to-search meant we captured less future renewal income.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY distribution_channel, policy_type;
```

### Direct Existing customer GP decline `RECURRING`

Over the last 7 days vs the same week last year, Direct existing-customer GP fell to £55k from £73k — down £18k or 25%. Early-funnel weakness did most of the damage: sessions were down 4%, session-to-search fell from 23% to 19%, and this has been weak for 10 of the last 10 trading days.

```sql-dig
SELECT
  customer_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND distribution_channel = 'Direct'
  AND customer_type = 'Existing'
GROUP BY customer_type;
```

### Bronze cover GP decline `EMERGING`

Over the last 7 days vs the same week last year, Bronze GP fell to £28k from £37k — down £9k or 24%. The hit is mostly Direct single-trip mobile, where fewer people reached quote and lower-value Bronze sales made less money per policy.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND cover_level_name = 'Bronze'
GROUP BY cover_level_name;
```

### Silver cover GP decline `EMERGING`

Over the last 7 days vs the same week last year, Silver GP fell to £54k from £63k — down £9k or 14%. This looks like the same Direct funnel weakness showing up in a bigger cover tier, with lower volume across both single and annual.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND cover_level_name = 'Silver'
GROUP BY cover_level_name;
```

### Partner Referral Single GP decline `NEW`

Over the last 7 days vs the same week last year, Partner Referral single-trip GP fell to £14k from £20k — down £6k or 28%. Volume did most of the damage, down 27%, and with no web funnel here this looks more like softer partner feed than an on-site conversion problem.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY distribution_channel, policy_type;
```

### Partner Referral Annual GP decline `NEW`

Over the last 7 days vs the same week last year, Partner Referral annual GP fell to £8k from £12k — down £4k or 34%. This may be a phone and commission-mix issue rather than broad annual weakness, so treat it as an acquisition volume problem first, not an annual margin problem.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
GROUP BY distribution_channel, policy_type, booking_source;
```

### Renewals GP increase `NEW`

Over the last 7 days vs the same week last year, renewal GP rose to £52k from £49k — up £3k or 5%. More expiring annual customers kept their cover, which helped offset weaker new business.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY distribution_channel, policy_type;
```

---

## Customer Search Intent

According to Google Sheets Dashboard Metrics, over the last 7 days vs the same week last year, overall travel demand intent is up 66% YoY, with insurance intent up about 75% and holiday intent up about 56%. According to the same source, insurance search interest is 11.5 vs 6.6 last year, so people are not just browsing trips — they are actively shopping for cover. Google Sheets Insurance Intent and AI Insights both show strength in annual, medical and cruise-related searches, plus more “comparison”, “price” and “do I need travel insurance” queries. That points to a live market and supports the view that our Direct weakness is a capture problem, not a demand problem.  
**Source:** Google Sheets — Dashboard Metrics tab  
**Source:** Google Sheets — Insurance Intent tab  
**Source:** AI Insights — what_matters, divergence, channels

---

## News & Market Context

According to AI Insights, summer 2026 seat releases and new routes from easyJet and Ryanair are pulling bookings forward and lifting insurance demand. [The Independent](https://www.the-independent.com/travel/news-and-advice/easyjet-2026-flight-sale-prices-b2793536.html?utm_source=openai) reports easyJet’s latest seat release is helping drive that demand. According to ABI, high-profile medical claim stories, including very high USA claim costs and repatriation costs from Spain of about £45k, are keeping medical-cover shopping high. [ABI](https://www.abi.org.uk/news/news-articles/2025/8/eight-to-embark-travel-insurance-tips/?utm_source=openai) and AI Insights also say GHIC-versus-insurance questions remain a strong trigger for travel insurance searches. The FCA’s travel insurance signposting threshold rose from £100 to £200 from 1 Jan 2026, which matters most for medical journeys and customer clarity. Paid search costs are also rising, so if rivals are bidding harder, weak Direct quote starts will show up quickly.  
**Source:** AI Insights — deep_dive, news, seasonal  
**Source:** [FCA review](https://www.fca.org.uk/publications/multi-firm-reviews/travel-insurance-signposting-rules-consumers-medical-conditions-review)  
**Source:** [Wired Media PPC commentary](https://www.wiredmedia.co.uk/2025/03/10/cpc-pricing-in-insurance-company-ppc-efforts/)

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Audit Direct mobile quote-start journeys end to end, starting with existing-customer and single-trip landing to search pages, and roll back any journey changes made in the last 4 weeks | Over the last 7 days vs the same week last year, Direct Existing and Direct Single lost about £30k/week, with session-to-search doing most of the damage | ~£30k/week |
| 2 | Check Direct single-trip pricing and underwriter cost by Bronze and Silver non-medical mobile journeys, then fix any scheme or price gaps where cost rose faster than price | Over the last 7 days vs the same week last year, Direct single avg GP per policy fell from £22 to £17, and Bronze plus Silver lost about £18k/week | ~£18k/week |
| 3 | Push harder into annual PPC and SEO demand now, with annual multi-trip made more prominent in Direct journeys | Over the last 7 days vs the same week last year, Direct annual volume fell 16% even though market insurance intent is up about 75%, so we are missing future renewal income | ~£8k/week |
| 4 | Review partner referral feeds and phone performance with top partners, starting with single-trip Europe demand and annual phone conversion | Over the last 7 days vs the same week last year, Partner Referral single lost about £6k/week and annual lost about £4k/week | ~£10k/week |
| 5 | Keep the current renewal treatment in place and identify what lifted retention this week so we can repeat it on the next expiry cohorts | Over the last 7 days vs the same week last year, Renewals added about £3k/week and were the only meaningful offset | ~£3k/week |

---

---
*Generated 15:13 17 Mar 2026 | Tracks: 23 + Follow-ups: 34 | Model: gpt-5.4*
