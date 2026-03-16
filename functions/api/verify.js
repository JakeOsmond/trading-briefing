/**
 * /api/verify — Human verification of contested findings
 *
 * GET  /api/verify?date=2026-03-17  → Returns all verification overrides for that date
 * POST /api/verify                   → Verify or remove a finding (requires password)
 *
 * Body: { finding_id, action: "verify"|"remove", date, password }
 * KV key: verification:{date}:{finding_id}
 */

export async function onRequest(context) {
  const { request, env } = context;

  // CORS headers
  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };

  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders });
  }

  // GET — fetch all verification overrides for a date
  if (request.method === "GET") {
    const url = new URL(request.url);
    const date = url.searchParams.get("date");
    if (!date) {
      return Response.json({ error: "Missing date parameter" }, { status: 400, headers: corsHeaders });
    }

    if (!env.VERIFICATION_KV) {
      return Response.json({ findings: {} }, { headers: corsHeaders });
    }

    // List all keys for this date
    const prefix = `verification:${date}:`;
    const list = await env.VERIFICATION_KV.list({ prefix });
    const findings = {};

    for (const key of list.keys) {
      const value = await env.VERIFICATION_KV.get(key.name, { type: "json" });
      if (value) {
        const findingId = key.name.replace(prefix, "");
        findings[findingId] = value;
      }
    }

    return Response.json({ findings }, { headers: corsHeaders });
  }

  // POST — verify or remove a finding
  if (request.method === "POST") {
    let body;
    try {
      body = await request.json();
    } catch {
      return Response.json({ error: "Invalid JSON body" }, { status: 400, headers: corsHeaders });
    }

    const { finding_id, action, date, password } = body;

    // Validate required fields
    if (!finding_id || !action || !date || !password) {
      return Response.json({ error: "Missing required fields: finding_id, action, date, password" }, { status: 400, headers: corsHeaders });
    }

    // Validate action
    if (!["verify", "remove"].includes(action)) {
      return Response.json({ error: "Action must be 'verify' or 'remove'" }, { status: 400, headers: corsHeaders });
    }

    // Check password
    const expectedPassword = env.VERIFY_PASSWORD;
    if (!expectedPassword) {
      return Response.json({ error: "Verification not configured — VERIFY_PASSWORD secret missing" }, { status: 500, headers: corsHeaders });
    }
    if (password !== expectedPassword) {
      return Response.json({ error: "Incorrect password" }, { status: 403, headers: corsHeaders });
    }

    // Check KV binding
    if (!env.VERIFICATION_KV) {
      return Response.json({ error: "KV storage not configured" }, { status: 500, headers: corsHeaders });
    }

    // Write to KV
    const key = `verification:${date}:${finding_id}`;
    const value = {
      action,
      timestamp: new Date().toISOString(),
    };

    await env.VERIFICATION_KV.put(key, JSON.stringify(value), {
      // Auto-expire after 90 days
      expirationTtl: 90 * 24 * 60 * 60,
    });

    return Response.json({ success: true, key, value }, { headers: corsHeaders });
  }

  return Response.json({ error: "Method not allowed" }, { status: 405, headers: corsHeaders });
}
