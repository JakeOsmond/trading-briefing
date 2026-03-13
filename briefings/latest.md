---
# HX Trading Briefing — 12 Mar 2026

## GP stayed soft yesterday and over the last 7 days vs the same week last year, even though market demand is hot, which means we’re missing traffic capture and making less on each sale.

---

## At a Glance

- 🔴 **Weekly GP** — Over the last 7 days vs the same period last year, GP was £147k, down £28k or 16%, with policies down only 180, so most of the damage came from weaker value per sale.
- 🔴 **Direct existing customers** — Over the last 7 days vs the same period last year, direct existing-customer GP fell £16k to £60k, with policies down 10% and GP per policy down 12%.
- 🔴 **Europe + worldwide** — Over the last 7 days vs the same period last year, Europe GP fell £14k and worldwide fell £14k, with volumes nearly flat, so this is mainly margin and mix getting worse.
- 🔴 **Direct single-trip** — Over the last 7 days vs the same period last year, direct single GP fell £9k to £35k, mostly because search-stage sessions dropped 13% and average GP per policy fell 20%.
- 🟡 **Annual capture** — Over the last 7 days vs the same period last year, annual policies fell 6% to 3,096; that’s a missed chance to invest in future renewal income while search demand is up sharply.

---

## What's Driving This

### Existing Direct customer GP decline `RECURRING`

Over the last 7 days vs the same period last year, direct existing-customer GP fell £16k to £60k. Traffic drove a lot of it: sessions were down 6%, search sessions were down 26%, and GP per policy was down 12%; this has been negative on 8 of the last 10 days.  
That tells us repeat customers are reaching the quote page less often, then buying a lower-value mix when they do.

```sql-dig
SELECT
  customer_type,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Direct'
GROUP BY 1;
```

### Europe destination GP decline `RECURRING`

Over the last 7 days vs the same period last year, Europe GP fell £14k to £98k while policies were only down 2%. The issue is value, not demand: avg GP per policy fell 12%, and the drag comes mainly from direct single, direct annual and partner single; negative on 8 of the last 10 days.  
Search demand in market is up, so we’re attracting a more price-sensitive Europe mix and not holding margin.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE destination_group = 'Europe'
GROUP BY 1,2;
```

### Worldwide destination GP decline `RECURRING`

Over the last 7 days vs the same period last year, worldwide GP fell £14k to £49k, with policies down only 5%. Avg GP per policy fell 18%, and the weakness sits in direct and renewals rather than a collapse in demand; negative on 8 of the last 10 days.  
Older, higher-value worldwide travellers were softer, so mix shifted away from our best-value customers.

```sql-dig
SELECT
  CASE
    WHEN max_age_at_purchase < 35 THEN 'Under 35'
    WHEN max_age_at_purchase < 55 THEN '35-54'
    WHEN max_age_at_purchase < 70 THEN '55-69'
    WHEN max_age_at_purchase < 80 THEN '70-79'
    ELSE '80+'
  END AS age_band,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE destination_group = 'Worldwide'
GROUP BY 1;
```

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same period last year, direct annual GP fell £10k to £43k, with policies down 12% and average GP down 7%. Traffic is the bigger problem: search-stage sessions were down 13%, especially on mobile; this has been negative on 7 of the last 10 days.  
This is not about annual margins. It’s a missed chance to invest in future renewal income while annual search demand is strong.

```sql-dig
SELECT
  booking_source,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Direct' AND policy_type = 'Annual'
GROUP BY 1;
```

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same period last year, direct single GP fell £9k to £35k, with policy volume basically flat, so this is a margin problem first. Search-stage sessions fell 13%, mobile search sessions fell 27%, and average GP per policy dropped 20%; this has been negative on 9 of the last 10 days.  
That’s the clearest commercial issue in the book: we’re not getting enough people to quote, and when they buy, Bronze and Silver singles are worth less.

```sql-dig
SELECT
  cover_level_name,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Direct' AND policy_type = 'Single'
GROUP BY 1;
```

### Silver cover level GP decline `RECURRING`

Over the last 7 days vs the same period last year, Silver GP fell £8k to £56k, with policies down 8% and GP per policy down 5%. Traffic mattered most here too: direct web search sessions were weaker, and Silver annual and single medical schemes both lost ground; negative on 7 of the last 10 days.  
This looks like a mainstream product problem, not a niche one.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE cover_level_name = 'Silver'
GROUP BY 1,2;
```

### Partner Referral Single GP decline `RECURRING`

Over the last 7 days vs the same period last year, partner single GP fell £7k to £15k, with policies down 29%. This is mainly a traffic and partner-volume problem, not just margin, and it has been negative on 7 of the last 10 days.  
The losses are concentrated in cruise-led partner relationships like P&O and Cunard, so this needs partner-specific action.

