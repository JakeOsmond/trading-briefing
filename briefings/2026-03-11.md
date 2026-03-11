---
# HX Trading Briefing — 10 Mar 2026

## Single trip profit keeps falling as cost squeeze bites, but annual renewals grow — week ending 10 Mar 2026 vs last year

---

## At a Glance

- 🔴 **Direct Annual GP** — GP dropped £6.2k over the last 7 days (down 12% YoY); margin now 32%, same number of policies, but costs and mix have eaten into profit.
- 🔴 **Partner Referral Single Trip GP** — GP fell £6.1k (down 28% YoY), all from a 27% drop in policy volume — the partner pipeline dried up, not a margin issue.
- 🔴 **Direct Single Trip GP** — GP slumped £3.8k (down 9% YoY); we sold 8% more policies but made nearly 16% less on each one as costs and mix went south.
- 🔴 **Aggregator Single Trip GP** — GP down £600 (25% off YoY); policies soared 43%, but average profit per policy halved as aggregator discounting hammered prices.
- 🟢 **Renewal Annual GP** — GP up £1.4k (3% lift YoY), with policy volume up 12% — classic renewal flywheel: more volume more future GP.

---

## What's Driving This

### Direct Annual GP `RECURRING`
GP is down £6.2k YoY (from £54k to £47.8k, -11.5%) over the last 7 days, with policy count flat at 964; margin squeezed from 36.5% to 32% due to higher underwriter costs (£26.40 → £30.30 per policy) and a shift toward lower-tier (Bronze/Classic) plans. No real traffic movement — it's pure cost inflation and cover-level drift. 
```sql-dig
SELECT SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp, SUM(policy_count) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Direct' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

### Partner Referral Single Trip GP `RECURRING`
GP dropped £6.1k YoY (down 28%), falling to £15.5k; volume cratered (policies -27%, 709 down from 972), but margin and commission % held steady. The hit is 100% lack of partner-driven traffic — nothing changed in pricing or margin.
```sql-dig
SELECT SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp, SUM(policy_count) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Partner Referral' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

### Direct Single Trip GP `RECURRING`
GP fell £3.8k YoY (to £38.7k, -8.9%); volume grew (+8.2%), but GP per policy dived from £22 to £18 (-16%). No movement in computer/mobile sessions but session-to-search conversion was down; improved mobile search-to-book rates offset a bit, but higher underwriter costs and more Bronze/Classic buyers squeezed margin hard (down to 31.5% from 37.8% LY).
```sql-dig
SELECT SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)), SUM(policy_count) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Direct' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

### Aggregator Single Trip GP `RECURRING`
GP down £600 (to £1.8k, -25% YoY); policy volume rose 43% but profit per policy imploded (£3.27 → £1.70). Price fell 23% as the aggregator market went into a price war, and margin on these sales is just 5% (from 7.4% LY); commission unchanged at 30%.
```sql-dig
SELECT SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)), SUM(policy_count) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Aggregator' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

### Renewal Annual GP `RECURRING`
GP grew £1.4k YoY (to £53.8k, up 2.8%); policy volume up 12% (1,301 vs 1,167), but average GP per renewal fell from £44.84 to £41.33, mostly from slight price and discounting shifts. This is what we want — investing in compounding renewal value, even as margins soften a bit.
```sql-dig
SELECT SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)), SUM(policy_count) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Renewals' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

### Partner Referral Annual GP `EMERGING`
GP up £1.1k YoY (now £10k, +12%); policy volume saw a small lift, no margin or commission moves. No profit risk — positive, if small.
```sql-dig
SELECT SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)), SUM(policy_count) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Partner Referral' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

### Direct Single Trip Volume `RECURRING`
Sold 2,091 direct single trip policies over the last week, up 158 on last year (+8% YoY) — nearly all these extra sales landed in low-GP plans, so they didn’t help profit much.
```sql-dig
SELECT SUM(policy_count) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Direct' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

### Aggregator Annual GP (Strategic, Still Loss-Making) `RECURRING`
Annual Aggregator GP is still negative (-£6.2k for the week), but that loss shrank by £1.1k YoY; volume steady, margin modestly better. This is deliberate — building the renewal book.
```sql-dig
SELECT SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)), SUM(policy_count) FROM `hx-data-production.commercial_finance.insurance_policies_new` WHERE distribution_channel='Aggregator' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-03' AND '2026-03-10'
```

---

## Customer Search Intent

Travel insurance search intent is extremely strong: insurance searches are up 57–74% YoY, versus holiday searches at +33–50% YoY. Demand is skewed towards annual, medical, and cancellation products, with Spain, Greece, and Italy showing the sharpest uptick as EU entry rules and medical cover questions push buyers to act. The Google Trends insurance/holiday gap is now +3 index points (was +1 last year), showing real buying signals. Most volume is being driven by earlier Easter bookings, flight sale bargain-hunters, and people worried about overseas hospital bills.  
**Source:** [Google Sheets — Insurance Intent tab](#) / [Google Trends](https://trends.google.com/trends/explore?date=today%205-y&q=travel%20insurance)

---

## News & Market Context

Strong travel demand is being driven by early Easter, major European flight releases (easyJet, Ryanair, Jet2), and extra urgency thanks to new EU border checks. Aggregator competition is fierce — discounting and new PPC campaigns are pushing prices down, confirmed by high aggregator traffic and thinner margins. BA’s continued Middle East flight suspensions keep medical/cancellation demand high ([BA update](https://uk.news.yahoo.com/british-airways-issues-today-flights-130432343.html)), and Google search terms show rising customer anxiety (“do I need travel insurance for Spain/USA?”). Competitors are targeting annual and medical products with aggressive pricing and paid ad spend. Regulatory landscape unchanged, but wider economic uncertainty (exchange rates, weather swings, global headlines) is feeding into both margin pressure and mix changes.  
**Source:** AI Insights — “trend”, “news”, “channels.”

---

## Actions

| Priority | What to do                                                          | Why (from the data)                                 | Worth     |
|----------|---------------------------------------------------------------------|-----------------------------------------------------|-----------|
| 1        | Review/tighten Direct Annual & Single Trip UW cost controls, cut deep discounts | Margin is dropping fast from higher UW cost and over-discounting | ~£9k/wk   |
| 2        | Double PPC on annual/medical keywords, especially Spain/Greece      | Surge in intent and competitor spend, opportunity to win LTV   | Future value |
| 3        | Push aggregator partners to cut commission, try value-based pricing | Aggregator single trip margin collapse from price war | ~£1k/wk   |
| 4        | Find & fix blockages in Partner Referral channel                   | Lost £6k GP due to volume shortfall — partner pipeline broke   | ~£6k/wk   |

---

_Generated 07:55 11 Mar 2026 | 22 investigation tracks | GPT-4_


---
*Generated 16:42 11 Mar 2026 | Tracks: 22 + Follow-ups: 32 | Model: gpt-4.1*
