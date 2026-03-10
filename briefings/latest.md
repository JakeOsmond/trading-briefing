---
# HX Trading Briefing — 09 Mar 2026

## Record Policy Sales Can't Offset Margin Crash as Price War Hits Hardest Europe, Worldwide, and Single Trip

---

## At a Glance

- 🔴 **Europe GP Down £4k** — Europe trips made £110k GP, £4k less than last year, even after selling 10% more; margin per policy now £20.50 (12% lower).
- 🔴 **Direct Single Margin Hit £1.6k** — Single trip GP from direct dropped £1.6k (to £42k); margin per policy sank 14% YoY despite higher sales.
- 🔴 **Aggregator Single Crash £900** — GP on aggregator single-trip fell £900 to just £2k as margin halved to £1.80 per policy, even with volume up 50%.
- 🔴 **Worldwide GP Down £1.4k** — Worldwide sales up but GP down £1.4k (now £59k); per-policy GP dropped from £30 to £24.
- 🟢 **Total Volume Up +730, Low GP** — We sold over 7,700 policies this week (+10%), but because margins shrank, total GP actually **fell** £11k.

---

## What's Driving This

### Europe Destination GP Softness `RECURRING`
Europe volume up nearly 500 policies (to 5,357), but lower margin (£20.50 vs £23.20) dragged regional GP down £4k. Flight sales to Spain/Turkey triggered intense deal-hunting and discounting for six straight weeks.
```sql-dig
SELECT destination_group, SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) as gp FROM hx-data-production.commercial_finance.insurance_policies_new WHERE destination_group='Europe' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09' GROUP BY 1
```

### Direct Single Policy GP Decline `RECURRING`
More direct single trips sold (2,239 vs 1,983 LY), but margin per policy down to £18.75 (from £21.90); GP fell £1.6k. Higher discounts (now 11%) and underwriter fees are biting—this is a regular squeeze, not a one-off.
```sql-dig
SELECT distribution_channel, policy_type, SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) as gp FROM hx-data-production.commercial_finance.insurance_policies_new WHERE distribution_channel='Direct' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09' GROUP BY 1,2
```

### Aggregator Single Policy GP Crash `RECURRING`
Single-trip aggregator GP halved per policy (£3.35 ➔ £1.78); total GP down nearly £900 despite 50% more volume (1,164 vs 772). Higher aggregator/underwriter cuts and price war pressure—structural, not temporary.
```sql-dig
SELECT distribution_channel, policy_type, SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) FROM hx-data-production.commercial_finance.insurance_policies_new WHERE distribution_channel='Aggregator' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09' GROUP BY 1,2
```

### Worldwide Destination GP Drop `RECURRING`
Worldwide sales up (2,429 vs 2,157), GP down £1.4k (now £58.9k); margin shrank 20% (now £24/policy). This price-led squeeze matches the pattern seen in Europe and is driven by cheap long-haul deals.
```sql-dig
SELECT destination_group, SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) FROM hx-data-production.commercial_finance.insurance_policies_new WHERE destination_group='Worldwide' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09' GROUP BY 1
```

### Aggregator Annual Margin More Negative `RECURRING`
Annual aggregator sales up (1,144, +9%), but GP now -£7.2k (worse than last year, -£6.7k); margin per policy steady at -£6.26. This is deliberate: we're investing for future renewals by growing annual volume.
```sql-dig
SELECT distribution_channel, policy_type, SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) FROM hx-data-production.commercial_finance.insurance_policies_new WHERE distribution_channel='Aggregator' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09' GROUP BY 1,2
```

### Total Volume Up, GP Still Down `RECURRING`
Sales soared to 7,786 (up 10% YoY), but margin erosion meant total GP dropped by £11k week-on-week. If margin had held, we'd be up £17k—real growth is eaten up by the price war.
```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) FROM hx-data-production.commercial_finance.insurance_policies_new WHERE transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

---

## Customer Search Intent

Travel insurance searches are up 57% over last year (index 11.5 vs 6.6). Most people are looking for “cheap flights,” “Spain/Turkey cover,” and “annual policy deals”—correlating directly with our single/annual high-volume, low-margin sales. Mobile conversion strong, but basket value and extras are way down.

---

## News & Market Context

Airlines (easyJet, Jet2) ramped up cheap fares and online travel agents are pushing last-minute Spain/Turkey deals. Insurance aggregators and rivals like Saga responded with heavy PPC activity and broad-based price cuts. No macro disruption, but BA Middle East flight rerouting continues—keep exclusions and extensions visible.

---

## Actions

| Priority | What to do                                                      | Why (from the data)                                 | Worth         |
|----------|-----------------------------------------------------------------|-----------------------------------------------------|---------------|
| 1        | Redirect marketing/PPC to drive more annual and Spain/Turkey sales, de-emphasise loss-leading singles | Aggregator/direct singles margin collapse, annuals drive future value | ~£3-5k/week   |
| 2        | Push mobile and aggregator buyers toward annual/AMT over single-trip offers | Mobile is volume-rich but GP-poor; annuals are our renewal base     | ~£2k/week     |
| 3        | Review and cut extra discounts on direct singles                 | Margin per policy fell 14% on direct singles        | ~£1.6k/week   |
| 4        | Pre-select annual/AMT on aggregator and remove “best” discount from single quotes | Aggregator single margins worst hit                 | ~£900/week    |
| 5        | Add renewal “pipeline” messaging to direct web journeys; highlight value over price | Total GP fell despite more sales; value buyers hold margin | ~£1-2k/week   |

---

_Generated 09:25 10 Mar 2026 | 22 investigation tracks | GPT-4_

---
*Generated 13:51 10 Mar 2026 | Tracks: 22 + Follow-ups: 34 | Model: gpt-4.1*
