---
# HX Trading Briefing — 29 Mar 2026

## Over the last 7 days vs the same period last year, GP fell again, and the biggest hit was direct existing and single-trip sales making less money even where traffic held up.

---

## At a Glance

- 🔴 **Weekly GP down** — Over the last 7 days vs the same period last year, GP was £145k, down £24k or 14%, with policy count flat at about 7.6k, so the hit came from making less on each sale.
- 🔴 **Direct existing down** — Over the last 7 days vs the same period last year, direct GP from existing customers fell £20k to £55k, with sessions flat but fewer people reaching prices and average GP down 19%.
- 🔴 **Direct single-trip squeezed** — Over the last 7 days vs the same period last year, direct single-trip GP fell £15k to £34k, with policies up 2% but average GP per policy down 33%.
- 🔴 **Europe margin squeezed** — Over the last 7 days vs the same period last year, Europe GP fell £19k to £93k even though policies rose 5%, so demand was there but yield was weaker.
- 🟢 **Renewals helped** — Over the last 7 days vs the same period last year, renewals added about £4k of GP to reach £56k because volume rose 26%, even though average GP per renewed policy fell 15%.

---

## What's Driving This

### Direct existing-customer GP decline `RECURRING`

Over the last 7 days vs the same period last year, direct GP from existing customers fell £20k to £55k. Sessions were flat at about 22.6k, but session-to-search fell from 23% to 19%, policy volume dropped 10%, and average GP fell from about £32 to £26.  
The data shows this is a funnel access and value problem, not a traffic problem. It has been negative 8 of the last 10 trading days.

```sql-dig
SELECT
  customer_type,
  distribution_channel,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-22' AND '2026-03-29'
  AND distribution_channel = 'Direct'
  AND customer_type = 'Existing'
GROUP BY 1,2;
```

### Direct single-trip GP deterioration `RECURRING`

Over the last 7 days vs the same period last year, direct single-trip GP fell £15k to £34k even though policies edged up 2% to about 2.2k. Traffic was mixed rather than weak, with desktop sessions up 34% and mobile up 2%, but desktop conversion worsened and average GP per policy fell from £23 to £16.  
The data shows we sold the volume but at much lower value. Customer price fell 10% while underwriter cost barely moved, which squeezed margin hard. This has been negative 9 of the last 10 trading days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-22' AND '2026-03-29'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Europe destination GP compression `RECURRING`

Over the last 7 days vs the same period last year, Europe GP fell £19k to £93k while policy count rose 5%. That means traffic and demand were fine, but we made less on each sale.  
This looks tied to lower-tier and shorter-lead mix, which fits the wider market move into Europe and later booking. It has been negative 8 of the last 10 trading days.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-22' AND '2026-03-29'
  AND destination_group = 'Europe'
GROUP BY 1;
```

### Bronze cover-level GP slump `RECURRING`

Over the last 7 days vs the same period last year, Bronze GP fell about £17k to £30k, with policies down only 13%, so most of the damage came from weaker value per sale.  
This is clearly concentrated in direct single-trip Bronze, especially medical Bronze. It has been negative every day for the last 10 trading days.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-22' AND '2026-03-29'
  AND cover_level_name = 'Bronze'
GROUP BY 1;
```

### Direct annual GP softness `RECURRING`

Over the last 7 days vs the same period last year, direct annual GP fell about £8k to £39k, with volume down 9% and average GP down 9%.  
Annual volume matters because that is future renewal income, so the issue here is weaker acquisition, not the margin line itself. This has been negative 7 of the last 10 trading days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-22' AND '2026-03-29'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

### Renewal average GP dilution `RECURRING`

Over the last 7 days vs the same period last year, renewal GP rose about £4k to £56k because policy volume rose 26%. Average GP per renewed policy still fell from about £42 to £35.  
So renewals are helping overall, but more of the sales are coming through lower-value paths. This has been a recurring pattern over the last week.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-22' AND '2026-03-29'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

### Partner referral single-trip contraction `RECURRING`

Over the last 7 days vs the same period last year, partner referral single-trip GP fell about £3k to £13k because policy count dropped 35%, while average GP improved.  
That points to weaker partner traffic, especially cruise-linked demand, rather than a pricing problem. This has been negative 7 of the last 10 trading days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp_per_policy
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-22' AND '2026-03-29'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Aggregator annual volume decline `NEW`

