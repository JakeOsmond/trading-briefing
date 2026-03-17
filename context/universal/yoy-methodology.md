# Year-on-Year Methodology

## 364-Day Offset
YoY comparisons use a **364-day offset** (not 365) to match day-of-week. This ensures we compare like-for-like (e.g. Monday vs Monday).

## COVID Structural Breaks
COVID years 2020-2021 are **structural breaks** — comparisons against these years are unreliable.

## Date Handling
- `transaction_date` is already a DATE type. Use it directly in WHERE clauses — no need for EXTRACT(DATE FROM ...).
- When building LY equivalents, always subtract 364 days (52 weeks exactly).
