# Uptime Kuma — monitor provisioning

`provision-monitors.py` (re-)creates the full homelab monitor wall in Uptime Kuma,
organised into three groups:

- **🌐 Public Sites** — every public hostname, end-to-end (DNS → Cloudflare → tunnel → app).
- **🧩 Internal Apps** — app health by container name on the `observatory` network
  (bypasses Cloudflare Access so gated apps still report true health).
- **🗄️ Databases** — TCP port checks (no credentials stored): Postgres ×3, Redis ×3, Mongo ×1.
- **🐳 Containers (no endpoint)** — Docker container running-state via the mounted
  `/var/run/docker.sock`, for services with no HTTP/TCP health to probe: `promtail`,
  `cloudflared`, `node-exporter`, `cadvisor`, and all 8 metrics exporters. Uses the
  `DOCKER` monitor type against a `local-socket` Docker host the script auto-creates.

The script is **idempotent** — monitors are keyed by name, so re-running only adds
what's missing. HTTP monitors accept `200-499` (only connection-refused / timeout /
5xx count as DOWN), which keeps auth-gated endpoints (401/403) and redirects green.

## Run

```bash
python3 -m venv venv && ./venv/bin/pip install uptime-kuma-api
./venv/bin/python provision-monitors.py 'YOUR_KUMA_PASSWORD'
```

Connects to `http://127.0.0.1:3001` as user `faizanxgp`. The password is passed as an
argument and is **not** stored in this repo.

## Forgot the Uptime Kuma password?

Interactive reset from the host (type a new password when prompted):

```bash
docker exec -it uptime-kuma node extra/reset-password.js
```
