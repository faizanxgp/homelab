# Cloudflare Tunnel — Zero-Trust Public Ingress

The single public door into the homelab. Cloudflare Tunnel creates an outbound-only encrypted connection from the VPS to Cloudflare's edge — no inbound ports, no exposed IP, no reverse proxy to maintain.

## How it works

```
Internet → Cloudflare edge → tunnel (outbound from VPS) → cloudflared container
                                                                    ↓
                                                         drawbridge network
                                                                    ↓
                                                    target container (e.g. n8n-main)
```

Every public-facing service just joins the `drawbridge` network. Cloudflared reaches them container-to-container by name — no host port mapping needed.

## deploy-tunnel.sh

A fully automated tunnel setup script. Run it once (or re-run when you add routes) and it:

1. Creates (or reuses) the named tunnel `bobo-prime`
2. Pushes all 17 ingress rules to Cloudflare via API
3. Creates/updates DNS CNAME records for every hostname (proxied, so Cloudflare handles TLS)
4. Creates Cloudflare Access apps with email-allowlist policies for sensitive endpoints
5. Writes `utility/cloudflared/.env` with the `TUNNEL_TOKEN`

### Cloudflare Access gates

These endpoints require email OTP before the request even reaches your container:

| Endpoint | Why gated |
|---|---|
| `obsidian.yourdomain.com` | Full desktop access |
| `uploads.yourdomain.com` | Write access to the server |
| `db.yourdomain.com` | Database UI |
| `tavern.yourdomain.com` | AI interface |

Services that can't do interactive OTP (CouchDB, WebDAV) are **not** Access-gated — they use their own auth (CouchDB admin credentials, WebDAV basic auth).

### Required API token permissions

Create a token at [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens) with:
- Account → Cloudflare Tunnel: **Edit**
- Account → Access: Apps and Policies: **Edit**
- Zone → DNS: **Edit** (your domain)
- Zone → Zone: **Read** (your domain)

### Adding a new route

1. Add a line to the `ROUTES` array in `deploy-tunnel.sh`:
   ```bash
   "myservice.yourdomain.com    http://mycontainer:8080"
   ```
2. If it needs an Access gate, add the hostname to `ACCESS_HOSTS`.
3. Re-run the script: `bash deploy-tunnel.sh`
4. Add the new service to the `drawbridge` network in its `docker-compose.yml`.
5. Restart cloudflared: `docker restart cloudflared`

## Environment

| Variable | Purpose |
|---|---|
| `TUNNEL_TOKEN` | Written by `deploy-tunnel.sh` — do not set manually |

## Networks

| Network | Why |
|---|---|
| `drawbridge` | The gateway — cloudflared routes requests to containers on this net |
| `observatory` | cloudflared exposes tunnel metrics on `:60123` — Prometheus scrapes this |

## Bring up

```bash
# Run the deploy script first (writes .env with TUNNEL_TOKEN)
bash deploy-tunnel.sh

# Then start the container
docker compose up -d
```

## Verify the tunnel is connected

```bash
docker logs cloudflared --tail 10
# Should show: "Registered tunnel connection" with connection IDs
```
