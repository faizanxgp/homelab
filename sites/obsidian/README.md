# Obsidian — web vault (BoBo Prime)

Real Obsidian in the browser (linuxserver KasmVNC image) at **https://obsidian.itproxima.com**.
Single gate: **Cloudflare Access email-OTP** (to mianfaizanxgp@gmail.com). No inner
KasmVNC login — same model as uploads/db. The CF identity is SSO, so once you've
OTP'd into any *.itproxima.com Access app, the others auto-allow without re-prompting.

## What's where
- **Vault** lives at `/config/vault` inside the container (`./volumes/config/vault` on host).
- `vault/downloads` ← bind of `../downloads/files` — the **same** dir `downloads.itproxima.com` serves.
  Drop a file there and it's instantly downloadable; it also shows up in the vault.
- `vault/uploads` ← bind of `../uploads/files` — the **same** dir `uploads.itproxima.com` writes to.
  Upload a file at uploads.itproxima.com and it appears in the vault.

## Gate
**Cloudflare Access** — email OTP to mianfaizanxgp@gmail.com, set in `cloudflared/deploy-tunnel.sh`.
(To add an inner KasmVNC basic-auth login too, set `CUSTOM_USER`/`PASSWORD` env in the compose.)

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

> Tip: in LiveSync, add `storage/` to the sync **ignore** list (a vault-root `.gitignore`
> with `storage/` already does this) so the bulk WebDAV folders never replicate to your phone —
> they stay browsable on the web vault and the desktop mount.

## Backup to GitHub (notes only, Mon & Thu)
`vault-to-github.sh` mirrors **`.md` files only** (folder structure preserved) from this web
vault into the private repo **github.com/faizanxgp/Obsidian** and pushes. It deliberately
excludes `.obsidian/` (themes, plugins, and the LiveSync `data.json` that holds the CouchDB
password + E2E passphrase), `storage/`, `.trash/`, and all non-markdown files.
- Schedule: `cron/obsidian-vault` → installed at `/etc/cron.d/obsidian-vault`, **Mon & Thu 09:00 Asia/Karachi**.
- Mirror repo lives at `/opt/obsidian-vault` (outside the homelab repo). Logs: `/var/log/homelab/vault-push.log` (also in Loki / the "Vault & Files — Logs" Grafana dashboard).
- To make the green contribution graph public: GitHub → Settings → Profile → **"Include private contributions on my profile."**
