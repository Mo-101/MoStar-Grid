function backendCandidates(): string[] {
  const candidates = [
    process.env.GRID_API_BASE,
    "http://localhost:8001",
    "http://127.0.0.1:8001",
  ].filter((v): v is string => Boolean(v));

  return [...new Set(candidates)];
}

export async function GET() {
  let lastError = "unknown";

  for (const base of backendCandidates()) {
    try {
      const res = await fetch(`${base}/api/v1/status`, {
        signal: AbortSignal.timeout(6000),
        cache: "no-store",
      });

      if (!res.ok) {
        lastError = `HTTP ${res.status} via ${base}`;
        continue;
      }

      const data = await res.json();
      return Response.json({
        backend: { ok: true, data },
        graph: { ok: true, data: { status: data?.neo4j ?? "unknown" } },
        log: { entries: [] },
      });
    } catch (error) {
      lastError = `${String(error)} via ${base}`;
    }
  }

  return Response.json(
    { error: "Backend status unavailable", detail: lastError },
    { status: 503 }
  );
}