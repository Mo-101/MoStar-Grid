export async function GET() {
  const res = await fetch('http://localhost:8001/api/v1/status');
  const data = await res.json();
  return Response.json({
    backend: { ok: true, data },
    graph: { ok: true, data: { status: "connected", host: "localhost:7474" } },
    log: { entries: [] }
  });
}
