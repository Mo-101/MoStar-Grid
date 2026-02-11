import { NextResponse } from "next/server";

const CONSCIOUSNESS_API_BASE =
  process.env.CONSCIOUSNESS_API_BASE ?? "http://localhost:8001";

export async function GET() {
  try {
    const response = await fetch(`${CONSCIOUSNESS_API_BASE}/api/v1/status`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      // lightweight revalidate window for incremental static regens (Next.js hint)
      next: { revalidate: 10 },
    });

    if (!response.ok) {
      throw new Error(`Status check failed: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Status check error:", error);
    return NextResponse.json(
      {
        status: "error",
        message: error instanceof Error ? error.message : "Unknown error",
        layers: {
          dcx0: { status: "offline", lastPing: null },
          dcx1: { status: "offline", lastPing: null },
          dcx2: { status: "offline", lastPing: null },
        },
      },
      { status: 200 }
    );
  }
}
