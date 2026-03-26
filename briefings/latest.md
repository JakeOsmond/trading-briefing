---
# HX Trading Briefing — 25 Mar 2026

## GP was soft over the last 7 days vs the same week last year: we made £137k, down £25k or 16%, and most of the hit came from direct single and direct annual.

---

## At a Glance

- 🔴 **Direct single drag** — Over the last 7 days vs the same week last year, direct single GP fell £13k to £32k, down 29%, as quote reach weakened and we made less on each policy.
- 🔴 **Direct annual softer** — Over the last 7 days vs the same week last year, direct annual GP fell £11k to £40k, down 22%; volumes were down 9%, and this is softer acquisition into future renewal income rather than a reason to pull back.
- 🔴 **Bronze hurting quality** — Over the last 7 days vs the same week last year, Bronze GP fell £20k to £29k, down 40%, with fewer sales and much weaker GP per policy.
- 🔴 **Partner referral weak** — Over the last 7 days vs the same week last year, partner referral GP fell about £8k combined across single and annual, mostly cruise-partner softness.
- 🟢 **Renewals paid back** — Over the last 7 days vs the same week last year, renewals GP rose £4k to £49k, up 9%, offsetting some of the direct weakness.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct single GP fell £13k to £32k. The data shows this was both traffic and quality: mobile sessions were down 8%, mobile quote reach fell from 20% to 15%, policies fell 12%, and average GP dropped to about £17 from £21.  
This is clearly margin squeeze, not a price problem. Average customer price was up 2%, but underwriter cost rose from 46% to 50% of gross and GP margin compressed from 36% to 29%; this has been negative on 8 of the last 10 days.

```sql-dig
SELECT
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-18' AND '2026-03-25'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single';
```

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct annual GP fell £11k to £40k, down 22%, with policies down 9%. Traffic was softer, mainly desktop, and average GP per policy fell to about £48 from £56 as margin got squeezed.  
This is softer acquisition into future renewal income, not a reason to chase annual margin. The cause was higher underwriter cost, up from 47% to 51% of gross, plus discount rate rising from 10% to 11%; this has been a recurring pattern.

```sql-dig
SELECT
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price,
  SUM(CAST(total_discount_value AS FLOAT64)) / NULLIF(SUM(CAST(total_gross_inc_ipt AS FLOAT64)) + SUM(CAST(total_discount_value AS FLOAT64)), 0) AS discount_rate
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-18' AND '2026-03-25'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual';
```

### Existing customer GP decline in Direct `RECURRING`

Over the last 7 days vs the same week last year, direct GP from existing customers fell £20k to £54k, down 26%. Traffic was the main issue here: existing sessions were down 12% and quote sessions were down 30%, which hit both direct single and direct annual at the same time.  
The data shows we are losing more known-customer demand before the quote page, not just at checkout. That makes this a funnel and CRM capture problem, not just a pricing problem, and it has been recurring.

```sql-dig
SELECT
  customer_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-18' AND '2026-03-25'
  AND distribution_channel = 'Direct'
  AND customer_type = 'Existing'
GROUP BY 1;
```

### Partner Referral Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, partner referral single GP fell £5k to £12k, down 29%. The data shows this was mainly traffic and volume, with policies down 36%, while GP per policy actually improved.  
Day-one GP is still positive, and estimated 13-month customer value lifts this segment to about £14k total over the last 7 days, but that is still about £6k below last year. This looks like cruise-partner softness rather than an HX pricing failure.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm - COALESCE(ppc_cost_per_policy,0) AS FLOAT64)) AS gp_post_ppc,
  SUM(COALESCE(est_13m_ins_gp,0)) AS est_future_ins_gp,
  SUM(COALESCE(est_13m_other_gp,0)) AS est_future_other_gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm - COALESCE(ppc_cost_per_policy,0) AS FLOAT64)) + SUM(COALESCE(est_13m_ins_gp,0)) + SUM(COALESCE(est_13m_other_gp,0)) AS total_13m_customer_value
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-18' AND '2026-03-25'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Bronze cover level GP decline `RECURRING`

Over the last 7 days vs the same week last year, Bronze GP fell £20k to £29k, down 40%. We sold about 20% fewer Bronze policies and made about £16 each instead of £22, with the biggest damage in direct single Bronze.  
The data shows this is a real quality issue, not noise. Cheap single-trip shoppers look more price-sensitive, and that has been showing up consistently over the last 10 trading days.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-18' AND '2026-03-25'
  AND cover_level_name = 'Bronze'
