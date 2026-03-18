---
# HX Trading Briefing — 17 Mar 2026

## Over the last 7 days vs the same week last year, GP is down £24k because direct single-trip and Europe are losing far more value per sale, even with solid traffic.

---

## At a Glance

- 🔴 **Europe drag** — Over the last 7 days vs the same week last year, Europe GP was £89k, down £20k, while policies were only 2% lower, so most of the damage is weaker GP per sale.
- 🔴 **Direct single** — Over the last 7 days vs the same week last year, direct single-trip GP was £30k, down £12k, as desktop traffic rose 34% but fewer visitors got through to price and average GP per policy fell 21%.
- 🔴 **Direct annual acquisition** — Over the last 7 days vs the same week last year, direct annual GP was £37k, down £11k, because we sold 18% fewer annuals; that is weaker acquisition into future renewal income.
- 🔴 **Partner weakness** — Over the last 7 days vs the same week last year, partner referral GP was down about £11k across single and annual, with fewer partner sales and lower value per sale.
- 🟢 **Renewals offset** — Over the last 7 days vs the same week last year, renewal GP was £53k, up £8k, which partly offsets weaker new business.

---

## What's Driving This

### Direct Single GP deterioration `RECURRING`

Over the last 7 days vs the same week last year, direct single-trip GP fell £12k to £30k. Desktop sessions were up 34% YoY and mobile sessions were broadly flat, so traffic was not the main problem; fewer visitors reached price, desktop quote-to-book got worse, and average GP per policy fell 21% to about £17.  
This is clearly the biggest controllable issue. It has been negative on 8 of the last 10 trading days, with most of the damage in Bronze and Silver single-trip journeys.

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

### Europe destination mix weakening `RECURRING`

Over the last 7 days vs the same week last year, Europe GP fell £20k to £89k while policies were only down 2%. That tells us traffic and volume held up reasonably well, but the mix got cheaper and average GP per Europe policy dropped 17% to about £20.  
This is a recurring issue because Europe is where most of the single-trip weakness is landing. We are getting the demand, but more of it is lower-yield Europe business.

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

### Direct Annual volume decline `EMERGING`

Over the last 7 days vs the same week last year, direct annual GP was £37k, down £11k, because policies fell 18% to 729. Traffic with annual intent was softer and fewer visitors got through to price, so this is mainly weaker acquisition rather than a pricing problem.  
This matters because annual sales are future renewals. We are still investing in future renewal income, but the current market is pushing more people toward single trip instead of committing to annual cover.

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
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

### Partner Referral Single decline `EMERGING`

Over the last 7 days vs the same week last year, partner single GP was £13k, down £6k, with policies down 27%. For partners we cannot see web sessions in the same way as direct, but the size of the policy drop says traffic from partners is the main issue, with a small extra hit from lower GP per sale.  
This is building rather than one-day noise. Cruise partner softness looks part of it.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Partner Referral Annual decline `EMERGING`

Over the last 7 days vs the same week last year, partner annual GP was £8k, down £5k, with policies down 19% and average GP per policy also lower. Annual volume is still worth having because it feeds future renewals, but this partner stream is bringing in less volume and less value.  
This may be part traffic and part economics. Check partner commission and underwriter cost changes before assuming demand is the whole story.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(CAST(total_gross_inc_ipt AS FLOAT64)), 0) AS commission_rate
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

### Renewals growth from better renewal mechanics `EMERGING`

Over the last 7 days vs the same week last year, renewal GP was £53k, up £8k. We had fewer policies coming up for renewal, so the gain appears to be coming from better renewal take-up rather than a bigger eligible base.  
This is good news and one of the few clean offsets in the week. Treat it as encouraging, but prove it with a proper renewal-rate check using expiry dates.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS renewed_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS renewed_gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_renewed_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

### Worldwide destination decline `NEW`

Over the last 7 days vs the same week last year, Worldwide GP was £50k, down £4k, mostly because policies were down 7% while GP per sale held roughly flat at about £27. That points to less traffic or fewer bookings into Worldwide rather than weaker pricing.  
This may be customers switching destination plans from Worldwide into Europe rather than a deeper pricing issue.

