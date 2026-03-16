---
# HX Trading Briefing — 15 Mar 2026

## Weekly GP is down £25k over the last 7 days vs the same week last year, and the real problem is we are missing strong market demand because fewer web visits are reaching a quote.

---

## At a Glance

- 🔴 **Europe value drop** — Over the last 7 days vs the same week last year, Europe GP fell by £19k to £90k, with policies only down 4%, so we sold nearly as many but made a lot less on each one.
- 🔴 **Direct single-trip weakness** — Over the last 7 days vs the same week last year, direct single-trip GP fell £12k to £31k because quote generation got worse and average GP per policy dropped 21%.
- 🔴 **Partner single-trip loss** — Over the last 7 days vs the same week last year, partner referral single-trip GP fell £7k to £13k, mostly because volumes dropped 28%.
- 🔴 **Direct annual volumes down** — Over the last 7 days vs the same week last year, direct annual GP fell £6k to £41k because we sold 13% fewer annuals, which means less future renewal income.
- 🔴 **Overall GP down** — Over the last 7 days vs the same week last year, total GP was £140k, down £25k or about 15%, with policies down 4% and GP per policy down 12%.

---

## What's Driving This

### Direct Single GP decline `MEDIUM CONFIDENCE`

Over the last 7 days vs the same week last year, direct single-trip GP fell £12k to £31k. This appears to be real rather than a blip: web sessions were up 10% overall, but session-to-search fell from 17% to 14% and average GP per sale dropped from about £22 to £17; bank holiday timing makes YoY a bit messier.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Direct' AND policy_type='Single'
  AND transaction_date BETWEEN '2025-03-09' AND '2026-03-15';
```

### Europe destination mix deterioration `LOW CONFIDENCE`

Over the last 7 days vs the same week last year, Europe GP fell £19k to £90k. This may be a real mix problem, not a demand problem: policy volume was only down 4%, but average GP fell 14%, which fits more price-sensitive Europe shoppers and our weaker single-trip yield; bank holiday timing reduces confidence.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE destination_group='Europe'
  AND transaction_date BETWEEN '2025-03-09' AND '2026-03-15';
```

### Partner Referral Single volume loss `LOW CONFIDENCE`

Over the last 7 days vs the same week last year, partner referral single-trip GP fell £7k to £13k. This may be mostly a traffic problem in partner channels: volumes were down 28% while average GP only slipped 7%, with some extra squeeze from higher commission and underwriter cost.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Partner Referral' AND policy_type='Single'
  AND transaction_date BETWEEN '2025-03-09' AND '2026-03-15';
```

### Direct Annual volume decline `LOW CONFIDENCE`

Over the last 7 days vs the same week last year, direct annual GP fell £6k to £41k because annual volumes dropped 13% from 922 to 801. Annual margin is not the story here and we should not chase it — this is about losing future renewal income because fewer visitors got through to quote.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Direct' AND policy_type='Annual'
  AND transaction_date BETWEEN '2025-03-09' AND '2026-03-15';
```

### Partner Referral Annual decline `LOW CONFIDENCE`

Over the last 7 days vs the same week last year, partner referral annual GP fell £2k to £8k. This may be a partner economics problem more than demand: volumes were down 9% and average GP fell 14% as commission and underwriter cost rose faster than price.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Partner Referral' AND policy_type='Annual'
  AND transaction_date BETWEEN '2025-03-09' AND '2026-03-15';
```

### Aggregator Single GP erosion `LOW CONFIDENCE`

Over the last 7 days vs the same week last year, aggregator single-trip GP fell only about £300 to £2k, but that hides a bigger issue. We sold 44% more policies, yet average GP per policy fell 41% to about £2, so we are winning more low-value single-trip business with no renewal upside.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Aggregator' AND policy_type='Single'
  AND transaction_date BETWEEN '2025-03-09' AND '2026-03-15';
```

### Aggregator Annual volume decline `VERY LOW CONFIDENCE`

Over the last 7 days vs the same week last year, aggregator annual GP improved by about £1k, but annual volumes fell 15% from 960 to 813. This is likely noise in the short term, but the bit to watch is weaker annual acquisition into future renewals, not the still-negative margin.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Aggregator' AND policy_type='Annual'
  AND transaction_date BETWEEN '2025-03-09' AND '2026-03-15';
