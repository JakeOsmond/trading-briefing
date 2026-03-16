---
# HX Trading Briefing — 15 Mar 2026

## Direct single-trip did most of the damage over the last 7 days vs the same week last year — GP fell about £12k, and that was the biggest reason total weekly GP ended up about £25k down.

---

## At a Glance

- 🔴 **Direct single weak** — Over the last 7 days vs the same week last year, Direct single-trip GP fell £11.8k to £30.9k, down 28%, because traffic was slightly lower, fewer visitors reached a quote, and we made less on each sale.
- 🔴 **Europe drag** — Over the last 7 days vs the same week last year, Europe GP fell about £19k to £90k, down 17%, mostly because we kept less on each sale while policy volume was only down 4%.
- 🔴 **Partner single down** — Over the last 7 days vs the same week last year, Partner Referral single-trip GP fell £6.5k to £13.4k, down 33%, mainly because partner-led volume dropped 28%.
- 🔴 **Direct annual softer** — Over the last 7 days vs the same week last year, Direct annual GP fell about £6k to £41k, down 13%, because fewer customers got through to quote and booking, so we sold fewer annuals and missed future renewal income.
- 🟢 **Renewals steady** — Over the last 7 days vs the same week last year, renewal GP rose about £0.6k to £49k, up 1%, as better retention offset lower value per renewed policy.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, Direct single-trip GP fell £11.8k to £30.9k, down 28%. Traffic was slightly down overall at 56.2k sessions vs 58.2k, but the bigger problem was conversion and value: search sessions fell 10% to 9.0k, policies fell 8% to 1,809, and average GP per policy dropped 21% to about £17; this has been negative on 9 of the last 10 trading days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Direct' AND policy_type = 'Single'
GROUP BY 1,2;
```

### Europe destination weakness `RECURRING`

Over the last 7 days vs the same week last year, Europe GP fell about £19k to £90k, down 17%. Demand was not the main problem because policies were only down 4%; the bigger hit was lower value per sale, driven mainly by Direct single and Partner Referral single on Europe-heavy trips, and this pattern has shown up repeatedly through the last few weeks.

```sql-dig
SELECT
  destination_group,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE destination_group = 'Europe'
GROUP BY 1;
```

### Partner Referral Single volume loss `RECURRING`

Over the last 7 days vs the same week last year, Partner Referral single-trip GP fell £6.5k to £13.4k, down 33%. This was mainly a traffic and volume miss rather than a pricing collapse: policies fell 28% to 657 while average GP only slipped 7% to about £20, with the biggest hole in cruise-medical partner schemes; this has been negative for most of the last 10 trading days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Partner Referral' AND policy_type = 'Single'
GROUP BY 1,2;
```

### Direct Annual volume decline `EMERGING`

Over the last 7 days vs the same week last year, Direct annual GP fell about £6k to £41k, down 13%. This is not about annual margin — annual growth is good because we are investing in future renewal income — but here traffic did not turn into sales, with weaker quote capture and booking meaning roughly 120 fewer annual policies sold.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Direct' AND policy_type = 'Annual'
GROUP BY 1,2;
```

### Silver Main Single Med HX deterioration `EMERGING`

Over the last 7 days vs the same week last year, Silver Main Single Med HX lost about £5.3k of GP, down 36% to about £9k. Too early to call it fully structural, but traffic quality, conversion and value all weakened, especially on mobile and desktop, so this scheme explains a big chunk of the wider Direct single miss.

```sql-dig
SELECT
  scheme_name,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE scheme_name = 'Silver Main Single Med HX'
GROUP BY 1;
```

### Bronze Main Single Med HX deterioration `EMERGING`

Over the last 7 days vs the same week last year, Bronze Main Single Med HX lost about £5.2k of GP, down 34% to about £10k. Volume was nearly flat, so the issue was lower value per sale, with mobile monetisation doing most of the damage.

```sql-dig
SELECT
  scheme_name,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE scheme_name = 'Bronze Main Single Med HX'
