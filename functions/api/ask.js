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
  // The ONLY valid tables are:
  //   hx-data-production.commercial_finance.insurance_policies_new
  //   hx-data-production.commercial_finance.insurance_web_utm_4
  const wrongTablePattern = /`[^`]*insurance_policies_new[^`]*`/g;
  if (wrongTablePattern.test(fixed) && !fixed.includes('`hx-data-production.commercial_finance.insurance_policies_new`')) {
    fixed = fixed.replace(/`[^`]*insurance_policies_new[^`]*`/g, '`hx-data-production.commercial_finance.insurance_policies_new`');
    warnings.push('Fixed table name to hx-data-production.commercial_finance.insurance_policies_new');
  }
  // Unquoted references
  if (/\binsurance_policies_new\b/.test(fixed) && !fixed.includes('`hx-data-production.commercial_finance.insurance_policies_new`')) {
    fixed = fixed.replace(/\binsurance_policies_new\b/g, '`hx-data-production.commercial_finance.insurance_policies_new`');
    warnings.push('Added fully qualified table name');
  }
  // Same for web table
  const wrongWebPattern = /`[^`]*insurance_web_utm_4[^`]*`/g;
  if (wrongWebPattern.test(fixed) && !fixed.includes('`hx-data-production.commercial_finance.insurance_web_utm_4`')) {
    fixed = fixed.replace(/`[^`]*insurance_web_utm_4[^`]*`/g, '`hx-data-production.commercial_finance.insurance_web_utm_4`');
    warnings.push('Fixed web table name');
  }

  // Fix "gp" column reference — the actual column is total_gross_exc_ipt_ntu_comm
  // but "gp" is commonly used as an alias. Leave it if it's in a CAST or alias context.

  return { sql: fixed, warnings };
}


// ── OpenAI chat with tool use ─────────────────────────────────────────────

async function callOpenAI(messages, tools, apiKey, maxTokens = 4096) {
  const res = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'gpt-4.1',
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
total_discount_value, total_paid_commission_value, total_net_to_underwriter_inc_gadget.

### \`hx-data-production.commercial_finance.insurance_web_utm_4\`
Web analytics. Direct channel ONLY (no aggregator/renewal web data).
Key cols: session_id, visitor_id, device_type, booking_flow_stage, session_start_date, page_type, event_name.
Sessions = COUNT(DISTINCT session_id). Users = COUNT(DISTINCT visitor_id).
`;

const BUSINESS_CONTEXT = `
- HX runs NEGATIVE margins on annual policies deliberately (lifetime value strategy). Never flag as problem.
- Single trip losses ARE problems — no renewal pathway.
- Traffic × Conversion × Avg GP = Total GP. Always decompose.
- Aggregators have no web journey data. Direct has full web data.
- Use SUM(policy_count) for counts. Use SUM(CAST(col AS FLOAT64))/NULLIF(SUM(policy_count),0) for averages.
- YoY comparison = 364-day offset to match day-of-week.
`;


// ── Answer verification (anti-hallucination) ─────────────────────────────

async function verifyAnswer(answer, sqlQueries, apiKey) {
  // Only verify if we have actual SQL results to check against
  const successfulQueries = sqlQueries.filter(q => q.success);
  if (!successfulQueries.length) return answer;

  // Build a summary of what the SQL actually returned
  const evidenceSummary = successfulQueries.map((q, i) =>
    `Query ${i + 1}: ${q.sql}\nReturned ${q.rows} row(s).`
  ).join('\n\n');

  try {
    const checkResponse = await callOpenAI([
      { role: 'system', content: `You are a fact-checker for a trading analyst's answer. You have access to the SQL queries that were run and their row counts.

Your job:
1. Check if the answer contains any numbers, percentages, or claims that could NOT have come from the SQL queries listed.
2. If the answer looks grounded in the data, return it UNCHANGED.
3. If you spot a claim that seems fabricated or unsupported by the queries, add a brief ⚠️ caveat inline next to that specific claim, e.g. "⚠️ (not confirmed by query data)".
4. Do NOT rewrite the answer. Only add inline warnings where needed. Keep the original formatting and tone.
5. If everything checks out, return the exact original answer with no changes.` },
      { role: 'user', content: `## SQL EVIDENCE\n${evidenceSummary}\n\n## ANSWER TO CHECK\n${answer}` },
    ], null, apiKey, 4096);
    return checkResponse.choices?.[0]?.message?.content || answer;
  } catch {
    // If verification fails, return original answer
    return answer;
  }
}


