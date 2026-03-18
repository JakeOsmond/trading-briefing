---
# HX Trading Briefing — 17 Mar 2026

## Over the last 7 days vs the same period last year, GP was down about £24k, with Direct Single and Direct Annual doing most of the damage while Renewals partly bailed us out.

---

## At a Glance

- 🔴 **Weekly GP down** — Over the last 7 days vs the same period last year, GP was about £139k — down about £24k, or 15% worse, with Direct Single and Direct Annual making up most of the miss.
- 🔴 **Direct Single biggest drag** — Over the last 7 days vs the same period last year, Direct Single GP was about £30k — down about £12k, or 28% worse, because fewer people reached search and we made less on each sale.
- 🔴 **Direct Annual acquisition slower** — Over the last 7 days vs the same period last year, Direct Annual GP was about £37k — down about £11k, or 22% worse, because annual-converting traffic was lighter, so we sold fewer policies and invested less into future renewal income.
- 🟢 **Renewals offset some pain** — Over the last 7 days vs the same period last year, Renewals GP was about £53k — up about £8k, or 18% better, as a stronger renewal rate beat a smaller expiry base.
- 🟡 **Europe still soft on value** — Over the last 7 days vs the same period last year, Europe GP was down about £20k while policy volume was only down about 2%, which says value per sale got weaker more than demand did.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same period last year, Direct Single GP fell about £12k to about £30k. Traffic was mixed, but the bigger issue was conversion and value: mobile sessions were down 2%, desktop sessions were up 34%, session-to-search got worse on both devices, and average GP per policy fell 21% to about £17.  
The data shows this is mainly margin pressure first, then funnel weakness second. Underwriter cost rose faster than price, and the weakest value came from mobile Bronze and Silver single-trip sales. This has been a recurring pattern, not a one-day wobble.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Direct'
  AND policy_type = 'Single'
  AND transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
GROUP BY 1
ORDER BY gp DESC
```

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same period last year, Direct Annual GP fell about £11k to about £37k. The main issue was lower annual-converting traffic and lower volume, with policies down 18%, so we invested less into future renewal income.  
Average GP per policy also slipped about 5%, but that is not the story to chase on annuals. The bigger problem is fewer annual shoppers getting through the funnel, especially on mobile and desktop annual journeys. This has also been recurring.

```sql-dig
SELECT
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Direct'
  AND policy_type = 'Annual'
  AND transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
GROUP BY 1
ORDER BY gp DESC
```

### Direct existing-customer GP decline `RECURRING`

Over the last 7 days vs the same period last year, Direct GP from existing customers fell about £20k to about £51k. Sessions were only down about 4%, but fewer people got through to search and bought, so volume fell harder than traffic.  
That points to a top-of-funnel journey issue, not just weak demand. This has happened consistently across the last 10 trading days, so it looks entrenched.

```sql-dig
SELECT
  customer_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Direct'
  AND customer_type = 'Existing'
  AND transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
GROUP BY 1
```

### Europe destination GP decline `EMERGING`

Over the last 7 days vs the same period last year, Europe GP fell about £20k while policy volume was only down about 2%. That means traffic and demand broadly held up, but we made less on each Europe sale.  
The likely cause is mix and value. More shoppers appear to be buying cheaper Europe cover instead of higher-value Worldwide trips, and lower-tier Europe sales are carrying the book.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE destination_group = 'Europe'
  AND transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
GROUP BY 1,2
ORDER BY gp DESC
```

### Partner Referral Single GP decline `EMERGING`

Over the last 7 days vs the same period last year, Partner Referral Single GP fell about £6k to about £13k. Volume did most of the damage, down 27%, and we also made less on each sale.  
Traffic data is thinner here, so treat the cause with care, but the pattern points to partner-market softness more than a checkout issue on our side.

```sql-dig
SELECT
  agent_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
  AND transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
GROUP BY 1
ORDER BY gp DESC
```

### Partner Referral Annual GP decline `NEW`

Over the last 7 days vs the same period last year, Partner Referral Annual GP fell about £5k to about £8k. Policies were down 19%, so we brought in less annual acquisition through partners and invested less into future renewal income.  
There are signs partner mix got worse as well, but this is a small book, so treat it as a watchout rather than the main fire.

```sql-dig
SELECT
  insurance_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) AS commission_value,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
  AND transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
GROUP BY 1
ORDER BY gp DESC
```

### Aggregator Single GP decline `NEW`

