# Insurance Platforms and Partners

## Fire Melon (Booking Platform)

Fire Melon is the booking platform that powers HX insurance. The product is called **Magenta**. Fire Melon handles the end-to-end insurance booking flow — quote generation, payment processing, policy issuance. HX is launching the "Essential Travel" budget brand entirely through Fire Melon's tech stack as a test of their full capabilities.

## The Idol (Aggregator Platform)

The idol is the platform that serves the three main insurance aggregators:
- **Compare the Market** (CTM) — vast majority of aggregator volume. CTM does all its own tech.
- **Confused.com** — handles payment through idol
- **GoCompare** — everything handled by idol

Because CTM handles its own tech independently, platform changes at CTM can cause data quality issues that don't affect the other two.

## Wizard (Future Booking Flow)

The Wizard is a new AI-driven booking interface being prototyped by Matthew. Instead of a traditional search form, it shows customers only the options they're most likely to want next based on their selections. For example, if someone clicks "Annual", the wizard might show "Europe Excluding" as the most likely next choice. Currently a prototype — not covering all customer scenarios yet.

## White-Label Partner CTAs

HX provides white-label insurance platforms on partner websites. When a customer moves from a partner site (e.g., Carnival/P&O cruise booking) to the HX insurance flow, that's a "CTA" (call-to-action click-through). Key CTA integration points:
- **Online check-in** — 60% of cruise insurance volume comes from this CTA
- **Booking confirmation** — post-booking insurance offer
- **My account** — insurance upsell in partner account areas

Partners with white-label: Carnival (P&O, Princess, Cunard), Fred Olsen, specialist cruise partners.

## Underwriters

- **ERGO** — primary underwriter for HX insurance products
- **Collinson** — provides flight delay registration/data. Monthly file (working towards weekly). Customers register flight details on Collinson white-label, data sent back to HX with lag.

## WorldPay (Payment Processing)

Payment processor for insurance. Start purchase conversion in insurance is 90-92% (below the 98% target for the wider business). Issues with:
- Recurring MIDs (for renewal token payments)
- Expired payment tokens
- SCA (Strong Customer Authentication) challenges — no exemptions currently in insurance
- Moving to "Dragon Payment" being explored to enable SCA exemptions
