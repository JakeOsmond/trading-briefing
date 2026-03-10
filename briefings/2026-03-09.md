---
# HX Trading Briefing — 09 Mar 2026

## GP down £11k versus last year as strong demand meets even stronger price pressure in single trip; annuals grow but can't offset margin collapse.

---

## At a Glance

- 🔴 **Direct Single Trip GP Dive** — We lost about £6k this week on direct single-trip GP (down 14%), even though we sold more policies than last year.
- 🔴 **Partner Referral Single GP Drop** — Partner single-trip GP fell by £3.7k, dragged down by a 23% drop in volume, not price.
- 🔴 **Renewals Annual GP Down** — Annual renewal GP dropped £1.3k, mostly due to bigger discounts and a bump in UW costs, even though volume was up.
- 🟢 **Direct Annual Volume Up** — Direct annuals rose by 76 policies to 1,069, delivering a £3.7k weekly GP boost, even with 13% lower GP/policy — this is "future renewal" gold.
- 🟢 **Silver Tier Volume + GP Jump** — Silver sales up 11% (+193 YOY) and £1.8k GP lift; most of this is mobile, linking to more annual shopping.

---

## What's Driving This

### Direct Single Trip GP Shrink `RECURRING`
GP from direct single-trip took a £6k hit this week (down 14%) as average GP per policy fell from about £22 down to £19, even though we sold more trips (2,239 vs 1,983 last year). The margin drop is now structural—commissions and UW costs as a % of gross are steady, but price pressure, lower-value sales, and deal-seeking are biting for the third week running.
```sql-dig
SELECT SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp, SUM(policy_count) AS policies
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Direct' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

### Aggregator Single Trip Margin Collapse `RECURRING`
We sold 50% more single trips via aggregators (1,164 vs 772), but total GP was flat (+£500) as GP/policy nearly halved from £3.35 to just £1.78. This is a structural pricing war—customers chase cheap deals, so we get ultra-low-GP, low-ticket sales week after week.
```sql-dig
SELECT SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp, SUM(policy_count) AS policies
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Aggregator' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

### Direct Annual Volume Growth `RECURRING`
Direct annual sales grew to 1,069 (up 76 on last year), delivering £3.7k more GP—despite GP/policy slipping 13% to £49. Margin shrank a bit, but this is strong annual volume growth for the third week running—exactly what we want for future renewal income.
```sql-dig
SELECT SUM(policy_count) AS policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Direct' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

### Renewals Annual GP Down `RECURRING`
Annual renewal GP dropped £1.3k (down 11% on GP/policy) even as volume climbed to 1,291 (up 113). Heavier discounts (now 14%, up from 13%) and a small rise in UW cost per policy are squeezing margin—this has become a regular feature.
```sql-dig
SELECT SUM(policy_count) AS policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Renewals' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

### Partner Referral Single GP Drop `NEW`
GP from partner referral single-trip fell by £3.7k—sales dropped 23% YoY (down 212 policies), but GP/policy was steady so this is demand-led, not price or commission driven. This looks like a partner campaign gap, not a systemic issue.
```sql-dig
SELECT SUM(policy_count) AS policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Partner Referral' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

### Silver Tier Volume + GP Jump `NEW`
Silver cover sales jumped 11% (+193 policies) to 1,947, delivering an extra £1.8k GP. Growth mainly from mobile, linked to more annual intent.
```sql-dig
SELECT SUM(policy_count) AS policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE cover_level_name='Silver' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

---

## Customer Search Intent

Insurance search volume is booming—Google shows searches up 74% YoY, outpacing even holiday or “cheap flight” queries. “Annual travel insurance” searches are up over 100%, with Spain, Turkey, and USA trending. The lean to annual cover, and value-seeking around medical, is clear.

---

## News & Market Context

Airlines are flooding the market with cheap seats: easyJet, Jet2, and Ryanair just ramped up capacity. Aggregators are hammering prices—discounting on IMP, CTM, and Confused is up. Saga is now auto-extending Middle East disruption; cancellation cover searches climbed after the recent storm. Regulatory/tax noise is calm.

---

## Actions

| Priority | What to do                                                   | Why                                    | Worth      |
|----------|--------------------------------------------------------------|-----------------------------------------|------------|
| 1        | Cut lowest-value single-trip aggregator listings immediately | Margin on aggregator singles is now loss-making; deal-seekers dominate | ~£5k+/week |
| 2        | Push annual multi-trip on all landing and PPC                | Direct annuals are high-volume, strong future value, search intent is up | ~£3.7k/week |
| 3        | Relaunch partner referral single trip offers                 | Volume loss from partners cost £3.7k this week | ~£3.7k/week |
| 4        | Target Silver tier upsells to medical and mobile users       | Silver is converting mobile/medical buyers, up £1.8k this week | ~£1.8k/week |

---

_Generated 09:30 10 Mar 2026 | 22 investigation tracks | GPT-4_

---
*Generated 16:31 10 Mar 2026 | Tracks: 22 + Follow-ups: 31 | Model: gpt-4.1*
