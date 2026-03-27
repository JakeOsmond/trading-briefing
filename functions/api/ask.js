// Schema + business context injected at deploy time by scripts/inject-ask-context.sh
import { SCHEMA_KNOWLEDGE, BUSINESS_CONTEXT } from './_generated-context.js';

/**
 * Trading Covered — Interactive Q&A API
 * Cloudflare Pages Function
 *
 * POST /api/ask
 * Body: { question, driver_context?, conversation_history?, mode: "driver"|"general" }
 * Response: { answer, sql_queries, rounds }
 */

// ── BigQuery REST client (lightweight, no npm deps) ──────────────────────

async function getBQAccessToken(credentialJson) {
  const creds = typeof credentialJson === 'string' ? JSON.parse(credentialJson) : credentialJson;

  // Support both service_account and authorized_user credential types
  if (creds.type === 'authorized_user') {
    // OAuth2 refresh token flow (for local dev with gcloud ADC)
    const tokenRes = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'refresh_token',
        client_id: creds.client_id,
        client_secret: creds.client_secret,
        refresh_token: creds.refresh_token,
      }),
    });
    const tokenData = await tokenRes.json();
    if (!tokenData.access_token) throw new Error('Failed to refresh token: ' + JSON.stringify(tokenData));
    return tokenData.access_token;
  }

  // Service account JWT flow (for production on Cloudflare)
  const sa = creds;
  const now = Math.floor(Date.now() / 1000);
  const header = btoa(JSON.stringify({ alg: 'RS256', typ: 'JWT' }));
  const payload = btoa(JSON.stringify({
    iss: sa.client_email,
    scope: 'https://www.googleapis.com/auth/bigquery',
    aud: 'https://oauth2.googleapis.com/token',
    iat: now,
    exp: now + 3600,
  }));

  const pemContents = sa.private_key
    .replace(/-----BEGIN PRIVATE KEY-----/, '')
    .replace(/-----END PRIVATE KEY-----/, '')
    .replace(/\n/g, '');
  const binaryKey = Uint8Array.from(atob(pemContents), c => c.charCodeAt(0));

  const cryptoKey = await crypto.subtle.importKey(
    'pkcs8', binaryKey, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['sign']
  );

  const toSign = new TextEncoder().encode(`${header}.${payload}`);
  const signature = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', cryptoKey, toSign);
  const sig = btoa(String.fromCharCode(...new Uint8Array(signature)))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

  const jwt = `${header}.${payload}.${sig}`;

  const tokenRes = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=${jwt}`,
  });
  const tokenData = await tokenRes.json();
  if (!tokenData.access_token) throw new Error('Failed to get SA token: ' + JSON.stringify(tokenData));
  return tokenData.access_token;
}

async function runBQQuery(sql, accessToken, projectId = 'hx-data-production') {
  // Use the synchronous jobs.query endpoint — simpler, no polling needed for most queries
  const url = `https://bigquery.googleapis.com/bigquery/v2/projects/${projectId}/queries`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { Authorization: `Bearer ${accessToken}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: sql,
      useLegacySql: false,
      maxResults: 200,
      timeoutMs: 60000,
      maximumBytesBilled: '200000000000',
    }),
  });
  const data = await res.json();

  // Check for errors
  if (data.error) {
    const msg = data.error.message || JSON.stringify(data.error);
    throw new Error(msg);
  }
  if (data.errors && data.errors.length > 0) {
    throw new Error(data.errors.map(e => e.message).join('; '));
  }

  // If job isn't complete yet, poll for it
  if (!data.jobComplete && data.jobReference) {
    const jobId = data.jobReference.jobId;
    const location = data.jobReference.location || 'EU';
    const jobsUrl = `https://bigquery.googleapis.com/bigquery/v2/projects/${projectId}/queries/${jobId}`;
    for (let i = 0; i < 60; i++) {
      await new Promise(r => setTimeout(r, 1000));
      const pollRes = await fetch(`${jobsUrl}?timeoutMs=10000&location=${location}`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      const pollData = await pollRes.json();
      if (pollData.error) throw new Error(pollData.error.message || JSON.stringify(pollData.error));
      if (pollData.jobComplete) {
        if (!pollData.rows) return [];
        const fields = pollData.schema.fields.map(f => f.name);
        return pollData.rows.map(r =>
          Object.fromEntries(fields.map((f, i) => [f, r.f[i].v]))
        );
      }
    }
    throw new Error('BigQuery query timed out after 60 seconds');
  }

  // Results are inline
  if (!data.rows) return [];
  const fields = data.schema.fields.map(f => f.name);
  return data.rows.map(r =>
    Object.fromEntries(fields.map((f, i) => [f, r.f[i].v]))
  );
}


// ── SQL validation + autocorrect ──────────────────────────────────────────

