# Setup Guide — BoBo Prime Homelab

Complete walkthrough from a bare VPS to a fully running homelab. Every step is idempotent — safe to re-run if something goes wrong partway through.

---

## Prerequisites

| Requirement | Minimum | Recommended |
|---|---|---|
| VPS RAM | 2 GB | 4 GB |
| VPS vCPU | 1 | 2 |
| Disk | 20 GB | 50 GB |
| OS | Ubuntu 22.04 / Debian 12 | Ubuntu 24.04 |
| Docker | 24+ | latest |
| Docker Compose | v2 (plugin) | v2 |
| Cloudflare account | free | free |
| Domain in Cloudflare | required | required |

---

## 1. Server baseline

```bash
# Update and install essentials
apt update && apt upgrade -y
apt install -y curl git jq ufw

# Install Docker (official script)
curl -fsSL https://get.docker.com | sh

# Verify
docker version
docker compose version   # must say v2+
```

---

## 2. Firewall (UFW)

Lock down the server **before** you deploy anything. The Cloudflare Tunnel dials out — you don't need any inbound ports except SSH.

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh          # keep your own access
ufw enable
ufw status
```

> After this, no port on the server is reachable from the internet. Cloudflare Tunnel creates an outbound-only encrypted connection — your services are never directly exposed.

---

## 3. Clone the repo

```bash
git clone https://github.com/faizanxgp/homelab.git /opt/homelab
cd /opt/homelab
```

---

## 4. Create the three shared networks

Every stack attaches to one or more of these. Create them once — `docker network create` is idempotent if the network already exists.

```bash
docker network create automation
docker network create drawbridge
docker network create observatory
```

| Network | Purpose |
|---|---|
| `automation` | Internal data layer. Databases, Redis, internal services. No public traffic. |
| `drawbridge` | Public gateway. `cloudflared` lives here. Services that need a public URL join this. |
| `observatory` | Monitoring plane. Prometheus scrapes every container here. |

---

## 5. Configure secrets

Copy the `.env.example` from each stack you plan to run, then fill in real values:

```bash
cp automation/n8n/.env.example       automation/n8n/.env
cp automation/evoapi/.env.example    automation/evoapi/.env
cp automation/postgres/.env.example  automation/postgres/.env
cp utility/cloudflared/.env.example  utility/cloudflared/.env
cp utility/couchdb/.env.example      utility/couchdb/.env
cp sites/obsidian/.env.example     sites/obsidian/.env
cp utility/webdav/.env.example       utility/webdav/.env
```

Edit each file. Generate strong passwords with:

```bash
openssl rand -base64 32
```

### What each `.env` needs

**`automation/n8n/.env`**
```
N8N_DB_PASSWORD=<strong password>
N8N_ENCRYPTION_KEY=<32-char random string — used to encrypt stored credentials>
```

**`automation/evoapi/.env`**
```
EVO_DB_PASSWORD=<strong password>
EVO_API_KEY=<strong random string — used to call the Evolution API>
```

**`automation/postgres/.env`**
```
AUTOMATION_DB_PASSWORD=<strong password>
```

**`utility/couchdb/.env`**
```
COUCHDB_USER=<admin username>
COUCHDB_PASSWORD=<strong password>
```

**`utility/webdav/.env`**
```
WEBDAV_USER=mian          # or whatever username you prefer
WEBDAV_PASSWORD=<strong password>
```

**`observatory/.env`** (create this one)
```
GF_SECURITY_ADMIN_PASSWORD=<grafana admin password>
```

---

## 6. Deploy the Cloudflare Tunnel

You need a Cloudflare API token with these permissions:
- Account → Cloudflare Tunnel: **Edit**
- Account → Access: Apps and Policies: **Edit**
- Zone → DNS: **Edit** (your domain)
- Zone → Zone: **Read** (your domain)

Edit `deploy-tunnel.sh` to set your domain and routes, then run:

```bash
# Option A: pass token as env var
CF_API_TOKEN=your_token bash utility/cloudflared/deploy-tunnel.sh

