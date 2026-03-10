Your draft briefing is strong and covers almost everything required, but there are a few issues:

### Issues Found vs. Criteria

1. **Numerical Accuracy and Data Sourcing:**
   - Most £ claims match the investigation findings, but the headline overstates the week-on-week GP drop ("£11k drop")—the actual sum of listed impacts from the findings is closer to -£10k. Acceptable with rounding, but better to state a rounder "GP is down about £10k" and specify the drop is across single trip and annual segments.

2. **Material Movers:**
   - All key material movers from the investigation—Aggregator Single, Partner Referral Single, Direct Single, Direct Annual, Europe mix—are included. 
   - *Renewals:* The draft covers "Renewal Annual GP" with data matching the findings.
   - *Medical and Cruise:* The investigation findings did not mention these as material, so not needed.

3. **Annual Policy Margins:**
   - The draft correctly frames annual margin squeeze as a renewal investment rather than an immediate problem.

4. **Actions:**
   - Actions are specific, aligned to the drivers, and mostly quantifiable. One action ("Highlight automatic extension...") is marked unquantified, which is acceptably transparent.

5. **Market and Intent Context:**
   - Excellent—quotes sources, includes numbers, and cites Google Trends and AI Insights.

6. **Headline:**
   - Headline is accurate about direction and general reason, but slightly exaggerates the GP drop. Suggest rewording for precision.

7. **SQL Dig Blocks:**
   - All use real date literals and proper table references.

8. **Clarity and Style:**
   - Clear, direct, with context for every number. No jargon. Short sentences.

**Suggested Edits:**
- Tweak headline to clarify the GP drop is just under £11k and covers both single trip and annual falls.
- In the "At a Glance" bullets, clarify that the GP slide is close to £10k in total.
- Confirm capitalisation consistency for recurring tags.
- No other changes needed.

---

# HX Trading Briefing — 09 Mar 2026

## "GP sinks nearly £10k this week as more shoppers buy lower-margin policies—even with 11% more market demand"

---

## At a Glance

- 🔴 **Single Trip GP Slide** — We lost around £6.3k/week in single trip gross profit, mainly as aggregator and partner single-trip GP both fell hard (£1.1k and £3.7k down), plus direct is off by £1.5k—all margin, not volume.
- 🔴 **Annual Margin Squeeze** — Annual GP (direct, renewal, aggregator) fell by £5k+ combined; annual volume is up 9%, but margin per policy is down 11–13%.
- 🔴 **Europe Margin Hit** — Europe policies rose 9% but delivered £4k less GP, with avg profit per policy falling from £23 to £21 as customers bought cheaper deals.
- 🔴 **Conversion Rates Down** — Conversion slipped about 1 point YoY, costing us about £2.7k/week, as more people visit but fewer commit.
- 🟢 **Annual Volume Growth** — Annual sales up nearly 9% YoY, a win in acquisition terms and future renewals.

---

## What's Driving This

### Partner Referral Single Trip GP `RECURRING`
GP down £3.7k/week (to £16k), with sales volume down 23%—it’s a traffic problem, not pricing. Main blame is lower inbound volume from key referrers, while commission per policy is up.
```sql-dig
SELECT agent_name, SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Partner Referral' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09' GROUP BY agent_name ORDER BY SUM(policy_count) DESC
```

### Europe GP (Geo Mix) `RECURRING`
Europe volume up 9% but GP is £4k lower as avg profit per policy dropped nearly 12%, mostly because of price-seeking behaviour to Spain/Turkey and downgrades to cheaper cover. This is the fourth week of sharp margin fall in Europe.
```sql-dig
SELECT cover_level_name, SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE destination_group='Europe' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09' GROUP BY cover_level_name ORDER BY SUM(policy_count) DESC
```

### Direct Annual GP `RECURRING`
We sold 8% more annuals (growing future renewals), but made £3k less in GP as avg profit per annual is down 13% from £56 to £49—almost all due to aggressive price and discount competition. This margin squeeze is now a steady trend.
```sql-dig
SELECT discount_value, COUNT(*), SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Direct' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09' GROUP BY discount_value ORDER BY SUM(policy_count) DESC
```

### Overall Conversion Rate Drop `RECURRING`
Across the board, conversion is down about 1 point—from 9% to 8%—meaning 1,350 fewer buyers a week. The main hit is fewer mobile visitors moving from "just looking" to searching for prices, now running third week in a row.
```sql-dig
SELECT device_type, COUNT(DISTINCT session_id), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) FROM `hx-data-production.commercial_finance.insurance_web_utm_4` WHERE session_start_date BETWEEN '2026-03-02' AND '2026-03-09' GROUP BY device_type ORDER BY COUNT(DISTINCT session_id) DESC
```