function autocorrectSQL(sql) {
  const warnings = [];
  let fixed = sql;

  // Strip markdown code fences (LLM sometimes wraps SQL in ```sql ... ```)
  fixed = fixed.replace(/^```(?:sql)?\s*\n?/i, '').replace(/\n?```\s*$/i, '');

  // Strip smart/curly backticks and other Unicode quote variants that break BQ
  fixed = fixed.replace(/[\u0060\u2018\u2019\u201C\u201D\uFF40]/g, '`');

  // Fix COUNT(*) or COUNT(DISTINCT policy_id)
  if (/COUNT\s*\(\s*\*\s*\)/i.test(fixed) || /COUNT\s*\(\s*DISTINCT\s+policy_id\s*\)/i.test(fixed)) {
    fixed = fixed.replace(/COUNT\s*\(\s*\*\s*\)/gi, 'SUM(policy_count)');
    fixed = fixed.replace(/COUNT\s*\(\s*DISTINCT\s+policy_id\s*\)/gi, 'SUM(policy_count)');
    warnings.push('Replaced COUNT(*)/COUNT(DISTINCT policy_id) with SUM(policy_count)');
  }

  // Fix AVG() on financial columns
  const financialCols = ['gp', 'total_gross_exc_ipt_ntu_comm', 'total_gross_inc_ipt', 'total_gross_exc_ipt'];
  for (const col of financialCols) {
    const re = new RegExp(`AVG\\s*\\(\\s*(?:CAST\\s*\\()?${col}`, 'gi');
    if (re.test(fixed)) {
      warnings.push(`Replaced AVG(${col}) — use SUM/NULLIF pattern instead`);
    }
  }

  // Fix any wrong table references to the correct fully qualified names
  // Catch old table name (insurance_policies_new) and redirect to new table
  if (/insurance_policies_new/i.test(fixed)) {
    fixed = fixed.replace(/`[^`]*insurance_policies_new[^`]*`/g, '`hx-data-production.insurance.insurance_trading_data`');
    fixed = fixed.replace(/\binsurance_policies_new\b/gi, '`hx-data-production.insurance.insurance_trading_data`');
    warnings.push('Redirected old table insurance_policies_new to insurance_trading_data');
  }
  if (/commercial_finance\b/i.test(fixed) && !/insurance_web_utm_4/i.test(fixed)) {
    fixed = fixed.replace(/commercial_finance\.insurance_policies_new/gi, 'insurance.insurance_trading_data');
    warnings.push('Fixed old dataset commercial_finance to insurance');
  }
  const wrongTablePattern = /`[^`]*insurance_trading_data[^`]*`/g;
  if (wrongTablePattern.test(fixed) && !fixed.includes('`hx-data-production.insurance.insurance_trading_data`')) {
    fixed = fixed.replace(/`[^`]*insurance_trading_data[^`]*`/g, '`hx-data-production.insurance.insurance_trading_data`');
    warnings.push('Fixed table name to hx-data-production.insurance.insurance_trading_data');
  }
  if (/\binsurance_trading_data\b/.test(fixed) && !fixed.includes('`hx-data-production.insurance.insurance_trading_data`')) {
    fixed = fixed.replace(/\binsurance_trading_data\b/g, '`hx-data-production.insurance.insurance_trading_data`');
    warnings.push('Added fully qualified table name');
  }
  const wrongWebPattern = /`[^`]*insurance_web_utm_4[^`]*`/g;
  if (wrongWebPattern.test(fixed) && !fixed.includes('`hx-data-production.commercial_finance.insurance_web_utm_4`')) {
    fixed = fixed.replace(/`[^`]*insurance_web_utm_4[^`]*`/g, '`hx-data-production.commercial_finance.insurance_web_utm_4`');
    warnings.push('Fixed web table name');
  }

  // Fix date field references — transaction_date doesn't exist, use DATE(looker_trans_date)
  if (/\btransaction_date\b/i.test(fixed) && !/looker_trans_date/i.test(fixed)) {
    // Replace bare transaction_date with DATE(looker_trans_date)
    // But preserve it as an alias in "AS transaction_date"
    fixed = fixed.replace(/\bEXTRACT\s*\(\s*DATE\s+FROM\s+transaction_date\s*\)/gi, 'DATE(looker_trans_date)');
    fixed = fixed.replace(/(?<!AS\s)(?<!AS\s\s)\btransaction_date\b(?!\s*AS\b)/gi, 'DATE(looker_trans_date)');
    warnings.push('Replaced transaction_date with DATE(looker_trans_date)');
  }
  // Fix transaction_type used as a date (common LLM mistake — confuses transaction_type with transaction_date)
  if (/transaction_type\s+BETWEEN\s/i.test(fixed)) {
    fixed = fixed.replace(/\btransaction_type\s+(BETWEEN\s)/gi, 'DATE(looker_trans_date) $1');
    warnings.push('Replaced transaction_type BETWEEN with DATE(looker_trans_date) BETWEEN');
  }
  // Fix travel_end_date → looker_end_date, travel_start_date → looker_start_date
  if (/\btravel_end_date\b/i.test(fixed)) {
    fixed = fixed.replace(/\btravel_end_date\b/gi, 'looker_end_date');
    warnings.push('Replaced travel_end_date with looker_end_date');
  }
  if (/\btravel_start_date\b/i.test(fixed)) {
    fixed = fixed.replace(/\btravel_start_date\b/gi, 'looker_start_date');
    warnings.push('Replaced travel_start_date with looker_start_date');
  }
  // Fix engine_search_button → page_type = 'search_results' for counting searches
  if (/engine_search_button/i.test(fixed)) {
    // Replace COUNTIF(event_name = 'engine_search_button') pattern
    fixed = fixed.replace(/COUNTIF\s*\(\s*event_name\s*=\s*'engine_search_button'\s*\)/gi,
      "COUNT(DISTINCT CASE WHEN page_type = 'search_results' THEN session_id END)");
    // Replace COUNT(DISTINCT CASE WHEN ... engine_search_button pattern
    fixed = fixed.replace(/COUNT\s*\(\s*DISTINCT\s+CASE\s+WHEN\s+(?:event_type\s*=\s*'click'\s+AND\s+)?event_name\s*=\s*'engine_search_button'\s+THEN\s+session_id\s+END\s*\)/gi,
      "COUNT(DISTINCT CASE WHEN page_type = 'search_results' THEN session_id END)");
    // Replace any remaining bare references
    fixed = fixed.replace(/'engine_search_button'/gi, "'search_results'");
    fixed = fixed.replace(/event_name\s*=\s*'search_results'/gi, "page_type = 'search_results'");
    warnings.push('Replaced engine_search_button with page_type = search_results');
  }

  // Replace hardcoded epoch-era dates with CURRENT_DATE() expressions
  // Catches DATE '1970-01-01' or similar obviously-wrong dates
  if (/DATE\s*'19[67]\d-\d{2}-\d{2}'/i.test(fixed)) {
    warnings.push('Detected epoch-era date literal — query may have incorrect date anchoring');
  }

  // Enforce case-insensitive string comparisons on key categorical columns
  const catCols = ['distribution_channel', 'policy_type', 'cover_level_name', 'customer_type',
    'device_type', 'booking_source', 'medical_split', 'channel', 'booking_flow_stage'];
  for (const col of catCols) {
    // Match: col = 'value' (not already wrapped in LOWER)
    const pattern = new RegExp(`(?<!LOWER\\s*\\()\\b${col}\\b\\s*=\\s*'([^']+)'`, 'gi');
    if (pattern.test(fixed)) {
      fixed = fixed.replace(
        new RegExp(`(?<!LOWER\\s*\\()\\b${col}\\b\\s*=\\s*'([^']+)'`, 'gi'),
        `LOWER(${col}) = LOWER('$1')`
      );
      warnings.push(`Applied case-insensitive filter on ${col}`);
    }
  }

  return { sql: fixed, warnings };
}


