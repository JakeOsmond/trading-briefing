# BigQuery Schema Knowledge — Insurance

_Authoritative source for table schemas. Both `agentic_briefing.py` and `functions/api/ask.js` (via injection) should reflect this._

## `hx-data-production.insurance.insurance_trading_data`

The ONLY policy table. Every row is a transaction event on a policy.

### Critical Rules
- ALWAYS use the full backtick-quoted name: `hx-data-production.insurance.insurance_trading_data`
- Use `SUM(policy_count)` not `COUNT(*)` for policy counts — multiple rows per policy
- Use `SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))` for GP — NEVER `AVG()`
- Avg GP = `SUM(CAST(... AS FLOAT64)) / NULLIF(SUM(policy_count), 0)`
- All BIGNUMERIC financials must be CAST to FLOAT64 for aggregation
- YoY = 364-day offset (matches day-of-week)
- `looker_trans_date` is DATETIME type — wrap in `DATE()` for date comparisons, no `EXTRACT()`

### Transaction Model
Each policy goes through a lifecycle of transaction events, tracked by `version`:
- **version 1** = New Issue (original policy creation) — `policy_count = 1`
- **version 2** = Contra (reversal of a prior version) — `policy_count = -1`
- **version 3** = Cancellation — always preceded by a Contra (version 2)
- **version 4** = MTA Debit (amendment) — always preceded by a Contra (version 2)

So after the initial New Issue, every subsequent change creates TWO rows: a Contra (reversing the old state) and either a Cancellation or MTA Debit (the new state). This means `SUM(policy_count)` correctly nets out.

The `transaction_type` field has values: `New Issue`, `Contra`, `MTA Debit`, `Cancellation`.

### Identity & Tracking Columns
| Column | Type | Description |
|--------|------|-------------|
| `policy_key` | INT64 | Unique row identifier |
| `policy_id` | STRING | Policy identifier (e.g., "AH760101680") |
| `certificate_id` | INT64 | Certificate number — use CAST(certificate_id AS STRING) when joining to web table |
| `old_certificate_id` | INT64 | Previous certificate ID (for amendments/renewals) |
| `transaction_type` | STRING | New Issue / Contra / MTA Debit / Cancellation |
| `revision_number` | INT64 | Revision within a quote |
| `version` | INT64 | Transaction version: 1=new, 2=contra, 3=cancel, 4=amend |
| `transid` | INT64 | Transaction ID |
| `quote_number` | STRING | Quote reference |
| `quote_request_guid` | STRING | Unique quote request ID |
| `external_reference` | STRING | External reference for partner bookings |

### Date Columns
| Column | Type | Description |
|--------|------|-------------|
| `looker_trans_date` | DATETIME | **When the transaction happened** — primary date for trading analysis. Wrap in `DATE()` for date comparisons |
| `looker_start_date` | DATE | When the trip/cover starts |
| `looker_end_date` | DATE | When the policy expires — used for renewal rate calculations |
| `duration` | INT64 | Policy duration in days (365 for annual, 8-17 typical for single) |
| `looker_issue_datetime` | DATETIME | Original issue timestamp |
| `looker_quote_datetime` | DATETIME | Quote timestamp |
| `looker_cancellation_datetime` | DATETIME | Cancellation timestamp (NULL if not cancelled) |
| `cancellation_reason` | STRING | Reason for cancellation |

### Product & Scheme Columns
| Column | Type | Description |
|--------|------|-------------|
| `brand` | STRING | Brand (e.g., "Holiday Extras") |
| `policy_type` | STRING | **Annual** or **Single** — key product split |
| `scheme_id` | INT64 | Scheme identifier |
| `scheme_name` | STRING | Full scheme name (e.g., "Bronze Main Single Med HX", "Silver Cruise Renewal Annual Med HX") — encodes cover level, trip type, medical, brand |
| `scheme_version` | STRING | Scheme version (e.g., "2026/7") |
| `product` | STRING | Product category (e.g., "Direct Travel", "Direct Cruise") |
| `cover_level_name` | STRING | Cover tier: Bronze, Silver, Gold, etc. |
| `cover_level_tier` | INT64 | Numeric tier: 1=Bronze, 2=Silver, 3=Gold |

