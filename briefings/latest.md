---
# HX Trading Briefing — 17 Mar 2026

## Over the last 7 days vs the same period last year, GP fell £24k to £139k as direct single-trip and direct annual weakness outweighed stronger renewals.

---

## At a Glance

- 🔴 **Overall GP** — Over the last 7 days vs the same period last year, GP was £139k, down £24k or about 15%, with the biggest damage in direct single trip and direct annual.
- 🔴 **Direct single trip** — Over the last 7 days vs the same period last year, direct single-trip GP fell £12k, down 28%, as policies fell 8%, mobile session-to-search got worse, and GP per policy dropped 21%; this matters because single trip has no renewal payback.
- 🔴 **Direct annual** — Over the last 7 days vs the same period last year, direct annual GP fell £11k, down 22%, because annual booked sessions fell on both mobile and desktop and higher prices were more than wiped out by higher underwriter costs.
- 🔴 **Direct existing customers** — Over the last 7 days vs the same period last year, direct GP from existing customers fell £20k, down 28%, with sessions down 4% but search sessions down 22%, so the main leak is getting people through to price.
- 🟢 **Renewals** — Over the last 7 days vs the same period last year, renewal GP grew £8k, up 18%, because retention improved enough to beat a smaller expiry base.
- 🟡 **Partner referral** — Over the last 7 days vs the same period last year, partner referral GP fell about £11k across single and annual, mostly from weaker cruise-related volume and thinner margins.

---

## What's Driving This

### Direct Annual GP decline `RECURRING`

The data shows direct annual GP fell £11k over the last 7 days vs the same period last year, down 22%, and this has been negative on 8 of the last 10 days. Traffic was mixed rather than outright weak — mobile sessions were down 2% but desktop sessions were up 34% — so the real problem was fewer annual shoppers getting through and buying, with annual booked sessions down 16% on mobile and 20% on desktop.

Higher prices did not save it. Over the last 7 days vs the same period last year, average price rose 8% but GP per policy still fell 5% because underwriter cost share rose from 47% to 52% of gross.

```sql-dig
SELECT
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY 1;
```

### Direct Single Trip GP decline `RECURRING`

The data shows direct single-trip GP fell £12k over the last 7 days vs the same period last year, down 28%, and this has also been weak on 8 of the last 10 days. Traffic was mixed — mobile sessions were down 2% while desktop sessions were up 34% — but the bigger hit was conversion earlier in the funnel, with mobile session-to-search down 3.7 points and booked sessions down 9% on mobile and 14% on desktop.

We also made less on each sale. Over the last 7 days vs the same period last year, GP per policy fell from about £22 to £17, down 21%, as underwriter cost share rose from 46% to 52% of gross.

```sql-dig
SELECT
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1;
```

### Direct existing-customer GP decline `EMERGING`

Over the last 7 days vs the same period last year, direct GP from existing customers fell £20k, down 28%, and the main issue was not raw traffic. Sessions were only down 4%, but search sessions were down 22%, which says fewer people are getting through to a price once they land.

That points to an upper-funnel problem, especially for customers we should convert well. This looks tied to the same direct funnel softness showing up in annual and single trip rather than a demand shortage on its own.

```sql-dig
SELECT
  customer_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Direct'
  AND customer_type = 'Existing'
GROUP BY 1;
```

### Partner Referral Single Trip GP decline `EMERGING`

Over the last 7 days vs the same period last year, partner referral single-trip GP fell £6k, down 30%. We sold 27% fewer policies, and each one also made less once commission and underwriter costs took a bigger bite.

This looks more like softer partner demand than a pricing-only issue. Cruise market softness is the likely backdrop here, with partners still seeing weaker traffic and heavier promo pressure.

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
  AND policy_type = 'Single'
GROUP BY 1,2;
```

### Partner Referral Annual GP decline `NEW`

Over the last 7 days vs the same period last year, partner referral annual GP fell £5k, down 40%. Policies were down 19%, so we invested in fewer future renewals, and GP per policy fell from about £83 to £62 as commission rose.

This is small versus direct, but still worth acting on because the drop is sharp. The most likely cause is the same cruise-partner softness already showing up in referral single trip.

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
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

### Renewals Annual GP growth `EMERGING`

Over the last 7 days vs the same period last year, renewal GP grew £8k, up 18%, even though the expiry base was down 18%. That means retention improved enough to lift renewed volume and GP per policy.

This is clearly good news and one of the few areas offsetting the direct miss. It also matters because renewals are the payoff from our annual acquisition strategy.

```sql-dig
SELECT
  distribution_channel,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Renewals'