```sql-dig
SELECT
  destination_group,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND destination_group = 'Worldwide'
GROUP BY 1;
```

### Aggregator Single deterioration `NEW`

Over the last 7 days vs the same week last year, aggregator single GP was about £2k, down about £500, even though policies were up about 50%. We are clearly getting more comparison-site volume, but average GP per sale roughly halved, so we are buying that volume too cheaply.  
That is worth watching because single trip has no renewal payback. The growth is real, but the quality is poor.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

---

## Customer Search Intent

According to Google Sheets Dashboard Metrics, travel insurance search demand is up 74% YoY, ahead of holiday searches at 51% YoY, so demand is there. According to AI Insights and the Insurance Intent tab, broader insurance search demand is up roughly 57% to 63% YoY, with 4-week momentum up about 40% YoY. According to the Insurance Intent data, price-led searches are surging: “travel insurance deals” is up 986% YoY, “cheapest” is up 141% YoY, “travel insurance price” is up 321% YoY, and comparison intent is up 400% YoY over the latest tracked period vs last year. According to AI Insights, destination interest is tilting toward Spain, Greece and Italy, while ski holiday intent is up 188% YoY, which fits stronger Europe demand and more late-booking single-trip behaviour. According to AI Insights, competitor brand searches are also rising, with Staysure up 52% YoY and AllClear up 33% YoY, especially among older and medical customers.  
**Source:** Google Sheets — Insurance Intent tab  
**Source:** Google Sheets — Dashboard Metrics tab  
**Source:** AI Insights — what_matters, deep_dive, trend, channels

---

## News & Market Context

According to AI Insights, airlines are pushing cheap flights and holiday deals, which is bringing more insurance shoppers into market but making them more price-sensitive. According to AI Insights, Jet2, easyJet, Ryanair and TUI are adding capacity into Spain, Greece and Italy, which supports stronger Europe demand but also a cheaper mix. British Airways said it still cannot operate to some Middle East destinations and is offering flexible changes, which helps explain weaker Worldwide demand and switching into Europe. According to The Week, citing ABI guidance, standard travel insurance usually excludes war-related losses, so customers are likely shopping more carefully and asking more questions before they buy. Internal market context says Carnival traffic is down about 20%, which fits weaker partner referral volumes, especially in cruise-linked traffic. AI Insights also says Compare the Market search interest is up 16% YoY, which fits the rise in low-value aggregator single volume.  
**Source:** AI Insights — trend, deep_dive, news, channels  
**Source:** [British Airways issues update today on flights resuming from the Middle East](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai)  
**Source:** [How travel insurance works if your holiday is disrupted by war](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war?utm_source=openai)  
**Source:** Current Market Events — Iran Conflict, Cruise Partner Dynamics

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Fix direct single search reach first in Bronze and Silver on mobile and desktop, starting with the search gate and desktop quote-to-book journey | Over the last 7 days vs last year, direct single lost £12k, with weaker session-to-search and a sharp desktop quote-to-book drop | ~£12k/week |
| 2 | Protect Europe value by tightening product mix and pushing upgrades and extras on Europe single-trip sales, not by chasing more cheap volume | Over the last 7 days vs last year, Europe lost £20k mostly because average GP per policy fell 17% while volume was almost flat | ~£20k/week |
| 3 | Review partner referral economics and traffic source quality, starting with cruise-linked partners and annual deals | Over the last 7 days vs last year, partner single and annual were down about £11k combined from lower volume and weaker value per sale | ~£11k/week |
| 4 | Keep backing annual acquisition in direct, but shift marketing toward annual-intent demand pockets where customers still reach price | Over the last 7 days vs last year, direct annual volume was down 18%, which means weaker investment into future renewal income | ~£11k/week |
| 5 | Validate and then scale the renewal journeys that improved take-up, especially auto-renew prompts and renewal contact timing | Over the last 7 days vs last year, renewals added £8k and were the clearest offset to weaker new business | ~£8k/week |

---
*Generated 14:19 18 Mar 2026 | Tracks: 23 + Follow-ups: 34 | Model: gpt-5.4*