### Distribution & Channel Columns
| Column | Type | Description |
|--------|------|-------------|
| `distribution_channel` | STRING | **Primary channel**: Direct, Aggregator, Partner Referral, Renewals |
| `channel` | STRING | More specific: "Direct - Standard", "Direct - Medical", "Partner Referral - Standard", "Partner Referral - Medical" |
| `insurance_group` | STRING | Sub-channel grouping: "Cross Sell", "Direct Mailings", "Affiliates", "Independent", etc. |
| `agent_id` | INT64 | Agent identifier |
| `agent_code` | STRING | Agent attribution code (e.g., "AH760", "AW660", "MAPS1") |
| `agent_name` | STRING | Agent/partner name (e.g., "AIRLINE CC REF", "Solos Holiday Weblink", "Perkbox Insurance") |
| `agent_group` | STRING | Agent group code (e.g., "I9", "MO", "S6", "YA", "B6") |
| `campaign_id` | INT64 | Campaign identifier |
| `campaign_name` | STRING | Campaign name (e.g., "DIR-CRU-REN-Direct", "DIR-Direct", "REF-Referral") |
| `booking_source` | STRING | How the booking was made: "Web", "Contact Centre", "Auto Renewal" |
| `transaction_source` | STRING | Transaction origin: "Web", "Contact Centre", "Auto Renewal" |
| `return_agent` | STRING | Return agent code (e.g., "N") |
| `converted_by` | STRING | Who converted the sale (e.g., "Connect", "auto.renewal") |
| `last_updated_by` | STRING | Last user to update the record |
| `rid` | STRING | Agent RID code (e.g., "D", "I") |

### Customer Columns
| Column | Type | Description |
|--------|------|-------------|
| `customer_id` | STRING | Customer UUID |
| `customer_ext_id` | STRING | Hashed external customer ID |
| `customer_type` | STRING | **New, Existing, Lapsed, Re-engaged** — key segmentation dimension |
| `customer_type_insurance_only` | STRING | Customer type based on insurance history only |
| `lead_title` | STRING | Customer title (Mr/Mrs/Ms) |
| `lead_forename` | STRING | First name |
| `lead_surname` | STRING | Surname |
| `lead_postcode` | STRING | UK postcode |
| `lead_email` | STRING | Email address |
| `customer_area` | STRING | Geographic area (e.g., "Kilgetty", "Ferndale") |
| `customer_region` | STRING | Geographic region (e.g., "Pembrokeshire", "Rhondda Cynon Taf") |
| `lead_dob` | DATE | Customer date of birth |
| `highest_dob` | DATE | Oldest traveller's DOB |
| `max_age_at_purchase` | INT64 | Age of oldest traveller at purchase |
| `residence` | STRING | Country of residence (e.g., "GBR") |

### Traveller Columns
| Column | Type | Description |
|--------|------|-------------|
| `pax` | INT64 | Total passengers on the policy |
| `adults` | INT64 | Number of adults |
| `children` | INT64 | Number of children |
| `family_group` | STRING | Family grouping (e.g., "Couple", "Individual") |

### Destination Columns
| Column | Type | Description |
|--------|------|-------------|
| `destination_full` | STRING | Full destination (e.g., "Europe inc Spain, Cyprus, Malta, Greece & Turkey") |
| `destination` | STRING | Destination group (e.g., "Europe Inc", "Worldwide Exc") |
| `destination_group` | STRING | Broad destination category (e.g., "Europe", "Worldwide") |
| `highest_rated_country` | STRING | Highest-risk country in the destination |
| `trip_value` | BIGNUMERIC | Declared trip value |

### Medical Columns
| Column | Type | Description |
|--------|------|-------------|
| `medical_split` | STRING | "Medical" or "Non-Medical" |
| `max_medical_score` | NUMERIC | Maximum medical screening score across travellers |
| `max_medical_score_grouped` | NUMERIC | Grouped medical score (0, 2, 3, 4, etc.) |
| `has_undiagnosed_condition` | BOOL | Whether any traveller has undiagnosed conditions |
| `screened_pax` | INT64 | Number of passengers who went through medical screening |

### Financial Columns — Key Totals
| Column | Type | Description |
|--------|------|-------------|
| `total_gross_inc_ipt` | BIGNUMERIC | **Customer price** (what they paid, including IPT) |
| `total_gross_exc_ipt` | BIGNUMERIC | Customer price excluding IPT |
| `total_gross_exc_ipt_ntu` | BIGNUMERIC | Price minus IPT minus underwriter cost |
| `total_gross_exc_ipt_ntu_comm` | BIGNUMERIC | **THIS IS GP** — price minus IPT, underwriter, commission |
| `total_ipt` | BIGNUMERIC | Insurance Premium Tax |
| `total_net_to_underwriter_inc_gadget` | BIGNUMERIC | Net to underwriter (including gadget cover) |
| `total_paid_commission_perc` | BIGNUMERIC | Commission percentage |
| `total_paid_commission_value` | BIGNUMERIC | Commission paid to partner/agent |
| `total_discount_value` | FLOAT64 | Total discount applied |
| `base_discount_value` | FLOAT64 | Discount on base policy |
| `addon_discount_value` | FLOAT64 | Discount on add-ons |
| `campaign_discount_perc` | INT64 | Campaign discount percentage (e.g., 15, 20, 24) |
| `ipt_rate` | BIGNUMERIC | IPT rate applied |
| `ppc_cost_per_policy` | FLOAT64 | PPC advertising cost allocated per policy |