GROUP BY 1;
```

### Aggregator Annual volume decline reducing future renewal investment `NEW`

Over the last 7 days vs the same period last year, aggregator annual policies fell 16%, from 935 to 788. GP looked about £2k better because losses were smaller, but that is not the win here — we simply invested in fewer annual customers for future renewal income.

This may be market softness plus aggregator platform noise rather than a pricing issue. The important point is volume, not margin, because annual growth is how we build the renewal book.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Annual'
GROUP BY 1,2;
```

### Aggregator Single Trip GP decline `NEW`

Over the last 7 days vs the same period last year, aggregator single-trip GP fell by about £500 even though policies jumped 50%. We sold more, but made much less on each one, with average GP per policy roughly halving from about £3 to £2.

This is not the biggest £ issue yet, but it is poor-quality growth in a product with no renewal payback. Too early to call it structural, but it needs checking before volume scales further.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-10' AND '2026-03-17'
  AND distribution_channel = 'Aggregator'
  AND policy_type = 'Single'
GROUP BY 1,2;
```

---

## Customer Search Intent

According to Google Sheets data, travel insurance search intent is up about 74% over the last 7 days vs the same period last year, with the insurance index at 11.5 versus 6.6 last year, ahead of holiday searches at 8.5. According to AI Insights, price-led terms are rising fastest: “travel insurance deals” is up 986%, “cheapest” is up 141%, and comparison intent is up 400%, which says people are shopping harder rather than just travelling more. According to AI Insights, Spain, Greece and Italy are leading destination demand, while GHIC/EHIC and “do I need travel insurance” searches are also climbing, which points to customers checking rules and cover before buying. That fits this week: demand is there, but we are losing too many people before search and picking up too much lower-value single-trip demand. **Source:** Google Sheets — Insurance Intent tab; Google Sheets — Dashboard Metrics tab; AI Insights — trend, divergence, yoy, channels

---

## News & Market Context

According to AI Insights, British Airways is still not operating several Middle East routes and is offering flexible rebooking, which keeps disruption cover front of mind. According to [The Week](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war?utm_source=openai), standard travel insurance often excludes war-related losses, which can push customers to scrutinise wording and delay bigger annual commitments. According to [Saga](https://www.saga.co.uk/travel-insurance/middle-east-travel-disruption?utm_source=openai), insurers are actively publishing reassurance and disruption guidance, which raises the bar on customer messaging. Internal market context says Carnival is still running at about 80% of last year, while competitors are using heavy offers to stimulate demand, which helps explain weaker partner referral performance. According to AI Insights, competitors including Staysure and AllClear are seeing strong brand-search lifts, so this week looks more like an HX capture problem than a market demand problem. **Source:** AI Insights — news, deep_dive, what_matters; [Yahoo News — BA flights update](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai); [The Week — war disruption cover](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war?utm_source=openai); [Saga — Middle East travel disruption](https://www.saga.co.uk/travel-insurance/middle-east-travel-disruption?utm_source=openai); Internal — Current Market Events

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Fix direct mobile session-to-search in the upper funnel for existing customers, starting with the gatekeeper and search handoff | Direct existing GP is down £20k over the last 7 days vs the same period last year, while sessions are only down 4% and search sessions are down 22% | ~£20k/week |
| 2 | Review direct single-trip Bronze and Silver medical journeys, pricing and underwriter-cost changes | Direct single-trip GP is down £12k over the last 7 days vs the same period last year, with the biggest losses in Bronze and Silver and GP per policy down 21% | ~£12k/week |
| 3 | Rebuild annual acquisition through direct and aggregator campaigns, especially where annual intent has weakened | Direct annual GP is down £11k over the last 7 days vs the same period last year, and aggregator annual volumes are down 16%; we need to keep investing in future renewal income | ~£12k/week |
| 4 | Get with cruise partners now on referral traffic and commission pressure | Partner referral single and annual GP are down about £11k combined over the last 7 days vs the same period last year | ~£11k/week |
| 5 | Protect renewal conversion with auto-renew and retention comms while the rate is beating last year | Renewals are up £8k over the last 7 days vs the same period last year despite a smaller expiry base | ~£8k/week |

---

---
*Generated 20:21 18 Mar 2026 | Tracks: 23 + Follow-ups: 37 | Model: gpt-5.4*