```sql-dig
SELECT
  agent_name,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Partner Referral' AND policy_type = 'Single'
GROUP BY 1;
```

### Renewals Annual GP decline `EMERGING`

Over the last 7 days vs the same period last year, renewals annual GP fell £2k to £49k even though policies were up 6%. This is a value mix issue, not a retention issue: GP per policy fell 10%, and it has been negative on 6 of the last 10 days.  
More customers renewed, but more of them came through lower-value cohorts and opt-out/manual routes.

```sql-dig
SELECT
  auto_renew_opt_in,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN policy_count ELSE 0 END) AS ty_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2026-03-05' AND '2026-03-12' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ty_gp,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN policy_count ELSE 0 END) AS ly_policies,
  SUM(CASE WHEN transaction_date BETWEEN '2025-03-06' AND '2025-03-13' THEN CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64) ELSE 0 END) AS ly_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Renewals' AND policy_type = 'Annual'
GROUP BY 1;
```

---

## Customer Search Intent

According to Dashboard Metrics, insurance search demand is up 74% vs last year, with insurance searches at 11.5 vs 6.6 and holiday searches up 48%, so intent is growing faster for insurance than for trips. According to the same source, the insurance-minus-holiday gap widened to 3.1 from 1.0 last year, which says shoppers are closer to buying and thinking harder about risk and cover.  
According to AI Insights, the strongest terms are around travel insurance, annual multi-trip, pre-existing medical, GHIC/EHIC, disruption and “do I need travel insurance”, which should help AMT and medical if we capture it. AI Insights also flags Spain, Greece and Italy as strong destinations in the search mix, helped by airline seat sales and Easter planning.  
Bottom line: the market is hot, especially for annual and medical, so our weak week is an HX capture problem, not a demand problem. **Source:** Google Sheets — Insurance Intent tab. **Source:** Google Sheets — Dashboard Metrics tab.

---

## News & Market Context

According to AI Insights, easyJet, Ryanair, Jet2 and BA have all put more 2026 capacity and sale fares into market, which is pushing early summer and Easter planning and should support insurance demand. **Source:** AI Insights — deep_dive; [Yahoo Finance on easyJet seat release](https://uk.finance.yahoo.com/news/easyjet-releases-25-million-budget-162457150.html?utm_source=openai)  
According to AI Insights, new EU Entry/Exit checks moving toward full operation by 10 April 2026 are driving reassurance searches around travel rules and cover. **Source:** AI Insights — deep_dive  
According to MoneyWeek, confusion over Spain cover and reliance on GHIC is lifting medical-cover research, which fits the rise in risk-led searches. **Source:** [MoneyWeek](https://moneyweek.com/spending-it/travel-holidays/new-spanish-travel-insurance-rule?utm_source=openai)  
According to AP News and Met Office-linked reporting in AI Insights, recent disruption from strikes, storms and fog has kept cancellation and delay cover top of mind. **Source:** AI Insights — trend; [AP News](https://apnews.com/article/95179f730223cf9bb5184e650d33a515?utm_source=openai)  
Competitively, comparison shopping stays important and likely intensifies into spring as APD rises from 1 April 2026. **Source:** [FCA Handbook Notice 133](https://www.fca.org.uk/publication/handbook/handbook-notice-133.pdf); [UK Government APD rates](https://www.gov.uk/government/publications/changes-to-air-passenger-duty-rates-from-1-april-2026/air-passenger-duty-rates-from-1-april-2026-to-31-march-2027)

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Fix direct single web funnel on mobile Bronze and Silver. Review search-page drop, quote quality and pricing/discount settings today. | Direct single lost £9k/week YoY, with mobile search sessions down 27% and GP per policy down 20%. | ~£9k/week |
| 2 | Push paid search harder into annual multi-trip, medical and GHIC/EES terms, with AMT-first landing pages. | Market search demand is up 74% YoY but direct annual GP is down £10k/week and annual volume is down 6%. | ~£10k/week |
| 3 | Rework Europe pricing and cover mix on direct single and partner single, especially two-traveller and longer-lead trips. | Europe is down £14k/week with volume nearly flat, so margin and mix are the issue. | ~£14k/week |
| 4 | Call the worst-hit partner accounts now, especially P&O/Cunard/Fred Olsen routes, and check placement and campaign volume. | Partner single is down £7k/week and policies are down 29%, concentrated in named cruise partners. | ~£7k/week |
| 5 | Review renewal cohort pricing and opt-in journey for year 0/1 annual renewals. | Renewals annual lost £2k/week despite volume up 6%, so value per renewal has slipped. | ~£2k/week |

---

_Generated 06:50 13 Mar 2026 | 23 investigation tracks | GPT-5_

---
*Generated 10:26 13 Mar 2026 | Tracks: 23 + Follow-ups: 31 | Model: gpt-5.4*
