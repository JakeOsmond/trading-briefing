---
# HX Trading Briefing — 16 Mar 2026

## Over the last 7 days vs the same week last year, GP was weak because Direct missed strong market demand, with single-trip doing most of the damage.

---

## At a Glance

- 🔴 **Weekly GP** — Over the last 7 days vs the same week last year, GP was £143k — down £27k, about 16% worse, even though travel insurance search demand is sharply up.
- 🔴 **Direct single-trip** — Over the last 7 days vs the same week last year, Direct single-trip GP fell £12k to £31k as quote generation weakened, conversion slipped and margin got squeezed.
- 🔴 **Silver and Bronze** — Over the last 7 days vs the same week last year, Silver GP fell £9k to £54k and Bronze fell £9k to £28k, mainly inside Direct core products.
- 🔴 **Direct annual** — Over the last 7 days vs the same week last year, Direct annual GP fell £8k to £41k because we sold about 150 fewer policies, which means less investment into future renewal income.
- 🟢 **Renewals** — Over the last 7 days vs the same week last year, renewal GP rose £3k to £52k as retention improved, partly offsetting the shortfall elsewhere.

---

## What's Driving This

### Direct single-trip GP decline `RECURRING`

Over the last 7 days vs the same week last year, Direct single-trip GP fell £12k to £31k. Traffic mix was mixed, with desktop sessions up 32% but mobile sessions down 2%, yet session-to-search fell on both devices and average GP per policy dropped 22%, so we turned market demand into fewer quotes, fewer bookings and less value per sale; this is a recurring issue across the last 10 trading days.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-09' AND '2026-03-16' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-09' AND '2026-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-10' AND '2025-03-17' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-10' AND '2025-03-17' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-09' AND '2026-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) /
    NULLIF(SUM(CASE WHEN transaction_date BETWEEN '2026-03-09' AND '2026-03-16' THEN policy_count ELSE 0 END), 0) AS ty_avg_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-10' AND '2025-03-17' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) /
    NULLIF(SUM(CASE WHEN transaction_date BETWEEN '2025-03-10' AND '2025-03-17' THEN policy_count ELSE 0 END), 0) AS ly_avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Direct'
  AND policy_type = 'Single'
  AND transaction_date BETWEEN '2025-03-10' AND '2026-03-16'
```

### Direct annual GP decline `RECURRING`

Over the last 7 days vs the same week last year, Direct annual GP fell £8k to £41k because policies dropped 16%, while average GP per policy was almost flat. Desktop traffic was up 32% but mobile traffic slipped 2%, and session-to-search fell on both devices, so the main leak is earlier in the funnel; this is missed investment into future renewal income and has been recurring across the last 10 trading days.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-09' AND '2026-03-16' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-09' AND '2026-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-10' AND '2025-03-17' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-10' AND '2025-03-17' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Direct'
  AND policy_type = 'Annual'
  AND transaction_date BETWEEN '2025-03-10' AND '2026-03-16'
```

### Bronze cover-level GP decline `EMERGING`

Over the last 7 days vs the same week last year, Bronze GP fell £9k to £28k. This looks mostly like a Direct single-trip margin squeeze rather than a traffic problem on its own, with only a small policy drop but average GP per policy down about 18% as underwriter costs took more of the sale.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-09' AND '2026-03-16' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-09' AND '2026-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-10' AND '2025-03-17' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-10' AND '2025-03-17' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE cover_level_name = 'Bronze'
  AND transaction_date BETWEEN '2025-03-10' AND '2026-03-16'
```

### Silver cover-level GP decline `EMERGING`

Over the last 7 days vs the same week last year, Silver GP fell £9k to £54k. Traffic into Direct was there on desktop, but weaker quote generation and fewer booked sessions on both devices fed through into both annual and single-trip Silver sales, so this looks more like the product-level expression of the wider Direct funnel issue.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-09' AND '2026-03-16' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-09' AND '2026-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-10' AND '2025-03-17' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-10' AND '2025-03-17' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE cover_level_name = 'Silver'
  AND transaction_date BETWEEN '2025-03-10' AND '2026-03-16'
```

### Partner Referral single-trip volume decline `NEW`

Over the last 7 days vs the same week last year, Partner Referral single-trip GP fell £6k to £14k. This may be partner traffic or partner conversion softness rather than weaker market demand, because policies fell 27% while average GP per policy stayed about flat.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-09' AND '2026-03-16' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-09' AND '2026-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-10' AND '2025-03-17' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-10' AND '2025-03-17' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
  AND transaction_date BETWEEN '2025-03-10' AND '2026-03-16'
