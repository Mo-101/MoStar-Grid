const SERVICE_NAME = "profit-council-grid0-scheduler";
const DEFAULT_CRON = "*/5 * * * *";
const DEFAULT_TIMEOUT_MS = 25000;
const FIVE_MINUTES_MS = 300000;

export default {
  async scheduled(controller, env, ctx) {
    ctx.waitUntil(runGridScan(controller.scheduledTime, env));
  },

  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname !== "/health" || request.method !== "GET") {
      return new Response("Not found", { status: 404 });
    }

    return Response.json({
      service: SERVICE_NAME,
      configured: Boolean(
        env.PROFIT_COUNCIL_BASE_URL &&
          env.GRID_SCHEDULER_PATH &&
          env.OAI_SITES_BYPASS_TOKEN &&
          env.GRID_SCHEDULER_TOKEN
      ),
      cron: env.GRID_CRON_EXPRESSION || DEFAULT_CRON,
      trading_authority: "NONE",
    });
  },
};

export async function runGridScan(scheduledTime, env) {
  requireEnv(env, "PROFIT_COUNCIL_BASE_URL");
  requireEnv(env, "GRID_SCHEDULER_PATH");
  requireEnv(env, "OAI_SITES_BYPASS_TOKEN");
  requireEnv(env, "GRID_SCHEDULER_TOKEN");

  const timeoutMs = Number(env.GRID_REQUEST_TIMEOUT_MS || DEFAULT_TIMEOUT_MS);
  const scheduledDate = new Date(scheduledTime);
  const fiveMinuteWindow = Math.floor(scheduledTime / FIVE_MINUTES_MS);
  const idempotencyKey = `grid0-scan:${fiveMinuteWindow}`;

  const response = await fetch(
    `${env.PROFIT_COUNCIL_BASE_URL}${env.GRID_SCHEDULER_PATH}`,
    {
      method: "POST",
      signal: AbortSignal.timeout(timeoutMs),
      headers: {
        "content-type": "application/json",
        authorization: `Bearer ${env.GRID_SCHEDULER_TOKEN}`,
        "OAI-Sites-Authorization": `Bearer ${env.OAI_SITES_BYPASS_TOKEN}`,
        "x-idempotency-key": idempotencyKey,
      },
      body: JSON.stringify({
        source: "cloudflare-cron",
        cron: env.GRID_CRON_EXPRESSION || DEFAULT_CRON,
        scheduled_time: scheduledDate.toISOString(),
        scheduler_version: Number(env.GRID_SCHEDULER_VERSION || 1),
      }),
    }
  );

  const responseText = await response.text();

  console.log(
    JSON.stringify({
      event: response.ok
        ? "GRID_SCHEDULER_DELIVERY_SUCCEEDED"
        : "GRID_SCHEDULER_DELIVERY_FAILED",
      scheduled_time: scheduledDate.toISOString(),
      status: response.status,
      idempotency_key: idempotencyKey,
      response: responseText.slice(0, 500),
    })
  );

  if (!response.ok) {
    throw new Error(`Profit Council scheduler returned ${response.status}`);
  }
}

function requireEnv(env, name) {
  if (!env[name]) {
    throw new Error(`Missing required environment binding: ${name}`);
  }
}
