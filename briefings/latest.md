---
# HX Trading Briefing — 17 Mar 2026

## Over the last 7 days vs the same week last year, GP was weak and the biggest damage came from direct single-trip and direct annual, where fewer people got through to price and we made less on each sale.

---

## At a Glance

- 🔴 **Weekly GP down** — Over the last 7 days vs the same week last year, GP was £139k, down £24k or 15%, with most of the hit coming from weaker direct single-trip and direct annual performance.
- 🔴 **Direct single hurt most** — Over the last 7 days vs the same week last year, direct single GP fell £11.7k to £30.3k, mainly because fewer people reached price and average GP per policy dropped 21% to about £17 from £22.
- 🔴 **Direct annual also slipped** — Over the last 7 days vs the same week last year, direct annual GP fell £10.6k to £37.3k, with policies down 18%; this is softer acquisition into future renewals, not an annual pricing problem.
- 🔴 **Europe got less valuable** — Over the last 7 days vs the same week last year, Europe GP fell about £20k on almost flat volume, so demand broadly held up but the mix came through in cheaper shapes.
- 🟢 **Renewals helped** — Over the last 7 days vs the same week last year, renewal GP was up about £8k as renewal rate improved to 44% from 32%, offsetting some of the weakness elsewhere.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct single GP fell £11.7k to £30.3k. Traffic was mixed rather than collapsing — mobile sessions were down 2% but desktop was up 34% — and the real damage came from conversion and value, with session-to-search down 4pp on mobile and 3pp on desktop and average GP per policy down 21%; this has been negative on 8 of the last 10 trading days.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Direct'
  AND policy_type = 'Single'
  AND transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
GROUP BY 1;
```

### Direct Annual GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct annual GP fell £10.6k to £37.3k, with policies down 18% to 729 from 888. Traffic was again mixed with desktop up, but fewer annual shoppers got through to price and completed, and average GP per policy slipped 5%; this has been weak on 7 of the last 10 trading days, and the right read is softer acquisition into future renewal income, not a pricing issue on annuals.

```sql-dig
SELECT
  cover_level_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Direct'
  AND policy_type = 'Annual'
  AND transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
GROUP BY 1;
```

### Europe destination GP decline `EMERGING`

Over the last 7 days vs the same week last year, Europe GP fell about £20k while policy volume was almost flat, down about 2%. That points away from a demand collapse and towards cheaper mix, especially in single-trip sales, where customers are still buying Europe cover but landing in lower-value products.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE destination_group = 'Europe'
  AND transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
GROUP BY 1,2;
```

### Direct existing-customer GP decline `EMERGING`

Over the last 7 days vs the same week last year, direct GP from existing customers fell about £20k to £51k. Sessions were down 4%, but conversion did more of the damage, with session-to-search down to 19% from 23%, so fewer known customers even got through to seeing a price.

```sql-dig
SELECT
  customer_type,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Direct'
  AND customer_type = 'Existing'
  AND transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
GROUP BY 1,2;
```

### Partner Referral new-customer GP decline `NEW`

Over the last 7 days vs the same week last year, partner referral GP from new customers fell about £7k to £9k. This looks mainly like less traffic and fewer sales, down 32%, and it appears to be concentrated in cruise-led and phone-led business.

```sql-dig
SELECT
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Partner Referral'
  AND customer_type = 'New'
  AND transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
GROUP BY 1;
```

### Partner Referral Single GP decline `NEW`

Over the last 7 days vs the same week last year, partner referral single GP fell about £6k to £13k. This looks mostly traffic-led, with policies down 27%, while average GP only moved a little, so the main issue is fewer referral sales coming through.

```sql-dig
SELECT
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
  AND transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
GROUP BY 1;
```

### Renewals GP increase `NEW`

Over the last 7 days vs the same week last year, renewals GP rose about £8k to £53k. That looks like a real positive, with renewal rate up to 44% from 32%, even though fewer policies were up for renewal.

```sql-dig
SELECT
  booking_source,
  SUM(policy_count) AS renewed_policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Renewals'
  AND policy_type = 'Annual'
  AND transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
GROUP BY 1;
```