# Option B: write token to a file (chmod 600)
echo "your_token" > utility/cloudflared/.cf_api_token
chmod 600 utility/cloudflared/.cf_api_token
bash utility/cloudflared/deploy-tunnel.sh
```

The script:
1. Creates (or reuses) a named tunnel
2. Pushes all ingress rules to Cloudflare's API
3. Creates/updates DNS CNAMEs for every route
4. Creates Cloudflare Access apps + email-allowlist policies for sensitive endpoints
5. Writes `utility/cloudflared/.env` with the tunnel token

The script is **idempotent** — re-run it any time you add a new route.

---

## 7. Bring up stacks

Bring up services in this order (dependencies first):

### Observatory first — so everything is monitored from the start

```bash
docker compose -f observatory/docker-compose.yml    up -d
docker compose -f observatory/uptime-kuma/docker-compose.yml  up -d
```

### Tunnel — the public gateway

```bash
docker compose -f utility/cloudflared/docker-compose.yml up -d
```

### Automation

```bash
docker compose -f automation/postgres/docker-compose.yml up -d
docker compose -f automation/n8n/docker-compose.yml      up -d
docker compose -f automation/evoapi/docker-compose.yml   up -d
```

### Utility

```bash
docker compose -f utility/couchdb/docker-compose.yml   up -d
docker compose -f sites/obsidian/docker-compose.yml  up -d
docker compose -f utility/webdav/docker-compose.yml    up -d
docker compose -f sites/downloads/docker-compose.yml up -d
docker compose -f sites/uploads/docker-compose.yml   up -d
docker compose -f sites/apk-server/docker-compose.yml up -d
```

### Dashboards + misc

```bash
docker compose -f dashboards/docker-compose.yml     up -d
docker compose -f snippetbox/docker-compose.yml     up -d
docker compose -f sites/tavern/docker-compose.yml   up -d
```

### Verify everything is running

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | sort
```

All containers should show `Up` — none should be in a restart loop.

---

## 8. First-run configuration

### Grafana
1. Open `grafana.yourdomain.com` → log in with `admin` / your `GF_SECURITY_ADMIN_PASSWORD`.
2. Datasources (Prometheus and Loki) are provisioned automatically.
3. Import dashboards from `observatory/grafana/dashboards/`.

### n8n
1. Open `n8n.yourdomain.com` → create your owner account.
2. Settings → Community nodes → enable (if you use them).
3. Workers connect automatically — check Settings → Workers to confirm all three are online.

### Obsidian + LiveSync
See [`sites/obsidian/README.md`](sites/obsidian/README.md) for the full first-run setup (vault init + LiveSync config on web, phone, and laptop).

### Evolution API (WhatsApp)
1. Open `evolution.yourdomain.com` with header `apikey: <your EVO_API_KEY>`.
2. `POST /instance/create` with your instance name.
3. `GET /instance/connect/{instance}` to get the QR code.
4. Scan with WhatsApp → connected.

---

## 9. Optional: Obsidian vault → GitHub sync

Set up the cron job that mirrors Obsidian notes to a private GitHub repo twice a week:

```bash
# Create a GitHub PAT with repo write access and add it to git credential store
git config --global credential.helper store
echo "https://faizanxgp:YOUR_PAT@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

# Install the cron job (edit paths inside the script first)
cp sites/obsidian/vault-to-github.sh /usr/local/bin/vault-to-github
chmod +x /usr/local/bin/vault-to-github

# Add to crontab (Mon & Thu at 09:00 server time)
echo "0 9 * * 1,4 root /usr/local/bin/vault-to-github" > /etc/cron.d/obsidian-vault
```

Logs go to `/var/log/homelab/vault-push.log` — Promtail picks these up automatically and they appear in the Grafana "Vault & Files" dashboard.

---

## 10. Verify the full stack

```bash
# Check all containers
docker ps

# Check Prometheus targets (all should be UP)
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job:.labels.job, health:.health}'

# Check Cloudflare Tunnel is connected
docker logs cloudflared 2>&1 | tail -5

# Check n8n workers are registered
curl -s http://localhost:5678/healthz
```

---

## Updating a service

```bash
cd /opt/homelab
docker compose -f <path>/docker-compose.yml pull
docker compose -f <path>/docker-compose.yml up -d
```

All volumes persist across updates — your data is in `./volumes/` inside each stack directory, which is bind-mounted and git-ignored.

---

## Troubleshooting

**Container in restart loop**
```bash
docker logs <container-name> --tail 50
```

**Cloudflare Tunnel not connecting**
```bash
docker logs cloudflared --tail 20
# Check the TUNNEL_TOKEN in utility/cloudflared/.env is set correctly
```

**n8n worker not picking up jobs**
```bash
docker logs n8n-worker --tail 20
# Ensure n8n-redis and n8n-postgres are healthy first
docker inspect n8n-redis | jq '.[].State.Health'
```

**Prometheus not scraping a target**
```bash
# Check the target is on the observatory network
docker network inspect observatory | jq '.[].Containers | keys[]'
```

**Obsidian LiveSync not syncing**
- Confirm CouchDB is healthy: `curl -u user:pass https://couch.yourdomain.com/_up`
- In Obsidian → LiveSync settings → Run "Check database configuration"
- Ensure all clients use the exact same database name
