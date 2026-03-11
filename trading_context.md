# HX Trading Business Context

_This file is read automatically by Trading Covered. Edit it to add business knowledge that should inform the daily briefing. Anyone on the team can contribute via PR._

---

## Annual Policy Strategy

HX deliberately runs **negative margins on annual policies**, particularly via aggregators. This is a lifetime value acquisition strategy — we lose money on the first annual sale to build a renewal book that pays back over multiple years.

- Annual pricing is **always managed internally**. The briefing should never flag negative annual margins as a problem, concern, or action item.
- Annual volume growth is **always good news**. Frame it as: "We're investing in future renewal income."
- The focus should be on volume trends for annuals, not profitability per policy.

## Single Trip Policies

Single trip policies have **no renewal pathway**. Unlike annuals, there is no future income stream to offset an upfront loss.

- Single trip losses **are** problems worth flagging and investigating.
- When single trip GP falls, it matters — there is no second bite at the apple.
- The briefing should call out single trip margin erosion clearly and recommend action.

## Channel Context

HX sells through four distribution channels, each with different economics and data characteristics:

### Direct
- Customers come to us via our own website (holidayextras.com or staysure.co.uk etc.).
- Includes both "Direct - Standard" and "Direct - Medical" sub-channels.
- **Has full web journey data** — we can see device type, page views, funnel stages, clicks, and conversion at every step.
- Web data comes from the `insurance_web_utm_4` table and can be joined to policy data.
- Device split is roughly 50% mobile, 46% desktop, 3% tablet.

### Aggregator
- Sales through price comparison websites (e.g. GoCompare, CompareTheMarket, MoneySupermarket).
- Includes "Aggregator - Standard" and similar sub-channels.
- **No conventional web journey in our data** — we only see the policy transaction, not the customer's browsing behaviour on the comparison site.
- Do NOT try to join web session data for aggregator policies — it does not exist.
- We pay commission to aggregators, which is a significant cost line.
- Annual policies via aggregators deliberately run at negative margin (see Annual Policy Strategy above).

### Partner Referral
- Sales via partners who refer customers to us (e.g. travel agents, airlines).
- Includes "Partner Referral - Medical" and similar.
- Similar to aggregators in that web journey data is limited.

### Renewals
- Existing annual policyholders renewing their cover.
- This is the payoff of the annual acquisition strategy — renewals are high-margin because there is no acquisition cost.
- **No web journey data** — renewals happen via auto-renew or direct contact, not through the quote funnel.
- Key metrics: retention rate, auto-renew opt-in rate, renewal year cohorts.
- Do NOT try to join web session data for renewal policies.

## Traffic & Conversion

Traffic and conversion are the **primary levers** for understanding volume and GP movements. For every growth or decline identified, the briefing should decompose the movement into its traffic and conversion components.

### The Bridge
The fundamental equation is: **Traffic x Conversion x Average GP = Total GP**.

When explaining any mover, state which of these three levers moved and by how much. For example: "Direct single-trip GP fell £8k — mostly traffic (sessions down 12% YoY) with conversion flat and average GP slightly up."

### Traffic
- Measured as sessions or visits, year-on-year and week-on-week, by channel (direct, aggregator, renewal).
- Traffic is often the dominant driver of volume changes — never attribute a change purely to pricing, mix, or margin without first checking whether traffic moved.
- If sessions are up or down significantly, say so prominently.

### Conversion
- Key rates: session-to-search (how many visitors get a quote), search-to-book (how many quoted visitors buy), quote-to-buy.
- `booking_flow_stage = 'Search'` is where the customer sees a price — this is the key conversion gate.
- If conversion shifted, quantify it and explain what drove the change (device mix, medical screening, cover level, funnel drop-off, etc.).

