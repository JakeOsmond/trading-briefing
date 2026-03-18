---
# HX Trading Briefing — 17 Mar 2026

## Over the last 7 days vs the same week last year, GP was down because Europe value got squeezed and direct single-trip is still the clearest recurring drag, despite healthy market demand.

---

## At a Glance

- 🔴 **Weekly GP down** — Over the last 7 days vs the same week last year, GP was £139k, down £24k or 15%, with the biggest drag from cheaper Europe sales and weaker direct single-trip value.
- 🔴 **Europe value squeezed** — Over the last 7 days vs the same week last year, Europe GP fell by £20k to £89k on almost flat volume, so we kept the customers but made a lot less on each sale.
- 🔴 **Direct single still the main recurring issue** — Over the last 7 days vs the same week last year, direct single GP fell by £12k to £30k because fewer web sessions reached quote and average GP per policy dropped 21%.
- 🟢 **Renewals helped** — Over the last 7 days vs the same week last year, renewal GP grew by about £8k to about £53k, up 18%, which is exactly the payoff from earlier annual acquisition.
- 🔴 **Yesterday was soft too** — Yesterday vs the same day last year, GP was £19k, down £3k or 12%, with 731 policies sold, down 72 or 9%.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct single GP fell by £12k to £30k, and this has now been down on 9 of the last 10 days. Traffic was not the main problem: desktop sessions were up 34% and mobile was only down 2%, but search sessions fell 8%, so fewer people reached a price, and average GP per policy dropped 21% to about £17.

The data shows this is a funnel-and-value problem inside core direct single-trip journeys, especially mobile Bronze and Silver, rather than weak demand. Search-to-book actually improved, but not enough to offset lower quote reach and weaker single-trip yield.

```sql-dig
SELECT
  p.distribution_channel,
  p.policy_type,
  p.booking_source,
  SUM(p.policy_count) AS policies,
  SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new` p
WHERE p.transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND p.distribution_channel = 'Direct'
  AND p.policy_type = 'Single'
GROUP BY p.distribution_channel, p.policy_type, p.booking_source;
```

### Europe destination GP decline `RECURRING`

Over the last 7 days vs the same week last year, Europe GP fell by £20k to £89k, while volume was only down 2%, and this has been negative on 8 of the last 10 days. Traffic held up, but average GP per policy fell 17% to about £20, so this was clearly a value squeeze, not a demand collapse.

The data points back to the same issue as direct single: Europe is heavy in Bronze and Silver single-trip products, and those journeys monetised worse, especially on mobile. Market demand is there, but it is arriving more price sensitive and more heavily shopped.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND destination_group = 'Europe'
GROUP BY destination_group;
```

### Bronze cover level GP decline `RECURRING`

Over the last 7 days vs the same week last year, Bronze GP fell by about £9k to about £28k, with average GP per policy down 19% to about £17. Traffic was there through direct web, but the cheaper single-trip mix and weaker mobile monetisation meant Bronze did less work for us.

This looks like the clearest product-level read-across from the direct single problem. It has been dragged down by lower-value Europe-heavy single-trip sales rather than a broad collapse in demand.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND cover_level_name = 'Bronze'
GROUP BY cover_level_name;
```

### Silver cover level GP decline `RECURRING`

Over the last 7 days vs the same week last year, Silver GP fell by about £9k to about £52k, mostly because volume was down about 13%. Traffic into direct web was healthy overall, so this looks more like weaker conversion into quote and softer single-trip value than a top-of-funnel issue.

This is the same pattern as Bronze, just one tier up. The evidence points to weaker core direct single-trip economics, with Europe-heavy mobile journeys doing less GP per session.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND cover_level_name = 'Silver'
GROUP BY cover_level_name;
```

### Direct Annual GP decline `EMERGING`

Over the last 7 days vs the same week last year, direct annual GP fell by about £11k to about £37k because volume dropped about 18%. Traffic was weaker and fewer people got through to quote, but this matters as softer acquisition, not as a margin issue, because annual volume growth is how we invest in future renewal income.

The likely cause is the same market shift we have been seeing since the Iran conflict, with customers hesitating on annual commitments and choosing single-trip instead. This is worth watching because it affects the future renewal book.

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
GROUP BY distribution_channel, policy_type;
```

### Partner Referral Single GP decline `EMERGING`

Over the last 7 days vs the same week last year, partner referral single GP fell by about £6k to about £13k because we sold 27% fewer policies. Traffic is the likely main cause here, especially in cruise-linked partner journeys, with a smaller hit from weaker economics per sale.

This may reflect the wider market softness in cruise partner traffic rather than an HX-specific issue. It is material enough to act on, but the evidence is less clean than the direct web story.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_commission
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY distribution_channel, policy_type, booking_source;
```

