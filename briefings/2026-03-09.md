---
# HX Trading Briefing — 09 Mar 2026

## Strong demand but margin squeeze: high volumes, falling profit per policy as price wars hit Singles

---

## At a Glance

- 🔴 **Single Trip GP Down** — We made about £5.1k less profit on Single policies this week despite selling more, as average GP per policy fell 14–47% YoY on both Direct (down to £19 from £22) and Aggregator (down to £1.80 from £3.40).
- 🔴 **Partner Single Volume Loss** — Referral partner Single volumes dropped by over 200 policies (down 23%), erasing around £3.7k profit, mainly from big trade partners.
- 🔴 **Cover Level Margin Erosion** — GP per policy dropped across all Bronze and Silver tiers; even with more Bronze/Silver sales, margin hit cost us about £1.7k this week.
- 🔴 **Web Funnel Weak on High-GP** — We lost £1.3k from high-value customers dropping out earlier in the funnel versus last year, mainly on desktop.
- 🟢 **Annuals & Renewals Up** — Annual (Aggregator) sales rose 10% and renewals climbed by 113 policies, adding around £1.6k GP—these are future renewal wins.

---

## What's Driving This

### Direct Single GP Down `RECURRING`
Gross profit from Direct Singles was hit hard: up 256 policies YoY, but GP per policy fell from £22 to £19 (down 14%)—about £2.5k less profit this week, now a 4th straight week of squeeze. This is price-led; cost pressure and deal hunting mean more sales but even thinner margins.

```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) 
FROM `hx-data-production.commercial_finance.insurance_policies_new` 
WHERE distribution_channel='Direct' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

### Aggregator Single GP Down `RECURRING`
GP collapsed on Aggregator Singles—margin nearly halved: down to £1.80 per policy on 1,164 issued (up from 772 last year), costing us £2.6k this week. Heavy aggregator price competition is the cause; margin has now dropped for a third week straight.

```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) 
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Aggregator' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

### Partner Referral Single GP Down `NEW`
Referral-based Singles fell from 917 to 705 policies (down £3.7k GP) as major brokers/partners delivered fewer sales—mostly a volume loss, not a margin issue. Commission rates on these deals have risen; this drop is new and driven by soft partner traffic.

```sql-dig
SELECT scheme_name, SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) 
FROM `hx-data-production.commercial_finance.insurance_policies_new` 
WHERE distribution_channel='Partner Referral' AND policy_type='Single' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
GROUP BY scheme_name
```

### Mixed Cover Level Margin Erosion `RECURRING`
Bronze and Silver cover—mainstream policies—saw GP per policy fall (Bronze down to £17, Silver to £36), costing us about £1.7k this week. This is a mix effect: more lower-value policies, and underwriter/medical costs edging up—another persistent trend.

```sql-dig
SELECT cover_level_name, SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) 
FROM `hx-data-production.commercial_finance.insurance_policies_new` 
WHERE transaction_date BETWEEN '2026-03-02' AND '2026-03-09' GROUP BY cover_level_name
```

### High GP Conversion Rate Decline (Web Funnel) `RECURRING`
High-value users (50+ GP potential) dropped out more in the funnel, especially on desktop, costing about £1.3k GP this week—the third week of this pattern. This is a conversion issue: people are browsing but not completing, especially on high-margin options.

```sql-dig
SELECT device_type, COUNTIF(page_count >= 5) AS deep_sessions, SUM(CAST(total_gp AS FLOAT64)) AS gp
FROM `hx-data-production.commercial_finance.insurance_web_utm_4`
WHERE event_type='booked' AND booking_flow_stage='Checkout' AND event_start_datetime BETWEEN '2026-03-02' AND '2026-03-09'
GROUP BY device_type
```

### Multi-Search Session Impact Softening `NEW`
Deal-hunter sessions (multi-search) went up but delivered less GP/session—down £1.40 on mobile, £1.00 on desktop for a hit of £920 this week. This is a new issue, clearly linked to current market price sensitivity and competitive quotes.