Over the last 7 days vs the same period last year, aggregator annual policy count fell 19% to about 1k. That matters because this is future renewal pipeline.  
Day-one GP improved from a loss of about £9k to a loss of about £6k, which is fine because annuals are an acquisition play. The issue is volume. For new customers in this segment, 13-month value is still negative in this track, with day-one GP at about -£5.7k and no offsetting future value showing, so this cohort is not yet paying back.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(COALESCE(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(ppc_cost_per_policy,0),0)) AS gp_post_ppc,
  SUM(COALESCE(est_13m_ins_gp,0)) AS est_future_ins_gp,
  SUM(COALESCE(est_13m_other_gp,0)) AS est_future_other_gp,
  SUM(COALESCE(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) - COALESCE(ppc_cost_per_policy,0),0) + COALESCE(est_13m_ins_gp,0) + COALESCE(est_13m_other_gp,0)) AS total_13m_customer_value
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-22' AND '2026-03-29'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

---

## Customer Search Intent

Insurance intent still looks healthy. [Annual travel insurance](https://trends.google.com/explore?q=annual%20travel%20insurance&date=2024-03-29%202026-03-29&geo=GB) is up 150% year on year, well ahead of [book holiday](https://trends.google.com/explore?q=book%20holiday&date=2024-03-29%202026-03-29&geo=GB) at 42%. [Travel insurance cover Europe](https://trends.google.com/explore?q=travel%20insurance%20cover%20europe&date=2024-03-29%202026-03-29&geo=GB) is up 257%, [medical travel insurance UK](https://trends.google.com/explore?q=medical%20travel%20insurance%20UK&date=2024-03-29%202026-03-29&geo=GB) is up 236%, and [cruise travel insurance](https://trends.google.com/explore?q=cruise%20travel%20insurance&date=2024-03-29%202026-03-29&geo=GB) is up 143%. [Single trip travel insurance](https://trends.google.com/explore?q=single%20trip%20travel%20insurance&date=2024-03-29%202026-03-29&geo=GB) and [travel insurance comparison](https://trends.google.com/explore?q=travel%20insurance%20comparison&date=2024-03-29%202026-03-29&geo=GB) are broadly flat, which backs up what we see in trading: the single-trip problem is more about conversion and yield than demand. [Turkey holiday packages](https://trends.google.com/explore?q=Turkey%20holiday%20packages&date=2024-03-29%202026-03-29&geo=GB) are up 93%, which fits the Europe-heavy mix.

---

## News & Market Context

Middle East disruption is still affecting routes and airspace, which is pushing customers toward shorter-lead and Europe trips rather than stopping travel altogether. **Source:** [AP News](https://apnews.com/article/0346e29ee99eaee2838c8e08f4facb78), [AP News](https://apnews.com/article/6c16a15a7f4a90022064dd26c405b956)  
Carnival traffic is down about 20%, which lines up with the weakness in partner referral single-trip and cruise-linked demand. **Source:** Internal — Insurance Weekly Trading w/c 09/03/2026  
Internal pricing and product context also fits the numbers: direct yielding changes went live on 12 March, and growth tests are affecting Search CTR, both of which can explain weaker direct funnel reach and poorer value capture. **Source:** Internal — Weekly Pricing Updates; Internal — Insurance Trading - Insights, Product & Pricing Mar26  
Google Trends and internal trading notes both point to softer summer demand but better short-lead demand, which matches Europe volume holding up while GP per policy weakens. **Source:** Internal — UKD Trading 51: WC 16th Mar 26  
The FCA is still focused on fair access and vulnerable customers, which matters while medical travel insurance searches are rising sharply. **Source:** [FCA](https://www.fca.org.uk/publication/regulatory-priorities/insurance-report.pdf)

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Roll back or narrow the live direct growth tests hitting session-to-search, then check existing-customer funnel reach by device within 24 hours | Over the last 7 days vs the same period last year, direct existing GP is down £20k with sessions flat but session-to-search down from 23% to 19% | ~£20k/week |
| 2 | Reprice or repackage direct single-trip Bronze, especially Europe and medical Bronze, and review underwriter-cost pass-through | Over the last 7 days vs the same period last year, direct single-trip GP is down £15k, with average GP per policy down 33% and Bronze the worst scheme drag | ~£15k/week |
| 3 | Audit desktop direct funnel changes since 12 Mar, especially search results to book | Over the last 7 days vs the same period last year, desktop traffic was up but desktop session-to-search fell from 14% to 13% and search-to-book fell from 46% to 32% in direct single-trip | ~£8k/week |
| 4 | Push higher-tier upsell and extras harder in Europe journeys, especially short-lead direct traffic | Over the last 7 days vs the same period last year, Europe sold 5% more policies but lost £19k of GP, so mix and value are the issue | ~£10k/week |
| 5 | Protect aggregator annual quote share and volume, but only where 13-month value improves to at least break-even | Over the last 7 days vs the same period last year, aggregator annual volume is down 19%, and this cohort still shows about -£5.7k day-one GP with no positive 13-month payback in the current track | ~£3k/week |

---
*Generated 13:01 30 Mar 2026 | Tracks: 29 + Follow-ups: 30 | Model: gpt-5.4*