**GP Post PPC:** GP is calculated as `total_gross_exc_ipt_ntu_comm` minus `COALESCE(ppc_cost_per_policy, 0)` to account for PPC advertising spend.

### Estimated 13-Month Customer Value
| Column | Type | Description |
|--------|------|-------------|
| `est_13m_ins_gp` | FLOAT64 | Estimated GP from future insurance purchases by this customer over 13 months (NULL if not new) |
| `est_13m_other_gp` | FLOAT64 | Estimated GP from future non-insurance HX purchases by this customer over 13 months (NULL if not new) |

**Total 13-Month Customer Value** = GP (Post PPC) + COALESCE(est_13m_ins_gp, 0) + COALESCE(est_13m_other_gp, 0)

Key rules:
- Only populated for **new customers** (customer_type = 'New', transid = 1, version = 1)
- NULL for renewals and returning customers — they already have purchasing history
- Values are estimates based on the purchasing behaviour of customers who booked 13 months ago and shared the same **policy_type**, **medical_split**, **distribution_channel**, and **destination_group**
- Critical for evaluating negative-margin strategies: a channel losing on immediate GP may be profitable when 13-month customer value is considered (e.g., aggregator single-trip acquisition funds future renewal and cross-sell revenue)
- Analyse at the distribution_channel level: does the total machine (all policy types combined) deliver positive 13-month customer value, even if individual segments are negative on day-one GP?
- The mix of genuinely new vs returning customers affects the aggregate — more new customers means more 13-month upside in the numbers

### Financial Columns — Component Breakdown
The financials decompose into **base** (core policy), **medical** (medical screening top-up), **option** (add-ons), and **gadget** (gadget cover). Each has inc_ipt, exc_ipt, ntu, commission variants. The naming pattern is:
- `base_*` — core policy premium
- `medical_*` — medical screening premium
- `option_*` — optional add-ons
- `total_*` — sum of all components
- `*_exc_gadget_*` — excluding gadget cover component
- `*_exc_options_*` — excluding optional add-ons

### Policy Status Columns
| Column | Type | Description |
|--------|------|-------------|
| `policy_count` | INT64 | **Signed count**: +1 for new/amend, -1 for contra/cancel. Always SUM() this. |
| `policy_status` | STRING | "Live" or "Cancelled" |
| `policy_renewal_year` | INT64 | Which renewal year (0=new, 2=second renewal, 3=third, etc.) |
| `underwriter` | STRING | Underwriter name (e.g., "ERGO") |
| `auto_renew_opt_in` | BOOL | Whether customer opted into auto-renewal |
| `currency` | STRING | Currency code (e.g., "Pound") |
| `user` | STRING | System user who created the record |

### Renewal Columns
| Column | Type | Description |
|--------|------|-------------|
| `renewed_flag` | BOOL/STRING | Whether the policy was renewed |
| `renew_lag_to_expiry` | INT64 | Days between renewal purchase and original policy expiry |
| `previous_cover_level_name` | STRING | Cover level of the previous (expiring) policy |
| `renewal_journey` | STRING | The renewal journey/path taken (e.g., auto-renewal, manual renewal) |

---

## `hx-data-production.commercial_finance.insurance_web_utm_4`

Web analytics — event-level data for the Direct channel ONLY (no aggregator/renewal web data).

### Critical Rules
- Each row is a **single event** within a session (click, page view, auto_capture, etc.)
- Sessions = `COUNT(DISTINCT session_id)`, Users = `COUNT(DISTINCT visitor_id)`
- `certificate_id` is STRING here but INT64 in policies — always CAST for joins
- `session_start_date` is the date field for filtering (DATE type)

### Session & Identity Columns
| Column | Type | Description |
|--------|------|-------------|
| `session_id` | STRING | Unique session identifier |
| `visitor_id` | STRING | Unique visitor identifier |
| `certificate_id` | STRING | Policy certificate ID (links to policies table — CAST to match) |
| `policy_id` | STRING | Policy ID |
| `session_seconds` | INT64 | Total session duration in seconds |
| `session_start_date` | DATE | **Session date** — primary date for web analysis |
| `session_landing_path` | STRING | First page URL path (e.g., "/travel-insurance.html") |
| `session_landing_agent` | STRING | Landing agent code (e.g., "MAPS1") |
| `session_browser_name` | STRING | Browser (e.g., "Mobile Safari", "Chrome") |
| `customer_type` | STRING | New, Existing, Lapsed, Re-engaged |