```

### Renewal rate-driven annual GP support `VERY LOW CONFIDENCE`

Over the last 7 days vs the same week last year, renewals annual GP was up about £600 to £49k. This is likely encouraging but still early: fewer policies expired, yet renewal rate improved from 32% to 42%, which more than offset the smaller base.

```sql-dig
SELECT
  SUM(CASE WHEN distribution_channel='Renewals' AND transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN policy_count ELSE 0 END) AS ty_renewed_policies,
  SUM(CASE WHEN distribution_channel='Renewals' AND transaction_date BETWEEN '2026-03-08' AND '2026-03-15' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN distribution_channel='Renewals' AND transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN policy_count ELSE 0 END) AS ly_renewed_policies,
  SUM(CASE WHEN distribution_channel='Renewals' AND transaction_date BETWEEN '2025-03-09' AND '2025-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`;
```

## Customer Search Intent

According to Dashboard Metrics, overall market demand is up 65% vs last year, with insurance searches up 74% and holiday searches up 53%, so demand is strong and insurance intent is growing faster than trip planning. According to AI Insights, “travel insurance comparison” is up 375% and “do I need travel insurance” is up 31%, which fits what we are seeing in Europe and aggregator single-trip business: more shoppers, but more price-checking too. According to AI Insights, “book holiday 2026” is up 420%, which should help annual multi-trip demand if we capture it properly. Google Trends data also shows travel insurance search interest has recovered well beyond the old COVID-distorted years, so this is a live market, not a weak one.  
**Source:** Google Sheets — Insurance Intent tab  
**Source:** Google Sheets — Dashboard Metrics tab  
**Source:** AI Insights — what_matters, divergence, yoy

## News & Market Context

According to Jet2, it has put its biggest ever Summer 2026 programme on sale, including a new Gatwick base and nearly 900,000 seats, which should be feeding more travel insurance demand into Spain, the Canaries and Greece. According to AI Insights, easyJet is also adding routes and TUI has a large Summer 2026 programme, so the market backdrop is supportive for both single and annual travel insurance. According to ITIJ, millions of UK EHIC/GHIC cards are expiring and the NHS is clear they do not replace travel insurance, which should help value-led messaging rather than pure price selling. According to UK government bank holiday dates, we are moving into the Easter booking window, which should lift demand through late March. On disruption, British Airways is still not operating several Middle East routes and ABI-style war exclusions remain relevant, so clear wording matters for trust and conversion.  
**Source:** [Jet2 Summer 2026 launch](https://www.jet2.com/news/2024/09/Jet2_com_and_Jet2holidays_launch_biggest_ever_Summer_programme_for_2026?utm_source=openai)  
**Source:** [ITIJ on EHIC/GHIC expiry](https://www.itij.com/latest/news/millions-uk-ehicghic-cards-set-expire-2025-raising-insurance-concerns?utm_source=openai)  
**Source:** [UK bank holidays](https://www.gov.uk/bank-holidays)  
**Source:** [BA Middle East update](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai)  
**Source:** AI Insights — deep_dive, seasonal, news

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Fix direct quote-start drop on mobile and desktop this week | Direct single and direct annual are down because session-to-search fell from 17% to 14% despite sessions being up 10% | ~£18k/week |
| 2 | Review direct single-trip pricing and underwriter cost on Bronze and Silver Europe business | Direct single lost £12k and Europe lost £19k, with average GP down hard not just volume | ~£12k/week |
| 3 | Push annual multi-trip harder in PPC and landing pages | Search demand is up 74% YoY and “book holiday 2026” is surging, but direct annual volume is down 13% | ~£6k/week |
| 4 | Challenge partner single-trip volumes with top referral partners now | Partner referral single lost £7k, mostly from a 28% volume drop | ~£7k/week |
| 5 | Tighten aggregator single-trip trading, especially low-value comparison cohorts | We sold 44% more aggregator singles but made £300 less GP, so more of this volume is not helping | ~£1k/week |

---

_Generated 00:00 16 Mar 2026 | 23 investigation tracks | gpt-5_

---
*Generated 21:49 16 Mar 2026 | Tracks: 23 + Follow-ups: 30 | Model: gpt-5.4*
