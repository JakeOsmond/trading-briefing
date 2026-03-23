# Renewal Rate Calculation

True renewal rate = total policies purchased in the 'Renewal' distribution channel (on transaction date) / total annual policies expiring (by travel end date — the expiry date, i.e. the number of annual policies expiring).

- You must use `looker_end_date` for expiring policies and `DATE(looker_trans_date)` for new purchased policies.
- This means it is a join on 2 separate SQL queries.
- This tells us how many customers are going on and keeping an annual policy with us.
- Renewal rate is **blended only** — never calculate per-channel renewal rates, as the denominator (expiring policies) doesn't split meaningfully by new-purchase channel.

- Auto-renewal process updated with new Dockyard field/rules — Source: Drive: 'Daily Auto Renewals Tracker', 2026-03-18
