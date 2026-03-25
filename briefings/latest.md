---
# HX Trading Briefing — 24 Mar 2026

## Europe was the biggest drag over the last 7 days vs the same week last year, with GP down about £18k as lower-margin Direct Single and Bronze mix kept squeezing value.

---

## At a Glance

- 🔴 **Europe margin squeeze** — Over the last 7 days vs the same week last year, Europe GP fell about £18k, down from about £103k to £85k, while policies were only down 3%, so the hit was mostly worse value per sale, not demand vanishing.
- 🔴 **Bronze drag** — Over the last 7 days vs the same week last year, Bronze GP fell about £19k, down from about £79k to £60k, as we sold 19% fewer policies and made about 27% less on each one.
- 🔴 **Direct Single** — Over the last 7 days vs the same week last year, Direct Single GP fell about £13k, down from about £42k to £29k, because quote-stage traffic fell 11%, desktop conversion got worse, and GP per policy dropped from about £21 to £16.
- 🔴 **Direct Annual softer** — Over the last 7 days vs the same week last year, Direct Annual GP fell about £12k as volume dropped 8%; that means we are bringing in fewer annual customers and building a smaller future renewal book.
- 🟢 **Renewals helping** — Over the last 7 days vs the same week last year, Renewals Annual GP grew about £6k because retention improved from 31% to 47%, which partly offset weaker new business.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

The data shows Direct Single is a real recurring problem: over the last 7 days vs the same week last year, GP fell about £13k from about £42k to £29k. Quote-stage traffic fell 11%, desktop session-to-search slipped from 14% to 13%, desktop search-to-book fell from 42% to 30%, and GP per policy dropped from about £21 to £16; this has gone the wrong way on 9 of the last 10 trading days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Europe destination GP decline `RECURRING`

The data shows Europe was the biggest £ drag: over the last 7 days vs the same week last year, GP fell about £18k from about £103k to £85k. Policies were only down 3%, so the real issue was average GP per policy dropping from about £22 to £19 as mix shifted into lower-margin Direct Single and Bronze business; this has been negative on 8 of the last 10 trading days.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
  AND destination_group = 'Europe'
GROUP BY 1;
```

### Bronze cover-level GP decline `RECURRING`

The data shows Bronze is still the clearest recurring mix problem: over the last 7 days vs the same week last year, GP fell about £19k. We sold 19% fewer Bronze policies and made about £16 each instead of about £22, and that weakness has shown up on 10 straight trading days.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
  AND cover_level_name = 'Bronze'
GROUP BY 1;
```

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same week last year, Direct Annual GP fell about £12k. That is mainly weaker traffic and volume, with annual sales down 8%, so the issue is not thin day-one margin — it is that we are investing in fewer future renewals; this has been weak on 8 of the last 10 trading days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

### Renewals Annual GP growth `RECURRING`

Over the last 7 days vs the same week last year, Renewals Annual added about £6k of GP. There is no traffic story here; retention improved from 31% to 47%, and that stronger renewal take-up is doing useful work against weaker new business.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

### Partner Referral Single GP decline `HIGH`

Over the last 7 days vs the same week last year, Partner Referral Single GP fell about £5k. Volume was down 35% while GP per policy improved, so this looks like weaker partner traffic, especially cruise-linked demand, rather than broken pricing.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  insurance_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1,2,3;
```

### Worldwide destination GP decline `MEDIUM`

This may be partly conflict-driven market caution: over the last 7 days vs the same week last year, Worldwide GP fell about £7k. Policies were down 14% while GP per policy was basically flat, so this looks more like weaker demand and destination caution than an HX pricing problem.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
  AND destination_group = 'Worldwide'
GROUP BY 1;
```

### PPC-acquired direct business deterioration `LOW`

This is still a small cell and too early to overreact, but over the last 7 days vs the same week last year PPC volume tripled and return got much worse. Bronze Main Single Med HX lost about £1.4k after PPC; across Direct PPC Single, day-one GP after PPC was about £600 down, but estimated 13-month value added about £1.1k, made up of about £700 future insurance GP and about £400 other HX GP, leaving the segment about £600 up overall.

```sql-dig
SELECT
  insurance_group,
  scheme_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp_pre_ppc,
  SUM(COALESCE(ppc_cost_per_policy, 0) * policy_count) AS total_ppc,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) - SUM(COALESCE(ppc_cost_per_policy, 0) * policy_count) AS gp_post_ppc,
  SUM(COALESCE(est_13m_ins_gp, 0)) AS est_future_ins_gp,
  SUM(COALESCE(est_13m_other_gp, 0)) AS est_future_other_gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) - SUM(COALESCE(ppc_cost_per_policy, 0) * policy_count)
    + SUM(COALESCE(est_13m_ins_gp, 0)) + SUM(COALESCE(est_13m_other_gp, 0)) AS total_13m_customer_value
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
  AND insurance_group = 'Web Advertising PPC'
GROUP BY 1,2;
```

### Medical value mix softening `MEDIUM`

Medical is still high value, but over the last 7 days vs the same week last year even the better-quality Direct Single medical traffic made less money. Mobile medical declared avg GP per policy fell from about £34 to £27, which says the margin squeeze is not just in cheap non-med business.

