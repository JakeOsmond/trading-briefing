---
# HX Trading Briefing — 15 Mar 2026

## Over the last 7 days vs the same week last year, GP was down about £25k and the biggest hit came from Europe and direct single-trip, even though market demand stayed strong.

---

## At a Glance

- 🔴 **Weekly GP down** — Over the last 7 days vs the same week last year, GP was about £140k — down about £25k, roughly 15% worse, as we sold about 260 fewer policies and made about £3 less on each one.
- 🔴 **Europe hurt most** — Over the last 7 days vs the same week last year, Europe GP was down about £19k, roughly 17% worse, with policy volume down only 4%, so the bigger problem was weaker value per sale.
- 🔴 **Direct single slipped** — Over the last 7 days vs the same week last year, direct single-trip GP was down about £12k, mostly because fewer visitors reached a quote and average GP fell about 21%.
- 🔴 **Warm direct traffic weak** — Over the last 7 days vs the same week last year, direct existing-customer GP was down about £17k and Direct Mailings GP was down about £12k, showing our known-user traffic is not getting to price often enough.
- 🟢 **Renewals helped** — Over the last 7 days vs the same week last year, renewal GP was up about £600 as better retention offset a smaller expiry base.

---

## What's Driving This

### Direct Single GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct single-trip GP fell about £12k to about £31k. Traffic was mixed, with mobile sessions down 3% and desktop sessions up 25%, but conversion was the bigger issue as mobile session-to-search fell to 16% from 20% and desktop fell to 13% from 15%, while average GP dropped to about £17 from £22.  
The data shows this is a real HX problem, not weak demand. Underwriter costs took a bigger share, price was flat to down, and this has been negative on 9 of the last 10 days.

```sql-dig
SELECT
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Direct'
  AND policy_type = 'Single';
```

### Europe destination mix deterioration `RECURRING`

Over the last 7 days vs the same week last year, Europe GP fell about £19k to about £90k. Policy volume was down only 4%, so most of the damage came from average GP falling to about £20 from £23, with lower-value single-trip and lower-tier cover mix doing the damage.  
Traffic and demand outside HX look healthy, so this points to weaker capture and monetisation on our side. This has been negative on 8 of the last 10 days.

```sql-dig
SELECT
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND destination_group = 'Europe';
```

### Direct existing-customer GP decline `RECURRING`

Over the last 7 days vs the same week last year, direct GP from existing customers fell about £17k to about £55k. Existing-user sessions were down 6% and session-to-search fell to 19% from 23%, so fewer known users are getting far enough to see a price.  
The miss is mainly web-led, not phone-led, and this has been down on 10 of the last 10 days. That points to a persistent issue in the warm-traffic journey rather than a one-off demand wobble.

```sql-dig
SELECT
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Direct'
  AND customer_type = 'Existing';
```

### Direct Mailings GP decline `RECURRING`

Over the last 7 days vs the same week last year, Direct Mailings GP fell about £12k to about £20k, with policies down 34%. This looks mainly traffic-led in a source that normally converts efficiently.  
The likely cause is CRM cadence or landing-page quality rather than market demand, and it has been down on 9 of the last 10 days. That makes this a persistent warm-traffic problem, not just a soft week.

```sql-dig
SELECT
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND insurance_group = 'Direct Mailings';
```

### Bronze cover level GP decline `RECURRING`

Over the last 7 days vs the same week last year, Bronze GP fell about £8k to about £27k. Volume was down only 5%, but average GP fell to about £16 from £20, so we are still selling Bronze but making much less on each sale.  
This looks tied to lower-value single-trip mix, especially in Europe and mobile journeys, and it has been down on 7 of the last 10 days. The problem is value capture more than demand.

```sql-dig
SELECT
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND cover_level_name = 'Bronze';
```

### Partner Referral Single volume and margin decline `EMERGING`

Over the last 7 days vs the same week last year, partner referral single-trip GP fell about £7k to about £13k. Policies were down 28% and average GP slipped 7%, so both traffic and value per sale worked against us.  
This may be partner mix rather than broad market weakness, with too much lower-value volume and not enough richer medical or cruise business. It is worth acting on, but confidence is lower than the direct-channel issues.

```sql-dig
SELECT
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Partner Referral'
  AND policy_type = 'Single';
```

### Silver Main Annual Med HX scheme decline `NEW`

Over the last 7 days vs the same week last year, this annual scheme lost about £6k of GP and about 110 policies. That volume drop matters because annual sales are future renewals, so this means we are investing less in future renewal income.  
This looks mostly web-led and may be a share-capture issue rather than weak demand. It is too early to call this structural, but we should not ignore it.

