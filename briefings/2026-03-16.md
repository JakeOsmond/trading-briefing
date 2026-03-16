---
# HX Trading Briefing — 15 Mar 2026

## Direct single-trip was the main drag over the last 7 days vs the same week last year, down about £12k, and that is why total GP weakened by about £25k despite healthy market demand.

---

## At a Glance

- 🔴 **Direct single-trip** — Over the last 7 days vs the same week last year, direct single-trip GP fell about £12k to £31k, down 28%, with weaker quote creation and about £5 less GP per policy.
- 🔴 **Europe drag** — Over the last 7 days vs the same week last year, Europe GP fell about £19k to £90k, down 17%, mostly because direct and partner single-trip stayed weak and we made less on each policy.
- 🔴 **Partner single-trip** — Over the last 7 days vs the same week last year, partner single-trip GP fell about £7k to £13k, down 33%, mainly because we sold about 250 fewer policies and margin got squeezed.
- 🔴 **Worldwide soft** — Over the last 7 days vs the same week last year, worldwide GP fell about £6k to £50k, down 11%, from slightly fewer sales and weaker value per policy.
- 🟢 **Renewals held up** — Over the last 7 days vs the same week last year, renewal GP was up about £600 to £49k, up 1%, because a better renewal rate offset fewer expiries.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct single-trip GP fell about £12k to £31k, down 28%, and the data shows this is the clearest issue. Traffic was mixed, with mobile sessions down 3% and tablet down 20% partly offset by desktop up 25%, but conversion weakened at the top of funnel, with session-to-search down on mobile to 16% from 20% and on desktop to 13% from 15%, while GP per policy fell to about £17 from £22; this has been negative on 9 of the last 10 trading days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY distribution_channel, policy_type;
```

### Direct single Bronze Main scheme decline `EMERGING`

Over the last 7 days vs the same week last year, Bronze Main single-trip GP fell about £5k to £10k, down 34%, and this looks like one of the biggest reasons direct single-trip is hurting. Traffic into the funnel softened, but the bigger hit was value, with GP per policy dropping to about £11 from £16, especially on mobile no-screening journeys.

```sql-dig
SELECT
  scheme_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND scheme_name = 'Bronze Main Single Med HX'
GROUP BY scheme_name;
```

### Partner Referral Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, partner single-trip GP fell about £7k to £13k, down 33%, and the data shows this is a real recurring problem. We cannot see session traffic here, but policy volume fell 28% to about 660 from about 910 and GP per policy slipped to about £20 from £22 as commission and underwriter costs rose faster than price; this has been negative on 8 of the last 10 days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY distribution_channel, policy_type;
```

### Europe destination GP decline `EMERGING`

Over the last 7 days vs the same week last year, Europe GP fell about £19k to £90k, down 17%. Traffic demand in market still looks healthy, so this points more to weaker single-trip conversion and value capture in direct and partner than to weak Europe demand.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND destination_group = 'Europe'
GROUP BY destination_group;
```

### Worldwide destination GP decline `NEW`

Over the last 7 days vs the same week last year, worldwide GP fell about £6k to £50k, down 11%. This may still be timing noise, but it lines up with slightly fewer profitable single-trip sales and softer value per policy.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND destination_group = 'Worldwide'
GROUP BY destination_group;
```

### Direct Annual GP decline `NEW`

Over the last 7 days vs the same week last year, direct annual GP fell about £6k to £41k, down 13%. This is not a margin problem to fix; we simply sold about 120 fewer annual policies, so we captured less future renewal income, and traffic into annual-buying journeys looks softer.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY distribution_channel, policy_type;
```

### Partner Referral Annual GP decline `NEW`

Over the last 7 days vs the same week last year, partner annual GP fell about £2k to £8k, down 22%. Too early to call a trend, but fewer higher-tier sales and higher commission appear to be the main reasons, so we are bringing in less future renewal income from this channel.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
GROUP BY distribution_channel, policy_type;
```

### Aggregator Single GP decline `NEW`

