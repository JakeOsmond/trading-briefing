---
# HX Trading Briefing — 17 Mar 2026

## Over the last 7 days vs the same week last year, GP was down £24k, about 15% worse, as direct single and direct annual web weakness outweighed stronger renewals.

---

## At a Glance

- 🔴 **Weekly GP down** — Over the last 7 days vs the same week last year, GP was £139k, down £24k, about 15% worse, with most of the hit coming from direct single down £12k and direct annual down £11k.
- 🔴 **Direct single is the biggest drag** — Over the last 7 days vs the same week last year, direct single GP fell £11.7k, with traffic mixed, quote-stage conversion weaker, and average GP per policy down to about £17 from £22.
- 🔴 **Direct annual sales slowed** — Over the last 7 days vs the same week last year, direct annual GP fell £10.6k because fewer annual shoppers got through and bought; that means slower investment in future renewal income.
- 🟢 **Renewals offset some of the pain** — Over the last 7 days vs the same week last year, renewal GP was up about £8k, with renewed policies up 14% from 1,091 to 1,246.
- 🔴 **Partner referrals stayed weak** — Over the last 7 days vs the same week last year, partner referral GP was down about £11k across single and annual, with cruise-heavy contact centre sales the softest.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct single GP fell £11.7k to £30.3k. Traffic was mixed rather than collapsing, but quote-stage conversion got worse on both mobile and desktop, and average GP per policy fell to £17 from £22; this has been down on 8 of the last 10 days.

```sql-dig
SELECT
  booking_source,
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct annual GP fell £10.6k to £37.3k. Sessions and booked sessions were down on mobile and desktop, while GP per converted session held up, so this is mainly fewer annual sales coming through the funnel; this has been down on 7 of the last 10 days, which means slower investment in future renewal income.

```sql-dig
SELECT
  booking_source,
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

### Existing customer Direct GP decline `EMERGING`

Over the last 7 days vs the same week last year, direct GP from existing customers was down about £20k. Traffic only slipped a little, so the bigger problem is fewer existing customers getting through to a quote and buying.

```sql-dig
SELECT
  customer_type,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Direct'
GROUP BY 1,2;
```

### Europe destination GP decline `EMERGING`

Over the last 7 days vs the same week last year, Europe GP was down about £20k while policy count was only down about 2%. That says demand broadly held up, but we made less on each Europe sale, especially in direct and partner mainstream products.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND destination_group = 'Europe'
GROUP BY 1,2;
```

### Bronze cover level GP decline `EMERGING`

Over the last 7 days vs the same week last year, Bronze GP was down about £9k. We sold fewer Bronze policies and made less on each one, with average GP per Bronze policy down to about £17 from £21.

```sql-dig
SELECT
  scheme_name,
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND cover_level_name = 'Bronze'
GROUP BY 1,2,3;
```

### Partner Referral Single GP decline `NEW`

Over the last 7 days vs the same week last year, partner referral single GP fell about £6k. This looks mostly volume-led, and the weakest pocket was cruise-heavy contact centre business.

```sql-dig
SELECT
  scheme_name,
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Partner Referral Annual GP decline `NEW`

Over the last 7 days vs the same week last year, partner referral annual GP fell about £5k. This may be lower volume first, with some commission pressure on cruise-heavy assisted sales, but the signal is weaker than the direct-channel story.

```sql-dig
SELECT
  booking_source,
  scheme_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_commission
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

### Renewals Annual GP growth `NEW`

Over the last 7 days vs the same week last year, renewals GP was up about £8k and renewed policies rose 14% from 1,091 to 1,246. This clearly cushioned a worse week, even if it is too early to call it a lasting step-change.

```sql-dig
SELECT
  booking_source,
  scheme_name,
  SUM(policy_count) AS renewed_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS renewed_gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

## Customer Search Intent

According to Google Sheets — Dashboard Metrics tab, travel insurance search demand is up 74% vs last year, ahead of holiday search demand at 51%, so the market is growing faster than our recent sales. According to AI Insights and Google Sheets — Insurance Intent tab, broader insurance searches are up roughly 57% to 63% YoY, with the last 4 weeks up about 40%, which points to healthy customer demand. According to Google Sheets — Insurance Intent tab, “travel insurance deals” is up 986% YoY, “cheapest travel insurance” is up 141%, and comparison-led terms are up about 400%, which matches weaker Bronze and Silver economics and a more price-sensitive shopper. According to AI Insights, Spain, Greece and Italy are the main destination winners, while GHIC/EHIC and “do I need travel insurance” searches are also rising, suggesting customers are still buying but checking value and cover details more carefully.  
**Source:** Google Sheets — Insurance Intent tab  
**Source:** Google Sheets — Dashboard Metrics tab  
**Source:** AI Insights — deep_dive

## News & Market Context

According to AI Insights, competitors are seeing strong demand too, with Staysure search interest up 52% and AllClear up 33%, so we are competing in a busier and more price-led market. According to [Yahoo News](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai), British Airways is still not flying to some Middle East destinations, which keeps disruption in the news and may be pushing shoppers toward Europe and single-trip cover. According to [The Week](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war?utm_source=openai) and [Saga](https://www.saga.co.uk/travel-insurance/middle-east-travel-disruption?utm_source=openai), war exclusions and disruption cover remain front of mind, which makes clear cover wording more important than usual. According to internal context and AI Insights, Carnival traffic is down about 20%, which lines up with the cruise-heavy partner referral weakness. According to the FCA, travel insurance signposting rules for customers with medical conditions remain in force, so trust and clarity still matter in the funnel for medical shoppers.  
**Source:** AI Insights — what_matters  
**Source:** AI Insights — news  
**Source:** [FCA travel insurance signposting review](https://www.fca.org.uk/publications/multi-firm-reviews/travel-insurance-signposting-rules-consumers-medical-conditions-review)

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Fix the quote-stage drop in direct single on Bronze and Silver, starting with mobile and desktop search entry pages | Over the last 7 days vs the same week last year, direct single GP lost £11.7k because fewer sessions reached quote and average GP per policy fell | ~£12k/week |
| 2 | Put more annual shoppers through the direct web funnel with focused landing-page and funnel fixes, especially mobile | Over the last 7 days vs the same week last year, direct annual GP lost £10.6k mostly because fewer annual shoppers converted; this is missed future renewal income | ~£11k/week |
| 3 | Review partner cruise contact centre performance by scheme and booking source, then renegotiate any weak commission terms | Over the last 7 days vs the same week last year, partner referral GP was down about £11k combined across single and annual, with cruise-heavy assisted sales weakest | ~£11k/week |
| 4 | Push PPC and SEO pages that answer “cheap”, “deals”, “GHIC/EHIC” and cover-value questions, with Bronze/Silver pricing and trust messages tested separately | Over the last 7 days vs the same week last year, market search demand was up 57% to 74% YoY, but shoppers were more comparison-led and our cheaper tiers underperformed | ~£10k/week |
| 5 | Keep leaning into renewal journeys and auto-renew optimisation | Over the last 7 days vs the same week last year, renewals added about £8k and were the clearest offset to weaker new business | ~£8k/week |

---

---
*Generated 16:38 18 Mar 2026 | Tracks: 23 + Follow-ups: 31 | Model: gpt-5.4*
