---
# HX Trading Briefing — 09 Mar 2026

## Margin squeeze deepens on single trip policies, annual growth funds future renewal gains

---

## At a Glance

- 🔴 **Direct Single Trip Margin** — Profit per policy fell to £19 from £22 YoY, costing us about £7k a week, even as volumes rose.
- 🔴 **Partner Referral Single Margin** — Volume fell from 900+ to 700/week, dropping GP by £2.3k weekly.
- 🔴 **Direct Annual Margin** — GP per direct annual policy dropped to £49 from £56 YoY, costing £1.6k a week—volumes up, so we’re investing for future renewals.
- 🔴 **Aggregator Single Margin** — Profit nearly halved (£3.35 down to £1.78), erasing most margin—about £900 hit per week.
- 🔴 **Aggregator Annual Negative Margin** — Margin stuck at -£6.40 per policy as volume keeps rising; short-term pain, but it grows our renewal pot.

---

## What's Driving This

### Direct Single Trip Margin Decline `RECURRING`
We’re making about £7k less GP per week as direct single margins dropped from £22 to £19 YoY. The hit comes from higher UW cost, heavier discounting and commission; volumes are growing, but every policy is less profitable—third week running.

```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel = 'Direct' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

### Partner Referral Single Margin Drop `RECURRING`
GP crashed £2.3k/week as policies tumbled (900+ to 700), with steady per-policy profit but far fewer sales. Higher average price and commission rate, but most damage is just fewer customers.

```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Partner Referral' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

### Direct Annual Margin Drop `RECURRING`
Margin per policy dropped £7 (now £49), taking £1.6k off the weekly GP. Volumes are up—so we’re still investing for future renewals—but higher UW costs and more aggressive discounting squeezed this week's bottom line.

```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Direct' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

### Aggregator Single Margin and Mix Erosion `RECURRING`
Profit per aggregator single fell from £3.35 to £1.78; volume soared (770 to 1,160), but almost all margin was wiped out—£900 lost per week. Lower prices, higher commission and weaker medical risk mix are to blame.

```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Aggregator' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

### Aggregator Annual Margin Slight Worsening `RECURRING`
Annual aggregator margin stayed deeply negative at -£6.40 (worse than last year), costing another £500 this week, as policy numbers grew by about 10%. This is by design to drive future retention, even if it stings for now.

```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Aggregator' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

### Discount Campaign Dilution `RECURRING`
Discounted sales made up a bigger share, but average discount shrank slightly—a squeeze that cost £700 a week. The heaviest impact was on margin in direct sales.

```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)), SUM(CAST(total_discount_value AS FLOAT64)) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE total_discount_value>0 AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

---

## Customer Search Intent

Travel insurance search demand is red-hot: Google Trends shows insurance queries up 74% YoY (11.5 vs 6.6 last year), overtaking holidays at +56%. Family ski, Easter and summer travel searches spiked in Feb, especially for Spain, Turkey, and the Canaries. "Cheap flights" traffic doubled, and “holiday deals” are up 33%. Passport renewal queries have jumped 25%, and insurance intent now leads holiday search by a record 2.7 points (+1 last year).  
**Source:** [Google Trends](https://trends.google.com), Dashboard Metrics — Insurance Intent tab

---

## News & Market Context

UK airlines are fuelling demand: easyJet has released 25 million winter seats with steep fare sales ([easyJet](https://www.easyjet.com/en/news/story/easyjet-puts-spring-2026-flights-on-sale?utm_source=openai)), and Jet2 is adding flights to Spain. Ryanair's regional Spain cuts mean more demand is shifting to larger, cheaper hubs. No strikes or severe disruptions this week ([The Independent](https://www.independent.co.uk/travel/news-and-advice/storm-goretti-travel-rail-road-air-ferry-b2896612.html?utm_source=openai)). British Airways is still not flying Middle East routes because of the ongoing conflict ([Yahoo News](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai)), nudging up interest in war/cancellation cover. Saga Insurance now auto-extends cover for customers stuck abroad—raising the bar for customer expectations ([Saga](https://www.saga.co.uk/travel-insurance/middle-east-travel-disruption?utm_source=openai)).  
**Sources:** AI Insights, [easyJet](https://www.easyjet.com/en/news/story/easyjet-puts-spring-2026-flights-on-sale?utm_source=openai), [Saga](https://www.saga.co.uk/travel-insurance/middle-east-travel-disruption?utm_source=openai), [Yahoo News](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai), Dashboard Metrics

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|------------|---------------------|-------|
| 1 | Cut discounting on direct single trips (run A/B to remove extra coupons) | Per-policy profit is falling fast, costing £7k/week | ~£7k/wk |
| 2 | Re-engage lapsed partner referral partners or launch new partnerships | Partner referral single sales drop is costing £2.3k/week | ~£2.3k/wk |
| 3 | Test upsell of medical upgrades and higher cover plans, especially for singles | Mix shift to lower-GP, high-risk aggregators/WW is hurting margin | ~£900/wk |
| 4 | Keep pushing annual policy growth—margin loss funds future renewals | Annual volume up, negative margin is strategic | LTV |
| 5 | Add clear messaging/auto-extensions for stranded customers (Middle East) | Direct Saga move—sets new customer expectation on flexibility | Retention |

---

_Generated 07:22 10 Mar 2026 | 22 investigation tracks | GPT-4_

---

### Review Notes
- **All material movers** from the investigation are included and sized; none omitted. 
- **GP and volume numbers** match investigation details.
- **Partner Referral Single** is covered and prioritised by £ impact.
- **Annual margins** are properly framed as strategic, not a problem.
- **Headline** accurately reflects the main driver: margin decline on single trips, while annual growth is positive long-term.
- **Customer intent and market context** are sourced and specific.
- **All actions** are concrete, £-sized, and executable.
- **SQL**: all queries use the correct date range (`2026-03-02` to `2026-03-09`), without "period".
- **No unnecessary sections.**

**No changes needed.**

---
*Generated 16:52 10 Mar 2026 | Tracks: 22 + Follow-ups: 29 | Model: gpt-4.1*
