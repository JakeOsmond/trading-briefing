---
# HX Trading Briefing — 10 Mar 2026

## GP took a hit last week, down £13k YoY, as surging insurance demand failed to offset sharp margin squeeze on single trip and annual policies.

---

## At a Glance

- 🔴 **Partner Single Trip GP plunged** — Down £6.1k YoY over the last 7 days (to £15.5k, -28%), driven by big volume loss, despite flat margin.
- 🔴 **Direct Annual GP squeezed** — GP fell £6.2k YoY (-11.5%, to £47.8k) over the last 7 days; volume flat but average GP per policy dropped 12% on cost.
- 🔴 **Direct Single Trip GP dropped** — Down £3.8k YoY (-9%, to £38.7k) over the last 7 days, despite policy count up 8%, thanks to higher underwriter cost and deeper discounts.
- 🔴 **Europe Destination GP off** — Down £4.3k YoY (-4%, to £106k) over the last 7 days, as volume grew but margin per policy shrank 8%.
- 🔴 **Silver Main Annual Med margin hit** — Down £6.6k YoY (-28%, to £16.5k) over the last 7 days; solid volume, big cost jump.

---

## What's Driving This

### Partner Referral Single Trip GP `RECURRING`

Partner channel single trip gross profit collapsed by £6.1k YoY (down 28%) over the last 7 days as sales dropped 26%—average margin per policy was stable, but we lost volume. Carnival, Fred Olsen, and Co-op drove most of the drop, and 9 of the last 10 days were worse than last year.

```sql-dig
SELECT scheme_name, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp, SUM(policy_count) AS policies
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Partner Referral' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
GROUP BY scheme_name
```

### Direct Annual GP `RECURRING`

Direct annual GP fell £6.2k YoY (-12%) over the last 7 days as policy numbers held flat but margin fell due to higher underwriter costs (+11%). The squeeze is persistent—down on 7 of the last 10 days, especially for Silver schemes.

```sql-dig
SELECT scheme_name, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp, SUM(policy_count) AS policies
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Direct' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
GROUP BY scheme_name
```

### Direct Single Trip GP `RECURRING`

We lost £3.8k YoY on direct single trips (down 9%) over the last 7 days, despite 8% more policies, as average margin fell 16%—that’s down to higher underwriter cost, deeper discounts, and slightly higher commissions, with price barely moving. Traffic was flat, funnel conversion improved, but every sale is worth less; this has dragged for 7 of the last 10 days.

```sql-dig
SELECT cover_level_name, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp, SUM(policy_count) AS policies
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Direct' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
GROUP BY cover_level_name
```

### Europe Destination GP `RECURRING`

Europe trip GP is down £4.3k YoY (-4%, to £106k) over the last 7 days, with policy count up 5% but average margin down 8.5%. Most of the impact is direct channel—margin pressure is broad, not mix-driven.

```sql-dig
SELECT distribution_channel, SUM(policy_count) AS policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE destination_group='Europe' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
GROUP BY distribution_channel
```

### Silver Main Annual Med HX GP `RECURRING`

GP from Silver Main Annual Med HX fell £6.6k YoY (-28%) over the last 7 days, mainly due to a drop in margin per policy (-23%), with costs up. Medical mix did not change—it's just more expensive to serve.

```sql-dig
SELECT max_medical_score_grouped, SUM(policy_count) as policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) as gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE scheme_name='Silver Main Annual Med HX' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
GROUP BY max_medical_score_grouped
```

### Aggregator Single Trip GP `RECURRING`

Aggregator single trip GP fell £0.6k YoY (-25%) over the last 7 days, even as sales jumped 44%—margin per sale halved on fierce price competition, average price dropped £10. Losses are across the big comparison sites, 8 out of the last 10 days were negative.

```sql-dig
SELECT scheme_name, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp, SUM(policy_count) AS policies
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Aggregator' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
GROUP BY scheme_name
```

### Renewals Annual GP `RECURRING`

