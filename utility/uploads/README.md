# Uploads — Authenticated File Ingestion

A minimal Python HTTP server that accepts file uploads and saves them to `./files/`. Gated by Cloudflare Access — only email-allowlisted users can upload. The uploaded files land in the same directory that the Downloads server and Obsidian vault's `storage/uploads` folder are bound to.

## The triangle

```
uploads.yourdomain.com  →  writes to  → utility/uploads/files/
downloads.yourdomain.com →  reads from → utility/uploads/files/  (same dir, different container)
Obsidian vault           →  shows at   → vault/storage/uploads/   (bind mount of same dir)
```

Upload a file, and it instantly appears in the Obsidian web vault and is downloadable at the downloads URL. No sync, no copy — the same inode.

## Security

- **Cloudflare Access** gates the upload endpoint (email OTP required before any request reaches the container)
- Runs as a minimal Python 3.12 Alpine container with no extra packages
- No published host port — only reachable via the Cloudflare Tunnel on the `drawbridge` network

## Bring up

```bash
docker compose up -d
```

The `./files/` directory is kept in git as an empty directory (`.gitkeep`). Uploaded files are gitignored.

## Source

Upload handler is in `app.py` — a minimal `http.server` subclass. Modify it to add size limits, allowed file types, or a simple HTML form.
