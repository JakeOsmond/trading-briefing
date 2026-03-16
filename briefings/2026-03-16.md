---
# HX Trading Briefing — 15 Mar 2026

## GP was soft yesterday and over the last 7 days vs last year, even though the market is up hard — we’re missing demand in direct single and direct annual quote starts.

---

## At a Glance

- 🔴 **Weekly GP** — Over the last 7 days GP was £140k, down £25k vs the same week last year, about 15% worse, with average GP per policy down to £21 from £24.
- 🔴 **Direct single** — Over the last 7 days direct single-trip GP was down £12k vs last year, with traffic up overall but fewer people getting to quote and lower GP on each sale.
- 🔴 **Europe mix** — Over the last 7 days Europe GP was down £19k vs last year, about 17% worse, because we sold slightly fewer policies and made a lot less on each one.
- 🔴 **Partner single** — Over the last 7 days partner referral single-trip GP was down £7k vs last year, mostly because volumes fell 28%.
- 🟡 **Renewals helped** — Over the last 7 days renewals added about £600 more GP than last year because renewal rate improved to 42% from 32%, offsetting part of the weakness elsewhere.

---

## What's Driving This

### Europe destination mix deterioration `LOW CONFIDENCE`

Over the last 7 days Europe GP fell £19k vs last year, about 17% worse. Policies were only down 4%, but average GP per policy dropped from about £23 to £20, so this looks like weaker conversion into better-value Europe sales rather than a traffic collapse.  
This may be partly holiday timing noise, but it lines up with our direct single weakness in Europe-heavy trips while the market is full of price shoppers.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE destination_group = 'Europe';
```

### Direct Single GP decline `MEDIUM CONFIDENCE`

Over the last 7 days direct single-trip GP fell £12k vs last year, down 28%. Sessions were up 7% overall, but session-to-search dropped from 18% to 14% and search-to-book also slipped, so traffic was there but fewer people reached quote and bought.  
Average GP per direct single policy fell from about £22 to £17 because underwriter cost rose faster than price. This has been weak on 9 of the last 10 days.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) / NULLIF(SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END),0) AS ty_avg_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) / NULLIF(SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END),0) AS ly_avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Direct' AND policy_type = 'Single';
```

### Partner Referral Single volume-led drop `LOW CONFIDENCE`

Over the last 7 days partner referral single-trip GP fell £7k vs last year, down 33%. We cannot see partner web traffic, but policies fell from 908 to 657, so this is mainly a volume problem before customers reach us.  
Average GP per policy only fell about £2, so the bigger issue is fewer referrals, especially in cruise-heavy partner business. Holiday timing may be muddying the YoY read.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Partner Referral' AND policy_type = 'Single';
```

### Silver Main Annual Med HX scheme decline `LOW CONFIDENCE`

Over the last 7 days Silver Main Annual Med HX GP fell £6k vs last year, down 34%. Policies fell 28%, and the annual issue looks to be fewer people getting to quote on both mobile and desktop.  
Price was up about 7%, but that did not help because cost pressure ate it. This is really the scheme-level version of the wider direct annual shortfall.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE scheme_name = 'Silver Main Annual Med HX';
```

### Direct Annual volume shortfall `LOW CONFIDENCE`

Over the last 7 days direct annual GP fell £6k vs last year, down 13%. That is still bad in-week because annual volume is future renewal income, and policies were down 13% even though market demand is strong.  
Traffic was up overall, but fewer sessions reached quote, which cut booked annual sessions on both mobile and desktop. We should treat this as missed acquisition, not a margin issue.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Direct' AND policy_type = 'Annual';
```

### Bronze Main Single Med HX scheme decline `MEDIUM CONFIDENCE`

Over the last 7 days Bronze Main Single Med HX GP fell £5k vs last year, down 34%, and policies were basically flat. That means the problem is quality of sale, not volume.  
Average GP per policy dropped from about £16 to £11, with mobile no-screening journeys doing most of the damage. This has been weak for 10 straight days.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE scheme_name = 'Bronze Main Single Med HX';
```

### Aggregator Single margin squeeze despite volume growth `LOW CONFIDENCE`

