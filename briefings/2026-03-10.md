---
# HX Trading Briefing — 10 Mar 2026

## Margin stays under pressure despite hot insurance demand — GP down £9k over the last 7 days vs last year

---

## At a Glance

- 🔴 **Direct Annual & Single Trip GP** — We lost £10k in GP this week vs last year across direct annual (£6k) and single trip (£4k), with flat volume but margins squeezed 12–16%.
- 🔴 **Partner Single Trip GP** — Partner channel GP down £6k (−28% YoY) as traffic from partners dried up; conversion and margin held flat.
- 🔴 **Aggregator Single Trip Margin** — Despite 43% more aggregator single trip sales, GP dropped £600 (−25%), as average profit per policy nearly halved on deeper commission.
- 🟢 **Renewal Book Grows** — Renewal annual GP rose £1.4k (+3% YoY) as more existing customers came back, offsetting 8% lower margin per policy.
- 🔴 **Gold/Bronze Med GP Down** — Direct Gold and Bronze Main Single Medical schemes lost £2.9k in GP, but volumes rose; lower-value cases and price pressure drove down average profit per sale.

---

## What's Driving This

### Direct Annual GP `RECURRING`
Direct annual GP is down £6k this week (−11% YoY); volumes held at 964, but GP per policy dropped from £56 to £50. Main reason: cost per policy rose and discounts deepened slightly — part of our strategy, with no real movement on traffic or conversion. This follows our annual plan and is negative on 8 of the last 10 days.
```sql-dig
SELECT SUM(policy_count) AS policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Direct' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

### Direct Single Trip GP `RECURRING`
We’re £3.8k down on direct single trip GP (−9% YoY), despite 8% more sales; margin per policy shrank 16% (now £18.49). Flat traffic, but session-to-search conversion dropped 23% and higher underwriter costs plus heavier discounting ate into profit — this is now recurring (8 of last 10 days).
```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Direct' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

### Partner Referral Single Trip GP `RECURRING`
Partner single trip GP fell £6k (−28% YoY) from 26% lower policy count and steady margins. Main story is lost partner traffic; conversion and margin didn’t move — negative 8 of last 10 days.
```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Partner Referral' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

### Aggregator Single Trip Volume & GP `RECURRING`
Aggregator single trip GP fell £600 (−25% YoY), despite 43% more sales; profit per policy nearly halved (now £1.70). Squeeze comes from greater share via lowest-margin aggregators and commission pressure. Negative 9 of last 10 days.
```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))/NULLIF(SUM(policy_count),0) AS avg_gp FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Aggregator' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

### Gold Plus Main Single Med (Direct) GP `RECURRING`
Gold Plus Main Single Med HX GP is down £300 (−3% YoY) on 22% higher volume, as profit per policy slumped 20%. The shift is tied to increased price pressure and higher claim risk.
```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))/NULLIF(SUM(policy_count),0) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE scheme_name='Gold Plus Main Single Med HX' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

### Direct Bronze Main Single Med HX GP `RECURRING`
Bronze Main Single Med HX GP fell £2.6k (−19% YoY) on 10% higher sales; average profit per policy dropped 27%, with deep discounting and more price-sensitive cases.
```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))/NULLIF(SUM(policy_count),0) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE scheme_name='Bronze Main Single Med HX' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

### Medical Screening Conversion Gap `RECURRING`
GP from sessions with medical screening is down £1.7k for the week. Conversion on mobile improved, but average profit per sale shrank due to a swing toward lower-risk, lower-value cases.
```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) FROM `hx-data-production.commercial_finance.insurance_web_utm_4` a INNER JOIN `hx-data-production.commercial_finance.insurance_policies_new` b ON a.policy_id=b.policy_id WHERE a.booking_flow_stage='screening' AND a.transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

### Renewals GP `RECURRING`
Renewal annual GP is up £1.4k (+3% YoY) on 11% higher volume, even as margin per policy fell 8%. Our growing renewal book is the payoff from last year’s annual growth.
```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))/NULLIF(SUM(policy_count),0) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Renewals' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

---

## Customer Search Intent

Travel insurance search intent is up 57–74% YoY, far outpacing holiday demand, which is up 33–50%. Insurance-specific queries like “annual multi-trip”, “pre-existing medical”, and “Spain medical cover” jumped — the Google Trends index rose to 11.5 from 6.6 last year. The spread between insurance and holiday search has widened from +1 to +3 index points. There’s been a step-change since airlines announced 2026 seat launches and the countdown to new EU border checks began — people are proactively searching for cancellation and medical protection before booking trips.  
**Source:** [Insurance Intent](https://trends.google.com), Dashboard Metrics, AI Insights "trend" and "channels"

---

## News & Market Context

Major airlines have released extra seats early (easyJet, Jet2, Ryanair) and an early Easter is fuelling demand — traffic is real, performance is lagging only on margin. New EU border checks taking effect in April (EES) are driving a flood of medical and Spain/Greece cover queries, with UK press pushing out “GHIC isn’t enough” guides ([moneyweek.com](https://moneyweek.com/spending-it/travel-holidays/new-spanish-travel-insurance-rule?utm_source=openai)). Aggregator competition is fiercer; margins are being squeezed as rivals undercut and commission rates climb. Ongoing unrest in the Middle East is leading to BA flight disruption and an uptick in claims, with some insurers extending cover for stranded travellers ([uk.news.yahoo.com](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html?utm_source=openai), [saga.co.uk](https://www.saga.co.uk/travel-insurance/middle-east-travel-disruption?utm_source=openai)). Marketing spend is shifting to annual multi-trip and targeted medical product ads to catch intent.  
**Source:** AI Insights — "trend", "channels", "news"; [easyjet.com](https://www.easyjet.com/en/news/story/massive-flight-and-holiday-savings-for-2026?utm_source=openai)

---

## Actions

| Priority | What to do                                                         | Why (from the data)                    | Worth        |
|----------|--------------------------------------------------------------------|----------------------------------------|-------------|
| 1        | Pull back deep discounts on direct single trip pricing              | Margin squeeze costing us £3.8k/wk     | ~£3.8k/week |
| 2        | Re-bid and tighten price points on key aggregator schemes           | Volume is up but margin loss is severe | ~£0.6k/week |
| 3        | Escalate partner channel loss to business dev for a volume reset    | Partner GP down £6k due to lost volume | ~£6k/week   |
| 4        | Raise AMT/medical/Spain cover PPC/SEO to absorb search surge        | Market intent has shifted; opportunity | Renewals LT |
| 5        | Launch renewal comms now to lock in retention pre-Easter rush       | Renewal book is growing, defend margin | Renewals LT |

---

_Generated 09:32 11 Mar 2026 | 22 investigation tracks | GPT-4_

---
*Generated 15:44 11 Mar 2026 | Tracks: 22 + Follow-ups: 29 | Model: gpt-4.1*
