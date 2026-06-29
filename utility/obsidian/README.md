# Obsidian — web vault (BoBo Prime)

Real Obsidian in the browser (linuxserver KasmVNC image) at **https://obsidian.itproxima.com**
(Cloudflare Access email-OTP gate → then the KasmVNC login from `.env`).

## What's where
- **Vault** lives at `/config/vault` inside the container (`./volumes/config/vault` on host).
- `vault/downloads` ← bind of `../downloads/files` — the **same** dir `downloads.itproxima.com` serves.
  Drop a file there and it's instantly downloadable; it also shows up in the vault.
- `vault/uploads` ← bind of `../uploads/files` — the **same** dir `uploads.itproxima.com` writes to.
  Upload a file at uploads.itproxima.com and it appears in the vault.

## Two gates
1. **Cloudflare Access** (outer) — email OTP to mianfaizanxgp@gmail.com, set in `cloudflared/deploy-tunnel.sh`.
2. **KasmVNC login** (inner) — `KASM_USER` / `KASM_PASSWORD` in `.env`.

## Bring up
```bash
docker compose -f docker-compose.yml up -d
```

## First-run setup (one time, in the web GUI)
1. Open obsidian.itproxima.com, pass both gates.
2. Obsidian → **Open folder as vault** → `/config/vault`.
3. Settings → Community plugins → turn off Restricted mode → Browse → install
   **Self-hosted LiveSync** (vrtmrz) → Enable.
4. LiveSync setup → **Remote type: CouchDB**:
   - URI: `https://couch.itproxima.com`
   - Username / Password: the `COUCHDB_USER` / `COUCHDB_PASSWORD` from `../couchdb/.env`
   - Database name: `obsidiandb` (use the SAME name on phone + laptop)
   - Run **Check database configuration** (all green), then **Apply**.
5. Do the same LiveSync config on phone + laptop (same URI/creds/db name) → all three live-sync.

> Tip: in LiveSync, add `downloads/` and `uploads/` to the sync **ignore** list if you don't
> want big drop/upload files replicated to your phone — they'll still be browsable on the web vault.
