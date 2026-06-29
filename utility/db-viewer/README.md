# DB Viewer — On-Demand Postgres Web UI

A pgweb instance for inspecting the `automation-postgres` database. **Designed to be ephemeral** — bring it up when you need to do schema work or debug queries, take it down when you're done.

## Why ephemeral?

The `automation` network (where the DB lives) and `drawbridge` (the public tunnel) are deliberately kept separate — the database should never be directly reachable from the internet. DB Viewer bridges the two networks only while it's running, and only through the pgweb UI (which is itself Cloudflare Access-gated).

## Bring up / tear down

```bash
# Start
docker compose -f /opt/homelab/utility/db-viewer/docker-compose.yml up -d

# Open db.yourdomain.com → log in with CF Access → enter Postgres credentials in pgweb

# Tear down when done
docker compose -f /opt/homelab/utility/db-viewer/docker-compose.yml down
```

## Security model

```
Internet → Cloudflare Access (email OTP) → cloudflared tunnel → db-viewer:8081
                                                                       ↓
                                                          automation network
                                                                       ↓
                                                     postgres-automation:5432
```

- No host port published — the container is only reachable container-to-container
- Cloudflare Access gates the pgweb UI before any request reaches the container
- The DB itself is on `automation` only — never on `drawbridge`

## Networks

| Network | Why |
|---|---|
| `drawbridge` | Public URL via tunnel → Access gate |
| `automation` | Can reach `postgres-automation:5432` |
| `observatory` | cAdvisor/Promtail observe it while running |
