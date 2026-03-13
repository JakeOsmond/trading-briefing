---
# HX Trading Briefing — 12 Mar 2026

## GP fell again over the last 7 days vs the same week last year, down £28k or 16%, and the biggest hit is still direct web under-capture — traffic is there, but too few people are reaching quotes and buying.

---

## At a Glance

- 🔴 **Overall GP** — Over the last 7 days vs the same week last year, GP was £147k, down £28k or 16%, with average GP per policy down to £22 from £25 while volumes were only down 3%.
- 🔴 **Direct annuals** — Over the last 7 days vs the same week last year, direct annual GP was £43k, down £10k or 19%, because mixed traffic turned into fewer quotes and fewer annual sales, which means less investment into future renewal income.
- 🔴 **Direct single trips** — Over the last 7 days vs the same week last year, direct single-trip GP was £35k, down £9k or 21%; sessions were mixed, but weaker conversion and higher underwriter cost did most of the damage.
- 🔴 **Direct web capture** — Over the last 7 days vs the same week last year, direct web sessions rose 15% but search-stage sessions fell 13%, which left us about £18k short because more visitors failed to reach a quote.
- 🔴 **Partner single trips** — Over the last 7 days vs the same week last year, partner single-trip GP was £15k, down £7k or 33%, driven by lower partner flow and weaker cruise and medical economics.

---

## What's Driving This

### Overall web funnel under-capture `RECURRING`

Over the last 7 days vs the same week last year, direct web sessions rose 15% to about 68k, but search-stage sessions fell 13% to about 9.4k, costing us about £18k of GP. This has been negative on 9 of the last 10 trading days, and the main issue is desktop traffic quality: sessions were up 34% on desktop, but too few visitors moved through to quote and sale.

```sql-dig
SELECT
  COUNT(DISTINCT CASE WHEN session_start_date BETWEEN '2026-03-05' AND '2026-03-12' THEN session_id END) AS ty_sessions,
  COUNT(DISTINCT CASE WHEN session_start_date BETWEEN '2026-03-05' AND '2026-03-12' AND booking_flow_stage = 'Search' THEN session_id END) AS ty_search_sessions,
  COUNT(DISTINCT CASE WHEN session_start_date BETWEEN '2025-03-06' AND '2025-03-13' THEN session_id END) AS ly_sessions,
  COUNT(DISTINCT CASE WHEN session_start_date BETWEEN '2025-03-06' AND '2025-03-13' AND booking_flow_stage = 'Search' THEN session_id END) AS ly_search_sessions
FROM `hx-data-production.commercial_finance.insurance_web_utm_4`;
```

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct annual GP fell £10k to £43k, with policies down 12% to 852. Traffic was mixed rather than weak overall, but quote capture got worse on both desktop and mobile, so we sold fewer annuals and invested less into future renewal income; this has been negative on 7 of the last 10 trading days.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Direct' AND policy_type = 'Annual';
```

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct single-trip GP fell £9k to £35k, even though policy volume was almost flat at about 2.0k. Traffic was mixed, but conversion weakened and average GP per policy dropped 20% to £17 from £22 as underwriter cost rose and Bronze and Silver economics got worse; this has been negative on 8 of the last 10 trading days.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Direct' AND policy_type = 'Single';
```

### Aggregator Annual volume decline despite strategic investment `RECURRING`

Over the last 7 days vs the same week last year, aggregator annual volume fell 16% to 862 policies, so we invested less into future renewal income even though reported GP was about £2k better. This has been soft on volume in 7 of the last 10 trading days, which points to weaker competitiveness or lower bid exposure while demand is strong.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Aggregator' AND policy_type = 'Annual';
```

### Partner Referral Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, partner single-trip GP fell £7k to £15k, with policies down 29% to 640. We cannot see web traffic here, but lower partner flow plus weaker cruise and medical economics did the damage, and this has been negative on 8 of the last 10 trading days.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Partner Referral' AND policy_type = 'Single';
```

### Renewals Annual GP decline `EMERGING`

