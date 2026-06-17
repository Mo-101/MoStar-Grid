/**
 * Production server — serves dist/client/ as static, falls back to SSR.
 */
import { createServer } from "node:http";
import { createReadStream, statSync, existsSync } from "node:fs";
import { join, extname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = fileURLToPath(new URL(".", import.meta.url));
const STATIC = join(ROOT, "dist/client");
const PORT = Number(process.env.PORT ?? 41012);

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js":   "application/javascript",
  ".css":  "text/css",
  ".png":  "image/png",
  ".jpg":  "image/jpeg",
  ".jpeg": "image/jpeg",
  ".svg":  "image/svg+xml",
  ".ico":  "image/x-icon",
  ".mp4":  "video/mp4",
  ".webp": "image/webp",
  ".woff": "font/woff",
  ".woff2":"font/woff2",
  ".ttf":  "font/ttf",
  ".json": "application/json",
  ".txt":  "text/plain",
};

// Lazy-load the SSR handler once on first request
let ssrHandler = null;
async function getSsr() {
  if (!ssrHandler) {
    const mod = await import("./dist/server/server.js");
    ssrHandler = mod.default ?? mod;
  }
  return ssrHandler;
}

function tryStatic(pathname) {
  const abs = join(STATIC, decodeURIComponent(pathname));
  try {
    const st = statSync(abs);
    if (st.isFile()) return abs;
  } catch {}
  return null;
}

const server = createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);

  const file = tryStatic(url.pathname);
  if (file) {
    const mime = MIME[extname(file).toLowerCase()] ?? "application/octet-stream";
    res.writeHead(200, {
      "Content-Type": mime,
      "Cache-Control": url.pathname.startsWith("/assets/")
        ? "public, max-age=31536000, immutable"
        : "public, max-age=3600",
    });
    createReadStream(file).pipe(res);
    return;
  }

  try {
    const ssr = await getSsr();
    const request = new Request(`http://localhost:${PORT}${req.url}`, {
      method: req.method,
      headers: Object.fromEntries(
        Object.entries(req.headers).filter(([, v]) => v != null)
      ),
      body: ["GET", "HEAD"].includes(req.method) ? undefined : req,
      duplex: "half",
    });
    const response = await ssr.fetch(request, {}, {});
    res.writeHead(response.status, Object.fromEntries(response.headers.entries()));
    if (response.body) {
      const reader = response.body.getReader();
      const write = async () => {
        const { done, value } = await reader.read();
        if (done) { res.end(); return; }
        res.write(value);
        await write();
      };
      await write();
    } else {
      res.end();
    }
  } catch (err) {
    console.error(err);
    res.writeHead(500, { "Content-Type": "text/plain" });
    res.end("Internal Server Error");
  }
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`MoStar Frontend → http://localhost:${PORT}`);
});