```sql-dig
SELECT
  medical_split,
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.insurance.insurance_trading_data`
WHERE DATE(looker_trans_date) BETWEEN '2026-03-17' AND '2026-03-24'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1,2,3;
```

---

## Customer Search Intent

Travel insurance demand is up sharply and is still outpacing holiday demand, which says the market is there even if customers are shopping harder. Searches for [travel insurance](https://trends.google.com/explore?q=travel%20insurance&date=2024-03-24%202026-03-24&geo=GB), [holiday insurance](https://trends.google.com/explore?q=holiday%20insurance&date=2024-03-24%202026-03-24&geo=GB), [annual travel insurance](https://trends.google.com/explore?q=annual%20travel%20insurance&date=2024-03-24%202026-03-24&geo=GB), [single trip travel insurance](https://trends.google.com/explore?q=single%20trip%20travel%20insurance&date=2024-03-24%202026-03-24&geo=GB), and [travel insurance comparison](https://trends.google.com/explore?q=travel%20insurance%20comparison&date=2024-03-24%202026-03-24&geo=GB) are all ahead of holiday terms like [book holiday](https://trends.google.com/explore?q=book%20holiday&date=2024-03-24%202026-03-24&geo=GB) and [package holiday](https://trends.google.com/explore?q=package%20holiday&date=2024-03-24%202026-03-24&geo=GB).  
The biggest movers are [holiday insurance UK](https://trends.google.com/explore?q=holiday%20insurance%20UK&date=2024-03-24%202026-03-24&geo=GB), [cheap travel insurance](https://trends.google.com/explore?q=cheap%20travel%20insurance&date=2024-03-24%202026-03-24&geo=GB), [cruise travel insurance](https://trends.google.com/explore?q=cruise%20travel%20insurance&date=2024-03-24%202026-03-24&geo=GB), and [holiday cancellation policy](https://trends.google.com/explore?q=holiday%20cancellation%20policy&date=2024-03-24%202026-03-24&geo=GB), which fits a more comparison-led and reassurance-led market.  
Searches for [FCDO travel advice](https://trends.google.com/explore?q=FCDO%20travel%20advice&date=2024-03-24%202026-03-24&geo=GB) also spiked, which fits the shift toward Europe and shorter-lead trips.  
Bottom line: demand is healthy, but customers are more price-sensitive, which matches the Direct Single and Bronze squeeze.

---

## News & Market Context

The Iran conflict is still distorting travel demand, with customers shifting away from Worldwide and toward Europe and shorter-lead bookings. **Source:** Internal — [Current Market Events — Active Context].  
British Airways has continued to suspend some Middle East routes and offer flexible rebooking, which keeps uncertainty high for long-haul demand and helps explain weaker Worldwide traffic ([British Airways update](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai)).  
Cruise partner demand is still soft, with Carnival running at about 80% of last year internally, which fits the Partner Referral Single volume drop. **Source:** Internal — [Insurance Weekly Trading w/c 09/03/2026].  
Competitors are leaning into reassurance. Staysure has published guidance and support for customers affected by the Middle East conflict, which raises the bar for trust messaging ([Staysure Middle East Conflict](https://help.staysure.co.uk/hc/en-us/articles/44368785322257-Middle-East-Conflict)).  
The FCA’s travel insurance signposting changes for customers with medical conditions have been in force since 1 January 2026, which should help medical customers find specialist cover more easily across the market ([ITIJ report](https://www.itij.com/latest/news/amendments-rules-travel-insurance-signposting-system-uk-consumers); [FCA review](https://www.fca.org.uk/publication/multi-firm-reviews/post-implementation-review-travel-insurance-signposting-rules-consumers-medical-conditions-2024.pdf)).  
Internal pricing updates also show Europe Including is already at its margin cap, so the Europe problem is not one we can fix just by yielding harder. **Source:** Internal — [Weekly Pricing Updates].

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Review Direct Single desktop funnel changes since 12 Mar, starting at search results to checkout | Direct Single lost about £13k over the last 7 days vs the same week last year, and desktop search-to-book fell from 42% to 30% | ~£13k/week |
| 2 | Shift Direct messaging and merchandising away from Bronze-only value cues and toward Silver/Gold benefits on Europe journeys | Europe lost about £18k and Bronze lost about £19k over the last 7 days vs the same week last year, with margin per policy doing most of the damage | ~£10k/week |
| 3 | Push annual-first placement harder on Direct mobile and cross-sell entry points | Direct Annual GP fell about £12k over the last 7 days vs the same week last year, which means fewer future renewals in the book | ~£12k/week |
| 4 | Pull back PPC on Bronze Main Single Med HX and move spend into Direct PPC cells that stay positive over 13 months | Bronze Main Single Med HX lost about £1.4k after PPC over the last 7 days vs the same week last year, while Direct PPC Single overall was still about £600 positive over 13 months | ~£1k/week |
| 5 | Ask Carnival and P&O for stronger insurance CTA placement around check-in and booking confirmation | Partner Referral Single lost about £5k over the last 7 days vs the same week last year, with volume down 35% and cruise demand still soft | ~£5k/week |

---

---
*Generated 09:30 25 Mar 2026 | Tracks: 29 + Follow-ups: 29 | Model: gpt-5.4*