Over the last 7 days aggregator single-trip GP was down only about £300 vs last year, but that hides a bad trade-off. Policies were up 44%, yet average GP per policy fell from about £3 to under £2.  
So the traffic came in, but it was cheaper and lower-margin comparison traffic. Single-trip losses matter because there is no renewal payback.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) / NULLIF(SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END),0) AS ty_avg_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) / NULLIF(SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END),0) AS ly_avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Aggregator' AND policy_type = 'Single';
```

### Renewals GP uplift from stronger renewal rate `VERY LOW CONFIDENCE`

Over the last 7 days renewals added about £600 more GP than last year. Renewal volume rose 9% even though expiring annuals were down 17%, because renewal rate improved from 32% to 42%.  
This is helpful, but evidence is thin and holiday timing could distort it, so I would treat it as a small cushion rather than a trend yet.

```sql-dig
WITH expiring AS (
  SELECT
    SUM(CASE WHEN travel_end_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_expiring,
    SUM(CASE WHEN travel_end_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_expiring
  FROM `hx-data-production.commercial_finance.insurance_policies_new`
  WHERE policy_type = 'Annual'
),
renewed AS (
  SELECT
    SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' AND distribution_channel = 'Renewals' THEN policy_count ELSE 0 END) AS ty_renewed,
    SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' AND distribution_channel = 'Renewals' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
    SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' AND distribution_channel = 'Renewals' THEN policy_count ELSE 0 END) AS ly_renewed,
    SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' AND distribution_channel = 'Renewals' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
  FROM `hx-data-production.commercial_finance.insurance_policies_new`
)
SELECT * FROM expiring CROSS JOIN renewed;
```

---

## Customer Search Intent

According to Google Sheets dashboard data, overall travel demand is up 65% vs last year, and insurance searches are up 74% vs last year, faster than holiday searches at 53%. Insurance intent is also ahead of holidays right now, with an index gap of 3 points vs 1 point last year, which usually means more people are actively shopping cover, not just dreaming about trips.  
According to AI Insights, “travel insurance comparison” is up 375% and “do I need travel insurance” is up 31%, which says shoppers are more price-led and want simple reassurance. That fits what we’re seeing: demand exists, but direct is not turning enough of it into quote starts.  
The monthly Google Trends series also shows March is normally a strong insurance-search month, though 2020-21 is distorted by COVID and shouldn’t be used as a clean benchmark. **Source:** Google Sheets — Insurance Intent tab; Google Sheets — Dashboard Metrics tab.

---

## News & Market Context

According to AI Insights, Jet2, easyJet and TUI have all added Summer 2026 capacity, especially into Spain, Portugal, Greece and other Med routes, which should support demand for Europe cover rather than hurt it. **Source:** AI Insights — deep_dive; [Jet2 Summer 2026 programme](https://www.jet2.com/news/2024/09/Jet2_com_and_Jet2holidays_launch_biggest_ever_Summer_programme_for_2026?utm_source=openai)  
According to AI Insights, millions of EHIC/GHIC cards expiring and the EU Entry/Exit System going fully live by 10 April 2026 are adding friction and questions for travellers. That should help search demand for clear insurance guidance. **Source:** AI Insights — deep_dive; [ITIJ on EHIC/GHIC expiry](https://www.itij.com/latest/news/millions-uk-ehicghic-cards-set-expire-2025-raising-insurance-concerns?utm_source=openai)  
Middle East disruption is still in the news, with BA not operating some routes and war exclusions getting attention, but AI Insights says “travel chaos” and “airline strikes” are flat, so this does not look like the main trading driver this week. **Source:** AI Insights — news, trend; [BA update](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai)

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Fix direct quote-start friction on single-trip journeys, starting with mobile no-screening and desktop search pages | Direct single lost £12k/week and session-to-search fell from 18% to 14% | ~£12k/week |
| 2 | Push AMT harder in direct search and landing pages | Direct annual is down £6k/week on volume, and annual growth is future renewal income | ~£6k/week |
| 3 | Review Bronze single pricing and underwriter cost on direct web | Bronze Main Single Med HX lost £5k/week mostly from lower GP per sale, not lower volume | ~£5k/week |
| 4 | Go back to partner referrals with cruise-heavy partners and recover lost volume | Partner single lost £7k/week and volumes are down 28% | ~£7k/week |
| 5 | Tighten aggregator single-trip pricing floors or mix rules | Aggregator single volume is up but we are making under £2 a policy and losing money quality | ~£0k-£1k/week |

---

_Generated 08:00 16 Mar 2026 | 23 investigation tracks | gpt-5_

---
*Generated 11:37 16 Mar 2026 | Tracks: 23 + Follow-ups: 41 | Model: gpt-5.4*