Renewal GP grew £1.5k YoY (+3%) over the last 7 days, as more customers renewed (up 12% on volume), though margin per policy slipped a touch. This is our annual acquisition strategy paying off—renewal income is healthy and growing.

```sql-dig
SELECT cover_level_name, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp, SUM(policy_count) AS policies
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Renewals' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
GROUP BY cover_level_name
```

### Aggregator Annual GP `RECURRING`

Aggregator annual negative GP narrowed by £1.1k YoY over the last 7 days—losses are still strategic, but pricing is firmer (average price up 41%). Volumes are solid and we're continuing to build the renewal base.

```sql-dig
SELECT scheme_name, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp, SUM(policy_count) AS policies
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Aggregator' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
GROUP BY scheme_name
```

---

## Customer Search Intent

Travel insurance search intent is red-hot: up 74% YoY (insurance shoppers index 11.5 now vs 6.6 last year, over the last 7 days), outpacing even holiday searches (+50%, now 8.5 vs 5.7). The gap between insurance and holiday intent is the widest it's been (+3 index points vs +1), so prospects are searching for cover—especially medical, cancellation, and annual multi-trip. Destinations like Spain, Greece, and Italy lead the trends, driven by new EU border rules and lots of airline sales. Most of this is Google search volume, so we need to catch it early, especially via PPC/SEO to AMT/medical pages.  
**Source:** [Google Trends — Insurance Intent](https://trends.google.com/trends/explore?date=all&q=travel%20insurance), Dashboard Metrics, AI Insights

---

## News & Market Context

Demand for insurance is running 57%-74% up YoY and outpacing holiday bookings, fuelled by new seat releases (easyJet/Ryanair up sharply), entry rule changes (Spain/EU), and last month’s storms and strikes. Competitors are slashing pricing on aggregators to grab volume, driving the margin squeeze—confirmed in the latest [market stats](https://www.moneysupermarket.com/travel-insurance/travel-insurance-statistics/?utm_source=openai) and our own "Insurance Price Scrape" (11 Mar 2026). New UK rules require insurance for Schengen/Spain plus updated FCA conduct guidance, pushing people to shop around harder but also limiting our upsell. Saga and others are auto-extending cover for Middle East disruption—matching that could win us share. The market isn’t short of demand; we’re in a price and margin fight.
**Sources:** AI Insights — what_matters, trend, channels, news; [Consumer Intelligence](https://www.consumerintelligence.com/articles/unveiling-travel-insurance-trends-what-you-need-to-know-now?utm_source=openai); MoneySuperMarket stats; Internal docs (11 Mar 2026).

---

## Actions

| Priority | What to do                                            | Why                                      | Worth      |
|----------|------------------------------------------------------|-------------------------------------------|------------|
| 1        | Tighten costs and revisit pricing for direct/partner single trip | Margin squeeze is destroying GP, even as volumes hold | ~£10k/week |
| 2        | Shift more PPC and aggregator bids to AMT + medical annual | Renewal/AMT volumes are growing and margin is firmer | ~£1.5k/week |
| 3        | Launch targeted messaging on aggregator single trips to flag value, not just price | Heavy discounting isn't winning margin   | ~£0.5k/week |
| 4        | Push auto-extension and proactive alerts for Middle East routes | Competitors are gaining share via this move | Up to £1k/week |
| 5        | Take market share by boosting conversion at top of funnel (session-to-search) | Massive insurance intent but not enough quotes run | ~£2k/week   |

---

_Generated 08:15 11 Mar 2026 | 22 investigation tracks | gpt-4_1106-preview_ha_40k_coverage_27_oly_2026b_2_0_5_7_12_ensemble_20260310_0815_uk_eea_extra_qa_coverage_ly_oly_subsat_8xdriver_1track_1week_struct_1actions_



---
*Generated 14:28 11 Mar 2026 | Tracks: 22 + Follow-ups: 37 | Model: gpt-4.1*
