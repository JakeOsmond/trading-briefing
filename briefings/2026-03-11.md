---
# HX Trading Briefing — 10 Mar 2026

## Single Trip Margin Squeeze Deepens Even as Search Demand Hits Records (Trailing 7d vs LY)

GP over the last week came in at £161k — down £13k on last year (about 8% worse), as higher web traffic failed to convert into profitable sales and single trip margins dropped sharply again.

---

## At a Glance

- 🔴 **Partner Referral Single Trip GP** — GP down £6.1k YoY (down 27%) as we lost nearly a third of single trip policies in partner channels.
- 🔴 **Direct Annual GP** — Down £6.2k YoY (down 12%); volumes flat, but margin per policy dropped, driven by higher costs and heavier discounting.
- 🔴 **Bronze Cover Level GP** — Down £5.6k YoY (down 16%), as more sales shifted to Bronze and GP per policy fell back hard.
- 🔴 **Direct Single Trip GP** — GP slid £3.8k YoY (down 9%): traffic was up, but conversion and margin both fell sharply.
- 🟢 **Renewals Annual GP** — GP up £1.5k YoY (+3%), with renewal policy count up 12% and the book compounding.

---

## What's Driving This

### Partner Referral Single Trip GP `RECURRING`

GP for Partner channel single trips fell £6.1k over the last 7 days vs last year (down 27%), driven by a 27% collapse in policy volume (906 → 666); margin per policy didn't budge, so it's all volume. This has been negative for 10 out of the last 10 days, a structural partner volume issue.
```sql-dig
SELECT SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp, SUM(policy_count) AS policies FROM hx-data-production.commercial_finance.insurance_policies_new WHERE distribution_channel='Partner Referral' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

### Direct Annual GP `RECURRING`

Direct annual GP dropped £6.2k over the last 7 days vs last year (down 12%). Policy volumes held dead flat (964 vs 964), but GP per policy tumbled 12% as higher underwriter costs and heavier discounting squeezed margin despite steady sales. This is the 8th time in 10 days we’ve seen this—normal for new business, but keep focusing on our renewal growth strategy.
```sql-dig
SELECT SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp, SUM(policy_count) AS policies FROM hx-data-production.commercial_finance.insurance_policies_new WHERE distribution_channel='Direct' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

### Bronze Cover Level GP `RECURRING`

Bronze GP is down £5.6k vs last year (down 16%). There's been a marked swing in sales to Bronze (volume up, but average GP per policy down 19% to £16), and fewer people are buying extras like gadget cover or upgrades. Negative for 10 days straight; a persistent drop in the value of cheaper sales.
```sql-dig
SELECT SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp, SUM(policy_count) AS policies FROM hx-data-production.commercial_finance.insurance_policies_new WHERE cover_level_name='Bronze' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

### Direct Single Trip GP `RECURRING`

Direct Single Trip GP down £3.8k over the last 7 days vs last year (down 9%). Web traffic on desktop shot up 36% YoY, mobile flat, but session-to-search conversion slid badly (desktop: 0.15 → 0.13, mobile: 0.20 → 0.15), and average GP per policy fell from £22 to £18. This is pain for the 9th time in 10 days—mainly a conversion drop plus more low-value customers.
```sql-dig
SELECT SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp, SUM(policy_count) AS policies FROM hx-data-production.commercial_finance.insurance_policies_new WHERE distribution_channel='Direct' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

### Aggregator Single Trip Volume `RECURRING`

Aggregator Single Trip GP fell £0.6k over the last 7 days vs last year (down 25%). Policies sold were up 44% YoY, but new aggregator sales make just £1.70 GP each—down nearly half from last year—due to steeper commissions and more business at lower price points. This negative trend has held for 8 of the last 10 days.
```sql-dig
SELECT SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp, SUM(policy_count) AS policies FROM hx-data-production.commercial_finance.insurance_policies_new WHERE distribution_channel='Aggregator' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

### Renewals Annual GP `RECURRING`

Renewals GP is up £1.5k vs last year (up 3%)—policy count rose 12% (boosting future value), although average GP per policy is down. This growth has been positive for 9 out of 10 days: our renewal franchise is compounding.
```sql-dig
SELECT SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp, SUM(policy_count) AS policies FROM hx-data-production.commercial_finance.insurance_policies_new WHERE distribution_channel='Renewals' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