### Funnel Stages (customer journey)
1. **Landing** — entry page, product selection, search engine
2. **Gatekeeper** — screening/eligibility questions
3. **Screening** — medical screening (Verisk integration)
4. **Extra details** — trip details, traveller information
5. **Search results** — the quote page where the customer sees a price
6. **Add-on results** — upsell/cross-sell (gadget cover, upgrades, etc.)
7. **Checkout** — payment (new user / authenticated / recognised variants)
8. **Payment authentication** — 3DS / payment authorisation
9. **Just booked** — confirmation page

## Pricing & Margin

### GP (Gross Profit) Definition
GP means gross profit after underwriter cost and commission: the column `total_gross_exc_ipt_ntu_comm`. This is the money HX keeps.

### Price Decomposition
The customer price breaks down into:
- **IPT** (Insurance Premium Tax) — a tax, not revenue
- **Underwriter cost** — what we pay the underwriter to carry the risk
- **Commission** — what we pay the distribution partner (aggregator, partner)
- **Discount** — any promotional or campaign discount applied
- **GP** — what is left after all the above

When investigating margin changes, check whether the squeeze is coming from underwriter costs rising, commission increasing, discounting deepening, or price not keeping up.

### Discount Rate Calculation
True discount rate = total discount value / (gross price including IPT + total discount value). This gives the discount as a percentage of the pre-discount price. Use this to assess whether discounting is driving margin changes.

### Cover Levels
Products are tiered: Bronze, Classic, Silver, Gold, Deluxe, Elite, Adventure. Mix shifts between these tiers affect average GP because higher tiers carry higher premiums and (usually) higher margins.

### Add-ons and Extras
- **Gadget cover** — optional add-on for electronic devices
- **Medical screening premium** — additional premium for pre-existing conditions
- **Options** — other optional extras
- When fewer people add extras, it shows up as "attach rate" dropping. In plain English: "fewer people are adding gadget cover or upgrades."

## Data Quirks & Methodology

### Year-on-Year Comparisons
- YoY comparisons use a **364-day offset** (not 365) to match day-of-week. This ensures we compare like-for-like (e.g. Monday vs Monday).
- COVID years 2020-2021 are **structural breaks** — comparisons against these years are unreliable.

### Policy Counting
- The policy table has **multiple rows per booking** (New Issue, Contra, MTA Debit, Cancellation, Client Details Update, UnCancel).
- Never use COUNT(*) or COUNT(DISTINCT policy_id) for policy counts — this gives inflated figures.
- Always use **SUM(policy_count)** — the `policy_count` column is signed (positive for new, negative for cancellations), so SUM gives the correct net count.

### Financial Aggregation
- Financial columns are stored as BIGNUMERIC and must be cast to FLOAT64 for aggregation.
- Never use AVG() on financial columns — because rows are not one-per-policy, AVG() is meaningless.
- Correct average GP per policy: SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0).

### Transaction Date
- `transaction_date` is already a DATE type. Use it directly in WHERE clauses — no need for EXTRACT(DATE FROM ...).

### Web Data
- The web table (`insurance_web_utm_4`) is **web-only** — it does not include call centre or offline data.
- Use `booking_source` in the policies table to distinguish web vs phone sales.
- For unique users: COUNT(DISTINCT visitor_id). For unique sessions: COUNT(DISTINCT session_id).

### Session Flags
- **used_syd** — customer used the "Screen Your Destinations" tool (about 0.3% of sessions)
- **med_session** — session involved medical screening (about 12% of sessions)
- **Multiple_search** — customer did multiple quote searches in one session (about 3.5% of sessions; values are 'Yes'/'No')

## Aggregator Position

Aggregators (price comparison sites) are a major acquisition channel. Key things to understand:

- We deliberately accept negative margins on annual aggregator policies to build the renewal book.
- Commission paid to aggregators is a significant cost — changes in commission rates directly impact GP.
- We cannot see the customer's web journey on comparison sites, only the resulting policy transaction.
- `booking_source` (Web vs Phone) is available for aggregator policies and is a useful drill dimension.
- Device type analysis is **not meaningful** for aggregator sales — the device data reflects our checkout page, not the customer's comparison shopping journey.