Over the last 7 days vs the same period last year, Aggregator Single GP was down only about £500 to about £2k, but volume was up 50%. We sold a lot more single-trip policies and barely made anything on them, with GP per policy roughly halving to about £2.  
That says comparison-site demand is there, but we are winning low-value sales. This matters because single-trip losses do not have a renewal payoff.

```sql-dig
SELECT
  campaign_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
  AND transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
GROUP BY 1
ORDER BY policies DESC
```

### Renewals GP growth `EMERGING`

Over the last 7 days vs the same period last year, Renewals GP rose about £8k to about £53k. The likely driver was a better renewal rate, which more than offset fewer policies expiring.  
This is good news and worth protecting. The expiry base is smaller, so we should not over-read one week, but the direction is clearly helpful.

```sql-dig
SELECT
  booking_source,
  SUM(policy_count) AS renewed_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS renewed_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
  AND transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
GROUP BY 1
ORDER BY renewed_gp DESC
```

## Customer Search Intent

According to Google Sheets market data, insurance search intent is up 74% year on year, with the Insurance Intent index at 11.5 versus 6.6 last year. According to the same source, holiday search intent is also up, at 8.5, so this is a stronger demand market, not a weak one. According to AI Insights, broader market demand is up about 63% year on year and up 40% on 4-week momentum, which backs that up. According to the Insurance Intent tab, price-led searches are rising fastest: “travel insurance deals” is up 986%, “travel insurance comparison” is up 400%, and “travel insurance price” is up 321%. According to AI Insights, Spain, Greece and Italy are seeing stronger travel interest, which fits Europe volume holding up better than Europe value. **Source:** Google Sheets — Insurance Intent tab. **Source:** Google Sheets — Dashboard Metrics tab. **Source:** AI Insights — trend, deep_dive, yoy, channels.

## News & Market Context

According to the FCA, the travel insurance signposting review published after the 1 January 2026 rule change found better access for customers with medical conditions, which should support medical demand. **Source:** [FCA travel insurance signposting review](https://www.fca.org.uk/publications/multi-firm-reviews/travel-insurance-signposting-rules-consumers-medical-conditions-review)  
According to current HX market context, conflict-linked travel disruption since late February has pushed some customers away from Worldwide trips and towards Europe, which fits Europe holding volume better than value. **Source:** Current Market Events — Active Context, updated 18 Mar 2026.  
According to AI Insights, Staysure search interest is up 52% and AllClear is up 33%, which suggests older and medical customers are actively shopping around trusted brands. **Source:** AI Insights — what_matters.  
According to industry reporting, Middle East disruption is raising travel insurance awareness, but war-related disruption is often excluded from cover, so customer reassurance matters. **Source:** [Insurance Journal](https://www.insurancejournal.com/news/international/2026/03/05/860552.htm), [The Week](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war?utm_source=openai)  
According to internal pricing notes, specialist cruise product changes went live on 17 March 2026, so any cruise upside is more likely to show up next week than in this one. **Source:** Internal — Weekly Pricing Updates.

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Review Direct Single margin by mobile Bronze and Silver today, and decide whether the fix is price, underwriter cost, or cover mix | Over the last 7 days vs the same period last year, Direct Single GP is down about £12k, and the clearest leak is weaker GP per policy in mobile Bronze and Silver | ~£12k/week |
| 2 | Pull a direct funnel check on annual and existing-customer journeys, focused on session-to-search drop by device | Over the last 7 days vs the same period last year, Direct Annual is down about £11k and existing-customer Direct is down about £20k, with top-of-funnel conversion doing most of the damage | ~£11k–£20k/week |
| 3 | Protect renewal momentum by checking auto-renew exceptions and payment failures before week end | Over the last 7 days vs the same period last year, Renewals GP is up about £8k, and this is the one material area helping offset the wider miss | ~£8k/week |
| 4 | Review Partner Referral agents with the steepest single-trip volume drop, especially cruise-heavy partners | Over the last 7 days vs the same period last year, Partner Referral Single and Annual are down about £11k combined, with volume doing most of the damage | ~£11k/week |
| 5 | Tighten Aggregator Single trading in the lowest-value campaigns and price bands | Over the last 7 days vs the same period last year, Aggregator Single volume is up 50% but GP is only about £2k, so we are adding low-value single-trip sales with little payoff | ~£1k/week |

---

---
*Generated 17:58 18 Mar 2026 | Tracks: 23 + Follow-ups: 43 | Model: gpt-5.4*
