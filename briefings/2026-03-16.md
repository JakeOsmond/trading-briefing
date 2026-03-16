---
# HX Trading Briefing — 15 Mar 2026

## GP slipped over the last 7 days vs the same week last year, down £25k or 15%, and the biggest hit was direct single-trip where we under-captured healthy market demand and made less on each sale.

---

## At a Glance

- 🔴 **Overall GP** — Over the last 7 days vs the same week last year, GP was £140k — down £25k, about 15% worse, with policies down 264 or 4% and GP per policy down from £24 to £21.
- 🔴 **Direct single-trip** — Over the last 7 days vs the same week last year, direct single-trip GP fell £12k, about 28% worse, because fewer web visitors got to search and we made less on each sale.
- 🔴 **Europe weakness** — Over the last 7 days vs the same week last year, Europe GP fell £19k, about 17% worse, with most of the damage coming from lower GP per policy, down from £23 to £20.
- 🔴 **Existing direct customers** — Over the last 7 days vs the same week last year, existing direct customer GP fell £17k, about 24% worse, because fewer repeat visitors reached search and bought.
- 🟡 **Annual acquisition softer** — Over the last 7 days vs the same week last year, annual policy volume fell 176 or 6%; that is missed future renewal income, not a margin problem.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct single-trip GP fell £12k to £31k, down 28%, and this is the clearest problem in the pack. Traffic was mixed, with desktop sessions up 25% but mobile sessions down 3%, while conversion into search fell hard on both mobile, from 20% to 16%, and desktop, from 15% to 13%; this has been negative on 8 of the last 10 days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single'
GROUP BY 1,2,3;
```

### Partner Referral Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, partner referral single-trip GP fell £7k to £13k, down 33%, and the loss was mostly volume-led. We cannot see the full web funnel here, but policies dropped 28% while average GP per policy only slipped from £22 to £20, so this looks mainly like weaker referred traffic; this has been negative on 8 of the last 10 days.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp,
  SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_commission
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single'
GROUP BY 1,2,3;
```

### Europe destination GP decline `EMERGING`

Over the last 7 days vs the same week last year, Europe GP fell £19k to £90k, down 17%, and the bigger issue was weaker value per sale, with GP per policy down from £23 to £20. The data suggests direct single-trip Europe journeys are where we are missing demand, with lower search capture and cheaper, more price-shopped mix.

```sql-dig
SELECT
  destination_group,
  policy_type,
  distribution_channel,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND destination_group = 'Europe'
GROUP BY 1,2,3;
```

### Existing Direct customers GP decline `EMERGING`

Over the last 7 days vs the same week last year, existing direct customer GP fell £17k to £55k, down 24%, with policies down 17%. This looks like an upper-funnel problem: existing-customer sessions were down 6% and session-to-search fell from 23% to 19%, so fewer repeat customers even got to a price.

```sql-dig
SELECT
  customer_type,
  booking_source,
  policy_type,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Direct'
  AND customer_type = 'Existing'
GROUP BY 1,2,3;
```

### Bronze Main Single Med HX decline `RECURRING`

Over the last 7 days vs the same week last year, Bronze Main Single Med HX lost £5k of GP even though volume was only down 2%, so this was mainly a value problem, not a traffic collapse. Average GP per policy fell from £16 to £11, with web doing most of the damage, which lines up with the wider direct single-trip margin squeeze.

```sql-dig
SELECT
  scheme_name,
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND scheme_name = 'Bronze Main Single Med HX'
GROUP BY 1,2;
```

### Silver Main Single Med HX decline `RECURRING`

Over the last 7 days vs the same week last year, Silver Main Single Med HX lost £5k of GP, with policies down 20% and average GP per policy down from £25 to £20. That means both traffic capture and value per sale got worse, making this another important part of the direct single-trip problem.

```sql-dig
SELECT
  scheme_name,
  booking_source,
  max_medical_score_grouped,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND scheme_name = 'Silver Main Single Med HX'
GROUP BY 1,2,3;
```

### Direct Annual volume softness `NEW`

Over the last 7 days vs the same week last year, direct annual GP fell £6k to £41k because policies dropped 13%, not because the economics broke. This is missed acquisition while demand is up, so the priority is to win back annual volume and invest in future renewal income.

