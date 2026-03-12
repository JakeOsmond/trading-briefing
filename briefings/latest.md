---
# HX Trading Briefing — 11 Mar 2026

## Direct annual was the biggest drag over the last 7 days vs the same week last year: GP fell about £11k, and total GP ended at £154k, down £26k or 14%.

---

## At a Glance

- 🔴 **Overall GP** — Over the last 7 days vs the same week last year, GP was £154k, down £26k or 14%, with policy count flat at 7.1k and average GP down from £25 to £22.
- 🔴 **Direct annual** — Over the last 7 days vs the same week last year, direct annual GP fell £11k to £46k, with policies down 11% and average GP down 11%; traffic fell on mobile and desktop and conversion also weakened.
- 🔴 **Gold products** — Over the last 7 days vs the same week last year, Gold GP fell about £10k to £54k, with policies down 9% and average GP down 8%; we sold fewer higher-value policies.
- 🔴 **Partner single** — Over the last 7 days vs the same week last year, partner referral single-trip GP fell £8k to £14k, with policies down 28% and average GP down from £25 to £22.
- 🔴 **Direct single** — Over the last 7 days vs the same week last year, direct single-trip GP fell £7k to £38k even though policies rose 3%; weaker top-of-funnel conversion and lower GP per sale did the damage.

---

## What's Driving This

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct annual GP fell £11k to £46k. Policies were down 11% and average GP fell from £55 to £49, with annual sessions down on mobile and desktop and session-to-search conversion weaker on both devices.  
This is the third straight weak week and it has been negative on 8 of the last 10 days. Price rose a little, but underwriter cost rose faster and annual medical paths, especially Silver Main Annual Med HX, were worth less per session.

```sql-dig
SELECT
  transaction_date,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY 1
ORDER BY 1;
```

### Gold cover level GP decline `RECURRING`

Over the last 7 days vs the same week last year, Gold GP fell about £10k to £54k. Volumes were down 9% and average GP fell from £57 to £53, so we sold fewer Gold policies and made less on each one.  
This has been negative on 7 of the last 10 days. The weakness links back to direct single and direct annual paths where shoppers are buying down or landing in cheaper combinations.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND cover_level_name = 'Gold'
GROUP BY 1,2
ORDER BY gp DESC;
```

### Partner Referral Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, partner referral single-trip GP fell £8k to £14k. Policies dropped 28% and average GP fell from £25 to £22, so this was mainly fewer sales with some margin squeeze on top.  
This has been negative on 8 of the last 10 days. We cannot see web traffic here, but cruise-heavy partner schemes were especially weak and costs rose faster than price.

```sql-dig
SELECT
  scheme_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1
ORDER BY gp DESC;
```

### Silver Main Annual Med HX scheme decline `RECURRING`

Over the last 7 days vs the same week last year, Silver Main Annual Med HX lost about £8k of GP and ended at about £15k. Policies fell 16% and average GP dropped from £55 to £44, with weaker annual traffic and softer conversion into this medical path.  
This has been negative on 8 of the last 10 days. Search demand from older medical shoppers is up, so this looks more like a win-rate problem than a market demand problem.

```sql-dig
SELECT
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND scheme_name = 'Silver Main Annual Med HX'
GROUP BY 1;
```

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct single-trip GP fell £7k to £38k. Policies were up 3%, but average GP dropped from £22 to £18, while mobile sessions fell 4% and session-to-search conversion fell to 14% from 18% across the direct web estate.  
This has been negative on 9 of the last 10 days. Underwriter cost per policy rose much faster than price, discounting edged up, and the biggest mobile paths in Bronze and Gold were worth less per session.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1
ORDER BY gp DESC;
```

### Renewals Annual GP decline `RECURRING`

Over the last 7 days vs the same week last year, renewals annual GP fell £1k to £51k. Volume was up 9%, which is healthy, but average GP fell from £45 to £40, so we made less on each renewal.  
This has been negative on 7 of the last 10 days. The issue is value, not volume, with lower renewal price and heavier discounts offsetting the good retention trend.

```sql-dig
SELECT
  policy_renewal_year,
  auto_renew_opt_in,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY 1,2
ORDER BY 1,2;
```

