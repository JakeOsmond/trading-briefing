---
# HX Trading Briefing — 15 Mar 2026

## Over the last 7 days vs the same week last year, GP was down about £25k, led by a £12k hit in direct single-trip where strong demand did not turn into enough quotes or enough value per sale.

---

## At a Glance

- 🔴 **Direct single-trip** — Over the last 7 days vs the same week last year, direct single-trip GP fell about **£12k** to **£31k**, down **28%**, even though direct traffic was up overall because fewer visitors reached a quote and we made less on each sale.
- 🔴 **Midweek slump** — Over the last 7 days vs the same week last year, Wednesday and Thursday cost us about **£16k** of GP combined, with the weakness concentrated in direct web quote starts rather than soft demand.
- 🔴 **Partner single-trip** — Over the last 7 days vs the same week last year, partner referral single-trip GP fell about **£7k** to **£13k**, down **33%**, mainly from lower Europe cruise-led volume.
- 🔴 **Direct annual** — Over the last 7 days vs the same week last year, direct annual GP fell about **£6k** to **£41k**, down **13%**, because fewer visitors turned into sales, which means less future renewal income.
- 🟢 **Renewals held up** — Over the last 7 days vs the same week last year, renewal GP rose about **£600** to **£49k**, up **1%**, because better retention offset fewer annual policies expiring.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct single-trip GP fell about **£12k** to **£31k**, down **28%**. Traffic was not the main issue because desktop sessions were up **25%** and total direct traffic was up overall, but mobile session-to-search fell from **20%** to **16%**, desktop fell from **15%** to **13%**, and average GP per policy dropped from about **£22** to **£17**; this has been negative on **8 of the last 10 trading days**.

```sql-dig
SELECT
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single';
```

### Midweek trading slump `EMERGING`

Over the last 7 days vs the same week last year, Wednesday and Thursday were down about **£16k** of GP combined. The pattern points to weaker direct-web quote intent in the middle of the week, not weak market demand, but this is still emerging rather than fully entrenched.

```sql-dig
SELECT
  transaction_date,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
GROUP BY transaction_date
ORDER BY transaction_date;
```

### Direct Annual volume loss `EMERGING`

Over the last 7 days vs the same week last year, direct annual GP fell about **£6k** to **£41k**, down **13%**. This was mostly a traffic-to-booking problem, not a margin problem: desktop traffic was up, but annual booked sessions fell on mobile and desktop, and we sold **13%** fewer policies, which means less future renewal income.

```sql-dig
SELECT
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual';
```

### Bronze Main Single Med HX deterioration `RECURRING`

Over the last 7 days vs the same week last year, Bronze Main Single Med HX lost about **£5k** of GP, down from about **£15k** to **£10k**. Volume was only slightly lower, so most of the hit came from lower value per sale, with the weakness sitting in lower-tier single-trip traffic rather than a traffic collapse.

```sql-dig
SELECT
  scheme_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND scheme_name = 'Bronze Main Single Med HX'
GROUP BY scheme_name;
```

### Partner Referral Single contraction `NEW`

Over the last 7 days vs the same week last year, partner referral single-trip GP fell about **£7k** to **£13k**, down **33%**. The hit came mainly from lower Europe cruise-led referral volume rather than weaker value per sale, so this looks more like a partner traffic issue than a pricing issue for now.

```sql-dig
SELECT
  insurance_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY insurance_group
ORDER BY gp DESC;
```

### Silver Main Single Med HX deterioration `RECURRING`

Over the last 7 days vs the same week last year, Silver Main Single Med HX lost about **£5k** of GP, down from about **£15k** to **£9k**. We sold fewer policies and made less on each one, which lines up with the wider direct single-trip problem in lower-tier products.

```sql-dig
SELECT
  scheme_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND scheme_name = 'Silver Main Single Med HX'
GROUP BY scheme_name;
```

### Aggregator Single margin erosion `NEW`

Over the last 7 days vs the same week last year, aggregator single-trip GP was down only about **£300**, but that hides a worse quality mix because policy volume was up **44%** while average GP per policy fell from about **£3** to **£2**. Single-trip has no renewal payback, so more sales at lower value is still the wrong direction.

```sql-dig
SELECT
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single';
```

### Renewal GP support from higher retention `NEW`