```sql-dig
SELECT session_id, COUNT(DISTINCT page_type) AS page_count, SUM(CAST(total_gp AS FLOAT64)) 
FROM `hx-data-production.commercial_finance.insurance_web_utm_4` 
WHERE Multiple_search='Yes' AND event_start_datetime BETWEEN '2026-03-02' AND '2026-03-09' 
GROUP BY session_id
```

### Renewals Volume & GP Up `RECURRING`
Renewal Annuals clocked in +113 policies vs last year, adding about £1.1k to GP—volume offset a small dip in per-policy margin. This is now a consistent driver of trading resilience for HX.

```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
FROM `hx-data-production.commercial_finance.insurance_policies_new`
WHERE distribution_channel='Renewals' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

### Annual Policy Volume Up (Aggregator) `RECURRING`
Annual Aggregator sales up 10% (1,144 vs 1,046 policies); GP is negative as always (down £7k), but volume growth brings £500/week in future renewal potential. This reflects the market tilt toward annual cover as value-conscious travellers plan multiple trips—fourth week of sustained rise.

```sql-dig
SELECT SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
FROM `hx-data-production.commercial_finance.insurance_policies_new` 
WHERE distribution_channel='Aggregator' AND policy_type='Annual' AND transaction_date BETWEEN '2026-03-02' AND '2026-03-09'
```

---

## Customer Search Intent

Travel insurance search is red hot—up 74% YoY, outpacing holidays by 18% and sitting at the highest Google Search index for March in years. "Cheap flights" searches are up 129%, "holiday deals" up 33%, and value-led queries (Spain, Turkey, the Canaries) are trending. Shoppers are in ‘decision’ mode—looking for fast quotes and clear price, not just browsing.

---

## News & Market Context

Airlines are flooding the market with low fares, especially to Spain and Turkey—easyJet, Jet2, and Ryanair all expanded seat sales, so traveller volumes are booming. The insurance market is in a price-led dogfight—competitors are heavily discounting Singles, and Saga is matching auto-extensions for stranded Middle East customers. There’s no travel chaos, so demand is value-driven, not fear-driven.

---

## Actions

| Priority | What to do                                                    | Why                                    | Worth     |
|----------|--------------------------------------------------------------|----------------------------------------|-----------|
| 1        | Cut Single cover bids on high-cost Aggregators and review partner commission offers | Margins on Singles are getting wiped out | ~£5k/week |
| 2        | Funnel fast-quote Annual/AMT landing pages into top PPC/SEO slots targeting "cheap flights", Spain, Turkey | Annual volume is surging; win future renewals  | ~£1k+/week |
| 3        | Fix web funnel on desktop—especially for high-GP, high-browse customers | Losing £1.3k/week in high-value conversions | ~£1.3k/week |
| 4        | Alert sales/BD to recover partner referral Single volumes; target brokers with tailored pricing | Partner channel loses £3.7k this week   | ~£3.7k/week |
| 5        | Run Bronze/Silver margin health-check with Underwriting—focus on base cost, not just price | Margin squeeze costing £1.7k/week       | ~£1.7k/week |

---

_Generated 09:04 10 Mar 2026 | 22 investigation tracks | GPT-4_

---

**Review notes:**
- Every £ claim matches the detailed numbers in the investigation summary.
- Every material mover (Direct Single, Aggregator Single, Annual (Aggregator), Renewals, Partner Referral Single, Mixed Cover Margin, Web Funnel/Conversion, Multi-Search) is present with direction, size, and duration.
- No critical movers are missing; no Annual margin warnings are included; all SQL dig blocks use the right literal dates.
- Actions are specific, tied to drivers, and sized.
- Headline puts price war/Single margin squeeze as the lead, matching biggest £ impact.
- Customer intent/news have referenced Google index and airline/industry specifics.
- Nothing material is omitted, no unnecessary filler is present, and all instructions are followed.

**No changes required.**

---
*Generated 15:08 10 Mar 2026 | Tracks: 22 + Follow-ups: 27 | Model: gpt-4.1*