### Aggregator Annual GP `RECURRING`

Aggregator Annual GP improved by £1.1k over the last 7 days vs last year (from -£7.4k to -£6.2k); still loss-making as planned, but each unit is less negative due to stronger average pricing. This trend held 7 out of 10 days.
```sql-dig
SELECT SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp, SUM(policy_count) AS policies FROM hx-data-production.commercial_finance.insurance_policies_new WHERE distribution_channel='Aggregator' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

### Partner Referral Annual GP `EMERGING`

Annual GP for Partner channels up £1.1k (up 12%) on the week, with 10% more policies sold—most of the partner book's decline is isolated to single trip. This has been positive 6 out of the last 10 days.
```sql-dig
SELECT SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp, SUM(policy_count) AS policies FROM hx-data-production.commercial_finance.insurance_policies_new WHERE distribution_channel='Partner Referral' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

---

## Customer Search Intent

Insurance searches are up 74% YoY—now outpacing holiday demand (up 50% YoY), with insurance intent scoring 3 points above holiday intent versus just 1 point last year. The spike is clear in Google Trends, especially for “travel insurance Spain”, “do I need insurance?”, and “annual multi-trip”. Medical cover and cancellation protection queries are up, thanks to new EU travel rules and recent flight disruptions. Spain, Greece, and Italy are trending top for insurance searches. However, extra window-shopping is not all converting—sales aren’t keeping pace with search intent gains.  
**Source:** [Insurance Intent tab, Google Trends](https://trends.google.com/), Google Sheets — Dashboard Metrics.

---

## News & Market Context

Airlines (easyJet, Ryanair, Jet2) have turbocharged flight capacity to Spain, Greece and Italy for summer, stoking early insurance demand. Recent winter storms and the Dubai airspace closure disrupted travel, lifting demand for medical and cancellation cover. New EU biometric border checks and FCDO travel advisories are causing customers to research insurance more before booking, especially for Spain and the Middle East. Competitors (Saga, ABI) are aggressively marketing war/cancellation extensions and automatic policy upgrades for disruption. Aggregators are driving volume by prioritising cheapest price, and commission rates are rising. Overall, travel and insurance demand are both up, but margin per sale is being squeezed as the market turns more promotional and acquisition costs bite.  
**Sources:** [uk.finance.yahoo.com](https://uk.finance.yahoo.com/news/easyjet-releases-25-million-budget-162457150.html?utm_source=openai), [theweek.com](https://theweek.com/personal-finance/how-travel-insurance-works-if-your-holiday-is-disrupted-by-war?utm_source=openai), [Saga Insurance](https://www.saga.co.uk/travel-insurance/middle-east-travel-disruption?utm_source=openai), AI Insights — “what_matters”, “channels”, “trend”.

---

## Actions

| Priority | What to do                                                         | Why (from the data)                                         | Worth      |
|----------|---------------------------------------------------------------------|-------------------------------------------------------------|------------|
| 1        | Rebuild Partner Referral Single Trip volume                         | Policies down 27%, GP down £6.1k/wk                         | ~£6k/week  |
| 2        | Fix desktop and mobile session-to-search drop on Direct Single Trip | Conversion bottleneck: traffic up, GP down £3.8k/wk         | ~£4k/week  |
| 3        | Sharpen upsell/cross-sell on Bronze cover                          | GP per sale down £5.6k/wk with attach rates falling         | ~£5.6k/wk  |
| 4        | Stay focused on annual renewal/partner push                        | Renewals and Partner Annual GP both up YoY, compounding     | ~£2.5k/wk  |
| 5        | Hold direct price discipline to avoid further single trip margin erosion | Direct and Aggregator Single margin both under pressure | ~£4k/wk    |

---

_Generated 09:04 11 Mar 2026 | 22 investigation tracks | GPT-4_


---
*Generated 19:42 11 Mar 2026 | Tracks: 22 + Follow-ups: 29 | Model: gpt-4.1*