// ── OpenAI chat with tool use ─────────────────────────────────────────────

async function callOpenAI(messages, tools, apiKey, maxTokens = 4096, model = 'gpt-4.1-mini') {
  const res = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model,
      messages,
      tools: tools || undefined,
      max_completion_tokens: maxTokens,
    }),
  });
  return res.json();
}


// ── Extract chart data from SQL results ────────────────────────────────────

function extractChartData(sqlQueries) {
  const successful = sqlQueries.filter(q => q.success && q.result_rows && q.result_rows.length >= 2);
  if (!successful.length) return null;

  for (const q of successful) {
    const rows = q.result_rows;
    const cols = Object.keys(rows[0] || {});

    // Detect time-series: has a date-like column + a numeric column
    const dateCol = cols.find(c => /date|dt|day|week|month|period/i.test(c) && rows.some(r => /^\d{4}-\d{2}/.test(r[c])));
    const numCols = cols.filter(c => c !== dateCol && rows.some(r => !isNaN(parseFloat(r[c])) && r[c] !== null && r[c] !== ''));

    if (dateCol && numCols.length > 0) {
      // Pick the most interesting numeric column (prefer gp, then policies, then first)
      const valCol = numCols.find(c => /gp|gross/i.test(c))
        || numCols.find(c => /polic/i.test(c))
        || numCols.find(c => /session/i.test(c))
        || numCols[0];

      // Check for TY/LY split (yr column)
      const yrCol = cols.find(c => /^yr$/i.test(c));
      if (yrCol) {
        const tyRows = rows.filter(r => r[yrCol] === 'TY').sort((a, b) => a[dateCol].localeCompare(b[dateCol]));
        const lyRows = rows.filter(r => r[yrCol] === 'LY').sort((a, b) => a[dateCol].localeCompare(b[dateCol]));
        if (tyRows.length >= 2) {
          return {
            type: 'timeseries',
            label: valCol.replace(/_/g, ' '),
            points: tyRows.map(r => ({ date: r[dateCol], value: parseFloat(r[valCol]) || 0 })),
            ly_points: lyRows.length > 0 ? lyRows.map(r => ({ date: r[dateCol], value: parseFloat(r[valCol]) || 0 })) : null,
          };
        }
      }

      // Check for same-row LY columns — broad matching
      const valLower = valCol.toLowerCase();
      const lyCol = cols.find(c => {
        const cl = c.toLowerCase();
        if (cl === valLower) return false;
        // Match: gp_ly, gp_last_year, ly_gp, last_year_gp, gp_previous, previous_gp
        return cl === valLower + '_ly' || cl === valLower + '_last_year' || cl === valLower + '_previous'
          || cl === 'ly_' + valLower || cl === 'last_year_' + valLower
          || (cl.includes('ly') && cl.includes(valLower) && cl !== valLower);
      });
      // Also detect delta/change columns for colouring when no LY
      const deltaCol = cols.find(c => {
        const cl = c.toLowerCase();
        return (cl.includes(valLower) || cl.includes('delta') || cl.includes('change'))
          && (cl.includes('delta') || cl.includes('diff') || cl.includes('change') || cl.includes('pct'))
          && cl !== valLower;
      });
      const sorted = [...rows].sort((a, b) => a[dateCol].localeCompare(b[dateCol]));
      return {
        type: 'timeseries',
        label: valCol.replace(/_/g, ' '),
        points: sorted.map(r => ({ date: r[dateCol], value: parseFloat(r[valCol]) || 0 })),
        ly_points: lyCol ? sorted.map(r => ({ date: r[dateCol], value: parseFloat(r[lyCol]) || 0 })) : null,
        delta_values: deltaCol ? sorted.map(r => parseFloat(r[deltaCol]) || 0) : null,
      };
    }

    // Detect categorical: has a string column + a numeric column (e.g. customer_type × gp)
    const catCol = cols.find(c => !dateCol && rows.every(r => isNaN(parseFloat(r[c])) || r[c] === null));
    if (catCol && numCols.length > 0 && rows.length <= 30) {
      const valCol = numCols.find(c => /gp|gross/i.test(c))
        || numCols.find(c => /polic/i.test(c))
        || numCols[0];
      return {
        type: 'categorical',
        label: valCol.replace(/_/g, ' '),
        points: rows.map(r => ({ category: r[catCol] || 'Unknown', value: parseFloat(r[valCol]) || 0 })),
      };
    }
  }
  return null;
}


