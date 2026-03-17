# Insurance Distribution Channels

HX sells through four distribution channels, each with different economics and data characteristics:

## Direct
- Customers come via our own website (holidayextras.com or staysure.co.uk etc.).
- Includes both "Direct - Standard" and "Direct - Medical" sub-channels.
- **Has full web journey data** — device type, page views, funnel stages, clicks, conversion at every step.
- Web data comes from the `insurance_web_utm_4` table and can be joined to policy data.
- Device split is roughly 50% mobile, 46% desktop, 3% tablet.

## Aggregator
- Sales through price comparison websites (GoCompare, CompareTheMarket, MoneySupermarket).
- Includes "Aggregator - Standard" and similar sub-channels.
- **No conventional web journey in our data** — we only see the policy transaction.
- Do NOT try to join web session data for aggregator policies — it does not exist.
- We pay commission to aggregators, which is a significant cost line.
- Annual policies via aggregators deliberately run at negative margin (see policy-economics.md).

## Partner Referral
- Sales via partners who refer customers to us (travel agents, airlines).
- Includes "Partner Referral - Medical" and similar.
- Similar to aggregators in that web journey data is limited.

## Renewals
- Existing annual policyholders renewing their cover.
- This is the payoff of the annual acquisition strategy — renewals are high-margin (no acquisition cost).
- **No web journey data** — renewals happen via auto-renew or direct contact.
- Key metrics: retention rate, auto-renew opt-in rate, renewal year cohorts.
- Do NOT try to join web session data for renewal policies.