```sql-dig
SELECT
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND scheme_name = 'Silver Main Annual Med HX';
```

### Renewals GP improvement `NEW`

Over the last 7 days vs the same week last year, renewals GP was up about £600 to about £49k. The expiry base was down 17%, but retention improved enough to lift renewed policies by 9%.  
This is good news and shows the renewal engine is holding up. Confidence is lower here, so treat it as encouraging rather than fully proven.

```sql-dig
SELECT
  SUM(policy_count) AS policies,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
  SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE transaction_date BETWEEN '2026-03-08' AND '2026-03-15'
  AND distribution_channel = 'Renewals'
  AND policy_type = 'Annual';
```

## Customer Search Intent

According to Google Sheets data, travel insurance search demand is up 74% over the last 7 days vs the same week last year, ahead of holiday searches up 53%, and overall market demand is up 65% YoY with 38% four-week momentum. According to AI Insights, “travel insurance comparison” is up 375% YoY and “do I need travel insurance” is up about 31%, which says shoppers are actively comparing and want clearer reassurance content. According to AI Insights, “book holiday 2026” is up 420% YoY, which fits annual multi-trip demand and tells us the market is there. According to Google Sheets — Insurance Intent tab, insurance search interest is stronger than holiday intent, so weaker HX trading looks like a capture and conversion problem rather than weak category demand.  
**Source:** Google Sheets — Dashboard Metrics tab. **Source:** Google Sheets — Insurance Intent tab. **Source:** AI Insights — what_matters, divergence, yoy.

## News & Market Context

According to [Jet2’s Summer 2026 programme announcement](https://www.jet2.com/news/2024/09/Jet2_com_and_Jet2holidays_launch_biggest_ever_Summer_programme_for_2026), Jet2 is adding seats to Spain, the Canaries, Algarve and Greece, which should support Europe and annual multi-trip demand. According to the [European Commission’s Entry/Exit System page](https://home-affairs.ec.europa.eu/policies/schengen-borders-and-visa/smart-borders/entry-exit-system_en), Europe’s Entry/Exit System is due by 10 April 2026, which may add uncertainty for travellers and lift demand for simple reassurance content. According to [ITIJ](https://www.itij.com/latest/news/millions-uk-ehicghic-cards-set-expire-2025-raising-insurance-concerns), the [NHSBSA](https://www.nhsbsa.nhs.uk/get-healthcare-cover-travelling-abroad/where-you-can-use-your-card), and [Compare the Market](https://www.comparethemarket.com/travel-insurance/content/ghic/), millions of EHIC and GHIC cards are expiring and GHIC still does not replace travel insurance, which keeps comparison and explainer searches relevant. According to the [FCA’s review of medical signposting rules](https://www.fca.org.uk/publications/multi-firm-reviews/travel-insurance-signposting-rules-consumers-medical-conditions-review), medical-cover clarity remains commercially important from 1 Jan 2026. Overall, the market backdrop looks supportive, so our weak week is more likely down to HX journey and value capture issues than external demand.  
**Source:** Jet2, European Commission, ITIJ, NHSBSA, Compare the Market, FCA.

## Actions

| Priority | What to do | Why (from the data) | Worth |
|----------|-----------|---------------------|-------|
| 1 | Audit and fix the direct web quote-start journey by device, starting with mobile and desktop landing-to-search steps for single trip | Over the last 7 days vs the same week last year, direct single lost about £12k and session-to-search fell from 20% to 16% on mobile and from 15% to 13% on desktop | ~£12k/week |
| 2 | Review and, if needed, roll back the warm-traffic landing-page and CRM journey changes affecting existing users and Direct Mailings | Over the last 7 days vs the same week last year, direct existing and Direct Mailings together lost about £29k and both weakened before quote | ~£29k/week |
| 3 | Rework Europe single-trip value capture by checking cover-level pricing, upsell path and quote presentation on lower-tier products | Over the last 7 days vs the same week last year, Europe lost about £19k with volume down only 4%, so the bigger issue is weaker value per sale | ~£19k/week |
| 4 | Review Bronze single-trip economics, especially Europe and mobile non-medical journeys where GP per sale is being squeezed | Over the last 7 days vs the same week last year, Bronze lost about £8k and average GP fell from about £20 to £16 | ~£8k/week |
| 5 | Meet partner managers to review partner-referral single mix, commission and source quality, especially lower-value partners | Over the last 7 days vs the same week last year, partner referral single lost about £7k as both policy count and average GP fell | ~£7k/week |

---

_Generated 00:00 16 Mar 2026 | 23 investigation tracks | gpt-5_

---
*Generated 12:26 16 Mar 2026 | Tracks: 23 + Follow-ups: 31 | Model: gpt-5.4*
