# Trading Covered — Runbook

_What to do when the briefing looks wrong or doesn't appear._

---

## No briefing appeared this morning

1. Check GitHub Actions: https://github.com/JakeOsmond/trading-briefing/actions
2. Look for a failed run (red X) on today's date
3. Click into the failed run → expand "Run briefing script" → read the error
4. Common causes:
   - **OpenAI API error** → check if API key is valid in GitHub Secrets
   - **BigQuery auth error** → GCP credentials may have expired
   - **Timeout** → pipeline took >45 minutes (check Phase timing in logs)
5. To re-run: click "Re-run all jobs" on the failed run page

## Briefing appeared but shows a "stale" banner

The red banner means the briefing is >20 hours old. Either:
- Today's pipeline hasn't run yet (check Actions page)
- Today's pipeline failed (see above)
- The deploy step failed (pipeline ran but Cloudflare deploy didn't complete)

## A finding looks wrong

1. Check the **verification pill** on the driver heading
   - Green "VERIFIED" = both OpenAI and Claude agreed
   - Amber "DISPUTED" = the models disagreed — read the tooltip for details
2. Click **View SQL** on the finding to see the actual query
3. Copy the SQL into BigQuery and run it yourself to check the numbers
4. If wrong: click **Remove** (enter password when prompted) — the finding will be hidden for all viewers
5. If right: click **Verify** — enter who confirmed it and an optional note

## A finding was removed by mistake

1. Find the faded finding on the page
2. Click the **revert** link (small text next to the pill)
3. Enter the verification password
4. The page will reload with the original state

## Numbers don't match what I see in Looker

Common reasons:
- **Date offset**: Trading Covered uses a 364-day YoY offset (day-of-week matching). Looker may use 365 days.
- **Policy counting**: Trading Covered uses `SUM(policy_count)`. If Looker uses `COUNT(*)`, numbers will differ.
- **Financial columns**: Trading Covered casts BIGNUMERIC to FLOAT64. Rounding differences are expected at the penny level.
- **Time of data**: The pipeline runs at 05:00 UTC. If Looker refreshes later, it may have more recent data.

## Who to contact

- **Pipeline/code issues**: Jake Osmond
- **Data/BigQuery issues**: Data Engineering team
- **Cloudflare/deployment**: Jake Osmond or Dave Lee
- **Business context questions**: Commercial Finance team