### Direct Single Trip GP `RECURRING`
GP down £1.5k/week despite 13% more sales—margin per policy fell 15%, mainly as more buyers took low-value, heavily discounted products. This is consistently volume-up-but-margin-worse for the last month.
```sql-dig
SELECT cover_level_name, SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Direct' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09' GROUP BY cover_level_name ORDER BY SUM(policy_count) DESC
```

### Renewal Annual GP `RECURRING`
Renewal GP is £1.3k down, with 10% more renewals but avg margin down 11%, due to lower renewal offers and higher discounts. Been the same story since late January.
```sql-dig
SELECT discount_value, COUNT(*), SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Renewals' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09' GROUP BY discount_value ORDER BY SUM(policy_count) DESC
```

### Aggregator Single Trip GP `RECURRING`
We wrote 51% more single trips on aggregators, but margin crashed, with avg GP nearly halved (£3.35 → £1.78/policy, total -£1.1k/wk). This is structural: price is now the only differentiator for many customers.
```sql-dig
SELECT cover_level_name, SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Aggregator' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09' GROUP BY cover_level_name ORDER BY SUM(policy_count) DESC
```

### Aggregator Annual GP `RECURRING`
Annual aggregator GP is £463 further into the red, but this is expected—policy volume up 9%, negative margin as part of long-term renewal strategy. No short-term fix needed.
```sql-dig
SELECT insurance_group, SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)), AVG(total_paid_commission_perc) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Aggregator' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09' GROUP BY insurance_group ORDER BY SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) ASC
```

---

## Customer Search Intent

Insurance search interest is up 74% YoY; that's much stronger than holiday intent, with Google's index at 11.5 now vs 6.6 last year (**Source:** Google Sheets — Insurance Intent tab, Dashboard Metrics tab). Customers are actively looking for cheap flights (+129%) and deals (+33%), pushing volume but at lower average spend. Spain, Turkey, and the Canaries are the hottest destinations. “Do I need travel insurance for…” searches are up—customers are closer to buying, especially annual and medical cover. The gap between insurance and holiday search is almost triple last year’s, but most are shopping around for value and instant answers (**Source:** AI Insights — "what_matters", "trend", "yoy", [Google Trends](https://trends.google.com/trends/explore?date=today%205-y&q=travel%20insurance)).

---

## News & Market Context

Travel demand is running hot thanks to massive seat sales from easyJet and Jet2: Spain seats up, tickets as low as they've ever been ([easyjet.com](https://www.easyjet.com/en/news/story/easyjet-puts-spring-2026-flights-on-sale?utm_source=openai)). Cheap flights are feeding more insurance shoppers—but everyone’s shopping for the lowest price. There’s no disruption from strikes or travel chaos; headline risk is minimal (**Source:** AI Insights — "news", [independent.co.uk](https://www.independent.co.uk/travel/news-and-advice/storm-goretti-travel-rail-road-air-ferry-b2896612.html?utm_source=openai)). Competitors are leaning hard into value—Saga offers automatic extension if customers are stranded ([saga.co.uk](https://www.saga.co.uk/travel-insurance/middle-east-travel-disruption?utm_source=openai)). Middle East disruption is ongoing, but it's not impacting volume, just requiring clearer messaging on war cover ([uk.news.yahoo.com](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai)). The whole market is about volume wins, not fat margins right now.

---

## Actions

| Priority | What to do                                                       | Why (from the data)                                | Worth       |
|----------|------------------------------------------------------------------|----------------------------------------------------|-------------|
| 1        | Push aggregator and direct annual policies in all PPC/SEO ads    | Annual growth is strong; market intent is there    | ~£2.5k/wk+  |
| 2        | Tighten price floors and reduce discounts on single trip online  | Single trip GP loss is now structural, margin eroded | ~£6k/wk     |
| 3        | Launch “instant Europe travel quotes” PPC landing for Spain/Turkey value-seekers | Euro volume up, but yield is falling fast          | ~£4k/wk     |
| 4        | Speed up mobile funnel changes to convert browsing visitors      | Conversion down sharply on mobile/browser—1pt loss | ~£2.7k/wk   |
| 5        | Highlight automatic extension and clear war cover in renewal and annual journeys | Required for BA/Saga parity, high search intent    | Unquantified|

---

_Generated 08:30 09 Mar 2026 | 22 investigation tracks | GPT-4_

---
*Generated 17:23 10 Mar 2026 | Tracks: 22 + Follow-ups: 31 | Model: gpt-4.1*
