import http from "node:http";
import { readFile } from "node:fs/promises";
import { timingSafeEqual } from "node:crypto";
import { fileURLToPath } from "node:url";
import { createGrid } from "./lib/grid.mjs";

const publicDir = new URL("./public/", import.meta.url);
const files = { "/": ["index.html", "text/html"], "/app.js": ["app.js", "text/javascript"], "/style.css": ["style.css", "text/css"], "/favicon.svg": ["favicon.svg", "image/svg+xml"] };
const loopback = host => ["127.0.0.1", "::1", "localhost"].includes(host);
const equal = (a, b) => { const x = Buffer.from(a), y = Buffer.from(b); return x.length === y.length && timingSafeEqual(x, y); };

export function createServer({ env = process.env, fetchImpl = fetch } = {}) {
  const grid = createGrid({ env, fetchImpl });
  const attempts = new Map();
  const accessKey = env.VOKAL_ACCESS_KEY?.trim();
  if (!loopback(env.HOST || "127.0.0.1") && !accessKey) throw new Error("Set VOKAL_ACCESS_KEY before listening on a non-loopback host.");
  const server = http.createServer(async (req, res) => {
    const reply = (status, data, type = "application/json") => {
      res.writeHead(status, { "Content-Type": type + "; charset=utf-8", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer", "Permissions-Policy": "microphone=(self)", "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; media-src 'self' blob:; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'" });
      res.end(type === "application/json" ? JSON.stringify(data) : data);
    };
    try {
      const url = new URL(req.url, "http://localhost");
      if (req.method === "GET" && files[url.pathname]) {
        const [file, type] = files[url.pathname];
        return reply(200, await readFile(new URL(file, publicDir)), type);
      }
      if (req.method === "GET" && url.pathname === "/api/config") return reply(200, { locked: !!accessKey });
      if (!["/api/status", "/api/turn", "/api/speak"].includes(url.pathname)) return reply(404, { error: "Not found." });
      if (accessKey && !equal(req.headers.authorization || "", "Bearer " + accessKey)) return reply(401, { error: "Enter the correct access key." });
      if (req.method === "GET" && url.pathname === "/api/status") return reply(200, await grid.status());
      if (req.method !== "POST") return reply(405, { error: "Method not allowed." });
      let origin;
      try { origin = new URL(req.headers.origin || ""); } catch { return reply(403, { error: "Open MoVoKaL in your browser to talk." }); }
      if (origin.host !== req.headers.host || !["http:", "https:"].includes(origin.protocol)) return reply(403, { error: "This origin is not allowed." });
      if (!(req.headers["content-type"] || "").startsWith("application/json")) return reply(415, { error: "Expected JSON." });
      const now = Date.now();
      for (const [ip, value] of attempts) if (now > value.reset) attempts.delete(ip);
      const ip = req.socket.remoteAddress;
      const window = attempts.get(ip) || { count: 0, reset: now + 60_000 };
      attempts.set(ip, window);
      if (++window.count > 30) return reply(429, { error: "Give me a moment. Please try again in a minute." });
      let body = "";
      for await (const chunk of req) {
        body += chunk.toString();
        if (Buffer.byteLength(body) > 32_768) return reply(413, { error: "This message is too long." });
      }
      let data;
      try { data = JSON.parse(body); } catch { return reply(400, { error: "Invalid JSON." }); }
      if (typeof data.text !== "string" || !data.text.trim() || data.text.length > 4000) return reply(400, { error: "Send a message between 1 and 4,000 characters." });
      const controller = new AbortController();
      const abort = () => { if (!res.writableEnded) controller.abort(); };
      res.on("close", abort);
      const timeout = setTimeout(() => controller.abort(), 120_000);
      try {
        if (url.pathname === "/api/speak") {
          if (typeof data.voice !== "string" || !/^[a-zA-Z0-9_-]{1,80}$/.test(data.voice)) return reply(400, { error: "Choose an available voice." });
          const audio = await grid.speak(data.text, data.voice, controller.signal);
          return reply(200, Buffer.from(await audio.arrayBuffer()), "audio/wav");
        }
        const history = Array.isArray(data.history) ? data.history.slice(-12) : [];
        if (history.some(x => !x || !["user", "assistant"].includes(x.role) || typeof x.content !== "string" || x.content.length > 4000)) return reply(400, { error: "Invalid conversation history." });
        const userId = typeof data.sessionId === "string" && /^[a-zA-Z0-9-]{1,80}$/.test(data.sessionId) ? "vokal-" + data.sessionId : "vokal-anonymous";
        return reply(200, await grid.respond(data.text.trim(), history, userId, controller.signal));
      } finally { clearTimeout(timeout); res.off("close", abort); }
    } catch (error) {
      if (!res.destroyed && !res.headersSent) reply(502, { error: error.name === "AbortError" || error.name === "TimeoutError" ? "MoStar took too long to respond. Please try again." : (error.message.startsWith("MoStar") || error.message.startsWith("Grid") || error.message.startsWith("Voice") ? error.message : "Couldn't reach MoStar. Check the Grid and voice services, then try again.") });
    }
  });
  server.requestTimeout = 30_000;
  server.headersTimeout = 15_000;
  return server;
}
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const host = process.env.HOST || "127.0.0.1", port = Number(process.env.PORT || 4317);
  createServer().listen(port, host, () => console.log("MoVoKaL is ready at http://" + host + ":" + port));
}