```

### Partner Referral annual GP decline `NEW`

Over the last 7 days vs the same week last year, Partner Referral annual GP fell £4k to £8k. This may be a mix issue inside cruise-led partners, with policies down 19% and average GP per policy down 18%, which means we are writing less future renewal book through that route.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-09' AND '2026-03-16' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-09' AND '2026-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-10' AND '2025-03-17' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-10' AND '2025-03-17' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
  AND transaction_date BETWEEN '2025-03-10' AND '2026-03-16'
```

### Aggregator single-trip GP decline `NEW`

Over the last 7 days vs the same week last year, Aggregator single-trip GP fell by about £500 to £2k. Volume was up 49%, so demand through comparison sites looks healthy, but we won a lot more low-value business and average GP per policy roughly halved, which matters because single-trip losses do not renew.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-09' AND '2026-03-16' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-09' AND '2026-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-10' AND '2025-03-17' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-10' AND '2025-03-17' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
  AND transaction_date BETWEEN '2025-03-10' AND '2026-03-16'
```

### Renewals GP growth `NEW`

Over the last 7 days vs the same week last year, renewal GP rose £3k to £52k. That is directionally good and helped offset losses elsewhere, but it is too early to call it a durable step-up yet.

```sql-dig
SELECT
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-09' AND '2026-03-16' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-09' AND '2026-03-16' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-10' AND '2025-03-17' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-10' AND '2025-03-17' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
  AND transaction_date BETWEEN '2025-03-10' AND '2026-03-16'
```

---

## Customer Search Intent

According to Google Sheets Dashboard Metrics, over the last 7 days vs the same week last year, travel insurance search intent was up about 75%, with the insurance index at 11.5 versus 6.6 last year. According to the same source, holiday search intent was up about 56%, at 8.7 versus 5.6, so insurance demand is rising faster than trip demand. According to Google Sheets Insurance Intent and AI Insights, annual, medical, cruise, Spain, USA and Turkey searches are all strong, and comparison-style searches are also rising, which should be feeding both Direct and Aggregator. The read-across is simple: the market is there, but we are not turning enough of that intent into quotes and bookings. **Source:** Google Sheets — Dashboard Metrics tab. **Source:** Google Sheets — Insurance Intent tab. **Source:** AI Insights — what_matters, channels, quarterly.

---

## News & Market Context

According to AI Insights, airlines including easyJet and Ryanair are pushing summer seat releases and new routes, which is pulling booking and insurance demand forward. According to the ABI, medical travel cover remains a live consumer theme, with recent guidance stressing large claim costs and the limits of relying on GHIC alone. AI Insights also says Middle East disruption and war-exclusion stories are keeping insurance relevant, but they may be making customers shop around harder on cover detail and price. That should still be a supportive market for PPC, SEO and comparison sites, especially on annual, medical and cruise terms. So the weak result looks much more like an HX capture problem than a weak market. **Source:** AI Insights — deep_dive, news, seasonal. **Source:** [ABI travel insurance tips](https://www.abi.org.uk/news/news-articles/2025/8/eight-to-embark-travel-insurance-tips/?utm_source=openai). **Source:** [easyJet seat release coverage](https://www.the-independent.com/travel/news-and-advice/easyjet-2026-flight-sale-prices-b2793536.html?utm_source=openai).

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Audit Direct session-to-search performance by device from 13 Feb onward and roll back any losing landing-page, gatekeeper or quote-start changes | Over the last 7 days vs the same week last year, Direct single and annual lost about £20k combined while desktop traffic was up 32% but session-to-search fell on both desktop and mobile | ~£20k/week |
| 2 | Rework Direct single-trip pricing or underwriter settings on Bronze and Silver, starting with mobile non-med journeys | Over the last 7 days vs the same week last year, Direct single lost £12k and Bronze plus Silver lost about £18k combined, with average GP down and underwriter cost taking more of the sale | ~£12k/week |
| 3 | Shift paid search and SEO landing-page effort into annual, medical and cruise terms with faster quote-entry pages | Over the last 7 days vs the same week last year, search demand was up about 75% but Direct annual policies fell 16%, so we are missing future renewal income | ~£8k/week |
| 4 | Review partner performance with cruise-led schemes, especially Carnival, and fix any referral or pricing gaps | Over the last 7 days vs the same week last year, Partner Referral single and annual GP fell about £10k combined | ~£10k/week |
| 5 | Tighten Aggregator single-trip bidding or product settings on low-value web business | Over the last 7 days vs the same week last year, Aggregator single-trip GP fell about £500 even though volume was up 49%, so we are buying too much low-value single-trip business | ~£1k/week |

---

---
*Generated 16:36 17 Mar 2026 | Tracks: 23 + Follow-ups: 37 | Model: gpt-5.4*
