// Cloudflare Pages Function — Google OAuth middleware
// Protects all pages behind Google Workspace login
// Only @holidayextras.com users can access (enforced by Google Workspace "Internal" OAuth)

const COOKIE_NAME = "tc_session";
const SESSION_MAX_AGE = 60 * 60 * 24 * 30; // 30 days

async function handleAuth(context) {
  const { request, env, next } = context;
  const url = new URL(request.url);

  const CLIENT_ID = env.GOOGLE_CLIENT_ID;
  const CLIENT_SECRET = env.GOOGLE_CLIENT_SECRET;
  const REDIRECT_URI = `${url.origin}/auth/callback`;

  // Skip auth for the callback route itself
  if (url.pathname === "/auth/callback") {
    return handleCallback(request, env, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI);
  }

  // Skip auth for the logout route
  if (url.pathname === "/auth/logout") {
    return new Response("Logged out", {
      status: 302,
      headers: {
        Location: "/",
        "Set-Cookie": `${COOKIE_NAME}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax`,
      },
    });
  }

  // Check for valid session cookie
  const cookie = parseCookie(request.headers.get("Cookie") || "");
  const sessionToken = cookie[COOKIE_NAME];

  if (sessionToken) {
    try {
      const session = JSON.parse(atob(sessionToken));
      if (session.exp > Date.now() / 1000 && session.email) {
        // Valid session — pass through
        return next();
      }
    } catch (e) {
      // Invalid cookie — fall through to login
    }
  }

  // No valid session — redirect to Google OAuth
  const state = crypto.randomUUID();
  const authUrl = new URL("https://accounts.google.com/o/oauth2/v2/auth");
  authUrl.searchParams.set("client_id", CLIENT_ID);
  authUrl.searchParams.set("redirect_uri", REDIRECT_URI);
  authUrl.searchParams.set("response_type", "code");
  authUrl.searchParams.set("scope", "openid email profile");
  authUrl.searchParams.set("state", state);
  authUrl.searchParams.set("prompt", "select_account");
  // hd parameter restricts the Google login to holidayextras.com domain
  authUrl.searchParams.set("hd", "holidayextras.com");

  return new Response(null, {
    status: 302,
    headers: { Location: authUrl.toString() },
  });
}

async function handleCallback(request, env, clientId, clientSecret, redirectUri) {
  const url = new URL(request.url);
  const code = url.searchParams.get("code");

  if (!code) {
    return new Response("Missing authorization code", { status: 400 });
  }

  // Exchange code for tokens
  const tokenResponse = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      code,
      client_id: clientId,
      client_secret: clientSecret,
      redirect_uri: redirectUri,
      grant_type: "authorization_code",
    }),
  });

  const tokens = await tokenResponse.json();
  if (!tokens.id_token) {
    return new Response("Authentication failed", { status: 401 });
  }

  // Decode the ID token (JWT) to get user info
  const payload = JSON.parse(atob(tokens.id_token.split(".")[1]));
  const email = payload.email;
  const name = payload.name || email.split("@")[0];

  // Verify the email domain
  if (!email.endsWith("@holidayextras.com")) {
    return new Response(
      `<html><body style="font-family:sans-serif;text-align:center;padding:60px">
        <h2>Access Denied</h2>
        <p>${email} is not authorized. Only Holiday Extras accounts can access this tool.</p>
        <a href="/auth/logout">Try a different account</a>
      </body></html>`,
      { status: 403, headers: { "Content-Type": "text/html" } }
    );
  }

  // Create session cookie
  const session = {
    email,
    name,
    exp: Math.floor(Date.now() / 1000) + SESSION_MAX_AGE,
  };
  const sessionToken = btoa(JSON.stringify(session));

  return new Response(null, {
    status: 302,
    headers: {
      Location: "/",
      "Set-Cookie": `${COOKIE_NAME}=${sessionToken}; Path=/; Max-Age=${SESSION_MAX_AGE}; HttpOnly; Secure; SameSite=Lax`,
    },
  });
}

function parseCookie(cookieHeader) {
  const cookies = {};
  cookieHeader.split(";").forEach((c) => {
    const [key, ...val] = c.trim().split("=");
    if (key) cookies[key] = val.join("=");
  });
  return cookies;
}

export const onRequest = [handleAuth];
