# Drill-Down Dimensions

When the team talks about "drilling down", they mean these columns:

| Dimension | Column | Notes |
|-----------|--------|-------|
| Channel / Partner | `distribution_channel` | Direct, Aggregator, Partner Referral, Renewals |
| Sub-channel | `insurance_group` | "Direct - Standard", "Direct - Medical", "Aggregator - Standard", etc. |
| Cover level | `cover_level_name` | Bronze, Classic, Silver, Gold, Deluxe, Elite, Adventure |
| Policy type | `policy_type` | Annual or Single |
| Booking source | `booking_source` | Web vs Phone |
| Device | `device_type` (web table) | Mobile, Desktop, Tablet. Only meaningful for Direct channel. |
| Medical | `medical_split` or `max_medical_score_grouped` | Whether the customer declared medical conditions |

When investigating a mover, always start with `distribution_channel` and `policy_type` to isolate WHERE the issue is, then drill into `cover_level_name`, `booking_source`, or `device_type` to find WHY.
