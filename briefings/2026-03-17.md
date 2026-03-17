---
# HX Trading Briefing — 16 Mar 2026

## Over the last 7 days vs the same period last year, GP was weak because direct single-trip lost margin and direct annual sold fewer policies despite a growing market.

---

## At a Glance

- 🔴 **Weekly GP down** — Over the last 7 days vs the same period last year, GP was £143k, down £27k or 16%, and we sold about 4% fewer policies, so the bigger hit came from making less on each sale.
- 🔴 **Direct single hurting most** — Over the last 7 days vs the same period last year, direct single-trip GP fell £12k to £31k, with weaker funnel entry and conversion plus average GP per policy down 22%.
- 🔴 **Europe under-monetised** — Over the last 7 days vs the same period last year, Europe GP fell £20k to £92k, with policies only down 3%, so most of the damage came from lower value per policy.
- 🔴 **Direct annual volume missed** — Over the last 7 days vs the same period last year, direct annual GP fell £8k to £41k on 16% fewer policies, which means we are missing future renewal income.
- 🟢 **Market demand is up** — Over the last 7 days vs the same period last year, insurance search demand was up about 71%, so this looks like an internal execution problem more than a weak market.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same period last year, direct single-trip GP fell £12k to £31k. Desktop sessions were up 32% and mobile sessions were down 2%, but conversion got worse on both: desktop session-to-search fell from 15% to 12% and search-to-book fell from 38% to 30%, while mobile session-to-search fell from 20% to 16%; average GP per policy also dropped 22% from £22 to £17.  
This is clearly a funnel-and-margin problem, not weak demand. Underwriter cost per policy rose 12% while customer price fell 3%, and this has been negative on 9 of the last 10 trading days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same period last year, direct annual GP fell £8k to £41k because we sold 16% fewer policies, while average GP per policy was almost flat at about £51 vs £52 last year. Traffic was not the main issue here; the data shows weaker funnel entry, with booked annual sessions down 15% on mobile and 16% on desktop.  
This is a missed acquisition opportunity, not an annual margin problem. We are missing future renewal income in a market where search demand is growing.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

### Europe destination GP decline `EMERGING`

Over the last 7 days vs the same period last year, Europe GP fell £20k to £92k, with policies down only 3% but average GP down 15%. That says demand held up reasonably well, but we made less money from the business we did write.  
Most of this lines up with direct single and lower-tier cover weakness inside Europe rather than a Europe demand slump.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND destination_group = 'Europe'
GROUP BY 1;
```

### Existing customer Direct GP decline `EMERGING`

Over the last 7 days vs the same period last year, direct existing-customer GP fell £18k to £55k, with policies down 17% and average GP down 9%. The data suggests fewer returning customers are getting through to price pages, which then feeds both the direct annual and direct single shortfall.  
This looks more like a journey and re-entry problem than a demand problem, because the wider market is up.

```sql-dig
SELECT
  customer_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND distribution_channel = 'Direct'
  AND customer_type = 'Existing'
GROUP BY 1;
```

### Bronze cover level GP decline `EMERGING`

Over the last 7 days vs the same period last year, Bronze GP fell £9k to £28k, with policies down 6% and average GP down 18%. Traffic did not disappear, so the bigger problem is lower value per sale in a high-volume entry tier.  
This looks tied mainly to direct single-trip margin squeeze rather than heavier discounting.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND cover_level_name = 'Bronze'
GROUP BY 1;
```

### Silver cover level GP decline `EMERGING`

Over the last 7 days vs the same period last year, Silver GP fell £9k to £54k, with policies down 12% and average GP down 3%. This is a volume-led drop first, with some value pressure on top.  
It appears to be part of the broader direct annual and direct single weakness rather than a standalone product issue.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND cover_level_name = 'Silver'
GROUP BY 1;
```

### Worldwide destination GP decline `NEW`

Over the last 7 days vs the same period last year, Worldwide GP fell £7k to £51k, with policies down 6% and average GP down 7%. That points to some yield pressure as well as slightly lower demand.  
This may be part of the same value squeeze showing up in mainstream long-haul cover, but it is too early to call it structural.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND destination_group = 'Worldwide'
GROUP BY 1;
```

