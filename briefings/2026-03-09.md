---
# HX Trading Briefing — 09 Mar 2026

## Aggregator Singles Volume Up but Margin Collapses, Dragging Down Total GP

---

## At a Glance

- 🔴 **Aggregator Single Trip GP crash** — We made just £2.1k on aggregator singles this week, down £500 vs last year, even though we sold 1,164 policies (up nearly 400); margin per policy nearly halved.
- 🔴 **Partner Referral Singles volume & GP drop** — Referral singles lost £3.7k vs last year at £16.4k GP, driven by 200 fewer sales and fatter commission shares.
- 🔴 **Direct Single Trip GP slide** — Direct singles lost £1.5k GP vs last year at £42k total, with sales up 13% but profit per policy down by £3.
- 🔴 **Direct Annual GP down on margin squeeze** — Direct annuals rose 8% in volume but GP fell £3.3k as rising costs hit hard.
- 🟢 **Renewal Annual GP up** — Renewal annuals gave us £5.7k more GP, thanks to higher volume—even after heavier discounting.

---

## What's Driving This

### Aggregator Single Trip GP collapse `RECURRING`
GP on aggregator singles is just £1.78 per policy, nearly half last year’s £3.35, as relentless price cuts and 30% commissions hollow out profit. Despite selling over 390 more policies, this is the fifth week of ongoing collapse—mix is almost entirely cheap Classic tiers now.
```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
FROM hx-data-production.commercial_finance.insurance_policies_new
WHERE distribution_channel = 'Aggregator' AND policy_type = 'Single' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

### Partner Referral Single Trip GP drop `RECURRING`
Partner referral singles dropped by over 200 policies and £3.7k in GP year-on-year (now 705 policies, £16.4k GP). Volume fell, and higher commissions (£27 per policy, up 16%) ate into what margin remained.
```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
FROM hx-data-production.commercial_finance.insurance_policies_new
WHERE distribution_channel = 'Partner Referral' AND policy_type = 'Single' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

### Direct Single Trip GP drop `RECURRING`
GP on direct singles slid from £21.92 to £18.75 per policy, with sales up by 256 but yield hit by rising underwriter costs and more medicals. This erosion has been steady since January and now spans all main destinations.
```sql-dig
SELECT cover_area, SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
FROM hx-data-production.commercial_finance.insurance_policies_new
WHERE distribution_channel = 'Direct' AND policy_type = 'Single' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
GROUP BY cover_area
```

### Direct Annual GP small contraction `RECURRING`
We sold 76 more direct annuals, but GP fell £3.3k to £52.2k as per-policy profit dropped from £55.87 to £48.84; price rose but underwriter cost surged too. Margin pressure is now standard across all tiers.
```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
FROM hx-data-production.commercial_finance.insurance_policies_new
WHERE distribution_channel = 'Direct' AND policy_type = 'Annual' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

### Renewal Annual GP improvement `RECURRING`
Renewal annuals were up £5.7k GP (volume up 10%, to 1,291) even as policy price and yield slipped—discounting is higher but strong retention in older customers is paying off. This is a recurring, positive trend and key to future profit.
```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
FROM hx-data-production.commercial_finance.insurance_policies_new
WHERE distribution_channel = 'Renewals' AND policy_type = 'Annual' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

### Increase in Worldwide policy mix, but lower GP `RECURRING`
Worldwide policy sales jumped (+270), but GP fell £6.9k as per-policy profit dropped from £30 to £24 due to commission and product mix shifts. Value-seeking buyers are making up more of this segment.
```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
FROM hx-data-production.commercial_finance.insurance_policies_new
WHERE destination_group = 'Worldwide' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

### Cruise GP growth (Direct & Renewal) `NEW`
Cruise policies added £2.3k GP, mostly from direct and renewal channels; older age groups and premium add-ons drove the uptick. Growth in this area is recent but potentially sustainable.
```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
FROM hx-data-production.commercial_finance.insurance_policies_new
WHERE cruise_flag = 'Cruise' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

---

## Customer Search Intent

Insurance searches are up 74% year-on-year (index 11.5 vs 6.6)—especially for Spain, Turkey, and AMT. Queries are mostly price-sensitive (“cheap flights,” “holiday deals”) and medical-related. More people are searching for insurance before booking, but price resistance is strong.

---

## News & Market Context

Airlines keep dropping fares to Spain, Turkey, and the Canaries, flooding the market with lower-value customers. Google search volume for travel insurance is at a multi-year high, led by bargain-hunters. Major aggregators are slashing prices and jacking up commission demands—this is directly driving down our margins. Airline disruption in the Middle East is seeing some insurers (SAGA) add auto-extensions; we’re already getting renewal queries about war exclusions.

---

## Actions

| Priority | What to do                                                           | Why (from the data)                                    | Worth      |
|----------|---------------------------------------------------------------------|--------------------------------------------------------|------------|
| 1        | Tighten aggregator single trip pricing, start yield or volume cap    | Aggregator singles are eating £7k+/week in losses      | ~£7k/wk    |
| 2        | Push Direct Annual/AMT sales hard, lead with value and medical cover | Annuals are delivering net GP and are future renewals  | ~£6k/wk    |
| 3        | Renegotiate or pause referral commissions for single trips           | Referral GP is down £3.7k on higher commissions        | ~£4k/wk    |
| 4        | Double down on cruise add-ons in direct and renewal                  | We’re up £2.3k from cruise sales—room to grow         | ~£2k/wk    |

---

_Generated 12:01 10 Mar 2026 | 22 investigation tracks | GPT-4_

---
*Generated 15:49 10 Mar 2026 | Tracks: 22 + Follow-ups: 35 | Model: gpt-4.1*
