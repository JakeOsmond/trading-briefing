// Cloudflare Pages Function — no auth, pass all requests through
export const onRequest = [({ next }) => next()];
