---
# HX Trading Briefing — 16 Mar 2026

## GP was soft over the last 7 days vs the same week last year — down about £27k, with direct single and direct annual doing most of the damage despite a healthy market.

---

## At a Glance

- 🔴 **Direct single hurt most** — Over the last 7 days vs the same week last year, direct single GP fell £12k, about 28% worse, as total direct web traffic grew but fewer people got through to search and we made less on each sale.
- 🔴 **Direct annual stayed weak** — Over the last 7 days vs the same week last year, direct annual GP fell £8k, about 17% worse, because we sold 147 fewer annuals; that means weaker investment into future renewal income.
- 🔴 **Silver was a drag** — Over the last 7 days vs the same week last year, Silver cover GP fell £9k, about 14% worse, mainly because direct Silver annual and single underperformed.
- 🔴 **Partner single dropped** — Over the last 7 days vs the same week last year, partner referral single GP fell £6k, about 28% worse, driven by 248 fewer policies and weaker cruise-heavy economics.
- 🟢 **Renewals offset some pain** — Over the last 7 days vs the same week last year, renewals GP rose £3k, about 5% better, because more customers renewed from a smaller expiry pool.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct single GP fell £12k, about 28% worse. Total direct web traffic grew because desktop sessions were up 32% YoY, but mobile sessions dipped 2%, session-to-search fell on both devices, policy volume dropped 9%, and average GP per policy fell from about £22 to £17.  
The data shows this is an internal conversion and margin problem, not weak demand. It has been down on 8 of the last 10 trading days, with underwriter cost per policy up 12% while average price fell 3%.

```sql-dig
SELECT
  transaction_date,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_gp,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_price,
  SUM(CAST(total_net_to_underwriter_inc_gadget AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_uw_cost
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1
UNION ALL
SELECT
  transaction_date,
  SUM(policy_count),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0),
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count),0),
  SUM(CAST(total_net_to_underwriter_inc_gadget AS FLOAT64)) / NULLIF(SUM(policy_count),0)
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2025-03-10' AND '2025-03-17'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1;
```

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct annual GP fell £8k, about 17% worse, because volume dropped 16% from 934 to 787. Traffic was mixed, with desktop sessions up 32% YoY and mobile down 2%, but fewer sessions turned into searches and fewer annual-converting sessions booked on both mobile and desktop.  
This is mainly an acquisition softness issue, not a margin issue, so the problem is weaker investment into future renewal income. It has been down on 8 of the last 10 trading days and average GP per policy was broadly flat at about £51.

```sql-dig
SELECT
  transaction_date,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY 1
UNION ALL
SELECT
  transaction_date,
  SUM(policy_count),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0)
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2025-03-10' AND '2025-03-17'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY 1;
```

### Silver cover level mix deterioration `EMERGING`

Over the last 7 days vs the same week last year, Silver cover GP fell £9k, about 14% worse, with policy volume down 12%. Most of that came from direct Silver annual and single policies, where weaker funnel conversion meant fewer customers reached and bought our core mid-tier cover.  
This may be part of the wider direct weakness rather than a Silver-only issue. It matters because Silver is a big enough part of the book to amplify the direct problem.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND cover_level_name = 'Silver'
GROUP BY 1
UNION ALL
SELECT
  cover_level_name,
  SUM(policy_count),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2025-03-10' AND '2025-03-17'
  AND cover_level_name = 'Silver'
GROUP BY 1;
```

### Partner Referral Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, partner referral single GP fell £6k, about 28% worse, because policies dropped from 921 to 673. We cannot see the full web journey here, but the data shows a clear volume shortfall and weaker economics in cruise-heavy pockets.  
This has been weak on 9 of the last 10 trading days. It matters because these are single trips, so there is no renewal payback to recover the loss.

```sql-dig
SELECT
  transaction_date,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_commission
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1
UNION ALL
SELECT
  transaction_date,
  SUM(policy_count),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count),0)
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2025-03-10' AND '2025-03-17'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1;
```

### Core Silver single medical scheme deterioration `EMERGING`

Over the last 7 days vs the same week last year, Silver Main Single Med HX GP fell £6k. Traffic was there, especially on desktop, but fewer sessions got through to search and lower GP per sale meant both volume and value slipped.  
This may be the clearest scheme-level sign of the wider direct single problem. It lines up with the pressure seen across core direct single medical schemes.

```sql-dig
SELECT
  scheme_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND scheme_name = 'Silver Main Single Med HX'
GROUP BY 1
UNION ALL
SELECT
  scheme_name,
  SUM(policy_count),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0)
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2025-03-10' AND '2025-03-17'
  AND scheme_name = 'Silver Main Single Med HX'
