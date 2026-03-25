---
# HX Trading Briefing — 25 Mar 2026

## Europe and Direct single-trip drove the damage over the last 7 days vs the same period last year, with GP down hardest where direct conversion and value both weakened.

---

## At a Glance

- 🔴 **Europe GP down** — Over the last 7 days vs the same period last year, Europe-destination GP fell by about £18k to £85k, about 18% worse, with only a small policy drop but much weaker GP per sale.
- 🔴 **Direct single-trip weak** — Over the last 7 days vs the same period last year, Direct single GP fell by about £13k to £29k, down 32%, because mobile traffic fell, desktop conversion got worse, and we made about £5 less per policy.
- 🟡 **Conversion, not demand, is the issue** — Over the last 7 days vs the same period last year, Google Trends showed travel insurance demand up and comparison shopping rising, so the direct single weakness looks internal to our funnel and yield rather than the market going soft.
- 🟢 **Annual volume still matters** — Where annual sales grew over the last 7 days vs the same period last year, that is us investing in future renewal income, not a margin problem on day one.
- 🟡 **Europe mix needs watching** — Over the last 7 days vs the same period last year, more demand sat in Europe while Worldwide stayed softer, which is fine for volume but weaker for value if we convert more low-margin mainstream Europe singles.

---

## What's Driving This

### Europe destination GP decline `RECURRING`

Over the last 7 days vs the same period last year, Europe-destination GP fell by about £18k to £85k, down 18%. Policies were only down about 3%, so most of the damage came from average GP per policy falling from about £22 to £19, with the weakness sitting mainly inside direct single-trip Europe journeys.

The data shows this is not a one-day wobble. It has been negative on 8 of the last 10 trading days, and the likely causes are weaker direct conversion plus margin squeeze where underwriter cost rose faster than selling price in mainstream Europe single business.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(ppc_cost_per_policy,0)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(ppc_cost_per_policy,0)) / NULLIF(SUM(policy_count),0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
  AND destination_group = 'Europe'
GROUP BY 1;
```

### Direct single GP decline `RECURRING`

Over the last 7 days vs the same period last year, Direct single GP fell by about £13k to £29k, down 32%. Traffic was mixed, with desktop sessions up 24% but mobile down 6%, and conversion got materially worse, especially desktop search-to-book and mobile session-to-search.

This is clearly the core trading issue. It has been negative on 9 of the last 10 trading days, and we also made less on each sale, with average GP per policy down from about £21 to £16 as underwriter cost took a bigger share of price.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(ppc_cost_per_policy,0)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(ppc_cost_per_policy,0)) / NULLIF(SUM(policy_count),0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Mobile direct single funnel weakness `RECURRING`

Over the last 7 days vs the same period last year, mobile direct sessions for single-trip were down about 6%, but the bigger hit was conversion quality. Mobile session-to-search fell from 19% to 15%, a drop of 4 percentage points, which means fewer people even reached a quote.

That lines up with the GP/session collapse in core Bronze single paths. The data shows weaker funnel progression, not just less traffic, and this has been part of the broader direct single problem all week.

```sql-dig
SELECT
  device_type,
  COUNT(DISTINCT session_id) AS sessions
FROM `hx-data-production.commercial_finance.insurance_web_utm_4`
WHERE session_start_date BETWEEN '2026-03-17' AND '2026-03-24'
  AND scheme_type = 'Single'
  AND channel = 'Direct'
GROUP BY 1;
```

### Desktop direct single conversion collapse `RECURRING`

Over the last 7 days vs the same period last year, desktop direct traffic actually grew, with sessions up about 24%, but that did not convert. Desktop session-to-search fell from 14% to 13%, and search-to-book dropped from 42% to 30%, down 12 percentage points.

So traffic was not the problem here. We brought people in, but far fewer of them bought, which points to quote quality, pricing, or checkout friction in the direct single desktop journey.

```sql-dig
SELECT
  device_type,
  COUNT(DISTINCT session_id) AS sessions,
  COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Search' THEN session_id END) AS search_sessions,
  COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Just_Booked' THEN session_id END) AS booked_sessions
FROM `hx-data-production.commercial_finance.insurance_web_utm_4`
WHERE session_start_date BETWEEN '2026-03-17' AND '2026-03-24'
  AND scheme_type = 'Single'
  AND channel = 'Direct'
  AND device_type = 'computer'
GROUP BY 1;
```

### Direct single value per sale down `RECURRING`

Over the last 7 days vs the same period last year, average GP per direct single policy fell by about £5, from £21 to £16, down 23%. Price was flat at about £58, so we did not win this back through customer price.

The squeeze came from costs. Underwriter cost share rose from 46% to 50% of gross, which means the same kinds of sales were worth less even before the conversion hit.

```sql-dig
SELECT
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_price_inc_ipt,
  SUM(CAST(total_net_to_underwriter_inc_gadget AS FLOAT64)) / NULLIF(SUM(policy_count),0) AS avg_uw_cost,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(ppc_cost_per_policy,0)) / NULLIF(SUM(policy_count),0) AS avg_gp_post_ppc
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single';
```

### Bronze and Silver direct single paths deteriorated `EMERGING`

Over the last 7 days vs the same period last year, the biggest GP/session erosion sat in mainstream direct single paths, especially Bronze single non-medical and Bronze single medical on mobile. In plain English, our core entry products are turning sessions into much less money than they did a year ago.

That matters because these paths carry a lot of our direct single volume. If we fix only premium tiers, we will miss the biggest part of the loss.

```sql-dig
SELECT
  cover_level_name,
  medical_split,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(ppc_cost_per_policy,0)) AS gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1,2
