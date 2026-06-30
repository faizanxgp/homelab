# Postiz — self-hosted social scheduling & analytics

Open-source Buffer/Hootsuite: schedule + auto-post to X, LinkedIn, Instagram,
Facebook, TikTok, YouTube, Threads, Mastodon, Bluesky, with built-in AI content
generation and per-post analytics.

**Live:** https://postiz.itproxima.com (via the cloudflared tunnel)

## Architecture
- `postiz` — the app (Next.js frontend + NestJS backend + orchestrator), public on
  port 5000 via the tunnel. Local test bind: `127.0.0.1:5050`.
- `postiz-postgres` (Postgres 17) + `postiz-redis` (Redis 7) — dedicated, on the
  private `postiz-internal` network, never exposed.
- **Temporal** workflow engine (required by modern Postiz): `temporal`
  (auto-setup) + `temporal-postgres` + `temporal-elasticsearch`. ES is mandatory —
  the Postgres-only visibility store caps Text search attributes at 3 and Postiz
  needs more (`addSearchAttributes` fails otherwise). ES runs a small 512m heap.
- Secrets in `.env` (gitignored); see `.env.example`.

## Account (already created)
- Admin **`mianfaizanxgp@gmail.com`** is registered + activated; log in at
  https://postiz.itproxima.com. **Registration is now locked**
  (`DISABLE_REGISTRATION: "true"`); flip to `"false"` + `docker compose up -d` to
  add more users.

> Note: if ES's data dir ever resets, `chown -R 1000:0 volumes/temporal-es` before
> starting (ES runs as uid 1000).

## Connecting social accounts (for the real demo)
Each platform needs an OAuth app (client id/secret) you create in that platform's
developer portal, then add to Postiz's settings / env. Postiz docs list the exact
vars per provider. The OAuth callback is `https://postiz.itproxima.com/api/...`,
which is why this host is **not** behind Cloudflare Access (a gate would break the
callback).

## Manage
```bash
cd /opt/homelab/marketing/postiz
docker compose ps
docker compose logs -f postiz
docker compose up -d        # apply changes
docker compose down         # stop (data persists in ./volumes)
```

## See also
`marketing-arsenal.md` — the full self-hosted marketing-analytics stack brief
(PostHog, Metabase, Matomo, Umami, Listmonk, n8n AI scoring…) for the interview.
