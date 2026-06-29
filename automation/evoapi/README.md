# Evolution API — WhatsApp HTTP API

Self-hosted WhatsApp integration layer. Connects to WhatsApp Web and exposes a REST API for sending/receiving messages, managing contacts, and handling webhooks — used primarily as an n8n action target for workflow-triggered WhatsApp automation.

## Stack

```
evolution-api   — HTTP API server (port 8080 → drawbridge → tunnel)
evo-postgres    — full message/contact/chat history persistence (Postgres 16)
evo-redis       — session cache (Redis 7, AOF)
```

## Key config decisions

**WhatsApp Web version is pinned:**
```yaml
CONFIG_SESSION_PHONE_VERSION: 2.3000.1035194821
```
WhatsApp frequently rotates the accepted WA Web client version. When the image's bundled default goes stale, WhatsApp rejects the handshake and you never get a QR code. Pinning to a known-good version and updating it manually when needed is more reliable than trusting the image default. Check [WhatsApp Web version tracker](https://wppconnect.io/whatsapp-versions/) for current values.

**Full Postgres persistence enabled:**
All messages, contacts, chats, labels, and message updates are saved to Postgres. This lets you query your full WhatsApp history via SQL (or pgweb) and survive container restarts without losing state.

**Telemetry disabled:**
```yaml
TELEMETRY_ENABLED: "false"
```

## Environment

| Variable | Purpose |
|---|---|
| `EVO_DB_PASSWORD` | Postgres password |
| `EVO_API_KEY` | Bearer token for all Evolution API calls |

## Bring up

```bash
cp .env.example .env
# edit .env
docker compose up -d
```

## Connect a WhatsApp instance

```bash
# Create an instance
curl -X POST https://evolution.yourdomain.com/instance/create \
  -H "apikey: YOUR_EVO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"instanceName": "main", "qrcode": true}'

# Get the QR code (returns base64 PNG or a scannable link)
curl https://evolution.yourdomain.com/instance/connect/main \
  -H "apikey: YOUR_EVO_API_KEY"
```

Scan the QR with WhatsApp → the instance goes `open`. After that, n8n can call Evolution API to send messages, react to incoming webhooks, manage groups, and more.

## Webhook (incoming messages → n8n)

In the Evolution API dashboard or via API, set the webhook URL to your n8n webhook trigger:
```
https://n8n.yourdomain.com/webhook/whatsapp-incoming
```

## Networks

| Network | Why |
|---|---|
| `automation` | Internal: Postgres, Redis, and the API server all talk here |
| `drawbridge` | evolution-api only — gives it the public tunnel URL |
| `observatory` | All containers — Prometheus scrapes per-service exporters |