ORDER BY gp ASC;
```

### Annual acquisition remains strategic `HIGH`

Where annual new business was negative on day-one margin over the last 7 days vs the same period last year, that is expected. We are deliberately investing in future renewal income, so annual volume growth is good news unless the 13-month customer value is also negative.

The check to make is simple. If a negative-margin annual segment stays negative after adding estimated 13-month insurance and non-insurance GP for new customers, that segment is not paying back and needs attention.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(ppc_cost_per_policy,0)) AS day_one_gp,
  SUM(
    (CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(ppc_cost_per_policy,0))
    + COALESCE(est_13m_ins_gp,0)
    + COALESCE(est_13m_other_gp,0)
  ) AS value_13m
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
  AND policy_type = 'Annual'
  AND customer_type = 'New'
GROUP BY 1,2;
```

### Search demand remains supportive `HIGH`

Over the last 7 days vs the same period last year, customer search demand for travel insurance was up and comparison intent was also rising. That means the market backdrop is helping, not hurting, and reinforces that our direct single underperformance is an internal issue.

This fits the wider trading picture since the Iran conflict started. Customers are still travelling and still shopping for cover, but mix has tilted toward Europe and short-lead trips.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(ppc_cost_per_policy,0)) AS gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
GROUP BY 1,2,3;
```

---

## Customer Search Intent

Google Trends narrative points the right way for us today: travel insurance demand is up year on year, and comparison shopping is also strengthening, which usually means customers are still in-market and actively weighing options rather than dropping out altogether. Searches for [travel insurance](https://trends.google.com/trends/explore?q=travel%20insurance&geo=GB), [holiday insurance](https://trends.google.com/trends/explore?q=holiday%20insurance&geo=GB), and [travel insurance comparison](https://trends.google.com/trends/explore?q=travel%20insurance%20comparison&geo=GB) are all supportive.

The important read-across is that insurance intent appears to be keeping pace with, or slightly outperforming, broader holiday planning searches like [cheap flights](https://trends.google.com/trends/explore?q=cheap%20flights&geo=GB) and [package holiday](https://trends.google.com/trends/explore?q=package%20holiday&geo=GB). So this does not look like a market demand air pocket. It looks more like we are failing to convert demand that is still there.

---

## News & Market Context

The Middle East conflict is still distorting travel patterns, with HX context noting that since 28 February customers have shifted away from some Worldwide demand and toward Europe and shorter-lead trips. **Source:** Internal — Current Market Events — Active Context. That fits the Europe-heavy mix we are seeing, but it does not explain the full direct single conversion miss.

Internal pricing notes say Europe Including was already at maximum margin and Europe Excluding was capped, so mainstream Europe single-trip business had less room to recover higher underwriter costs through price. **Source:** Drive: [Weekly Pricing Updates](https://drive.google.com). HX notes also say search click-through stayed strong year on year after the Iran conflict began, which again points away from weak intent and toward an internal funnel or quote-quality issue. **Source:** Drive: [Weekly Pricing Updates](https://drive.google.com).

Google Trends and internal market commentary also point to active comparison shopping, which matters because it means customers are still willing to buy if the proposition is right. **Source:** Internal — Market Intelligence Sources. Separately, Ofgem’s new household energy price cap and rail fare increases are small headwinds for disposable income, but they are background pressure rather than the main story in this week’s insurance numbers. **Source:** Travel Events Log, 2026-03-23.

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Run a same-day diagnostic on direct single desktop quote-to-book by cover level, starting with Bronze and Silver, and check for pricing, quote competitiveness, or checkout breakage. | Over the last 7 days vs the same period last year, desktop sessions were up 24% but search-to-book fell 12 percentage points, which is the clearest recoverable loss. | ~£8k/week |
| 2 | Review mobile direct single funnel drop-off from landing to search for core Europe single journeys, then ship the fastest fix on the highest-exit step. | Over the last 7 days vs the same period last year, mobile session-to-search fell 4 percentage points and Europe was the biggest GP loss at about £18k. | ~£6k/week |
| 3 | Reprice or tighten underwriting where direct single underwriter cost has risen without price following, especially in mainstream Europe single products. | Over the last 7 days vs the same period last year, direct single average GP per policy fell about £5 while customer price stayed flat. | ~£5k/week |
| 4 | Check 13-month customer value for any annual segment that is negative on day one, and protect volume where 13-month value stays positive. | Annual losses on day one are strategic, but any annual segment that stays negative after 13-month value is destroying value, not building it. | ~£3k/week |
| 5 | Put a daily watch on Bronze non-medical and medical direct single GP/session until conversion stabilises. | These core paths are where the biggest GP/session erosion is showing up, so they are the fastest read on whether fixes are working. | ~£2k/week |

---
*Generated 07:42 25 Mar 2026 | Tracks: 29 + Follow-ups: 29 | Model: gpt-5.4*
