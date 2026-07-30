# Profit Council GRID-0 Scheduler Worker

Dedicated Cloudflare Worker scheduler for:

`https://profit-council-live.mostar1.chatgpt.site/api/grid0/scheduler/run`

It has no trading authority. It only sends a scheduled `POST` every five minutes with deterministic idempotency.

## Required Cloudflare Environment

Use a scoped API token, not a Cloudflare password or Global API Key:

```env
CLOUDFLARE_ACCOUNT_ID=<target-account-id>
CLOUDFLARE_API_TOKEN=<scoped-workers-deployment-token>
```

The token should be restricted to the target account and only the permissions needed to deploy/manage this Worker and its Cron trigger. DNS and zone-management permissions are not needed.

Do not reuse `CF_ACCESS_CLIENT_ID` or `CF_ACCESS_CLIENT_SECRET`; those remain dedicated to the Ollama Access gateway.

## Secrets

Create an independent random scheduler token and configure the same value in the Profit Council Sites environment as `GRID_SCHEDULER_TOKEN`.

```sh
wrangler secret put OAI_SITES_BYPASS_TOKEN
wrangler secret put GRID_SCHEDULER_TOKEN
```

Do not provide exchange API keys, Gemini/Ollama/Fugu/Vibe keys, trading credentials, database credentials, the Cloudflare password, or the Global API Key to this Worker.

## Deploy

```sh
cd cloudflare/profit-council-grid0-scheduler
npm install
wrangler whoami
wrangler deploy
```

## Request Contract

The scheduled Worker sends:

```http
POST /api/grid0/scheduler/run
Authorization: Bearer <GRID_SCHEDULER_TOKEN>
OAI-Sites-Authorization: Bearer <OAI_SITES_BYPASS_TOKEN>
Content-Type: application/json
X-Idempotency-Key: grid0-scan:<UTC-five-minute-window>
```

Body:

```json
{
  "source": "cloudflare-cron",
  "cron": "*/5 * * * *",
  "scheduled_time": "<ISO-8601 UTC timestamp>",
  "scheduler_version": 1
}
```

The idempotency key is deterministic:

```js
const window = Math.floor(scheduledTime / 300000);
const idempotencyKey = `grid0-scan:${window}`;
```

## Acceptance Evidence To Return

Return:

- Cloudflare account ID
- Worker name
- deployment/version ID
- Cron trigger status
- last scheduled invocation
- last HTTP response status
- scheduler log timestamp
- health endpoint URL

Verify:

- `wrangler whoami` identifies the intended account.
- Worker deployment succeeds.
- Cron trigger appears as `*/5 * * * *`.
- Manual scheduled-event test returns HTTP 2xx.
- Missing scheduler token returns 401/403.
- Repeating the same idempotency key creates no duplicate scan.
- A no-candidate scan still writes a completed scan receipt.
- Cloudflare logs contain no secret values.
- Worker has no exchange-order or trading endpoints.
- Profit Council dashboard changes scheduler state from `NOT OBSERVED`.

Expected Profit Council receipts:

- `GRID_SCAN_STARTED`
- `GRID_SCAN_COMPLETED_NO_CANDIDATE`
- `GRID_SCAN_COMPLETED_WITH_CANDIDATES`
- `GRID_SCAN_FAILED`
- `GRID_CANDIDATE_DEDUPED`
