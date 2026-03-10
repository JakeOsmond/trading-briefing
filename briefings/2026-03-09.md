---
# HX Trading Briefing — 09 Mar 2026

## GP falls £11k this week as price war drives huge volume but margin gets squeezed hard on single and renewals

---

## At a Glance

- 🔴 **GP Down** — Gross profit this week was about £169k, down £11k on last year (6% worse), mostly thanks to tougher single-trip and renewal margin.
- 🔴 **Single Trip Margin Squeeze** — GP from single policies is down £2k this week; we sold 13% more but average GP per policy dropped from £22 to £19 (down 14% YoY).
- 🔴 **Partner Single Volume Drop** — Partner-referral single GP down £3.7k (down 18% YoY), with volume off 23%.
- 🔴 **Renewal GP Down** — Renewal annual GP fell £1.3k (2% lower YoY), as steeper discounts trimmed profit per policy from £46 to £41.
- 🟡 **Annual Volumes Up** — We sold 9% more annual policies YoY—this is us buying future renewal income at a short-term GP loss.

---

## What's Driving This

### Direct Single Trip GP Decline `RECURRING`
Direct single trip GP fell by £1.2k to about £42k, with margin dropping from 38% to 32% despite volumes up 13%. This is because higher underwriter costs (up £3.60 per policy YoY) and bigger discounts (up £0.60) are eroding profit—this squeeze has now stuck for months.

```sql-dig
SELECT cover_level_name, SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)), 
SUM(CAST(total_gross_inc_ipt AS FLOAT64))/NULLIF(SUM(policy_count),0) as avg_customer_price
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Direct' AND policy_type='Single'
  AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
GROUP BY cover_level_name ORDER BY 3 ASC
```

### Aggregator Single Trip Margin Collapse `RECURRING`
Aggregator single trip GP dropped by £660 (down 20% YoY), with volume up 50% but GP per policy slashed from £3.35 to £1.80. Average price crashed (£47 to £35), commission only dipped a bit, and this low-margin aggregator mix is now our main earnings problem—this is structural, not a blip.

```sql-dig
SELECT scheme_name, SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Aggregator' AND policy_type='Single'
  AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
GROUP BY scheme_name ORDER BY 3 ASC
```

### Partner Single Volume Drop `RECURRING`
Partner referral single policy sales fell from 917 to 705 (down 23%), GP off by £3.7k, though GP per policy slightly improved (£22 to £23). Most of the pain is cruise-related partners; cruise demand is weak across the board and dragging down partner flows for the third week.

```sql-dig
SELECT scheme_name, SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Partner Referral' AND policy_type='Single'
  AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
GROUP BY scheme_name ORDER BY 2 ASC
```

### Renewals GP Weakness `RECURRING`
Renewal annual GP is down £1.3k (2% lower YoY) even with policy volume up 9%, as average profit per policy slid from £46 to £41 (down 11%). Deeper discounts and a price war mean renewal discounts are up and profit is down—six of the last eight weeks have looked like this.

```sql-dig
SELECT scheme_name, SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Renewals' AND policy_type='Annual'
  AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
GROUP BY scheme_name ORDER BY 3 ASC
```

### Mix Shift to Bronze and Low GP `RECURRING`
More customers are picking the cheapest (Bronze) cover: Bronze sales mix climbed, but GP per policy fell from £15.50 to £11.80. This shift cost us £1.3k in weekly GP and adds to the margin squeeze we've seen for three weeks straight.

```sql-dig
SELECT cover_level_name, SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
GROUP BY cover_level_name ORDER BY SUM(policy_count) DESC
```

### Aggregator Annual Policies (Strategic Loss) `RECURRING`
Aggregator annual sales rose 9%; as planned, these run at a negative margin (about -£6 per policy, same as last year). This is our renewal pipeline, not a margin issue.

```sql-dig
SELECT scheme_name, SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Aggregator' AND policy_type='Annual'
  AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
GROUP BY scheme_name ORDER BY 3 ASC
```

### Direct Annual Policies Slight GP Drop `NEW`
Direct annual policy volume increased 8%, but total GP dipped £3.3k (down 6%) as GP per policy fell from £56 to £49, again driven by bigger discounts and pricier underwriting.

```sql-dig
SELECT scheme_name, SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Direct' AND policy_type='Annual'
  AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
GROUP BY scheme_name ORDER BY 3 ASC
```

---

## Customer Search Intent

Travel insurance Google searches are up 74% YoY, outpacing holiday searches (up 65%). Value-led searches like “cheap flights” and “annual multi trip” dominate, with Spain, Turkey, and the Canaries top for destination terms. Cross-sell demand for airport parking is also up 60%.

---

## News & Market Context

External market is in full price war: airlines, big travel brands, and insurance competitors are hitting value and low-price messaging hard, especially on comparison sites. Competitor aggregator offers are aggressive. The FCA is making noise on product communications, and cruise lines are seeing weaker demand. No new travel disruptions—what we’re seeing is pure price competition.

---

## Actions

| Priority | What to do                                              | Why (from the data)                                          | Worth         |
|----------|--------------------------------------------------------|--------------------------------------------------------------|---------------|
| 1        | Tighten discounting rules, especially on single trips   | Discount-led margin squeeze is the biggest GP drag            | ~£1.5k/week   |
| 2        | Push Bronze upgrade flows—nudge more to Silver in web   | Bronze mix shift losing us £1.3k/week; Silver margin is better| ~£1.3k/week   |
| 3        | Audit aggregator single pricing vs competitors          | Aggregator single margin collapse is now structural           | ~£700/week    |
| 4        | Target PPC to AMT and medical (Spain/Turkey), with value-led copy | Demand is rising fast here                        | £1–2k/week+    |
| 5        | Review underwriter deal terms—direct/renewals           | Direct/renewal GP per policy cut by higher underwriter costs  | ~£600/week    |

---

_Generated 07:45 10 Mar 2026 | 22 investigation tracks | GPT-4_

---
*Generated 14:19 10 Mar 2026 | Tracks: 22 + Follow-ups: 28 | Model: gpt-4.1*
