---
# HX Trading Briefing — 17 Mar 2026

## Over the last 7 days vs the same week last year, GP was down mainly because Europe-heavy direct single-trip sales made less money per policy, while renewals softened the blow.

---

## At a Glance

- 🔴 **Europe GP** — Over the last 7 days GP from Europe sales was about £89k, down about £20k vs the same week last year, roughly 19% worse, with policy volume only down 2% so the problem was weaker value per sale, not demand collapsing.
- 🔴 **Direct single-trip** — Over the last 7 days direct single-trip GP was about £30k, down about £12k vs the same week last year, roughly 28% worse, because desktop traffic rose but fewer visitors got to a quote and average GP per policy fell by about £5.
- 🔴 **Direct annual volume** — Over the last 7 days direct annual GP was down about £11k vs the same week last year, mainly because we sold about 18% fewer policies, which means we are investing less into future renewal income.
- 🟢 **Renewals** — Over the last 7 days renewal GP was up about £8k vs the same week last year, roughly 18% better, because retention improved even though fewer policies were up for renewal.
- 🔴 **Partner referral** — Over the last 7 days partner referral single and annual GP were down about £11k combined vs the same week last year, with cruise-heavy traffic weaker and partner economics less favourable.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct single-trip GP fell by about £12k to about £30k. Desktop sessions grew strongly, up about 34%, and mobile was slightly down, down about 2%, but fewer visitors got to quote on both devices and average GP per policy fell from about £22 to £17, so this was a conversion-and-margin problem more than a traffic problem.  

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Europe destination GP decline `RECURRING`

Over the last 7 days vs the same week last year, Europe GP fell by about £20k to about £89k while policy volume was only down about 2%. That tells us traffic held up reasonably well, but the Europe mix skewed toward lower-value single-trip sales and average GP per policy dropped from about £24 to £20.  

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND destination_group = 'Europe'
GROUP BY 1;
```

### Direct Annual volume-led decline `RECURRING`

Over the last 7 days vs the same week last year, direct annual GP was down about £11k mainly because volume fell by about 18%. This is not an annual margin problem to fix on price — it means traffic into annual quotes was softer, so we are investing less into future renewal income.  

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

### Bronze cover level GP decline `RECURRING`

Over the last 7 days vs the same week last year, Bronze GP was down about £9k, with volume down about 6% and average GP per policy down about 19%. The biggest drag sat in direct single-trip Bronze, where we kept winning lower-priced demand but made less on each sale.  

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND cover_level_name = 'Bronze'
GROUP BY 1;
```

### Partner Referral Single GP decline `EMERGING`

Over the last 7 days vs the same week last year, partner referral single-trip GP fell by about £6k, mostly because volume was down about 27%. This looks traffic-led first, especially in cruise-heavy partner journeys, with commission and underwriter cost then taking a bigger bite out of what we keep.  

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1,2,3;
```

### Silver cover level GP decline `EMERGING`

Over the last 7 days vs the same week last year, Silver GP was down about £9k. This lines up with the same direct single-trip and Europe weakness as Bronze, so the data points to a broader quality problem in lower-tier cover rather than one isolated product issue.  

```sql-dig
SELECT
  cover_level_name,
  policy_type,
  distribution_channel,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND cover_level_name = 'Silver'
GROUP BY 1,2,3;
```

### Partner Referral Annual GP decline `NEW`

Over the last 7 days vs the same week last year, partner annual GP was down about £5k on about 19% lower volume. Annual volume matters because it feeds future renewals, so the issue here is weaker acquisition through partners, not that annual margins are negative.  

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_commission
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

### Renewals GP growth `NEW`

Over the last 7 days vs the same week last year, renewals added about £8k of GP even though the number of policies up for renewal was lower. That means retention improved and the renewal book is doing its job by paying back earlier annual acquisition.  

```sql-dig
SELECT
  distribution_channel,
  booking_source,
  SUM(policy_count) AS renewed_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS renewed_gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_renewed_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Renewals'
GROUP BY 1,2;
```

---

## Customer Search Intent

According to Google Sheets dashboard data, over the last 7 days vs the same week last year, insurance search demand was up 74% while holiday demand was up 51%, so the market is bigger and insurance is growing faster. According to the Insurance Intent and AI Insights tabs, price-led searches are doing most of the lifting: “travel insurance deals” was up 986%, “cheapest” was up 141%, and comparison intent was up 400% YoY. That fits what we are seeing in trading: more people are shopping, but more of them are bargain-hunting in lower-value Europe single-trip journeys. According to AI Insights, trust-heavy terms are also rising among older and medical shoppers, including reviews and Defaqto, while brand interest for Staysure and AllClear is growing faster than HX.  
**Source:** Google Sheets — Dashboard Metrics tab  
**Source:** Google Sheets — Insurance Intent tab  
**Source:** AI Insights — what_matters, deep_dive, trend, channels

---

## News & Market Context

According to AI Insights, this is a strong-demand but price-sensitive market, with customers booking holidays and then shopping hard on insurance price and trust. According to current internal market context, the Iran conflict is still pushing demand away from Worldwide and toward Europe, which helps volume but can dilute GP if the mix shifts into cheaper single-trip cover. British Airways said it still could not operate some Middle East routes including Abu Dhabi, Doha, Dubai, Amman, Bahrain and Tel Aviv, which keeps disruption and cover questions high for travellers. Consumer articles on war-risk exclusions are also keeping attention on what policies do and do not cover, which can slow purchase and make trust messaging more important. Internal context also shows Carnival traffic down about 20%, which matches the weakness in cruise-heavy partner referral sales.  
**Source:** AI Insights — news, trend, yoy  
**Source:** Internal — Current Market Events context  
**Source:** [British Airways issues update today on flights resuming from the Middle East](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai)  
**Source:** [How travel insurance works if your holiday is disrupted by war](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war?utm_source=openai)

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Check the direct web funnel for single-trip mobile and desktop from landing to quote, then fix the top-of-funnel drop on session-to-search for Bronze and Silver Europe journeys. | Over the last 7 days direct single-trip GP was down about £12k, with session-to-search weaker on both devices and average GP per policy down about 21%. | ~£12k/week |
| 2 | Review Bronze and Silver Europe single-trip pricing, cover display and upsell mix on direct web. | Over the last 7 days Europe GP was down about £20k and Bronze and Silver together were down about £18k, with the squeeze coming from lower GP per policy rather than a big traffic loss. | ~£18k/week |
| 3 | Increase direct annual quote traffic through paid and owned channels aimed at annual shoppers. | Over the last 7 days direct annual GP was down about £11k because volume was down about 18%, which means less future renewal income. | ~£11k/week |
| 4 | Review cruise partner CTA performance and partner economics for P&O-led referral traffic. | Over the last 7 days partner referral single and annual GP were down about £11k combined, with weaker cruise-heavy traffic and less favourable economics. | ~£11k/week |
| 5 | Protect renewal conversion with contact-centre save activity and renewal journey checks. | Over the last 7 days renewals were up about £8k and are the clearest offset to weaker new-business quality. | ~£8k/week |

---
*Generated 13:53 18 Mar 2026 | Tracks: 23 + Follow-ups: 32 | Model: gpt-5.4*