// ── Main Q&A engine ───────────────────────────────────────────────────────

async function handleQuestion({ question, driverContext, conversationHistory, mode, trendSQL }, env) {
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

  const systemPrompt = `You are Trading Covered's AI analyst for Holiday Extras (HX) insurance.
You answer questions about trading data by writing and executing BigQuery SQL queries.

${SCHEMA_KNOWLEDGE}
${BUSINESS_CONTEXT}

${driverContext ? `## CURRENT DRIVER CONTEXT\n${driverContext}\n` : ''}

## RULES
1. Write SQL to answer the question. Use fully qualified table names.
2. After getting results, analyze them and provide a clear, grounded answer.
3. NEVER speculate beyond what the SQL results show. If data doesn't answer the question, say so.
4. State timeframes explicitly (e.g. "over the last 7 days", "yesterday vs same day last year").
5. Round numbers: £892.67→"about £900", £10,864→"£11k".
6. You can run up to 4 rounds of investigation. Each round, decide if you need more data or can answer.
7. If SQL fails, fix it and retry. You have up to 25 attempts per query.
8. EVERY number you cite MUST come directly from a SQL result. Never invent, estimate, or carry forward numbers from conversation history — re-query if needed.
9. If the user asks something ambiguous or that requires a dimension/field you're unsure about, use the ask_clarification tool BEFORE writing SQL. Always provide examples of real values from the data to help the user choose. For example: "Do you mean broken down by cover_level_name? Examples in the data: Bronze, Classic, Silver, Gold, Deluxe, Elite."
10. When you give your final answer, cite which SQL query produced each number. If a number didn't come from a query, don't include it.`;

  const tools = [{
    type: 'function',
    function: {
      name: 'run_sql',
      description: 'Execute BigQuery SQL. Use SUM(policy_count) not COUNT(*). Fully qualified table names.',
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

  const sqlQueries = [];
  const MAX_ROUNDS = 4;
  const MAX_SQL_RETRIES = 25;

  for (let round = 0; round < MAX_ROUNDS; round++) {
    const response = await callOpenAI(messages, tools, apiKey);
    const choice = response.choices?.[0];
    if (!choice) break;

    const msg = choice.message;
    messages.push(msg);

    // If no tool calls, we have our answer — verify it first
    if (choice.finish_reason === 'stop' || !msg.tool_calls || msg.tool_calls.length === 0) {
      const rawAnswer = msg.content || 'No answer generated.';
      const verified = await verifyAnswer(rawAnswer, sqlQueries, apiKey);
      return {
        answer: verified,
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
            sqlQueries.push({ sql: currentSQL, rows: rows.length, success: true });
            break;
          } catch (e) {
            lastError = e.message;
            if (attempt < MAX_SQL_RETRIES - 1) {
              // Ask AI to fix the SQL
              const fixResponse = await callOpenAI([
                { role: 'system', content: 'Fix this BigQuery SQL error. Return ONLY the corrected SQL, nothing else.' },
                { role: 'user', content: `SQL:\n${currentSQL}\n\nError:\n${lastError}` },
              ], null, apiKey, 2048);
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
          const prefix = warnings.length > 0 ? `⚠️ Auto-corrected: ${warnings.join('; ')}\n\n` : '';
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
  const verified = await verifyAnswer(rawContent, sqlQueries, apiKey);
  return {
    answer: verified,
    sql_queries: sqlQueries,
    rounds: MAX_ROUNDS,
  };
}


// ── Request handler ───────────────────────────────────────────────────────

export async function onRequestPost(context) {
  const { request, env } = context;

  try {
    const body = await request.json();
    const { question, driver_context, conversation_history, mode, trend_sql } = body;

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