### Page & Event Columns
| Column | Type | Description |
|--------|------|-------------|
| `device_type` | STRING | "mobile", "computer", "tablet" |
| `page_type` | STRING | Page in the journey: landing, gatekeeper, description, screening, extra_details, search_results, addon_results, checkout_*, just_booked |
| `page_path` | STRING | URL path of the page |
| `page_agent` | STRING | Agent code on the page |
| `page_datetime_start` | TIMESTAMP | Page view timestamp |
| `event_name` | STRING | Specific event (e.g., "engine_search_button", "select_product", "chat_started", "verisk-radio-answer-*") |
| `event_type` | STRING | Event category: click, auto_capture, customer_state, focus, capture, ecommerce |
| `event_value` | STRING | Event payload/value |
| `event_start_datetime` | TIMESTAMP | Event timestamp |
| `booking_flow_stage` | STRING | **Funnel stage**: Landing, Gatekeeper, Screening, Search, Addon, Checkout, Just_Booked etc. |

### Product & Scheme Columns
| Column | Type | Description |
|--------|------|-------------|
| `scheme_search` | STRING | Policy type being searched: "Single" or "Annual" (NOTE: different from `policy_type` — this is the search intent) |
| `insurance_group` | STRING | **Sub-channel**: "Web Links", "Direct Mailings", "Affiliates", etc. — same dimension as policies table |
| `scheme_id` | INT64 | Scheme identifier |
| `scheme_name` | STRING | Full scheme name (e.g., "Bronze Main Single Med HX") |
| `scheme_type` | STRING | Scheme type: "Single" or "Annual" |
| `scheme_type_status` | STRING | Scheme type status |

### Destination & Travel Columns
| Column | Type | Description |
|--------|------|-------------|
| `region_name` | STRING | Destination region (e.g., "Europe inc Spain, Cyprus, Malta, Greece & Turkey") |
| `travel_start_date` | DATE | Trip start date |
| `travel_end_date` | DATE | Trip end date |
| `duration` | INT64 | Trip duration in days |
| `passenger_count` | INT64 | Number of travellers |

### Financial Columns (per-certificate, on the web row)
| Column | Type | Description |
|--------|------|-------------|
| `certificate_gross` | NUMERIC | Certificate gross premium |
| `certificate_ipt` | NUMERIC | IPT on the certificate |
| `certificate_nett` | NUMERIC | Net premium |
| `certificate_uw1_ex_ipt` | NUMERIC | Underwriter 1 cost ex IPT |
| `certificate_uw2_ex_ipt` | NUMERIC | Underwriter 2 cost ex IPT |
| `certificate_margin` | NUMERIC | Certificate margin |
| `total_gross` | NUMERIC | Total gross (for the session/certificate) |
| `total_gp` | NUMERIC | Total GP (for the session/certificate) |
| `policy_screening_gross` | NUMERIC | Medical screening premium |
| `policy_screening_margin` | NUMERIC | Medical screening margin |

### Marketing Attribution Columns
| Column | Type | Description |
|--------|------|-------------|
| `campaign` | STRING | UTM campaign |
| `source` | STRING | UTM source |
| `medium` | STRING | UTM medium |
| `channel` | STRING | UTM channel (e.g., "Direct") |
| `utm_id` | STRING | UTM ID |

### Session Flags
| Column | Type | Description |
|--------|------|-------------|
| `Multiple_search` | STRING | "Yes" or "No" — whether the session had multiple searches |
| `med_session` | BOOL | Whether the session involved medical screening |
| `used_syd` | BOOL | Whether the "see your data" feature was used |

---

## Joining the Tables

```sql
-- Always CAST certificate_id for joins (INT64 in policies, STRING in web)
CAST(p.certificate_id AS STRING) = w.certificate_id
```

The web table only has Direct channel data. Aggregator and Renewal bookings have no web journey data.

## customer_type Field (both tables)
- **New** = never seen by Holiday Extras before
- **Existing** = in our database, has booked in the last 3 years
- **Lapsed** = in our database but hasn't booked in the last 3 years
- **Re-engaged** = was lapsed but a recent purchase moved them out of lapsed

## insurance_group Field (both tables)
Sub-channel grouping within distribution channels. Common values:
- "Cross Sell" — cross-sold from other HX products
- "Direct Mailings" — email/DRM campaigns
- "Web Links" — web referral links
- "Affiliates" — affiliate partners (Perkbox, Blue Light Card, etc.)
- "Independent" — independent referral partners (Solos Holiday, etc.)