Over the last 7 days vs the same week last year, renewal GP rose about **£600** to **£49k**, up **1%**. Fewer annual policies expired over the week, but retention improved enough to keep renewed volume and GP slightly ahead, which is good news.

```sql-dig
WITH expiring AS (
  SELECT
    SUM(policy_count) AS expiring_policies
  FROM `hx-data-production.commercial_finance.insurance_policies_new`
  WHERE travel_end_date BETWEEN '2026-03-08' AND '2026-03-15'
    AND policy_type = 'Annual'
),
renewed AS (
  SELECT
    SUM(policy_count) AS renewed_policies,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
  FROM `hx-data-production.commercial_finance.insurance_policies_new`
  WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
    AND distribution_channel = 'Renewals'
)
SELECT * FROM expiring, renewed;
```

---

## Customer Search Intent

According to Google Sheets data, customer demand is strong, not weak. **Over the last 7 days vs the same week last year**, travel demand was up about **65% YoY**, insurance searches were up about **74% YoY**, and holiday searches were up about **53% YoY**, so insurance intent is growing faster than the travel market underneath it. According to Google Sheets — Insurance Intent tab, “travel insurance comparison” was up about **375% YoY** and “do I need travel insurance” was up about **31% YoY**, which suggests more shoppers are comparing before they buy. According to the Dashboard Metrics tab, the insurance-vs-holiday search gap widened to about **3 points** from **1 point** last year, which fits what we are seeing in trading: demand is there, but we are under-converting it in direct single and direct annual. **Source:** Google Sheets — Insurance Intent tab. **Source:** Google Sheets — Dashboard Metrics tab.

---

## News & Market Context

According to AI Insights, the market backdrop is supportive rather than weak. **Over the current period vs last year**, cheap-flight interest was up about **32%** and holiday-deal interest was up about **23%**, which should be feeding travel insurance demand. Jet2 has launched its biggest Summer 2026 programme, including nearly **900,000** extra seats from Gatwick and more Spain, Canaries and Algarve capacity, which points to a healthy outbound market. **Source:** AI Insights — deep_dive. **Source:** [Jet2 Summer 2026 programme](https://www.jet2.com/news/2024/09/Jet2_com_and_Jet2holidays_launch_biggest_ever_Summer_programme_for_2026?utm_source=openai)

According to ITIJ and AI Insights, expiring EHIC and GHIC cards and the EU’s EES rollout by **10 Apr 2026** are pushing more people to check whether they need cover. That should help us if our Google visibility and messaging are strong on GHIC, EHIC and medical reassurance. **Source:** [ITIJ on expiring EHIC/GHIC cards](https://www.itij.com/latest/news/millions-uk-ehicghic-cards-set-expire-2025-raising-insurance-concerns?utm_source=openai). **Source:** AI Insights — divergence.

According to AI Insights, BA is still restricting some Middle East routes, which may create some disruption-led demand, but the bigger commercial read-across is still heavier comparison shopping rather than a broad drop in travel appetite. **Source:** AI Insights — news. **Source:** [BA flights update](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai)

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Fix the direct quote-start leak on mobile and desktop single-trip journeys this week, starting with the pages before search results | Direct single-trip lost about **£12k/week** and traffic was there, but session-to-search fell on both devices | ~£12k/week |
| 2 | Review Bronze and Silver direct single-trip pricing and underwriter cost by lower-tier mainstream trips this week | Bronze and Silver single schemes lost about **£10k/week** combined because value per sale dropped sharply | ~£10k/week |
| 3 | Push more paid and organic demand into direct annual on comparison, GHIC/EHIC and annual multi-trip terms | Direct annual is down about **£6k/week** even though market intent is strong, so we are missing future renewal income | ~£6k/week |
| 4 | Speak to cruise referral partners on Europe single-trip volume, starting with the biggest referrers | Partner referral single-trip lost about **£7k/week**, mainly from weaker cruise-led volume | ~£7k/week |
| 5 | Set a minimum GP guardrail on aggregator single-trip schemes with the weakest value per sale | Aggregator single-trip volume is up but GP per policy fell from about **£3** to **£2** over the last 7 days vs last year | ~£0.3k/week |

---

_Generated 07:22 16 Mar 2026 | 23 investigation tracks | gpt-5_

---
*Generated 11:17 16 Mar 2026 | Tracks: 23 + Follow-ups: 35 | Model: gpt-5.4*
