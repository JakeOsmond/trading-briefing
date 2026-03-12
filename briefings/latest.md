---
# HX Trading Briefing — 11 Mar 2026

## Over the last 7 days vs the same period last year, GP was down £26k and the biggest drag was direct annual, with direct single and partner single also hurting despite stronger market demand.

---

## At a Glance

- 🔴 **7-day GP down** — Over the last 7 days vs the same period last year, GP was about £154k, down £26k or 14%, because we sold about the same number of policies but made less on each one.
- 🔴 **Direct annual weakest** — Over the last 7 days vs the same period last year, direct annual GP fell £11k, down 20%, with policies down 11% as fewer sessions got through to quote and average GP per policy dropped 11%.
- 🔴 **Gold cover weaker** — Over the last 7 days vs the same period last year, Gold GP fell about £10k, down 16%, with policies down 9% and average GP per policy down 8%, so we lost both volume and value.
- 🔴 **Partner single hurt** — Over the last 7 days vs the same period last year, partner referral single-trip GP fell about £8k, down 36%, mostly because policies were down 28%, especially in cruise.
- 🔴 **Direct single still a problem** — Over the last 7 days vs the same period last year, direct single-trip GP fell about £7k, down 15%, even though policies were up 3%, because margin got squeezed hard.

---

## What's Driving This

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same period last year, direct annual GP fell £11k to about £46k, down 20%, and policies fell 11% to 923. Traffic was mixed, with mobile sessions down 4% and desktop up 34%, but both devices got fewer sessions through to quote so the extra desktop traffic did not turn into enough sales.

Average GP per policy fell 11% to about £49 because underwriter cost rose faster than price, and high-value medical annual journeys were much less valuable than last year. This has been negative on 7 of the last 10 trading days, but annual volume is still investment in future renewal income, so the issue here is weaker capture rather than annual margin itself.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

### Gold cover level GP decline `RECURRING`

Over the last 7 days vs the same period last year, Gold GP fell about £10k to about £54k, down 16%. Policies were down 9% and average GP per policy fell 8% to about £53, so both volume and value weakened.

This showed up across direct annual and direct single, with weaker quote generation and softer value per sale. This has been negative on 7 of the last 10 trading days.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND cover_level_name = 'Gold'
GROUP BY 1;
```

### Partner Referral Single GP decline `RECURRING`

Over the last 7 days vs the same period last year, partner referral single-trip GP fell about £8k to about £14k, down 36%, with policies down 28%. This was mainly a traffic and demand problem through weaker partner sales, especially cruise, and margin also got squeezed.

Commission and underwriter cost rose faster than price, and this has been negative on 8 of the last 10 trading days. Because this is single-trip, there is no renewal payback, so this is a real profit issue.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_commission,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Silver Main Annual Med HX scheme decline `RECURRING`

Over the last 7 days vs the same period last year, Silver Main Annual Med HX GP fell about £8k to about £15k, down 33%, with policies down 16%. Traffic was mixed by device, but fewer annual sessions converted into this scheme and GP per converting session was lower on both mobile and desktop.

That matters because older and medical search demand is growing faster than the market, and we are under-catching it. This has been negative on 8 of the last 10 trading days.

```sql-dig
SELECT
  scheme_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND scheme_name = 'Silver Main Annual Med HX'
GROUP BY 1;
```

### Direct Single GP deterioration `RECURRING`

Over the last 7 days vs the same period last year, direct single-trip GP fell about £7k to about £38k, down 15%, even though policies were up 3%. Traffic was softer on mobile, desktop traffic rose strongly, but both devices got fewer sessions through to quote and the sales we did win were worth less.

Average GP per policy fell 18% to about £18 from about £22 because underwriter cost rose 17% while average price rose only 1%. This has been negative on 8 of the last 10 trading days, and because this is single-trip there is no future renewal income to rescue it.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Aggregator Single GP erosion `RECURRING`

Over the last 7 days vs the same period last year, aggregator single-trip GP was only about £500 lower, but the underlying quality got worse fast. Policies were up 42%, yet average GP per policy fell to about £2 from about £3, so we bought a lot more low-value single-trip sales.

This has been negative on 7 of the last 10 trading days. Traffic is clearly there through comparison sites, but it is very price-led traffic and the extra volume is not paying us back.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_commission,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Elite cover level GP collapse `EMERGING`

Over the last 7 days vs the same period last year, Elite GP fell about £2k to about £3k, down 40%, even though policies were up 21%. So this is not a traffic problem. It is a value problem.

Average GP per policy roughly halved to about £6 from about £11, driven mainly by weak aggregator Elite economics. This has been negative on 5 of the last 10 trading days.

```sql-dig
SELECT
  cover_level_name,
  distribution_channel,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND cover_level_name = 'Elite'