// ── Verify + format answer (single AI call — saves subrequests) ───────────

async function verifyAndFormat(answer, sqlQueries, apiKey) {
  const successfulQueries = sqlQueries.filter(q => q.success);

  const evidenceBlock = successfulQueries.length > 0
    ? `## SQL EVIDENCE\n${successfulQueries.map((q, i) =>
        `Query ${i + 1}: ${q.sql}\nReturned ${q.rows} row(s).${q.sample_data ? '\nSample: ' + q.sample_data : ''}`
      ).join('\n\n')}\n\n`
    : '';

  const noDataWarning = successfulQueries.length === 0
    ? '\n\n<p class="ai-summary"><em>No SQL queries succeeded. For verification, please speak with a member of the Commercial Finance team in Insurance.</em></p>'
    : '';

  try {
    const response = await callOpenAI([
      { role: 'system', content: `You are a combined fact-checker and formatter for a trading dashboard chat widget.

## STEP 1: VERIFY (if SQL evidence is provided)
- Check every number/percentage/claim against the SQL evidence
- If a claim is NOT supported by query results, silently REMOVE it
- If all claims are supported, keep them unchanged

## STEP 2: FORMAT AS HTML
Convert the verified answer into clean styled HTML (inserted via innerHTML).

OUTPUT FORMAT — use these exact CSS classes:

1. HEADLINE METRICS — the most important 2-4 numbers:
<div class="ai-metrics">
  <div class="ai-metric-card">
    <div class="ai-metric-label">Sessions</div>
    <div class="ai-metric-value">5,653</div>
    <div class="ai-metric-change up">+2,079 vs LY</div>
  </div>
</div>
Use class "up" for positive, "down" for negative.

2. SUMMARY — <p class="ai-summary">. Bold the key insight. 1-3 sentences.

3. DETAIL TABLE (if breakdowns exist):
<table class="ai-table">
  <thead><tr><th>Stage</th><th>Sessions</th><th>vs LY</th></tr></thead>
  <tbody><tr><td>Search</td><td>865</td><td class="up">+12%</td></tr></tbody>
</table>

4. SECTION HEADINGS — <h4 class="ai-section-heading">Title</h4>

RULES:
- CRITICAL: Format ALL numbers properly — £ values with commas and exactly 2dp (£10,864.23 not £10864.52999999997), percentages to 1dp with % (−12.0% not −0.12024140746527696), integers with commas (243,366 not 243366). NEVER show raw floating point artifacts or more than 2 decimal places on money.
- Do NOT change any verified numbers or facts (but DO clean up their formatting)
- Do NOT add analysis not in the original
- Do NOT use emojis or markdown — pure HTML only
- Remove "Source: Query N" citations, "Which SQL produced which numbers" sections, and referral messages
- Remove any offers to run more queries or suggestions of what to ask next
- Keep output concise — dashboard space is limited
- Confident, direct tone` },
      { role: 'user', content: `${evidenceBlock}## ANSWER TO VERIFY AND FORMAT\n${answer}` },
    ], null, apiKey, 4096);
    return (response.choices?.[0]?.message?.content || answer) + noDataWarning;
  } catch {
    return answer + noDataWarning;
  }
}


// ── Main Q&A engine ───────────────────────────────────────────────────────