Over the last 7 days vs the same week last year, renewals GP fell £2k to £49k even though renewal volumes rose 6% to about 1.2k policies. There is no traffic issue here; the drag is lower value per policy, with fewer higher-value renewals coming through.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Renewals' AND policy_type = 'Annual';
```

### Partner Referral Annual GP decline `NEW`

Over the last 7 days vs the same week last year, partner annual GP fell by about £1k to £9k with volume flat at 151 policies. That means the issue is economics, not demand, with medical annual schemes making less on each sale.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Partner Referral' AND policy_type = 'Annual';
```

### Aggregator Single GP decline `NEW`

Over the last 7 days vs the same week last year, aggregator single-trip GP fell about £300 to £1.8k, while volume jumped 45% to about 1.0k policies. We cannot see aggregator traffic, but the outcome is clear: we bought more single-trip sales at much worse economics, and that matters because single trips have no renewal payback.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Aggregator' AND policy_type = 'Single';
```

---

## Customer Search Intent

According to Google Sheets Dashboard Metrics, overall market demand is up 62% year on year, with 4-week momentum up 38%, so the market is giving us a real tailwind. According to the same Dashboard Metrics data, insurance searches are up 74% YoY to 11.5, ahead of holiday searches up 48% to 8.3, so people are not just planning trips — they are actively looking for cover. According to Google Sheets Insurance Intent and AI Insights, annual multi-trip, pre-existing medical, comparison, “travel insurance price”, “do I need travel insurance”, and over-70s terms are all stronger year on year, while cruise intent is softer. That lines up with what we are seeing: annual and medical demand should be available, but we are under-capturing it in direct and parts of partner. **Source:** Google Sheets — Dashboard Metrics tab. **Source:** Google Sheets — Insurance Intent tab. **Source:** AI Insights — what_matters.

---

## News & Market Context

According to AI Insights, early Easter timing and fresh seat releases from easyJet, Ryanair, Jet2 and BA are pulling travel planning forward, which supports travel insurance demand now rather than later. **Source:** AI Insights — what_matters. According to AI Insights, disruption from weather and border-rule uncertainty is also lifting insurance consideration, especially for medical cover. **Source:** AI Insights — deep_dive. MoneySuperMarket says average annual multi-trip prices are around £61, which tells us comparison shopping remains intense and aggregator competitiveness still matters. **Source:** [MoneySuperMarket travel insurance statistics](https://www.moneysupermarket.com/travel-insurance/travel-insurance-statistics/). FCA travel insurance access changes took effect from 1 January 2026, and broader FCA priorities still focus on fair customer outcomes, so any funnel or pricing fix needs to stay simple and clear. **Source:** [FCA ICOBS amendment](https://api-handbook.fca.org.uk/files/instrument/ICOBS/FCA%202025/45-2026-01-01.pdf). **Source:** [FCA insurance priorities](https://www.fca.org.uk/publication/regulatory-priorities/insurance-report.pdf).

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Audit and roll back any harmful direct-web landing, gatekeeper or quote-entry changes made since 13 Feb, starting with desktop paths | Over the last 7 days vs the same week last year, direct web sessions were up 15% but search-stage sessions were down 13%, costing about £18k | ~£18k/week |
| 2 | Rework direct single Bronze and Silver pricing and underwriting settings, starting with mobile medical and non-medical journeys | Over the last 7 days vs the same week last year, direct single-trip GP fell £9k and average GP per policy dropped 20% as underwriter cost rose | ~£9k/week |
| 3 | Fix direct annual quote capture on mobile and desktop search journeys to recover volume | Over the last 7 days vs the same week last year, direct annual GP fell £10k and policies were down 12%, which means less investment into future renewal income | ~£10k/week |
| 4 | Review partner cruise and medical single schemes, especially Europe-heavy and medical variants | Over the last 7 days vs the same week last year, partner single-trip GP fell £7k, with lower flow and weaker economics doing the damage | ~£7k/week |
| 5 | Push harder on aggregator annual bids and price points to win back annual volume | Over the last 7 days vs the same week last year, aggregator annual volume fell 16%, which means less investment into future renewal income | ~£2k/week now, bigger LTV upside |

---

_Generated 06:50 13 Mar 2026 | 23 investigation tracks | gpt-5_

---
*Generated 12:42 13 Mar 2026 | Tracks: 23 + Follow-ups: 32 | Model: gpt-5.4*
