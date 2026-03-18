# Trading Covered — Context Index

_This folder contains all business knowledge used by Trading Covered. The pipeline reads this index and loads relevant context files at runtime._

_When creating a new domain (e.g. parking, hotels), copy this folder structure. Keep `universal/` as-is, replace `insurance/` with your domain, and update `operational/`._

---

## Universal (domain-agnostic)

These apply to any HX trading product. Do not modify per domain.

| File | What it covers |
|------|---------------|
| [hx-group-structure.md](universal/hx-group-structure.md) | Group BU structure, how Insurance/Distribution/Europe/Adventures relate |
| [trading-framework.md](universal/trading-framework.md) | Traffic x Conversion x GP equation, how to decompose any movement |
| [financial-waterfall.md](universal/financial-waterfall.md) | Full Price → GP waterfall (discount, supplier cost, VAT, commission, PPC) |
| [yoy-methodology.md](universal/yoy-methodology.md) | 364-day offset, COVID structural breaks, calendar effects |
| [metrics-guide.md](universal/metrics-guide.md) | How to talk about GP, volume, average GP, conversion, mix, persistence |
| [financial-year.md](universal/financial-year.md) | FYTD definition, FY naming, forecasting cycle (BGT, F1, F2, F3) |
| [reporting-conventions.md](universal/reporting-conventions.md) | Standard abbreviations: TY/LY/BGT/Fcast, GP/GM/MAV/CpB, BU codes |
| [transaction-mechanics.md](universal/transaction-mechanics.md) | Book date vs stay date, revenue recognition, booked GP vs stay GP, cancellations |
| [travel-events.md](universal/travel-events.md) | External event categories, YoY comparison rules, ancillary booking delay theory |

## Insurance (domain-specific)

These are specific to the insurance trading domain. Replace entirely for other products.

| File | What it covers |
|------|---------------|
| [policy-economics.md](insurance/policy-economics.md) | Annual vs single strategy, negative margins, renewal payoff |
| [channels.md](insurance/channels.md) | Direct, Aggregator, Partner Referral, Renewals — economics and data |
| [pricing-margin.md](insurance/pricing-margin.md) | GP definition, price decomposition, discount rate, cover levels, add-ons |
| [renewal-rates.md](insurance/renewal-rates.md) | Blended renewal rate calculation, SQL methodology |
| [data-quirks.md](insurance/data-quirks.md) | Policy counting (SUM not COUNT), BIGNUMERIC casting, web table joins |
| [drill-dimensions.md](insurance/drill-dimensions.md) | Column names for channel, cover level, device, medical, booking source |
| [funnel-stages.md](insurance/funnel-stages.md) | 9-stage customer journey from Landing to Just Booked |
| [aggregator-position.md](insurance/aggregator-position.md) | Aggregator economics, commission, data limitations |
| [schema-knowledge.md](insurance/schema-knowledge.md) | BigQuery table schemas, column definitions, SQL rules (authoritative source for ask.js) |
| [platforms-and-partners.md](insurance/platforms-and-partners.md) | Fire Melon/Magenta, idol/aggregators, Wizard, white-label CTAs, ERGO, Collinson, WorldPay |

## Operational (partially transferable)

Update per deployment. Some items are universal, some are domain-specific.

| File | What it covers |
|------|---------------|
| [market-intelligence.md](operational/market-intelligence.md) | Google Trends, AI Insights sheet, Spike Log, Drive docs |
| [current-market-events.md](operational/current-market-events.md) | **Review weekly** — Iran conflict impact, cruise partner dynamics, pricing changes, PPC status, partner pipeline |
