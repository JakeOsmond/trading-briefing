/**
 * /api/verify — Human verification of contested findings
 *
 * GET  /api/verify?date=2026-03-17  → Returns all verification overrides for that date
 * POST /api/verify                   → Verify, remove, or revert a finding (requires password)
 *
 * Body: { finding_id, action: "verify"|"remove"|"revert", date, password, verified_by?, note? }
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

  // POST — verify, remove, or revert a finding (or authenticate for session)
  if (request.method === "POST") {
    let body;
    try {
      body = await request.json();
    } catch {
      return Response.json({ error: "Invalid JSON body" }, { status: 400, headers: corsHeaders });
    }

    const { finding_id, action, date, password, session_token, verified_by, note } = body;

    // Session auth — authenticate once, get a token for subsequent requests
    if (action === "auth") {
      const expectedPassword = env.VERIFY_PASSWORD;
      if (!expectedPassword || password !== expectedPassword) {
        return Response.json({ error: "Incorrect password" }, { status: 403, headers: corsHeaders });
      }
      // Generate a session token (random hex, 4h TTL)
      const token = Array.from(crypto.getRandomValues(new Uint8Array(16)))
        .map(b => b.toString(16).padStart(2, '0')).join('');
      if (env.VERIFICATION_KV) {
        await env.VERIFICATION_KV.put(`session:${token}`, "valid", { expirationTtl: 4 * 60 * 60 });
      }
      return Response.json({ success: true, session_token: token, expires_in: "4h" }, { headers: corsHeaders });
    }

    // Validate required fields
    if (!finding_id || !action || !date) {
      return Response.json({ error: "Missing required fields: finding_id, action, date" }, { status: 400, headers: corsHeaders });
    }

    // Validate action
    if (!["verify", "remove", "revert", "remove_context", "add_context"].includes(action)) {
      return Response.json({ error: "Invalid action" }, { status: 400, headers: corsHeaders });
    }

    // Authenticate via password OR session token
    const expectedPassword = env.VERIFY_PASSWORD;
    let authenticated = false;
    if (password && expectedPassword && password === expectedPassword) {
      authenticated = true;
    } else if (session_token && env.VERIFICATION_KV) {
      const tokenValid = await env.VERIFICATION_KV.get(`session:${session_token}`);
      if (tokenValid === "valid") authenticated = true;
    }
    if (!authenticated) {
      return Response.json({ error: "Authentication required — provide password or valid session_token" }, { status: 403, headers: corsHeaders });
    }

    // Check KV binding
    if (!env.VERIFICATION_KV) {
      return Response.json({ error: "KV storage not configured" }, { status: 500, headers: corsHeaders });
    }

    const key = `verification:${date}:${finding_id}`;

    // Revert — delete the KV entry
    if (action === "revert") {
      await env.VERIFICATION_KV.delete(key);
      return Response.json({ success: true, action: "reverted", key }, { headers: corsHeaders });
    }

    // Remove context — store removal request for pipeline to process
    if (action === "remove_context") {
      const ctxKey = `context_removal:${finding_id}`;
      const ctxValue = {
        action: "remove_context",
        filed_info: note ? JSON.parse(note) : {},
        requested_by: verified_by || "dashboard_user",
        timestamp: new Date().toISOString(),
      };
      await env.VERIFICATION_KV.put(ctxKey, JSON.stringify(ctxValue), { expirationTtl: 30 * 24 * 60 * 60 });
      return Response.json({ success: true, action: "context_removal_queued", key: ctxKey }, { headers: corsHeaders });
    }

    // Add context — store raw text for pipeline to reformat + classify + file
    if (action === "add_context") {
      const addKey = `context_add:${finding_id}`;
      const addValue = {
        action: "add_context",
        raw_text: note || "",
        added_by: verified_by || "dashboard_user",
        timestamp: new Date().toISOString(),
      };
      await env.VERIFICATION_KV.put(addKey, JSON.stringify(addValue), { expirationTtl: 30 * 24 * 60 * 60 });
      return Response.json({ success: true, action: "context_add_queued", key: addKey }, { headers: corsHeaders });
    }

    // Verify or remove — write to KV
    const value = {
      action,
      verified_by: verified_by || null,
      note: note || null,
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