### Partner Referral Single GP decline `NEW`

Over the last 7 days vs the same period last year, partner referral single-trip GP fell £6k to £14k, mostly because policies were down 27% while average GP was broadly flat. This looks more like weaker partner flow than a pricing problem.  
It may be tied to softer cruise-related referral volume, but it is too early to say that with confidence.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-09' AND '2026-03-16'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

---

## Customer Search Intent

According to Google Sheets Dashboard Metrics, over the latest tracked week vs the same period last year, travel demand was up 66%, holiday searches were up 56%, and insurance searches were up 71%. According to Google Sheets — Insurance Intent tab, insurance intent sits at about 11.5 vs 6.6 last year, so shoppers are searching for cover much more actively than they were a year ago. AI Insights says annual, medical and cruise-related terms are all benefiting, with Spain, Italy, Greece, France, USA and Turkey called out as stronger destinations. According to AI Insights — seasonal, demand should keep building from mid-March into Easter rather than soften from here. **Source:** Google Sheets — Insurance Intent tab. **Source:** Google Sheets — Dashboard Metrics tab. **Source:** AI Insights — what_matters, seasonal, channels.

---

## News & Market Context

According to AI Insights — deep_dive, airlines are supporting demand with summer seat releases and new routes, which fits the stronger insurance search trend. ABI guidance continues to highlight high medical claim costs, especially for the USA, which helps explain stronger medical-cover intent. British Airways disruption linked to the Middle East has kept travel disruption and cover terms in the news, which can push shoppers toward reassurance-led insurance buying. Saga is also publicly talking about automatic cover extensions for stranded customers, which is a useful competitor signal on reassurance messaging. MoneySuperMarket says average February 2026 prices were about £25 for single trip and £61 for annual multi-trip, which fits a competitive market where single-trip economics can get squeezed fast. **Source:** AI Insights — deep_dive, news. **Source:** [ABI travel insurance tips](https://www.abi.org.uk/news/news-articles/2025/8/eight-to-embark-travel-insurance-tips/?utm_source=openai). **Source:** [BA disruption update](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai). **Source:** [Saga Middle East disruption page](https://www.saga.co.uk/travel-insurance/middle-east-travel-disruption?utm_source=openai). **Source:** [MoneySuperMarket travel insurance statistics](https://www.moneysupermarket.com/travel-insurance/travel-insurance-statistics/).

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Rework direct single-trip pricing and underwriter terms on Bronze and Silver, then check mobile and desktop quote results side by side | Over the last 7 days vs last year, direct single lost £12k, with underwriter cost up 12%, price down 3%, and average GP per policy down 22% | ~£12k/week |
| 2 | Fix the direct funnel before the search-results page on mobile and desktop, starting with session-to-search drop points | Over the last 7 days vs last year, direct single and direct annual both lost volume because fewer visitors reached pricing pages | ~£8k/week |
| 3 | Put more paid and landing-page focus behind direct annual terms, especially annual, medical and cruise journeys | Over the last 7 days vs last year, direct annual GP was down £8k on 16% fewer policies in a market where insurance searches were up about 71% | ~£8k/week |
| 4 | Audit the returning-customer direct journey from CRM click through to quote page, and remove any blockers | Over the last 7 days vs last year, existing direct customer GP was down £18k because fewer returning customers converted | ~£18k/week |
| 5 | Check partner placement and referral volume by cruise and key partner account, then push make-good volume where needed | Over the last 7 days vs last year, partner referral single GP was down £6k mainly because sales were down 27% | ~£6k/week |

---
*Generated 08:26 17 Mar 2026 | Tracks: 23 + Follow-ups: 29 | Model: gpt-5.4*