GROUP BY 1,2;
```

### Renewals annual GP softness `EMERGING`

Over the last 7 days vs the same period last year, renewals annual GP slipped about £1k to about £51k, down 2%, even though policies were up 9%. Retention volume is healthy, but we made less on each renewal.

Average GP per policy fell about 11% as price dropped and discounting got a bit heavier. This is emerging rather than major, and the healthy annual volume still supports future renewal income.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_discount_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_discount,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-04' AND '2026-03-11'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

## Customer Search Intent

According to Google Sheets Dashboard Metrics, over the latest reporting window travel insurance search intent is up 74% vs last year, with the insurance index at 11.5 vs 6.6 last year, while holiday search intent is up 50%. According to Google Sheets Insurance Intent data and AI Insights, demand is getting more price-led, with “travel insurance comparison” up 826% year on year and “cheap flights” up 135%. According to AI Insights, “travel insurance over 70” is up 216% vs last year, which says older and medical customers are growing faster than the market. That fits our trading issue over the last 7 days: demand is there, but we are not converting and monetising direct annual medical traffic well enough. **Source:** Google Sheets — Insurance Intent tab; **Source:** Google Sheets — Dashboard Metrics tab; **Source:** AI Insights — what_matters, yoy, divergence.

## News & Market Context

According to AI Insights, market demand is supportive rather than weak, with overall demand up 63% year on year and 4-week momentum up 38%, so our issue is capture and margin rather than category demand. According to [AP News](https://apnews.com/article/5aad69a1bab3ebcbe1bb56d07e19d17b?utm_source=openai), airlines are adding Spain and Mediterranean capacity, which should keep travel demand firm into spring. According to [WTW](https://www.wtwco.com/en-gb/news/2025/11/double-digit-healthcare-cost-increases-projected-to-persist-into-2026-and-beyond?utm_source=openai), healthcare cost inflation is still running at double-digit levels, which supports the underwriter cost pressure showing up in direct single and direct annual. According to AI Insights, HX brand search is down 9% while Staysure and AllClear are gaining in older and medical demand, so competition is sharper exactly where we are weakest. According to [Yahoo News](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai) and [The Week](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war?utm_source=openai), Middle East disruption is back in the news, which can drive customer questions and destination anxiety, but standard war exclusions still limit any direct sales upside. **Source:** AI Insights — trend, channels, news.

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Audit and fix the direct quote-entry funnel on mobile and desktop today. Check any pricing, journey, screening or release changes made since 1 Feb, and roll back anything hurting session-to-search. | Over the last 7 days vs the same period last year, direct annual and direct single GP were down about £18k combined, and both devices got fewer sessions through to quote. | ~£18k/week |
| 2 | Rework the direct medical annual journey around Silver Main Annual Med HX. Shorten screening where possible, sharpen medical reassurance copy, and test landing pages that push annual first. | Over the last 7 days vs the same period last year, Silver Main Annual Med HX alone was down about £8k, while over-70 search demand is up 216%. | ~£8k/week |
| 3 | Review partner referral single-trip deals with the biggest cruise partners this week. Challenge commission, placement and cruise pricing where sales quality has weakened. | Over the last 7 days vs the same period last year, partner single-trip GP was down about £8k, mainly from a 28% drop in policies and weaker cruise performance. | ~£8k/week |
| 4 | Tighten direct single-trip pricing on Bronze, Silver and Gold where underwriter cost has outrun price. Start with the mobile journeys showing the biggest GP per session drop. | Over the last 7 days vs the same period last year, direct single-trip GP was down about £7k and average GP per policy fell 18% despite stable volume. | ~£7k/week |
| 5 | Cut back low-value aggregator single-trip exposure on Elite and similar weak-yield pockets, unless volume can be held at better GP per policy. | Over the last 7 days vs the same period last year, aggregator single-trip volume was up 42% but average GP per policy fell from about £3 to about £2, and Elite GP fell about £2k. | ~£2k–£3k/week |

---

_Generated 00:00 12 Mar 2026 | 22 investigation tracks | gpt-5_

---
*Generated 14:47 12 Mar 2026 | Tracks: 22 + Follow-ups: 36 | Model: gpt-5.4*