### Aggregator Single GP decline `NEW`

Over the last 7 days vs the same week last year, aggregator single GP fell about £500 to £2k. The £ impact is small, but the shape is worth watching because volume was up 50% while average GP per policy fell to about £2 from £3, and single-trip losses do matter because there is no renewal payback.

```sql-dig
SELECT
  scheme_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
  AND transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
GROUP BY 1;
```

### Medical single-tier squeeze in Bronze and Silver `RECURRING`

Over the last 7 days vs the same week last year, the biggest direct single losses sat in Bronze Main Single Med and Silver Main Single Med, down about £5k and £6k respectively. The data shows the pressure is concentrated in lower and mid-tier medical single-trip products, where fewer people are reaching price and the value per sale has dropped sharply.

```sql-dig
SELECT
  scheme_name,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel = 'Direct'
  AND policy_type = 'Single'
  AND medical_split = 'Medical'
  AND transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
GROUP BY 1;
```

---

## Customer Search Intent

According to Google Sheets dashboard data, travel insurance search intent is up 74% vs last year, ahead of holiday search growth at 51%, so demand is there. According to the Insurance Intent tab, price-led searches are driving that growth: “travel insurance deals” is up 986%, “cheapest” is up 141%, and comparison-style searches are up 400% YoY. According to AI Insights, broader insurance searches are running about 57% to 63% above last year, with 4-week momentum up about 40%, while Spain, Greece and Italy are the strongest destination themes. According to AI Insights, GHIC/EHIC, Defaqto and review searches are also rising, which suggests customers want cheap cover but still need trust and reassurance before they buy. **Source:** Google Sheets — Dashboard Metrics tab. **Source:** Google Sheets — Insurance Intent tab. **Source:** AI Insights — what_matters, deep_dive, trend, divergence.

---

## News & Market Context

According to AI Insights, competition looks sharper in exactly the areas where we are weak: Staysure brand interest is up 52% and AllClear is up 33%, especially among older and medical shoppers. According to AI Insights, cheap flights are up 39% and holiday deals are up 23%, which helps explain why Europe demand is still there but coming through in lower-yield shapes. The active Iran conflict is still affecting travel behaviour, and British Airways continues to restrict some Middle East flying and offer flexible changes, which supports single-trip flexibility over committing to annual cover. According to coverage on war disruption and travel insurance, customers remain alert to what is and is not covered, so clearer messaging may help conversion where trust is wavering. Internally, pricing updates and underwriting-rule testing over the last 3 weeks may also have added pressure to direct single performance. **Source:** AI Insights — what_matters, deep_dive, news. **Source:** [British Airways issues update today on flights resuming from the Middle East](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai). **Source:** [How travel insurance works if your holiday is disrupted by war](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war?utm_source=openai). **Source:** Internal — Weekly Pricing Updates; Insurance UW Rules for testing.

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Check direct single Bronze and Silver medical pricing, underwriter loads and search-page drop-offs introduced in the last 3 weeks | Over the last 7 days vs the same week last year, direct single GP lost £11.7k, with the biggest scheme hits in Bronze Main Single Med and Silver Main Single Med | ~£12k/week |
| 2 | Fix direct quote entry for existing customers on mobile and desktop, starting with the session-to-search drop | Over the last 7 days vs the same week last year, direct existing-customer GP was down about £20k and session-to-search fell to 19% from 23% | ~£20k/week |
| 3 | Push harder on renewal auto-renew take-up and renewal web completion | Over the last 7 days vs the same week last year, renewals added about £8k of high-quality GP and renewal rate improved to 44% from 32% | ~£8k/week |
| 4 | Work with cruise referral partners to recover phone-led single-trip volume | Over the last 7 days vs the same week last year, partner referral single GP lost about £6k and the weakness looks concentrated in cruise and phone-assisted sales | ~£6k/week |
| 5 | Review aggregator single-trip participation on the lowest-value compare products | Over the last 7 days vs the same week last year, aggregator single volume grew but average GP fell to about £2 from £3, with no renewal upside | ~£1k/week |

---
*Generated 13:09 18 Mar 2026 | Tracks: 23 + Follow-ups: 33 | Model: gpt-5.4*