GROUP BY 1;
```

### Aggregator Single GP dilution `NEW`

Over the last 7 days vs the same week last year, aggregator single-trip GP was down only about £0.3k. This is still worth a look because volume was up 44% but average GP per policy fell from about £3 to £2, so we sold more single trips and kept less on each one.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Aggregator' AND policy_type = 'Single'
GROUP BY 1,2;
```

### Renewals retention improvement `NEW`

Over the last 7 days vs the same week last year, renewals added about £0.6k of GP, up 1% to about £49k. Directionally this is good: higher retention offset lower GP per renewed policy, and because renewals are a high-margin payoff stream, any retention gain matters.

```sql-dig
WITH renewed AS (
  SELECT
    SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_renewed,
    SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
    SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_renewed,
    SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
  FROM `hx-data-production.commercial_finance.insurance_policies_new`
  WHERE distribution_channel = 'Renewals' AND policy_type = 'Annual'
)
SELECT * FROM renewed;
```

---

## Customer Search Intent

According to Google Sheets — Dashboard Metrics, over the latest tracked period travel insurance demand is up 65% vs last year, and insurance searches are up 74% vs last year, ahead of holiday searches at 53%. According to Google Sheets — Insurance Intent tab, “travel insurance comparison” is up about 375% vs last year and “do I need travel insurance” is up about 31%, which points to strong demand but more price-checking behaviour. According to Dashboard Metrics, the gap between insurance search growth and holiday search growth widened from 1 point last year to 3 points now, so insurance intent is rising faster than travel planning. According to AI Insights, Spain, the Canaries, Algarve, Greece, Turkey and the USA are among the strongest destinations for demand growth, which says the market is healthy even while our Europe GP is under pressure. **Source:** Google Sheets — Insurance Intent tab. **Source:** Google Sheets — Dashboard Metrics tab. **Source:** AI Insights — seasonal.

---

## News & Market Context

According to AI Insights, Jet2, easyJet and TUI have all added Summer 2026 capacity, especially into Spain, the Canaries, Portugal, Greece and Florida, which supports a healthy travel market rather than a weak one. **Source:** AI Insights — seasonal. [Jet2’s Summer 2026 launch](https://www.jet2.com/news/2024/09/Jet2_com_and_Jet2holidays_launch_biggest_ever_Summer_programme_for_2026?utm_source=openai) also points to more Med-sun and family trips, which usually supports single-trip demand. According to ITIJ, millions of UK GHIC and EHIC cards are due to expire in 2025, which is pushing more cover questions and may be helping “do I need travel insurance” searches. **Source:** [Millions of UK EHIC/GHIC cards set to expire in 2025](https://www.itij.com/latest/news/millions-uk-ehicghic-cards-set-expire-2025-raising-insurance-concerns?utm_source=openai). According to AI Insights, disruption linked to the Middle East remains in the background for some routes, but it does not look like the main reason for this week’s miss. **Source:** AI Insights — news.

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Check the Direct funnel at session-to-search by device and fix any blocker on mobile and desktop search entry this week | Direct single lost £11.8k over the last 7 days vs last year, with sessions only slightly down but search sessions down 10% | ~£12k/week |
| 2 | Review Bronze and Silver single-trip pricing, underwriter cost and mobile page economics by scheme | Bronze and Silver single schemes lost about £10.5k over the last 7 days vs last year, mostly from lower GP per sale | ~£10k/week |
| 3 | Ask the partner team to audit referral feed volume and campaign delivery on cruise-medical schemes | Partner Referral single lost £6.5k over the last 7 days vs last year, mainly because policy volume fell 28% | ~£7k/week |
| 4 | Push paid and organic capture on annual intent terms and check quote-start leakage in the annual journey | Direct annual is down about £6k over the last 7 days vs last year because we sold fewer annuals, which means less future renewal income | ~£6k/week |
| 5 | Review pricing floors and placement on low-value aggregator single trips | Aggregator single kept about £0.3k less GP over the last 7 days vs last year despite much higher volume | ~£0.3k/week |

---

_Generated 00:00 16 Mar 2026 | 23 investigation tracks | gpt-5_

---
*Generated 17:08 16 Mar 2026 | Tracks: 23 + Follow-ups: 43 | Model: gpt-5.4*