### Renewals GP growth `EMERGING`

Over the last 7 days vs the same week last year, renewals GP grew by about £8k to about £53k, up 18%. There is no web traffic read here, but this is good-quality growth and the clearest proof that earlier annual acquisition is feeding through into profit.

The uplift looks to be from more customers renewing and slightly better GP per renewed policy. Even if some of this is expiry mix, it is still one of the strongest offsets in the week.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  booking_source,
  SUM(policy_count) AS renewed_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS renewed_gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_renewed_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY distribution_channel, policy_type, booking_source;
```

### Aggregator Single GP decline `NEW`

Over the last 7 days vs the same week last year, aggregator single GP slipped by about £500 to about £2k even though volume jumped 50%. We got more sales, but average GP per policy nearly halved to about £2, so these extra single-trip sales were low value.

This looks like a pricing-and-commission quality issue rather than a traffic problem we can diagnose from web data, because aggregator journeys sit off-site. It is small in pounds today, but the direction is poor because single-trip losses do not have a renewal upside.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_commission,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
GROUP BY distribution_channel, policy_type;
```

---

## Customer Search Intent

According to Google Sheets Dashboard Metrics, travel insurance search demand is up 74% vs last year, ahead of holiday searches at 51%, so demand is clearly there. According to AI Insights and the Insurance Intent tab, overall insurance searches are up about 57% to 63% YoY, and 4-week momentum is up about 40%, which fits our strong traffic backdrop. According to the same sources, price-led terms are surging: “travel insurance deals” is up 986% YoY, “cheapest” is up 141%, and comparison intent is up 400%, which lines up with weaker single-trip yield and cheaper Europe mix. AI Insights also says older and medical shoppers are more active, with Staysure up 52% and AllClear up 33%, plus stronger demand for Defaqto and review-led searches. According to AI Insights seasonal tracking, ski demand is still elevated and Easter demand should build over the next 2 to 3 weeks. **Source:** Google Sheets — Insurance Intent tab; Google Sheets — Dashboard Metrics tab; AI Insights — what_matters, deep_dive, trend, seasonal

---

## News & Market Context

According to AI Insights, this is not a demand problem: customers are still shopping, but they are shopping harder on price and comparison. According to the current market events context, the Iran conflict is still pushing some customers away from annual commitments and from Worldwide into Europe, which fits softer direct annual acquisition and lower-value Europe mix. British Airways has continued to adjust parts of its Middle East operation and offered flexibility to customers, which keeps disruption and cover questions live. **Source:** [British Airways update via Yahoo News](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai) Standard travel insurance often excludes war-related losses, which helps explain why customers are scrutinising wording and value more closely. **Source:** [The Week on war exclusions](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war?utm_source=openai) According to Insurance Age, Staysure has moved onto aggregators, which may be adding competitive pressure in older and medical segments. **Source:** [Insurance Age on Staysure aggregators](https://www.insuranceage.co.uk/insight/7956783/staysure-moves-onto-aggregators) According to current market context, Carnival traffic is down about 20% at market level, which fits the weaker partner referral single-trip performance in cruise-linked flows. **Source:** Current Market Events — Cruise Partner Dynamics

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Audit the direct mobile single-trip funnel from landing to search for Bronze and Silver, then fix the biggest quote-reach drop-offs | Over the last 7 days vs last year, direct single lost ~£12k/week because sessions held up but search sessions fell 8% and avg GP per policy fell from ~£22 to ~£17 | ~£12k/week |
| 2 | Review Europe single-trip pricing, discounting and product presentation on core direct journeys so we defend value, not just volume | Over the last 7 days vs last year, Europe lost ~£20k/week on almost flat volume, so the problem is lower value per sale | ~£20k/week |
| 3 | Work with cruise partners to improve CTA visibility and traffic into insurance, starting with Carnival-linked journeys | Over the last 7 days vs last year, partner referral single lost ~£6k/week and the main hit was fewer policies sold | ~£6k/week |
| 4 | Check aggregator single-trip pricing floors and commission on mainstream compare schemes, and stop any schemes that are barely above break-even | Over the last 7 days vs last year, aggregator single volume was up 50% but GP was only about £2 per policy | ~£1k/week |
| 5 | Push renewal capture through CRM and contact-centre save activity while renewal demand is strong | Over the last 7 days vs last year, renewals added ~£8k/week and are the cleanest profit offset in the week | ~£8k/week |

---

---
*Generated 17:14 18 Mar 2026 | Tracks: 23 + Follow-ups: 33 | Model: gpt-5.4*
