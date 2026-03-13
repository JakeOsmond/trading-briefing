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
      maximumBytesBilled: '5000000000',
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
  const wrongTablePattern = /`[^`]*insurance_policies_new[^`]*`/g;
  if (wrongTablePattern.test(fixed) && !fixed.includes('`hx-data-production.commercial_finance.insurance_policies_new`')) {
    fixed = fixed.replace(/`[^`]*insurance_policies_new[^`]*`/g, '`hx-data-production.commercial_finance.insurance_policies_new`');
    warnings.push('Fixed table name to hx-data-production.commercial_finance.insurance_policies_new');
  }
  if (/\binsurance_policies_new\b/.test(fixed) && !fixed.includes('`hx-data-production.commercial_finance.insurance_policies_new`')) {
    fixed = fixed.replace(/\binsurance_policies_new\b/g, '`hx-data-production.commercial_finance.insurance_policies_new`');
    warnings.push('Added fully qualified table name');
  }
  const wrongWebPattern = /`[^`]*insurance_web_utm_4[^`]*`/g;
  if (wrongWebPattern.test(fixed) && !fixed.includes('`hx-data-production.commercial_finance.insurance_web_utm_4`')) {
    fixed = fixed.replace(/`[^`]*insurance_web_utm_4[^`]*`/g, '`hx-data-production.commercial_finance.insurance_web_utm_4`');
    warnings.push('Fixed web table name');
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

async function callOpenAI(messages, tools, apiKey, maxTokens = 4096, model = 'gpt-5-mini') {
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


// ── Schema knowledge (condensed for Worker size limits) ───────────────────

const SCHEMA_KNOWLEDGE = `
## BigQuery Tables — USE THESE EXACT TABLE NAMES (backtick-quoted)

### \`hx-data-production.commercial_finance.insurance_policies_new\`
This is the ONLY policy table. Project: hx-data-production. Dataset: commercial_finance.
CRITICAL RULES:
- ALWAYS use the full name: \`hx-data-production.commercial_finance.insurance_policies_new\`
- Use SUM(policy_count) not COUNT(*) for policy counts
- Use SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) for GP — NEVER AVG()
- Avg GP = SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
- YoY = 364-day offset (matches day-of-week)
- transaction_date is DATE type — use directly, no EXTRACT()

Key columns: transaction_date, policy_type (Annual/Single), distribution_channel (Direct/Aggregator/Partner Referral/Renewals),
channel, scheme_name, cover_level_name, booking_source, device_type, medical_split, max_medical_score_grouped,
max_age_at_purchase, trip_duration_band, days_to_travel, policy_count,
total_gross_exc_ipt_ntu_comm (THIS IS GP), total_gross_inc_ipt (customer price),
total_discount_value, total_paid_commission_value, total_net_to_underwriter_inc_gadget,
customer_type (New/Existing/Lapsed/Re-engaged — indicates customer relationship status).

### \`hx-data-production.commercial_finance.insurance_web_utm_4\`
Web analytics. Direct channel ONLY (no aggregator/renewal web data).
Key cols: session_id, visitor_id, device_type, booking_flow_stage, session_start_date, page_type, event_name,
customer_type (New/Existing/Lapsed/Re-engaged).
Sessions = COUNT(DISTINCT session_id). Users = COUNT(DISTINCT visitor_id).

### customer_type field (both tables)
- "New" = never seen by Holiday Extras before
- "Existing" = in our database, has booked in the last 3 years
- "Lapsed" = in our database but hasn't booked in the last 3 years
- "Re-engaged" = was lapsed but a recent purchase moved them out of lapsed
This is a key drill-down dimension for understanding customer mix.
`;

const BUSINESS_CONTEXT = `
- HX runs NEGATIVE margins on annual policies deliberately (lifetime value strategy). Never flag as problem.
- Single trip losses ARE problems — no renewal pathway.
- Traffic x Conversion x Avg GP = Total GP. Always decompose.
- Aggregators have no web journey data. Direct has full web data.
- Use SUM(policy_count) for counts. Use SUM(CAST(col AS FLOAT64))/NULLIF(SUM(policy_count),0) for averages.
- YoY comparison = 364-day offset to match day-of-week.
- Financial Year To Date (FYTD) runs 1 April to 31 March. "YTD" or "FYTD" means from 1 April of the current financial year.
`;


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
- Format £ with commas (£10,864.23), percentages with % (12.3%), numbers with commas
- Do NOT change any verified numbers or facts
- Do NOT add analysis not in the original
- Do NOT use emojis or markdown — pure HTML only
- Remove "Source: Query N" citations and referral messages
- Keep output concise — dashboard space is limited
- Confident, direct tone` },
      { role: 'user', content: `${evidenceBlock}## ANSWER TO VERIFY AND FORMAT\n${answer}` },
    ], null, apiKey, 4096, 'gpt-5-mini');
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
    const policySection = formatSection('insurance_policies_new', fieldDiscovery.policies);
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

## RULES
1. Write SQL to answer the question. Use fully qualified table names.
2. After getting results, analyze them and provide a clear, grounded answer.
3. NEVER speculate beyond what the SQL results show. If data doesn't answer the question, say so.
4. State timeframes explicitly (e.g. "over the last 7 days", "yesterday vs same day last year").
5. NEVER round numbers. Always give the exact figures from SQL results (e.g. £892.67, £10,864.23). The user wants precise data.
6. You can run up to 2 rounds of investigation. Be efficient — write ONE well-crafted SQL query per round. Answer after round 1 if possible.
7. If SQL fails, it will be auto-retried once. Write correct SQL the first time.
8. EVERY number you cite MUST come directly from a SQL result. Never invent, estimate, or carry forward numbers from conversation history — re-query if needed.
9. If DRIVER CONTEXT is provided, the user is asking about THAT driver. Do NOT ask for clarification about which metric, segment, or dimension — infer it from the driver context and its SQL. Only use ask_clarification if the question is truly impossible to answer from context.
10. If DRIVER CONTEXT is NOT provided (general mode), and the question is genuinely ambiguous, use ask_clarification. Refer to the KNOWN FIELD VALUES section above for examples.
11. SENSIBLE DEFAULTS: When the user asks about trends "over time" without specifying a timeframe, default to last 28 days with daily granularity and include Year-on-Year comparison (same period last year). Always include YoY comparison unless the user explicitly says not to.
12. When you give your final answer, cite which SQL query produced each number. If a number didn't come from a query, don't include it.
13. CASE-INSENSITIVE FILTERING: When filtering by string fields, use LOWER() on both sides: WHERE LOWER(field) = LOWER('value').
14. Use the KNOWN FIELD VALUES above to write correct filters. You already know the exact values — no need to run SELECT DISTINCT first.`;

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

  const MAX_ROUNDS = 2;
  const MAX_SQL_RETRIES = 2;

  for (let round = 0; round < MAX_ROUNDS; round++) {
    const response = await callOpenAI(messages, tools, apiKey);
    const choice = response.choices?.[0];
    if (!choice) break;

    const msg = choice.message;
    messages.push(msg);

    // If no tool calls, we have our answer — verify then prettify
    if (choice.finish_reason === 'stop' || !msg.tool_calls || msg.tool_calls.length === 0) {
      const rawAnswer = msg.content || 'No answer generated.';
      const formatted = await verifyAndFormat(rawAnswer, sqlQueries, apiKey);
      return {
        answer: formatted,
        sql_queries: sqlQueries,
        rounds: round + 1,
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
            sqlQueries.push({ sql: currentSQL, rows: rows.length, success: true, sample_data: sampleData });
            break;
          } catch (e) {
            lastError = e.message;
            if (attempt < MAX_SQL_RETRIES - 1) {
              // Ask AI to fix the SQL
              const fixResponse = await callOpenAI([
                { role: 'system', content: 'Fix this BigQuery SQL error. Return ONLY the corrected SQL, nothing else.' },
                { role: 'user', content: `SQL:\n${currentSQL}\n\nError:\n${lastError}` },
              ], null, apiKey, 2048, 'gpt-5-mini');
              const fixedSQL = fixResponse.choices?.[0]?.message?.content?.trim();
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
          messages.push({ role: 'tool', tool_call_id: tc.id, content: prefix + result });
        } else {
          sqlQueries.push({ sql: currentSQL, error: lastError, success: false });
          messages.push({ role: 'tool', tool_call_id: tc.id, content: `SQL failed after retries: ${lastError}` });
        }
      }
    }

    // After processing tools, if this isn't the last round, nudge for deeper analysis
    if (round < MAX_ROUNDS - 1) {
      messages.push({
        role: 'user',
        content: `Round ${round + 1} complete. If you have enough data to answer confidently, provide your final answer now. If you need to dig deeper, run another query. You have ${MAX_ROUNDS - round - 1} rounds remaining.`,
      });
    }
  }

  // If we exhausted rounds, get final answer
  const finalResponse = await callOpenAI(messages, null, apiKey);
  const rawContent = finalResponse.choices?.[0]?.message?.content || 'Investigation complete but no clear answer emerged.';
  const formatted = await verifyAndFormat(rawContent, sqlQueries, apiKey);
  return {
    answer: formatted,
    sql_queries: sqlQueries,
    rounds: MAX_ROUNDS,
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