Over the last 7 days vs the same week last year, aggregator single-trip GP fell about £300 to £2k, down 14%, and that still matters because single-trip has no renewal upside. We cannot see upstream traffic here, but policy volume rose 44% while GP per policy dropped from about £3 to under £2, so this looks like a pricing or cost issue rather than weak demand.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
GROUP BY distribution_channel, policy_type;
```

### Renewals GP improvement `NEW`

Over the last 7 days vs the same week last year, renewal GP was up about £600 to £49k, up 1%, which is helpful but still small. We had fewer expiries over the last 7 days vs the same week last year, but renewal rate improved enough to offset that and keep the renewal book moving in the right direction.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS renewed_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS renewed_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY distribution_channel, policy_type;
```

---

## Customer Search Intent

According to Google Sheets dashboard data, over the last 7 days vs the same week last year, overall travel insurance demand is up about 65% and insurance searches are up about 74%, ahead of holiday searches at about 53%. According to AI Insights, “travel insurance comparison” is up about 375% YoY and “do I need travel insurance” is up about 31% YoY, which says shoppers are in-market and more price-conscious. According to Dashboard Metrics, the insurance intent index is 11.5 vs 6.6 last year, so demand is clearly stronger than a year ago. According to AI Insights, Spain, the Canaries, Algarve, Greece, Turkey and the USA are the main demand pockets, and early-planner terms like “book holiday 2026” are up about 420% YoY. That points to a healthy market and a share-capture problem for us, especially in direct single-trip. **Source:** Google Sheets — Insurance Intent tab. **Source:** Google Sheets — Dashboard Metrics tab. **Source:** AI Insights — trend, deep_dive.

---

## News & Market Context

According to [Jet2’s Summer 2026 announcement](https://www.jet2.com/news/2024/09/Jet2_com_and_Jet2holidays_launch_biggest_ever_Summer_programme_for_2026?utm_source=openai), Jet2 is expanding Summer 2026 capacity across Spain, the Canaries, Algarve, Greece and Florida, which supports outbound demand. According to AI Insights, easyJet is also adding capacity and new routes, which fits with strong comparison-led shopping. According to [ITIJ](https://www.itij.com/latest/news/millions-uk-ehicghic-cards-set-expire-2025-raising-insurance-concerns?utm_source=openai), millions of EHIC and GHIC cards are due to expire, which should push more travellers to think about cover, especially for Europe trips. According to AI Insights, cheap-flight searches are up about 32% YoY and holiday-deal searches are up about 23% YoY, so demand looks booking-led rather than disruption-led. Middle East disruption remains in the background, but AI Insights says it is not a main trading driver over the last 7 days. **Source:** AI Insights — news, trend, deep_dive.

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Fix direct mobile and desktop quote-start on single-trip journeys, starting with the top-of-funnel step before search results | Over the last 7 days vs the same week last year, direct single-trip lost about £12k and session-to-search fell from 20% to 16% on mobile and from 15% to 13% on desktop | ~£12k/week |
| 2 | Review direct single-trip pricing and underwriter cost on Bronze and Silver core schemes | Over the last 7 days vs the same week last year, direct single-trip GP per policy fell about £5 and underwriter cost rose to 53% of gross from 46% | ~£10k/week |
| 3 | Rework partner single-trip pricing and partner commercial terms on the biggest single-trip accounts | Over the last 7 days vs the same week last year, partner single-trip lost about £7k, with volume down about 250 policies and commission and underwriter cost rising faster than price | ~£7k/week |
| 4 | Push more PPC and SEO spend into comparison, GHIC/EHIC and early-booking terms that are already rising | Over the last 7 days vs the same week last year, search intent is up about 65% to 74%, so demand is there and we need to win more of it in direct | ~£6k/week |
| 5 | Set a floor-price review on aggregator single-trip and cut back any partner feeds below target GP per policy | Over the last 7 days vs the same week last year, aggregator single-trip GP per policy fell from about £3 to under £2 and single-trip losses do not repay later | ~£1k/week |

---

_Generated 07:22 16 Mar 2026 | 23 investigation tracks | gpt-5_

---
*Generated 16:39 16 Mar 2026 | Tracks: 23 + Follow-ups: 34 | Model: gpt-5.4*