```sql-dig
SELECT
  distribution_channel,
  policy_type,
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Annual'
GROUP BY 1,2,3;
```

### Silver Main Annual Med HX decline `NEW`

Over the last 7 days vs the same week last year, Silver Main Annual Med HX was down £6k to £13k, mostly because volume fell 28%. This matters because we are missing future renewal income, and the weakness looks web-led rather than a pricing issue.

```sql-dig
SELECT
  scheme_name,
  booking_source,
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND scheme_name = 'Silver Main Annual Med HX'
GROUP BY 1,2;
```

---

## Customer Search Intent

According to Google Sheets Dashboard Metrics, over the last 7 days vs the same week last year, overall travel insurance demand is up 65%, insurance searches are up 74%, and holiday searches are up 53%. According to Google Sheets Insurance Intent and AI Insights, customers are shopping around harder: “travel insurance comparison” is up 375% and “do I need travel insurance” is up 31%. According to Dashboard Metrics, insurance search interest is now 11.5 vs 6.6 last year, so the market is bigger and more comparison-led at the same time. According to AI Insights, Spain, Turkey and Greece terms are strong, which fits the pressure we are seeing in Europe where demand is there but we are not capturing enough of it. According to AI Insights seasonal notes, early Easter planning and Mother’s Day short-break buying should keep intent firm through late March. **Source:** Google Sheets — Insurance Intent tab; **Source:** Google Sheets — Dashboard Metrics tab; **Source:** AI Insights — what_matters, divergence, seasonal.

---

## News & Market Context

According to [Jet2’s Summer 2026 programme update](https://www.jet2.com/news/2024/09/Jet2_com_and_Jet2holidays_launch_biggest_ever_Summer_programme_for_2026), Jet2 is adding nearly 900,000 seats and opening a new Gatwick base, which should support demand for Europe and annual cover. According to AI Insights — deep_dive, easyJet and TUI are also adding capacity into Italy, Portugal, Spain and Florida, so the market backdrop is supportive rather than weak. According to [ITIJ](https://www.itij.com/latest/news/millions-uk-ehicghic-cards-set-expire-2025-raising-insurance-concerns), millions of EHIC and GHIC cards are expiring and the NHS is reminding travellers they do not replace travel insurance, which should help simple explainer content and comparison searches. According to the [FCA review of travel insurance signposting rules](https://www.fca.org.uk/publications/multi-firm-reviews/travel-insurance-signposting-rules-consumers-medical-conditions-review), the rules changed from 1 January 2026, which keeps medical journeys and clarity important. Internal change logs show landing page, promo and rebuild changes over the last 30 days, so some of this looks HX-made, not market-made. **Source:** Internal — Landing Page Changes 13th Feb 2026; **Source:** Internal — Insurance Promotion Across HX Sessions Feb 2026; **Source:** Internal — Insurance Rebuild Notes.

---

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Audit all direct single-trip web changes made since 13 Feb, starting with mobile search-entry, gatekeeper and search page progression | Over the last 7 days vs the same week last year, direct single-trip lost about £12k/week and mobile session-to-search fell from 20% to 16% | ~£12k/week |
| 2 | Reprice or tighten underwriting on Bronze Main Single Med HX and Silver Main Single Med HX for web single-trip journeys, especially Europe | Over the last 7 days vs the same week last year, those two schemes lost about £11k/week combined and average GP per policy fell sharply | ~£11k/week |
| 3 | Review cruise partner volumes and commercial terms with the biggest partner referrers | Over the last 7 days vs the same week last year, partner referral single-trip lost about £7k/week and cruise schemes were the biggest hole | ~£7k/week |
| 4 | Fix repeat-customer journeys and CRM sends into quote for direct web | Over the last 7 days vs the same week last year, existing direct customers lost about £17k/week and session-to-search fell from 23% to 19% | ~£17k/week |
| 5 | Shift more PPC, SEO and on-site traffic to direct annual quote pages | Over the last 7 days vs the same week last year, direct annual volume was down 13%, which is missed future renewal income while market demand is up | ~£6k/week |

---

_Generated 10:00 16 Mar 2026 | 23 investigation tracks | gpt-5_

---
*Generated 16:06 16 Mar 2026 | Tracks: 23 + Follow-ups: 31 | Model: gpt-5.4*
