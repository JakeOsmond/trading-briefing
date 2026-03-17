# Trading Covered — Context Index

_This folder contains all business knowledge used by Trading Covered. The pipeline reads this index and loads relevant context files at runtime._

_When creating a new domain (e.g. parking, hotels), copy this folder structure. Keep `universal/` as-is, replace `insurance/` with your domain, and update `operational/`._

---

## Universal (domain-agnostic)

These apply to any HX trading product. Do not modify per domain.

| File | What it covers |
|------|---------------|
| [trading-framework.md](universal/trading-framework.md) | Traffic x Conversion x GP equation, how to decompose any movement |
| [yoy-methodology.md](universal/yoy-methodology.md) | 364-day offset, COVID structural breaks, date handling rules |
| [metrics-guide.md](universal/metrics-guide.md) | How to talk about GP, volume, average GP, conversion, mix, persistence |
| [financial-year.md](universal/financial-year.md) | FYTD definition (1 April – 31 March) |

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

## Operational (partially transferable)

Update per deployment. Some items are universal, some are domain-specific.

| File | What it covers |
|------|---------------|
| [market-intelligence.md](operational/market-intelligence.md) | Google Trends, AI Insights sheet, Spike Log, Drive docs |