async function handleQuestion({ question, driverContext, conversationHistory, mode, trendSQL, fieldDiscovery }, env) {
  const apiKey = env.OPENAI_API_KEY;
  const serviceAccount = env.GCP_SERVICE_ACCOUNT_KEY;

  if (!apiKey || !serviceAccount) {
    return { error: 'Missing API keys. Configure OPENAI_API_KEY and GCP_SERVICE_ACCOUNT_KEY in Cloudflare Pages settings.' };
  }

  const bqToken = await getBQAccessToken(serviceAccount);

  // ── Trend mode: run TY + LY SQL directly, no AI needed ──
  if (mode === 'trend' && trendSQL) {
    try {
      const tyResult = await runBQQuery(trendSQL.ty, bqToken);
      const lyResult = await runBQQuery(trendSQL.ly, bqToken);
      return { trend: { ty: tyResult, ly: lyResult } };
    } catch (e) {
      return { error: 'Trend query failed: ' + e.message };
    }
  }

  // ── Date: use Worker server time (no BQ call needed) ──
  const sqlQueries = [];
  const todaysDate = new Date().toISOString().slice(0, 10);

  // ── Field discovery: pre-computed by pipeline, passed from frontend ──
  let fieldValuesContext = '';
  if (fieldDiscovery && typeof fieldDiscovery === 'object') {
    const formatSection = (tableName, data) => {
      if (!data || typeof data !== 'object') return '';
      return `### ${tableName}\n` + Object.entries(data).map(([field, values]) => {
        const valStr = Array.isArray(values) ? values.join(', ') : String(values);
        return `- ${field}: ${valStr}`;
      }).join('\n');
    };
    const policySection = formatSection('insurance_trading_data', fieldDiscovery.policies);
    const webSection = formatSection('insurance_web_utm_4', fieldDiscovery.web);
    if (policySection || webSection) {
      fieldValuesContext = `\n## KNOWN FIELD VALUES (from last 30 days — use these exact values in filters)\n\n${policySection}\n\n${webSection}\n`;
    }
  }

  const systemPrompt = `You are Trading Covered's AI analyst for Holiday Extras (HX) insurance.
You answer questions about trading data by writing and executing BigQuery SQL queries.

${SCHEMA_KNOWLEDGE}
${BUSINESS_CONTEXT}

## DATE CONTEXT — CRITICAL
Today's date is ${todaysDate} (confirmed from BigQuery CURRENT_DATE()).
ALWAYS use CURRENT_DATE() in your SQL for date calculations. Examples:
- "yesterday" = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
- "last 7 days" = BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) AND DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
- "same day last year" = DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY) (or 364 for day-of-week match)
- "FYTD" = BETWEEN DATE(EXTRACT(YEAR FROM DATE_SUB(CURRENT_DATE(), INTERVAL 3 MONTH)), 4, 1) AND CURRENT_DATE()
NEVER hardcode date literals like DATE '2026-03-11'. ALWAYS use CURRENT_DATE() expressions so the query is always correct regardless of when it runs.
If the driver context below mentions a specific date, IGNORE it for SQL purposes and use CURRENT_DATE() instead.
${fieldValuesContext}
${driverContext ? `## CURRENT DRIVER CONTEXT (use for topic context only, NOT for dates)\nThe user is asking about THIS specific driver. Assume all questions relate to it unless they explicitly say otherwise.\n${driverContext}\n` : ''}

## INVESTIGATION APPROACH — GET TO THE "WHY"
When the user asks WHY something is happening (conversion changed, GP moved, volume shifted), don't just
confirm the headline number. DECOMPOSE it by running a query that breaks the metric down by the most
relevant dimensions. Use up to 8 rounds to drill into the real driver.

Drill-down dimensions (pick the most relevant 2-3 for the question):
- **distribution_channel** — Direct, Aggregator, Partner Referral, Renewals
- **policy_type** — Single, Annual
- **cover_level_name** — Bronze, Silver, Gold, Elite (only available in trading table, not in web pre-search)
- **device_type** — mobile, computer, tablet (web table)
- **insurance_group** — sub-channel (Web Links, Direct Mailings, Affiliates, etc.)
- **customer_type** — New, Existing, Lapsed, Re-engaged
- **booking_source** — Web, Phone
- **medical_split** — Medical, Non-Medical
- **destination_group** — Europe Inc, Worldwide Exc, UK, etc.
- **scheme_name** — specific product scheme

Strategy:
1. Round 1: Get the headline metric with a YoY comparison (confirm the movement)
2. Round 2: Break it down by the most likely driver dimension (e.g. device_type for conversion, distribution_channel for GP)
3. Round 3-4: If one segment stands out, drill deeper into it by a second dimension
4. In your answer, lead with "The main driver is X" — not just a data table

For web funnel questions: session-to-search can only be broken down to distribution_channel → insurance_group →
customer_type → device_type (policy_type and cover_level are NOT known until after search results).

## RULES
1. Write SQL to answer the question. Use fully qualified table names.
2. After getting results, analyze them and provide a clear, grounded answer. Get to the WHY, not just the WHAT.
3. NEVER speculate beyond what the SQL results show. If data doesn't answer the question, say so.
4. State timeframes explicitly (e.g. "over the last 7 days", "yesterday vs same day last year").
5. FORMAT ALL NUMBERS PROPERLY: £ values with commas and 2dp (£10,864.23 not £10864.23000000001), percentages to 1dp with % sign (12.3% not 0.12345678), integers with commas (243,366 not 243366). NEVER show raw floating point artifacts. Round £ to 2dp, % to 1dp.
6. You have up to 8 rounds. Always try to get to the WHY. Round 1 = confirm the headline with YoY. Round 2 = break by the most likely driver dimension. Round 3-4 = drill the standout segment by a second dimension. Round 5-8 = keep drilling if there's more to uncover. For simple "what is X?" factual questions, 1-2 rounds is fine. For "why?" questions, use as many rounds as needed to find the actual driver.
7. If SQL fails, it will be auto-retried once. Write correct SQL the first time.
8. NEVER present options or menus to the user. NEVER ask "which option do you want?" Just run the best query using your judgement and explain what you ran afterwards.
9. EVERY number you cite MUST come directly from a SQL result. Never invent, estimate, or carry forward numbers from conversation history — re-query if needed.
10. If DRIVER CONTEXT is provided, the user is asking about THAT driver. Do NOT ask for clarification about which metric, segment, or dimension — infer it from the driver context and its SQL. Only use ask_clarification if the question is truly impossible to answer from context.
11. If DRIVER CONTEXT is NOT provided (general mode), and the question is genuinely ambiguous, use ask_clarification. Refer to the KNOWN FIELD VALUES section above for examples.
12. SENSIBLE DEFAULTS: When the user asks about trends "over time" without specifying a timeframe, default to last 28 days with daily granularity and include Year-on-Year comparison (same period last year). Always include YoY comparison unless the user explicitly says not to.
17. SQL FOR CHARTING: When writing daily time-series SQL, include BOTH TY and LY values as separate columns in the same row (e.g. gp, gp_ly, gp_delta, gp_pct_change) so the chart can show red/green bars and growth. Use a 364-day offset for LY to match day-of-week. Name LY columns with a _ly suffix (e.g. sessions_ly, gp_ly).
13. CASE-INSENSITIVE FILTERING: When filtering by string fields, use LOWER() on both sides: WHERE LOWER(field) = LOWER('value').
14. Use the KNOWN FIELD VALUES above to write correct filters. You already know the exact values — no need to run SELECT DISTINCT first.
15. SELF-VERIFY before answering: Re-read the SQL results and check every number in your answer matches the data. If a number doesn't appear in the results, DELETE that claim. Never include unverifiable figures. Remove any "which SQL produced what" meta-commentary — just state the facts.
16. FORMAT AS CLEAN HTML. Use classes: ai-metrics, ai-metric-card, ai-metric-label, ai-metric-value, ai-metric-change (up/down) for headline metrics; ai-summary for narrative; ai-table for breakdowns; ai-section-heading for headings. No markdown, no emojis. Do NOT offer to run more queries or present follow-up suggestions.
18. CONVERSION RATE SANITY: If any conversion rate exceeds 100%, your query is WRONG. This usually means you joined the web table and trading table on a field that only exists in one table, causing row multiplication. Fix: calculate sessions and bookings SEPARATELY from their respective tables, then divide. Never join row-level then aggregate for conversion metrics.
19. CROSS-TABLE QUERIES: When you need data from both the web table and trading table, only use fields that exist in BOTH: certificate_id, insurance_group, customer_type. Do NOT filter/group the trading table by session_id, page_type, or device_type. Do NOT filter/group the web table by distribution_channel, policy_type, or cover_level_name.
20. SEARCH TRAFFIC: To count sessions that searched/got quotes, use COUNT(DISTINCT CASE WHEN page_type = 'search_results' THEN session_id END). NEVER use event_name = 'engine_search_button' — that field counts button clicks, not sessions that reached results. Session-to-search rate = sessions reaching search_results / total sessions.`;

  const tools = [{
    type: 'function',
    function: {
      name: 'run_sql',
      description: 'Execute BigQuery SQL. Use SUM(policy_count) not COUNT(*). Fully qualified table names. Use CURRENT_DATE() for date calculations — never hardcode dates.',
      parameters: {
        type: 'object',
        properties: { sql: { type: 'string', description: 'The SQL query' } },
        required: ['sql'],
      },
    },
  }, {
    type: 'function',
    function: {
      name: 'ask_clarification',
      description: 'Ask the user a clarifying question before running SQL. Use when the question is ambiguous, refers to a field/dimension you need to confirm, or could be interpreted multiple ways. ALWAYS include examples of real data values to help the user.',
      parameters: {
        type: 'object',
        properties: {
          question: { type: 'string', description: 'The clarifying question to ask the user, including examples of values/fields' },
        },
        required: ['question'],
      },
    },
  }];

  const messages = [{ role: 'system', content: systemPrompt }];

  // Add conversation history if present
  if (conversationHistory && conversationHistory.length > 0) {
    for (const msg of conversationHistory) {
      messages.push({ role: msg.role, content: msg.content });
    }
  }

  messages.push({ role: 'user', content: question });

  const MAX_ROUNDS = 8;
  const MAX_SQL_RETRIES = 2;
  let headlineResult = null; // Store first successful query result as the headline

  for (let round = 0; round < MAX_ROUNDS; round++) {
    const response = await callOpenAI(messages, tools, apiKey);
    const choice = response.choices?.[0];
    if (!choice) break;

    const msg = choice.message;
    messages.push(msg);

    // If no tool calls, we have our answer
    if (choice.finish_reason === 'stop' || !msg.tool_calls || msg.tool_calls.length === 0) {
      let rawAnswer = msg.content;
      // If AI returned empty content, force a summary from the data we have
      if (!rawAnswer || rawAnswer.trim().length < 10) {
        const successQ = sqlQueries.filter(q => q.success);
        if (successQ.length > 0) {
          // Ask AI to summarise the data we got
          const summaryResponse = await callOpenAI([
            { role: 'system', content: 'You are a trading data analyst. Summarise the SQL results below into a concise HTML answer using classes: ai-metrics, ai-metric-card, ai-metric-label, ai-metric-value, ai-metric-change (up/down), ai-summary, ai-table. Format £ with commas and 2dp, % to 1dp, integers with commas. No markdown, no emojis. Be direct and concise.' },
            { role: 'user', content: successQ.map((q, i) => `Query ${i + 1} (${q.rows} rows):\n${q.sample_data || 'No sample data'}`).join('\n\n') },
          ], null, apiKey, 4096);
          rawAnswer = summaryResponse.choices?.[0]?.message?.content || null;
        }
      }
      if (!rawAnswer || rawAnswer.trim().length < 10) {
        const failedQ = sqlQueries.filter(q => !q.success);
        rawAnswer = '<p class="ai-summary">The query didn\'t return usable results this time. ' +
          (failedQ.length > 0 ? 'Error: <em>' + (failedQ[0].error || 'Unknown').replace(/</g, '&lt;') + '</em>. ' : '') +
          'Try rephrasing your question or asking about a specific metric (e.g. "GP trend last 28 days").</p>';
      }
      const chartData = extractChartData(sqlQueries);
      return {
        answer: rawAnswer,
        sql_queries: sqlQueries.map(q => { const { result_rows, ...rest } = q; return rest; }),
        rounds: round + 1,
        chart_data: chartData,
      };
    }

    // Process tool calls
    for (const tc of msg.tool_calls) {
      // Handle clarification requests — return immediately so user can respond
      if (tc.function.name === 'ask_clarification') {
        let clarQ;
        try { clarQ = JSON.parse(tc.function.arguments).question; }
        catch { clarQ = 'Could you clarify your question?'; }
        return {
          answer: clarQ,
          needs_clarification: true,
          sql_queries: sqlQueries,
          rounds: round + 1,
        };
      }

      if (tc.function.name === 'run_sql') {
        let args;
        try {
          args = JSON.parse(tc.function.arguments);
        } catch {
          messages.push({ role: 'tool', tool_call_id: tc.id, content: 'Invalid JSON in arguments' });
          continue;
        }

        let currentSQL = args.sql;
        const { sql: corrected, warnings } = autocorrectSQL(currentSQL);
        if (warnings.length > 0) currentSQL = corrected;

        let result = null;
        let lastError = null;

        for (let attempt = 0; attempt < MAX_SQL_RETRIES; attempt++) {
          try {
            const rows = await runBQQuery(currentSQL, bqToken);
            result = JSON.stringify(rows.slice(0, 100), null, 2);
            if (rows.length > 100) result += `\n... (${rows.length} total rows, showing 100)`;
            const sampleData = rows.slice(0, 5).map(r => JSON.stringify(r)).join('\n');
            sqlQueries.push({ sql: currentSQL, rows: rows.length, success: true, sample_data: sampleData, result_rows: rows.slice(0, 200) });
            // Store first successful result as the headline
            if (!headlineResult && rows.length > 0) {
              headlineResult = sampleData;
            }
            break;
          } catch (e) {
            lastError = e.message;
            if (attempt < MAX_SQL_RETRIES - 1) {
              // Ask AI to fix the SQL
              const fixResponse = await callOpenAI([
                { role: 'system', content: 'Fix this BigQuery SQL error. Return ONLY the corrected SQL, nothing else.' },
                { role: 'user', content: `SQL:\n${currentSQL}\n\nError:\n${lastError}` },
              ], null, apiKey, 2048);
              let fixedSQL = fixResponse.choices?.[0]?.message?.content?.trim() || '';
              // Strip markdown code fences from fix response
              fixedSQL = fixedSQL.replace(/^```(?:sql)?\s*\n?/i, '').replace(/\n?```\s*$/i, '').trim();
              if (fixedSQL && fixedSQL !== currentSQL) {
                currentSQL = fixedSQL;
              } else {
                // Can't fix, break
                break;
              }
            }
          }
        }

        if (result) {
          const prefix = warnings.length > 0 ? `Auto-corrected: ${warnings.join('; ')}\n\n` : '';
          // Sanity check: flag any values that look like >100% conversion rates
          let sanityWarning = '';
          try {
            const parsed = JSON.parse(result);
            if (Array.isArray(parsed)) {
              for (const row of parsed) {
                for (const [k, v] of Object.entries(row)) {
                  if (/rate|conversion|pct|percent/i.test(k) && typeof v === 'number' && v > 100) {
                    sanityWarning = `\n\nWARNING: ${k}=${v} exceeds 100%. This is impossible for a conversion rate. Your query likely has a bad join causing row multiplication. Recalculate sessions and bookings SEPARATELY from their respective tables, then divide.`;
                    break;
                  }
                }
                if (sanityWarning) break;
              }
            }
          } catch { /* not JSON, skip */ }
          messages.push({ role: 'tool', tool_call_id: tc.id, content: prefix + result + sanityWarning });
        } else {
          sqlQueries.push({ sql: currentSQL, error: lastError, success: false });
          messages.push({ role: 'tool', tool_call_id: tc.id, content: `SQL failed after retries: ${lastError}` });
        }
      }
    }

    // After processing tools, inject a thinking prompt to guide next investigation step
    if (round < MAX_ROUNDS - 1) {
      const successCount = sqlQueries.filter(q => q.success).length;
      const anyFailed = sqlQueries.some(q => !q.success);

      if (successCount === 0) {
        messages.push({
          role: 'user',
          content: `Round ${round + 1} complete. Your SQL failed. Try again with a simpler, corrected query. Check table names, column names, and date expressions carefully.`,
        });
      } else if (successCount === 1) {
        // First successful query — drill deeper but remember the headline
        messages.push({
          role: 'user',
          content: `Round ${round + 1} complete. Good, you have the headline number. REMEMBER this headline — you MUST include it in your final answer (the WHAT). Now THINK: what dimension would most likely explain WHY? Break it down by that dimension in your next query.`,
        });
      } else if (successCount < 4) {
        // Have some data — keep drilling if needed
        const headlineReminder = headlineResult ? `\n\nREMEMBER your headline result from Round 1:\n${headlineResult}\nPresent THIS first in your answer (the WHAT), then explain the WHY.` : '';
        messages.push({
          role: 'user',
          content: `Round ${round + 1} complete. Review your results so far. THINK: does one segment stand out as the main driver? If yes, drill deeper. If you have enough to explain the WHY, provide your final answer as formatted HTML. Structure: (1) The headline WHAT with the actual number and YoY comparison, THEN (2) The WHY — what is driving it, broken down by dimension. Always give the WHAT first.${headlineReminder}`,
        });
      } else {
        // Enough data gathered — synthesise
        const headlineReminder2 = headlineResult ? `\n\nYour headline result from Round 1 (present THIS first):\n${headlineResult}` : '';
        messages.push({
          role: 'user',
          content: `Round ${round + 1} complete. You have substantial data across ${successCount} queries. Provide your final answer as formatted HTML. Structure: (1) THE WHAT — the headline metric with the actual number and YoY change. (2) THE WHY — what is driving it, with dimensional breakdown. Always give the overall number first before explaining what's behind it.${headlineReminder2}`,
        });
      }
    }
  }

  // If we exhausted rounds, get final answer
  const finalResponse = await callOpenAI(messages, null, apiKey);
  let rawContent = finalResponse.choices?.[0]?.message?.content;
  if (!rawContent || rawContent.trim().length < 10) {
    const successQ = sqlQueries.filter(q => q.success);
    if (successQ.length > 0) {
      const summaryResponse = await callOpenAI([
        { role: 'system', content: 'You are a trading data analyst. Summarise the SQL results below into a concise HTML answer using classes: ai-metrics, ai-metric-card, ai-metric-label, ai-metric-value, ai-metric-change (up/down), ai-summary, ai-table. Format £ with commas and 2dp, % to 1dp, integers with commas. No markdown, no emojis. Be direct and concise.' },
        { role: 'user', content: successQ.map((q, i) => `Query ${i + 1} (${q.rows} rows):\n${q.sample_data || 'No sample data'}`).join('\n\n') },
      ], null, apiKey, 4096);
      rawContent = summaryResponse.choices?.[0]?.message?.content || null;
    }
    if (!rawContent || rawContent.trim().length < 10) {
      const failedQ = sqlQueries.filter(q => !q.success);
      rawContent = '<p class="ai-summary">The query didn\'t return usable results this time. ' +
        (failedQ.length > 0 ? 'Error: <em>' + (failedQ[0].error || 'Unknown').replace(/</g, '&lt;') + '</em>. ' : '') +
        'Try rephrasing your question or asking about a specific metric (e.g. "GP trend last 28 days").</p>';
    }
  }
  const chartData = extractChartData(sqlQueries);
  return {
    answer: rawContent,
    sql_queries: sqlQueries.map(q => { const { result_rows, ...rest } = q; return rest; }),
    rounds: MAX_ROUNDS,
    chart_data: chartData,
  };
}


// ── Request handler ───────────────────────────────────────────────────────

export async function onRequestPost(context) {
  const { request, env } = context;

  try {
    const body = await request.json();
    const { question, driver_context, conversation_history, mode, trend_sql, field_discovery } = body;

    if (!question && mode !== 'trend') {
      return new Response(JSON.stringify({ error: 'Missing question' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const result = await handleQuestion({
      question: question || '',
      driverContext: driver_context || '',
      conversationHistory: conversation_history || [],
      mode: mode || 'general',
      trendSQL: trend_sql || null,
      fieldDiscovery: field_discovery || null,
    }, env);

    return new Response(JSON.stringify(result), {
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

// Handle CORS preflight
export async function onRequestOptions() {
  return new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}