GROUP BY 1;
```

### Renewals GP growth `RECURRING`

Over the last 7 days vs the same week last year, renewals GP rose £4k to £49k, up 9%. Renewed policies were up 18%, which more than offset slightly lower GP per renewal.  
This is clearly the annual strategy paying back. We are seeing more high-margin renewal income come through while new annual acquisition stays soft.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-18' AND '2026-03-25'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

### Aggregator Single GP decline despite volume growth `RECURRING`

Over the last 7 days vs the same week last year, aggregator single GP fell only about £400 to £2.1k, but the quality dropped hard underneath that: volumes were up 53% while GP per policy almost halved to about £1.80.  
Because this is single trip, thin margins matter. Day-one GP stayed positive at about £2.1k, and estimated 13-month customer value lifts it to about £2.9k, still around £100 below last year, so we should protect a floor margin rather than just chase more volume.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm - COALESCE(ppc_cost_per_policy,0) AS FLOAT64)) AS gp_post_ppc,
  SUM(COALESCE(est_13m_ins_gp,0)) AS est_future_ins_gp,
  SUM(COALESCE(est_13m_other_gp,0)) AS est_future_other_gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm - COALESCE(ppc_cost_per_policy,0) AS FLOAT64)) + SUM(COALESCE(est_13m_ins_gp,0)) + SUM(COALESCE(est_13m_other_gp,0)) AS total_13m_customer_value
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-18' AND '2026-03-25'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Partner Referral Annual GP decline `EMERGING`

Over the last 7 days vs the same week last year, partner referral annual GP fell £3k to £7k, down 29%. Policies were down 17% and average GP per policy fell to about £57 from £67.  
This may be transitional because specialist cruise changes only went live on 23 Mar 2026. Estimated 13-month customer value still lifts the segment to about £8k total over the last 7 days, but that is about £3k below last year, so it is too early to call a fix.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm - COALESCE(ppc_cost_per_policy,0) AS FLOAT64)) AS gp_post_ppc,
  SUM(COALESCE(est_13m_ins_gp,0)) AS est_future_ins_gp,
  SUM(COALESCE(est_13m_other_gp,0)) AS est_future_other_gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm - COALESCE(ppc_cost_per_policy,0) AS FLOAT64)) + SUM(COALESCE(est_13m_ins_gp,0)) + SUM(COALESCE(est_13m_other_gp,0)) AS total_13m_customer_value
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-18' AND '2026-03-25'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

---

## Customer Search Intent

Insurance demand is still running ahead of holiday demand. “Holiday insurance” is up 132% YoY ([Google Trends](https://trends.google.com/explore?q=holiday%20insurance&date=2024-03-25%202026-03-25&geo=GB)), well ahead of “book holiday” up 42% YoY ([Google Trends](https://trends.google.com/explore?q=book%20holiday&date=2024-03-25%202026-03-25&geo=GB)).  
The biggest search spikes are “annual travel insurance UK” up 691% ([Google Trends](https://trends.google.com/explore?q=annual%20travel%20insurance%20UK&date=2024-03-25%202026-03-25&geo=GB)), “cruise holiday insurance” up 646% ([Google Trends](https://trends.google.com/explore?q=cruise%20holiday%20insurance&date=2024-03-25%202026-03-25&geo=GB)), and “cheap holiday insurance” up 462% ([Google Trends](https://trends.google.com/explore?q=cheap%20holiday%20insurance&date=2024-03-25%202026-03-25&geo=GB)).  
Brand and comparison intent is up too, with “Staysure holiday insurance” up 414% ([Google Trends](https://trends.google.com/explore?q=Staysure%20holiday%20insurance&date=2024-03-25%202026-03-25&geo=GB)) and “MoneySupermarket travel insurance” up 173% ([Google Trends](https://trends.google.com/explore?q=MoneySupermarket%20travel%20insurance&date=2024-03-25%202026-03-25&geo=GB)). That fits our trading over the last 7 days: demand is there, but shoppers are more price-sensitive and comparison-led.

---

## News & Market Context

The market does not look weak. Google Trends shows strong UK insurance demand over the last week, especially around annual, cruise and cheap-cover searches. **Source:** Google Trends narrative.  
The Iran conflict is still pushing some travellers away from annual cover and toward shorter-lead single trips, which fits softer annual acquisition over the last 7 days vs last year. **Source:** Internal — Current Market Events — Active Context.  
Cruise demand is still being fought over hard by competitors, including [MoneySuperMarket cruise insurance](https://www.moneysupermarket.com/travel-insurance/cruise/) and [Compare the Market cruise insurance](https://www.comparethemarket.com/travel-insurance/cruise/), so weak partner cruise performance looks more like share pressure than category weakness.  
FCA signposting rules for customers with medical conditions remain in force, keeping medical cover highly visible in market. **Source:** [FCA review](https://www.fca.org.uk/publications/multi-firm-reviews/travel-insurance-signposting-rules-consumers-medical-conditions-review).  
Internally, specialist cruise pricing went live on 23 Mar 2026, renewal discount parity went live on 25 Mar 2026, and more direct rate changes are due on 28 Mar 2026. **Source:** Internal — Weekly Pricing Updates.

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Rework direct single Bronze non-medical pricing and discount coverage this week, then read through by mobile and desktop separately | Over the last 7 days vs last year, direct single lost £13k and Bronze lost £20k; the biggest issue is margin squeeze, not price demand | ~£13k/week |
| 2 | Fix quote reach for direct existing customers by checking landing-to-search drop-off, especially on mobile | Over the last 7 days vs last year, direct existing-customer GP is down £20k, with sessions down 12% and quote sessions down 30% | ~£10k/week |
| 3 | Keep annual acquisition live, but push more owned CRM into direct annual while the 28 Mar 2026 rate changes bed in | Over the last 7 days vs last year, direct annual GP is down £11k, but this is future renewal income and renewals are already paying back | ~£11k/week |
| 4 | Escalate Carnival and cruise-partner CTA placement checks now that specialist cruise changes are live | Over the last 7 days vs last year, partner referral is down about £8k combined, mainly cruise-led traffic softness | ~£8k/week |
| 5 | Set and enforce a floor margin for aggregator single by partner, rather than buying more volume at £1.80 GP per policy | Over the last 7 days vs last year, aggregator single volume is up 53% but 13-month value is only about £2.9k total | ~£1k/week |

---
*Generated 11:56 26 Mar 2026 | Tracks: 29 + Follow-ups: 35 | Model: gpt-5.4*
