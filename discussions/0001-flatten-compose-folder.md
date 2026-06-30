# How do you flatten a Docker Compose folder without restarting the running containers?

> Posted as a Q&A discussion: https://github.com/faizanxgp/homelab/discussions/9

## Question

I had a monitoring stack at `observatory/monitoring/` (Prometheus, Grafana, Loki, Promtail) and wanted to flatten it up to `observatory/` to drop a redundant nesting level. All the volume/config mounts are **relative** (`./prometheus`, `./volumes/grafana`, …). The containers are long-lived and I did **not** want to disturb them. Docker resolves bind mounts to absolute host paths at container-creation time, so naively I expected moving the folder would yank the data directories out from under the running Prometheus. What is the safe way?

## Answer

A same-filesystem `mv` is safe for the *running* containers; the only thing you must manage is the Compose *project name* for when you re-apply.

**Why the live containers survive** — A bind mount binds to the **inode**, not the path string. On a single filesystem, `mv` is a `rename(2)` that preserves the inode, so the running container's mount stays attached. Confirm `df` shows the same filesystem for source and destination first.

```bash
mv observatory/monitoring/.env observatory/.env
mv observatory/monitoring/* observatory/
rmdir observatory/monitoring
```

**The gotcha: project name on re-apply** — Compose's default project name is the basename of the launch dir. The live stack was `up`'d from `observatory/monitoring/` → project `monitoring`. Re-applying from `observatory/` would create project `observatory` and collide on the fixed `container_name:`s. Pin it:

```yaml
name: monitoring   # top of docker-compose.yml
```

**Host-side refs** — Update anything outside Compose that hard-codes the old path (e.g. `/etc/cron.d/*`).
