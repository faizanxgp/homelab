# Snippetbox — Code & Note Snippet Manager

Self-hosted snippet manager at `snippets.yourdomain.com`. Stores code snippets, commands, configs, and notes with syntax highlighting, tags, and search.

## Bring up

```bash
docker compose up -d
```

Data persists in `./volumes/data/`. No environment variables needed — create your account on first visit.

## Networks

`drawbridge` (public URL) + `observatory` (monitoring).
