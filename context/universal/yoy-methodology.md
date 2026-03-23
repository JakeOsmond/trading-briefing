# Year-on-Year Methodology

## 364-Day Offset
YoY comparisons use a **364-day offset** (not 365) to match day-of-week. This ensures we compare like-for-like (e.g. Monday vs Monday). In most years there is a one-day shift in day-of-week alignment — the 364-day offset corrects for this.

## COVID Structural Breaks
COVID years 2020-2021 are **structural breaks** — comparisons against these years are unreliable.

## Date Handling
- `looker_trans_date` is a DATETIME type. Wrap in `DATE()` for date comparisons — use `DATE(looker_trans_date)` in WHERE clauses. No need for EXTRACT(DATE FROM ...).
- When building LY equivalents, always subtract 364 days (52 weeks exactly).

## Calendar Effects
- **Easter** moves substantially between years — week-containing-Easter comparisons need special handling
- **School holidays** vary by region and year — see travel-events.md
- **Bank holidays** shift day-of-week alignment. The pipeline uses gov.uk API + holiday awareness to flag these.