### Aggregator Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, aggregator single-trip GP fell by about £500 to £2k. Volumes jumped 42%, but average GP fell from about £3 to £2, so we won more single-trip sales at worse economics.  
This has been negative on 7 of the last 10 days. Unlike annuals, single-trip losses do not build future renewal income, so this needs an economics floor by partner and trip type.

```sql-dig
SELECT
  insurance_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) AS total_commission,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_commission,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
GROUP BY 1
ORDER BY policies DESC;
```

### Europe destination GP decline `EMERGING`

Over the last 7 days vs the same week last year, Europe GP fell £13k to £102k. Policy count was flat, so this was mostly lower value per policy, down from £23 to £20.  
This has been negative on 6 of the last 10 days. Demand for short-haul trips looks healthy, but more of it is coming through cheaper single-trip and aggregator sales.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND destination_group = 'Europe'
GROUP BY 1,2
ORDER BY gp DESC;
```

## Customer Search Intent

According to Google Sheets Dashboard Metrics, travel insurance search intent is up 74% over the latest period vs the same period last year, with the insurance index at 11.5 vs 6.6 last year. According to AI Insights, that growth is heavily price-led: “travel insurance comparison” is up 826%, “travel insurance price” is up 312%, and “compare travel insurance” is up 31% over the latest period vs last year. According to AI Insights, older medical demand is also rising, with “travel insurance over 70” up 216% over the latest period vs last year, which should support annual medical if we win the click and convert it. According to Dashboard Metrics, 4-week momentum is also up 38%, so market demand is not the core problem right now. According to AI Insights, HX brand search is down 9% over the latest period vs last year, which fits weaker direct win rates in high-value paths. **Source:** Google Sheets — Insurance Intent tab; **Source:** Google Sheets — Dashboard Metrics tab; **Source:** AI Insights — what_matters, yoy, channels

## News & Market Context

According to AI Insights, cheap-flight searches are up 135% over the latest period vs last year, which fits the weaker Europe mix we are seeing: plenty of travel demand, but more price-led short-haul demand. According to AI Insights, Staysure and AllClear are both growing while over-70s search demand is up 216%, which helps explain why Silver Main Annual Med HX is under pressure in a growing medical market. According to [AP News](https://apnews.com/article/5aad69a1bab3ebcbe1bb56d07e19d17b?utm_source=openai), Spain is seeing record visitor demand, which supports volume into Europe but not necessarily good margin if customers are shopping on price. According to [WTW](https://www.wtwco.com/en-gb/news/2025/11/double-digit-healthcare-cost-increases-projected-to-persist-into-2026-and-beyond?utm_source=openai), medical cost inflation remains in double digits into 2026, which matches the underwriter cost pressure showing up in direct and renewal margins over the last 7 days. According to AI Insights and [Yahoo’s BA update](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai), Middle East disruption is still live, but it looks more like a service and claims risk than the main reason for this week’s sales mix shift. **Source:** AI Insights — news

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Reprice direct single on the worst-hit mobile Bronze and Gold paths where underwriter cost rose faster than price, and cap discounting there this week | Over the last 7 days vs the same week last year, direct single lost £7k and average GP fell 18%, with the sharpest GP/session drop on mobile | ~£7k/week |
| 2 | Fix the direct annual medical journey, starting with Silver Main Annual Med HX landing pages, quote flow and price points on mobile and desktop | Over the last 7 days vs the same week last year, direct annual lost £11k, and Silver Main Annual Med HX alone was down about £8k with weaker traffic and conversion | ~£11k/week |
| 3 | Review partner single cruise-heavy schemes and renegotiate commission or price where GP per policy has slipped below target | Over the last 7 days vs the same week last year, partner single lost £8k, driven by lower volume and weaker margin | ~£8k/week |
| 4 | Put a minimum GP floor on aggregator single by partner and trip type, while keeping annual volume growth intact as renewal investment | Over the last 7 days vs the same week last year, aggregator single sold 42% more policies but made about £500 less GP, and single-trip losses do not create renewal value | ~£1k/week |
| 5 | Raise renewal price floors by cohort where discounting is doing the damage, without hurting retention | Over the last 7 days vs the same week last year, renewals GP fell £1k even though volumes were up 9%, so the issue is value per sale | ~£1k/week |

---

_Generated 06:57 12 Mar 2026 | 22 investigation tracks | gpt-5_

---
*Generated 16:30 12 Mar 2026 | Tracks: 22 + Follow-ups: 35 | Model: gpt-5.4*
