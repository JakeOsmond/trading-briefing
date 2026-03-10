---
# HX Trading Briefing — 09 Mar 2026

## Single trip margin collapse wipes out GP gains from record demand, despite strong mobile and annual growth.

---

## At a Glance

- 🔴 **GP down £11k YoY** — We landed £169k GP this week, down £11k (6%) on last year, mainly because single trip margins got hammered.
- 🟢 **Mobile web conversion surge** — Mobile booked sessions up 16% (+500), adding £7k GP, thanks to a cleaner funnel and search-to-book leaps.
- 🔴 **Partner Referral single trip slide** — Lost £3.7k GP on this route, with single trip volume down 23% — pure volume drop, not margin.
- 🔴 **Aggregator single trip margin crushed** — GP fell £1.5k (down 40%), as avg. margin per policy halved, even though sales jumped 51%.
- 🟢 **Annuals (Gold Plus/Gold Cruise) upsell** — Uplift worth £1.6k this week, driven by AMT web buyers switching to higher cover.

---

## What's Driving This

### Mobile Web Funnel Shifts `RECURRING`
Mobile bookings up 16% (+496 sessions YoY), adding £7k GP—search-to-book rate up 0.2pts, driven by funnel fixes and more deep-engaged mobile shoppers. This trend’s persisted for several weeks, powered by heavy mobile PPC.
```sql-dig
SELECT COUNT(DISTINCT session_id) AS mobile_sessions, SUM(policy_count) AS bookings, SUM(total_gross_exc_ipt_ntu_comm) AS gp
FROM `hx-data-production.commercial_finance.insurance_web_utm_4`
WHERE device_type = 'Mobile' AND session_start_date BETWEEN '2026-03-02' AND '2026-03-09'
```

### Partner Referral Single Trip Volume Fall `RECURRING`
GP dropped £3.7k (to £16.4k), all due to volume falling 23% YoY—no shift into annuals, just lost sales. The drop has lasted for a month and isn’t just seasonality.
```sql-dig
SELECT SUM(policy_count) AS policies, SUM(total_gross_exc_ipt_ntu_comm) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
AND distribution_channel='Partner Referral' AND policy_type='Single'
```

### Aggregator Single Trip Margin Collapse `RECURRING`
We sold 51% more aggregator single trips (1,164 vs 772), but GP plunged £1.5k as average margin halved to £1.78 per policy. Commission (30%+) and a race to the bottom on price are killing profit for the third week running.
```sql-dig
SELECT SUM(policy_count) AS policies, SUM(total_gross_exc_ipt_ntu_comm) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
AND distribution_channel='Aggregator' AND policy_type='Single'
```

### Direct Single Trip Margin Drop `RECURRING`
Direct single trip sales up 13%, but GP fell £1.5k as margin per policy slid to £18.75 (from £21.92). Extra claims risk and small increases in cover cost are the culprits; steady drop for several weeks.
```sql-dig
SELECT SUM(policy_count) AS policies, SUM(total_gross_exc_ipt_ntu_comm) AS gp,
SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))/NULLIF(SUM(policy_count),0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
AND distribution_channel='Direct' AND policy_type='Single'
```

### Aggregator Annual Margin Still Negative, But Volume Up `RECURRING`
Annuals via aggregator grew 9% in policy count, but GP is still -£7.2k as discounts and commission outweigh volume. This is by design—building future renewal pool—even though short-term losses increased by £460.
```sql-dig
SELECT SUM(policy_count) AS policies, SUM(total_gross_exc_ipt_ntu_comm) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
AND distribution_channel='Aggregator' AND policy_type='Annual'
```

### Renewal Annual Volume and GP Growth `RECURRING`
Renewal annuals up 10% (+113 policies), adding £660 GP vs last year (to £52.9k). AMT repeat buyers continue to prop up our future income, even as margin per policy dipped a bit.
```sql-dig
SELECT SUM(policy_count) AS policies, SUM(total_gross_exc_ipt_ntu_comm) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
AND distribution_channel='Renewals' AND policy_type='Annual'
```

### Gold Plus/Gold Cruise Annual Scheme Switch `NEW`
Gold Plus and Gold Cruise AMT schemes lifted GP by £1.6k this week, as more AMT web buyers took higher cover. Upsell momentum started this week, led by medical and multi-search shoppers.
```sql-dig
SELECT SUM(policy_count) AS policies, SUM(total_gross_exc_ipt_ntu_comm) AS gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
AND (scheme_name LIKE '%Gold Plus%' OR scheme_name LIKE '%Gold Cruise%') AND policy_type = 'Annual'
```

### Deep Web Engagement Drives High GP `NEW`
Shoppers engaging with >5 pages delivered £900 extra GP, mainly from mobile AMT buyers going for pricier cover. This has ticked up for two weeks, tracking with mobile funnel investments.
```sql-dig
SELECT COUNT(DISTINCT session_id) AS sessions, SUM(total_gross_exc_ipt_ntu_comm) AS gp
FROM `hx-data-production.commercial_finance.insurance_web_utm_4`
WHERE session_seconds > 240 AND session_start_date BETWEEN '2026-03-02' AND '2026-03-09'
```

---

## Customer Search Intent

Travel insurance search demand is booming—up 57% YoY (Google index 11 this week vs 7 last year). Most of the spike is for annual multi-trip, Spain, Turkey, and medical-related cover; searchers are chasing bargains thanks to headline flight deals.

---

## News & Market Context

EasyJet and Jet2 unleashed major fare sales, bringing in price-driven buyers and pushing up AMT demand. UK aggregators are locked in a margin-killing price war—commission rates are crushing single trip GP. Saga's cover extensions are live for stranded travellers; market is hyper-competitive on volume at the expense of profit.

---

## Actions

| Priority | What to do                                                     | Why (from the data)                                 | Worth      |
|----------|---------------------------------------------------------------|-----------------------------------------------------|------------|
| 1        | Double down on mobile/AMT PPC and fast-quote landing pages    | £7k/week gain in GP from better mobile conversion   | ~£7k/week  |
| 2        | Push Gold Plus/Gold Cruise AMT upsell on web/partner flows    | £1.6k/week incremental GP from higher cover         | ~£2k/week  |
| 3        | Pause or reprice aggregator single trip loss-leader products  | -£1.5k/week wiped by negative margins               | ~£1.5k/week|
| 4        | Ramp up new partner referral offers—claw back volume          | -£3.7k/week lost in partner single trips            | ~£4k/week  |
| 5        | Smooth web onboarding from session start to quote             | High-intent conversions lag; more deep sessions pay | £2.5k/week |

---

_Generated 08:11 10 Mar 2026 | 22 investigation tracks | GPT-4_

---
*Generated 14:45 10 Mar 2026 | Tracks: 22 + Follow-ups: 35 | Model: gpt-4.1*
