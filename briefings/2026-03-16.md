---
# HX Trading Briefing — 15 Mar 2026

## GP was about £140k over the last 7 days vs the same week last year — down £25k, or 15% worse, because we turned more web traffic into fewer quotes and made less on core single-trip sales.

---

## At a Glance

- 🔴 **Europe drag** — Over the last 7 days vs the same week last year, Europe GP was £90k — down £19k, about 17% worse, mostly because average GP per policy fell 14% on mainstream short-haul business.
- 🔴 **Direct single-trip squeeze** — Over the last 7 days vs the same week last year, Direct single GP was £31k — down £12k, about 28% worse, with weaker quote generation and lower GP per policy.
- 🔴 **Existing customers softer** — Over the last 7 days vs the same week last year, Existing-customer GP was £109k — down £19k, about 15% worse, as Direct traffic got to quote less often.
- 🔴 **Bronze and Silver weaker** — Over the last 7 days vs the same week last year, Bronze GP was £27k and Silver GP was £52k — both down about £8k, driven by weaker web sales in core Direct products.
- 🟢 **Renewals helped a bit** — Over the last 7 days vs the same week last year, Renewal GP was £49k — up about £600, with renewal rate up to 42% from 32%, partly offsetting a smaller expiry book.

---

## What's Driving This

### Direct Single GP decline `MEDIUM CONFIDENCE`

This appears to be the clearest real issue over the last 7 days vs the same week last year: Direct single GP fell £12k to £31k. Traffic was up overall across web sessions, but session-to-search fell to 14% from 18%, and Direct single got hit hardest as mobile and desktop were both worse at turning visits into quotes; bank holiday timing makes YoY a bit messier, but this has been weak 9 of the last 10 days.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Direct' AND policy_type = 'Single';
```

### Europe destination GP decline `LOW CONFIDENCE`

This may be a real portfolio-level drag over the last 7 days vs the same week last year: Europe GP fell £19k to £90k. Volume was only down 4%, so most of the damage came from lower GP per policy, which fits the weaker Direct single and partner single performance in price-shopped short-haul trips.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE destination_group = 'Europe';
```

### Direct Annual volume shortfall `LOW CONFIDENCE`

This may be share loss rather than a value problem over the last 7 days vs the same week last year: Direct annual GP fell £6k to £41k because policies were down 13% while GP per policy stayed flat. Traffic was there in the market, but fewer Direct annual visits turned into quotes, so we missed annual volume that we do want because it feeds future renewal income.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Direct' AND policy_type = 'Annual';
```

### Partner Referral Single volume loss `LOW CONFIDENCE`

This may be partner-specific weakness over the last 7 days vs the same week last year: Partner single GP fell £7k to £13k as policies dropped 28%. We cannot see partner web traffic, but the pattern looks volume-led, especially Europe and cruise partners like Carnival, with a bit of extra squeeze from higher commission and underwriter cost.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Partner Referral' AND policy_type = 'Single';
```

### Existing customer GP decline `LOW CONFIDENCE`

This may be another angle on the same Direct problem over the last 7 days vs the same week last year: Existing-customer GP fell £19k to £109k. Existing web sessions were down 6% and session-to-search dropped to 19% from 23%, so fewer known customers even got far enough to see a price.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE customer_type = 'Existing';
```

### Bronze cover level deterioration `LOW CONFIDENCE`

This may be noise at cover-level, but Bronze GP was down £8k to £27k over the last 7 days vs the same week last year. Traffic weakness shows up mainly in Direct web, and the bigger problem is poorer value per sale, especially in Bronze Main Single.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE cover_level_name = 'Bronze';
```

### Silver cover level deterioration `VERY LOW CONFIDENCE`

