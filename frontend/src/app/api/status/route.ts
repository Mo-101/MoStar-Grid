import { NextResponse } from "next/server";

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
      const response = await fetch(`${base}/api/v1/status`, {
        signal: AbortSignal.timeout(6000),
        cache: "no-store",
      });

      if (!response.ok) {
        lastError = `HTTP ${response.status} via ${base}`;
        continue;
      }

      const data = await response.json();
      return NextResponse.json(data);
    } catch (error) {
      lastError = `${String(error)} via ${base}`;
    }
  }

  return NextResponse.json(
    { error: "Backend status unavailable", detail: lastError },
    { status: 503 }
  );
}