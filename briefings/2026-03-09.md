---
# HX Trading Briefing — 09 Mar 2026

## GP down £11k on last year as margin squeeze hits all major channels, despite record demand and policy volumes rising fast.

---

## At a Glance

- 🔴 **Direct Single Trip margin shrank** — We made £4.2k GP, down £150 YoY (about 3%), with policy volume up 13% but avg GP/policy down 14% to £18.75.
- 🔴 **Direct Annual margin slipped** — We're investing in renewals (annual policy volume up 8%), but GP per policy fell £7 (now £49, was £56); weekly GP £5.2k, down £330.
- 🔴 **Renewal GP under pressure** — GP down £125 (to £5.3k, -2%) even as renewal volumes rose 9%; more customers grabbed discounts or downgraded cover.
- 🔴 **Partner Referral Single policy drop** — GP down 24% (£2.1k to £1.6k), policy volumes fell by 23%; fewer bookings from partners.
- 🔴 **Aggregator Single Trip margin collapsed** — Margin per policy nearly halved (now £1.78, was £3.35), weekly GP down £510, even as volume jumped 51%.

---

## What's Driving This

### Direct Single Trip Margin Shrink `RECURRING`
We made £4.2k GP—down £150 on last year, despite selling 2,239 policies (+13%). Average GP per policy slipped from £21.90 to £18.75 as heavier discounts and a shift to Bronze/Silver cover persist (this is the 6th week running).

```sql-dig
SELECT SUM(policy_count) AS policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM hx-data-production.commercial_finance.insurance_policies_new
WHERE transaction_date BETWEEN '2026-03-02' AND '2026-03-09' AND distribution_channel='Direct' AND policy_type='Single'
```

### Direct Annual Policy GP Decline `RECURRING`
Annual GP down to £5.2k from £5.5k last year (-6%), with 1,069 policies sold (+8%). Average GP per policy fell from £56 to £49 due to more discounting and mix shift toward Silver; this is intentional to grow next year's renewal base.

```sql-dig
SELECT SUM(policy_count) AS policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM hx-data-production.commercial_finance.insurance_policies_new
WHERE transaction_date BETWEEN '2026-03-02' AND '2026-03-09' AND distribution_channel='Direct' AND policy_type='Annual'
```

### Renewals GP Weakness `RECURRING`
Renewal GP dipped to £5.3k (down £125, -2%), but volume is up 9% to 1,291. More customers switched to cheaper or discounted options, so average GP per policy fell to £41 (was £46).

```sql-dig
SELECT SUM(policy_count) AS policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM hx-data-production.commercial_finance.insurance_policies_new
WHERE transaction_date BETWEEN '2026-03-02' AND '2026-03-09' AND distribution_channel='Renewals'
```

### Partner Referral Single Policy Mix Shift `RECURRING`
GP from partner referral singles dropped 24% (£2.1k to £1.6k), as volumes fell 23% to 705. No change in discount or commission—the drop is all about less core partner traffic.

```sql-dig
SELECT SUM(policy_count) AS policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM hx-data-production.commercial_finance.insurance_policies_new
WHERE transaction_date BETWEEN '2026-03-02' AND '2026-03-09' AND distribution_channel='Partner Referral' AND policy_type='Single'
```

### Aggregator Single Trip Margin Compression `RECURRING`
Weekly GP fell to £2.1k (from £2.6k), even though policies leapt 51% (1,164 sold). Margin per policy collapsed as average price fell (£35 vs £47 last year) and commission still took a big chunk; price-led competition is structural.

```sql-dig
SELECT SUM(policy_count) AS policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM hx-data-production.commercial_finance.insurance_policies_new
WHERE transaction_date BETWEEN '2026-03-02' AND '2026-03-09' AND distribution_channel='Aggregator' AND policy_type='Single'
```

### Aggregator Annual Policy Margin Squeeze `RECURRING`
Aggregator annuals ran negative margin again (-£7.2k this week) as planned, on higher volumes. This adds to our future renewal pool, not short-term profit.

```sql-dig
SELECT SUM(policy_count) AS policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM hx-data-production.commercial_finance.insurance_policies_new
WHERE transaction_date BETWEEN '2026-03-02' AND '2026-03-09' AND distribution_channel='Aggregator' AND policy_type='Annual'
```

### Conversion Rate Drop: Computer Device `NEW`
Search-to-book rate on computers dropped from 38% to 30%, costing ~£830 in GP this week. Losses are mostly in higher-value policies, with the worst drop-off at add-ons and medical steps.

```sql-dig
SELECT page_type, COUNT(DISTINCT session_id)
FROM hx-data-production.commercial_finance.insurance_policies_new
WHERE transaction_date BETWEEN '2026-03-02' AND '2026-03-09' AND device_type='computer'
GROUP BY page_type
```

### Europe Destination GP Decline `RECURRING`
GP from Europe fell £4k YoY (now £110k, down 4%) as average GP/policy slipped to £21 from £23, despite 9% more sales. It’s the 6th straight week of city-break, bargain cover dominating the mix.

```sql-dig
SELECT SUM(policy_count) AS policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM hx-data-production.commercial_finance.insurance_policies_new
WHERE transaction_date BETWEEN '2026-03-02' AND '2026-03-09' AND destination_group='Europe'
```

---

## Customer Search Intent

Demand for travel insurance on Google is up 74% vs last year, with “travel insurance” searches at a record high (index 11 vs 7 LY). Cheap flights (+129%) and package holidays (+33%) are pulling in bargain-hunters; Spain, Turkey, and the Canaries are the top trending spots. People are researching earlier and comparing more before buying.

---

## News & Market Context

Cheap fares from easyJet, Jet2, and Ryanair drove record travel search volumes and 25 million extra seats. MoneySupermarket and other aggregators are locked in a price war: that’s why single-trip margins everywhere are under pressure. No major travel chaos this week; Saga is extending Middle East cover, and most big names are sweetening claims or price-matching—keep alert for new scheme launches.

---

## Actions

| Priority | What to do                                                                     | Why (from the data)                                                  | Worth      |
|----------|-------------------------------------------------------------------------------|----------------------------------------------------------------------|------------|
| 1        | Shift Google and aggregator ads/landing pages to push higher cover tiers & upgrades (Gold/Silver) | Tackles margin drag from bargain policies in price-sensitive segments | ~£1.2k/wk  |
| 2        | Tune aggregator commission deals for 'Classic' single products                | Margin collapsed as base price fell and commission stayed high        | ~£670/wk   |
| 3        | Simplify desktop quote funnel/add-ons, focus especially on medical steps       | Computer conversion slide costing us £830 this week                   | ~£830/wk   |
| 4        | Push cross-sell (parking, medical, annual) at checkout, Spain/Turkey focus     | High-intent, volume spike in these destinations, untapped upsell      | ~£500/wk   |
| 5        | Keep pushing annuals (direct + aggregator) to lock in renewal base             | Growing renewals pool matters most for future margin                  | Strategic  |

---

_Generated 10:12 10 Mar 2026 | 22 investigation tracks | GPT-4_

---
*Generated 16:11 10 Mar 2026 | Tracks: 22 + Follow-ups: 35 | Model: gpt-4.1*