This is likely directionally right but still noisy over the last 7 days vs the same week last year: Silver GP fell £8k to £52k. It looks mostly volume-led, with fewer web sales in core Direct annual and single products rather than a sharp change in conversion at checkout.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE cover_level_name = 'Silver';
```

### Renewal book smaller but rate stronger `VERY LOW CONFIDENCE`

This is likely a small genuine positive over the last 7 days vs the same week last year: Renewal GP was up about £600 to £49k. We had fewer expiries to work with, but renewal rate improved to 42% from 32%, which is good news even if average GP on renewed policies was lower.

```sql-dig
WITH expiring AS (
  SELECT
    SUM(CASE WHEN travel_end_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_expiring,
    SUM(CASE WHEN travel_end_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_expiring
  FROM `hx-data-production.commercial_finance.insurance_policies_new`
  WHERE policy_type = 'Annual'
),
renewed AS (
  SELECT
    SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_renewed,
    SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
    SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_renewed,
    SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
  FROM `hx-data-production.commercial_finance.insurance_policies_new`
  WHERE distribution_channel = 'Renewals' AND policy_type = 'Annual'
)
SELECT * FROM expiring CROSS JOIN renewed;
```

---

## Customer Search Intent

According to Google Sheets dashboard data, travel insurance search demand is up 74% vs last year, ahead of holiday searches at 53%, and overall market demand is up 65% YoY with 38% 4-week momentum. According to AI Insights, “travel insurance comparison” is up 375% and “do I need travel insurance” is up 31%, which says shoppers are in market but are price-checking hard. According to AI Insights, “book holiday 2026” is up 420%, so early planners are there too, which should support annual multi-trip demand if we catch it well. The gap between insurance and holiday searches has widened to 3 from 1 last year, so insurance intent is accelerating faster than general holiday dreaming. This fits what we saw internally: traffic is available, but we are losing too many people before quote. **Source:** Google Sheets — Insurance Intent tab. **Source:** Google Sheets — Dashboard Metrics tab. **Source:** AI Insights — what_matters, divergence, yoy, quarterly.

---

## News & Market Context

According to Jet2, it has put its biggest ever Summer 2026 programme on sale, including a new Gatwick base and more Spain, Canaries, Algarve and Greece capacity, which supports strong short-haul demand. easyJet is also adding routes and a Newcastle base, while TUI has a large Summer 2026 programme, so the market backdrop is supportive rather than weak. According to ITIJ, millions of EHIC/GHIC cards are expiring and new EU entry rules are adding uncertainty, which helps search demand for travel insurance explainers. According to the NHS guidance cited in AI Insights, GHIC is not a replacement for travel insurance, so there is a live content and PPC opportunity around clear cover messaging. On competition, the FCA is still scrutinising insurance and PCW sales journeys into 2026, and Which? has kept pressure on confusing comparison-led customer outcomes, which matters because shoppers are clearly getting more price-led. Middle East disruption is in the news, but that looks more like servicing and content demand than the cause of this week’s Direct weakness. **Source:** [Jet2 Summer 2026 programme](https://www.jet2.com/news/2024/09/Jet2_com_and_Jet2holidays_launch_biggest_ever_Summer_programme_for_2026?utm_source=openai) **Source:** [ITIJ on EHIC/GHIC expiry](https://www.itij.com/latest/news/millions-uk-ehicghic-cards-set-expire-2025-raising-insurance-concerns?utm_source=openai) **Source:** [FCA Insurance Regulatory Priorities](https://www.fca.org.uk/publication/regulatory-priorities/insurance-report.pdf) **Source:** [FCA response to Which? super-complaint](https://www.fca.org.uk/publication/corporate/fca-response-which-super-complaint.pdf) **Source:** AI Insights — deep_dive, news.

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Fix Direct quote generation on mobile and desktop for single-trip paths, starting with Bronze and Silver entry journeys | Direct single lost about £12k over the last 7 days vs LY, with session-to-search down hard despite strong traffic | ~£12k/week |
| 2 | Push AMT-first PPC and landing pages on “travel insurance comparison”, GHIC/EHIC and destination terms | Search intent is up 74% YoY and Direct annual volume is down 13%, so we are missing future renewal income | ~£6k/week |
| 3 | Review Bronze and Silver Direct single pricing and underwriter cost by scheme this week | Bronze and Silver together lost about £15k over the last 7 days vs LY, mostly from weaker value per sale | ~£8k/week |
| 4 | Get Partner team into Carnival and other weak cruise partners to recover lost volume | Partner Referral single GP is down about £7k over the last 7 days vs LY, mainly volume-led | ~£7k/week |
| 5 | Re-market Existing customers with fast quote journeys and clearer value copy | Existing-customer GP is down about £19k over the last 7 days vs LY because fewer visitors reach quote | ~£11k/week |

---

_Generated 08:00 16 Mar 2026 | 23 investigation tracks | gpt-5_

---
*Generated 18:04 16 Mar 2026 | Tracks: 23 + Follow-ups: 29 | Model: gpt-5.4*