## Common Terminology & Drill-Down Dimensions

When the team talks about "drilling down by channel" or "by partner", they mean:

- **Channel / Partner** → `distribution_channel` column (Direct, Aggregator, Partner Referral, Renewals). For a more granular view, use `insurance_group` which breaks these into sub-channels (e.g. "Direct - Standard", "Direct - Medical", "Aggregator - Standard").
- **Cover level** → `cover_level_name` column — Bronze, Classic, Silver, Gold, Deluxe, Elite, Adventure. This is the tier of cover the customer bought.
- **Scheme type / Policy type** → `policy_type` column — Annual or Single. "Annual vs single split" means breaking data by this column.
- **Booking source** → `booking_source` column — Web vs Phone. Tells you whether the sale came through the website or call centre.
- **Device** → `device_type` column from the web table — Mobile, Desktop, Tablet. Only meaningful for Direct channel (aggregators and renewals don't have web journey data).
- **Medical** → `medical_split` or `max_medical_score_grouped` — whether the customer declared medical conditions during screening.

When investigating a mover, always start with distribution_channel and policy_type to isolate WHERE the issue is, then drill into cover_level_name, booking_source, or device_type to find WHY.

## How We Think About Key Metrics

### GP (Gross Profit)
The single most important number. Always quote it with direction, size of change, and context. Never say "GP was £168k" — say "GP was £168k — down £11k on last year, about 6% worse."

### Volume (Policy Count)
Total policies sold, split by annual vs single, and by channel. Volume up is generally good, but check whether the mix is healthy (i.e. are we growing in profitable segments or loss-making ones?).

### Average GP per Policy
Total GP divided by policy count. This tells you whether the quality of each sale is improving or deteriorating. A volume increase with falling average GP means we are selling more but making less on each one.

### Conversion Rates
- **Session-to-search**: what proportion of website visitors get far enough to see a price.
- **Search-to-book**: what proportion of people who see a price actually buy.
- Both matter, but search-to-book is closer to the commercial outcome.

### Mix
The composition of sales across dimensions: annual vs single, direct vs aggregator, cover level, medical vs non-medical, cruise vs non-cruise, destination, etc. Mix shifts can explain GP changes even when volume and price are stable.

### Persistence (Recurring / Emerging / New)
When assessing a mover, look at the last 10 trading days and count how many days the metric moved in the same direction:
- **Recurring** (7+ of 10 days consistent) — a persistent, entrenched pattern. Gets the deepest investigation (5 drill-downs). State the count: "This has been negative on 8 of the last 10 days."
- **Emerging** (5-6 of 10 days consistent) — building momentum but not yet entrenched. Gets 4 drill-downs. Worth watching closely.
- **New** (fewer than 5 of 10 days) — a recent shift or one-off. Gets 3 drill-downs.

Recurring and emerging issues warrant more attention because they suggest something systemic rather than a blip.

## Market Intelligence Sources

The briefing system draws on several external and internal data sources:

- **Google Trends** — search intent for travel insurance and holiday terms, tracked weekly.
- **AI Insights** (Google Sheet tab) — pre-generated strategic insights, refreshed regularly.
- **Dashboard Metrics** — headline market metrics (direction, value, description).
- **Market Demand Summary** — quarterly demand indices (UK passengers, visits abroad, aviation).
- **Spike Log** — known anomalies and structural breaks (COVID, Thomas Cook collapse, etc.).
- **Insurance Intent / Holiday Intent** — normalised Google Trends data for specific search terms.
- **Internal Google Drive docs** — recent pricing changes, campaign briefs, product releases (insurance only; Adventures/Shortbreaks docs are excluded).

When the briefing cites external context, it should always attribute the source (e.g. "According to Google Trends data..." or a link to the article).