GROUP BY 1;
```

### Partner Referral Annual GP decline `EMERGING`

Over the last 7 days vs the same week last year, partner annual GP fell £4k, with policies down 19%. That means less annual acquisition into future renewal income.  
This may still be early, with only 5 of the last 10 trading days pointing the same way. Older cruise-heavy customers look like the main weak pocket.

```sql-dig
SELECT
  transaction_date,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_commission
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
GROUP BY 1
UNION ALL
SELECT
  transaction_date,
  SUM(policy_count),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count),0)
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2025-03-10' AND '2025-03-17'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
GROUP BY 1;
```

### Aggregator Single GP dilution `NEW`

Over the last 7 days vs the same week last year, aggregator single GP fell by about £500, but volume jumped 49% while average GP per policy fell from about £3 to £2. Traffic through price comparison sites is clearly stronger, but the extra single-trip sales are much cheaper.  
Too early to tell if this gets bigger. It matters because single-trip dilution has no renewal upside.

```sql-dig
SELECT
  transaction_date,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
GROUP BY 1
UNION ALL
SELECT
  transaction_date,
  SUM(policy_count),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count),0)
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2025-03-10' AND '2025-03-17'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
GROUP BY 1;
```

### Renewals GP improvement `NEW`

Over the last 7 days vs the same week last year, renewals GP rose £3k, about 5% better, and renewed policies rose 11% even though fewer annuals were expiring. That points to better renewal conversion, helped by more customers renewing online and through auto-renew.  
This is encouraging, but still early. Treat it as a positive signal rather than a proven shift.

```sql-dig
SELECT
  transaction_date,
  SUM(policy_count) AS renewed_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY 1
UNION ALL
SELECT
  transaction_date,
  SUM(policy_count),
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2025-03-10' AND '2025-03-17'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY 1;
```

## Customer Search Intent

According to Google Sheets dashboard data, over the latest measured period vs the same period last year, overall market demand is up 66%, travel insurance searches are up 75%, and holiday searches are up 56%. According to the Dashboard Metrics tab, the insurance search index is 11.5 versus 6.6 last year, so shoppers are moving closer to purchase rather than just browsing. According to the Insurance Intent and AI Insights tabs, annual, medical and cruise searches are the strongest pockets, with Spain, USA, Turkey and Greece all called out as growing destinations. According to the same dashboard data, 4-week momentum is up 40%, so demand is still building into Easter. This supports the view that direct weakness over the last 7 days is mostly internal, not a market demand problem.  
**Source:** Google Sheets — Dashboard Metrics tab  
**Source:** Google Sheets — Insurance Intent tab  
**Source:** AI Insights — what_matters, channels, seasonal

## News & Market Context

According to AI Insights, airline seat releases and new routes are pulling summer demand forward, which fits the stronger search market. [easyJet’s latest route and sale activity](https://www.the-independent.com/travel/news-and-advice/easyjet-2026-flight-sale-prices-b2793536.html?utm_source=openai) supports that view. According to the ABI, high-cost medical claims in destinations like the USA and Spain are keeping travel insurance purchase intent high, especially for medical-heavy travellers. **Source:** [ABI travel insurance guidance](https://www.abi.org.uk/news/news-articles/2025/8/eight-to-embark-travel-insurance-tips/?utm_source=openai) Comparator pressure also looks intense, with price-led messaging still prominent across the market, which fits stronger aggregator volume but weaker single-trip yield. **Source:** [Consumer Intelligence](https://www.consumerintelligence.com/articles/travel-insurance-policies-nearly-100-cheaper-on-pcws), [MoneySuperMarket](https://www.moneysupermarket.com/travel-insurance/) According to the FCA, the medical signposting threshold changed in January 2026, which may be moving some medical shoppers around the market. **Source:** [FCA Handbook Notice 133](https://www.fca.org.uk/publication/handbook/handbook-notice-133.pdf)

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Audit the direct web funnel from screening to search by device, and check any March CRO, routing or underwriting rule changes | Over the last 7 days vs the same week last year, direct single lost £12k/week and direct annual lost £8k/week while traffic held up but session-to-search fell on mobile and desktop | ~£20k/week |
| 2 | Reprice or tighten direct single Bronze and Silver medical schemes where underwriter cost has risen fastest | Over the last 7 days vs the same week last year, direct single lost £12k/week, with core medical schemes driving the margin squeeze | ~£8k/week |
| 3 | Review partner cruise single deals and commission terms with the biggest partners | Over the last 7 days vs the same week last year, partner single lost £6k/week and weaker cruise-heavy economics look to be part of it | ~£6k/week |
| 4 | Push harder on direct annual acquisition through medical intent pages and paid search | Over the last 7 days vs the same week last year, direct annual sold 147 fewer policies even though market insurance searches are up 75% YoY, so we are missing future renewal income | ~£8k/week |
| 5 | Keep renewal web and auto-renew exposure live while conversion is improving | Over the last 7 days vs the same week last year, renewals added about £3k/week from a smaller expiry pool | ~£3k/week |

---

---
*Generated 12:57 17 Mar 2026 | Tracks: 23 + Follow-ups: 39 | Model: gpt-5.4*
