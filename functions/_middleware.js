// Cloudflare Pages Function — Team password gate
// Protects all briefings behind a simple shared password
// Password is stored as a Cloudflare Pages secret (SITE_PASSWORD)

const COOKIE_NAME = "tc_auth";
const SESSION_DAYS = 30;

async function handleAuth(context) {
  const { request, env, next } = context;
  const url = new URL(request.url);

  const SITE_PASSWORD = env.SITE_PASSWORD;

  // If no password is configured, allow everything through
  if (!SITE_PASSWORD) return next();

  // Handle login form submission
  if (url.pathname === "/auth/login" && request.method === "POST") {
    const form = await request.formData();
    const password = form.get("password");

    if (password === SITE_PASSWORD) {
      const expiry = Date.now() + SESSION_DAYS * 24 * 60 * 60 * 1000;
      const token = btoa(JSON.stringify({ exp: expiry, v: 1 }));
      return new Response(null, {
        status: 302,
        headers: {
          Location: "/",
          "Set-Cookie": `${COOKIE_NAME}=${token}; Path=/; Max-Age=${SESSION_DAYS * 86400}; HttpOnly; Secure; SameSite=Lax`,
        },
      });
    }

    // Wrong password — show form again with error
    return loginPage("Incorrect password. Try again.", url.origin);
  }

  // Handle logout
  if (url.pathname === "/auth/logout") {
    return new Response(null, {
      status: 302,
      headers: {
        Location: "/",
        "Set-Cookie": `${COOKIE_NAME}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax`,
      },
    });
  }

  // Check session cookie
  const cookie = parseCookie(request.headers.get("Cookie") || "");
  const sessionToken = cookie[COOKIE_NAME];

  if (sessionToken) {
    try {
      const session = JSON.parse(atob(sessionToken));
      if (session.exp > Date.now()) {
        return next();
      }
    } catch (e) { /* invalid cookie */ }
  }

  // No valid session — show login page
  return loginPage(null, url.origin);
}

function loginPage(error, origin) {
  const html = `<!DOCTYPE html>
<html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trading Covered — Login</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:#0F121E;color:#E2E8F0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
    display:flex;justify-content:center;align-items:center;min-height:100vh}
  .card{background:rgba(30,34,52,0.9);border:1px solid rgba(146,95,255,0.15);border-radius:16px;
    padding:40px;width:min(380px,90vw);text-align:center;
    box-shadow:0 20px 60px rgba(0,0,0,0.4)}
  .logo{width:40px;height:40px;margin:0 auto 16px;filter:drop-shadow(0 0 10px rgba(84,46,145,0.5))}
  h1{font-size:20px;font-weight:700;margin-bottom:4px}
  h1 span{color:#925FFF}
  .sub{font-size:12px;color:#94A3B8;margin-bottom:28px}
  input{width:100%;padding:12px 16px;background:rgba(15,18,30,0.8);border:1px solid rgba(146,95,255,0.2);
    border-radius:10px;color:#E2E8F0;font-size:14px;outline:none;transition:border-color 0.2s}
  input:focus{border-color:rgba(146,95,255,0.5)}
  button{width:100%;padding:12px;margin-top:12px;background:rgba(84,46,145,0.3);color:#925FFF;
    border:1px solid rgba(84,46,145,0.4);border-radius:10px;font-size:14px;font-weight:600;
    cursor:pointer;transition:all 0.2s}
  button:hover{background:rgba(84,46,145,0.5);transform:scale(1.02)}
  .error{color:#FF5F68;font-size:12px;margin-bottom:12px}
</style>
</head><body>
<div class="card">
  <img src="https://dmy0b9oeprz0f.cloudfront.net/holidayextras.co.uk/brand-guidelines/logo-tags/png/microchip.png" alt="HX" class="logo">
  <h1><span>Trading Covered</span></h1>
  <div class="sub">by Holiday Extras</div>
  ${error ? `<div class="error">${error}</div>` : ""}
  <form method="POST" action="/auth/login">
    <input type="password" name="password" placeholder="Enter team password" autofocus required>
    <button type="submit">Access Briefings</button>
  </form>
</div>
</body></html>`;

  return new Response(html, {
    status: 401,
    headers: { "Content-Type": "text/html" },
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
