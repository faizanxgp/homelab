# WebDAV — bulk storage as a network drive (BoBo Prime)

Serves the vault's **bulk folders** — `downloads`, `uploads`, `archive` — over WebDAV at
**https://dav.itproxima.com**. Mount it on the desktop so those folders appear inside the
one master Obsidian vault (under `storage/`) and stream on demand — the 50 GB **never lands
on the laptop**.

## Why it's not Cloudflare-Access gated
A mounted drive can't do interactive email-OTP, so (like couch) `dav.itproxima.com` is **not**
behind CF Access. Its own basic auth is the gate — user/password in `.env` (`WEBDAV_USER` /
`WEBDAV_PASSWORD`, user `mian`). CRUD enabled (read + write + delete).

## On-disk sources (bind-mounted into the container at /data)
| WebDAV path  | Server path                        | Also reachable at            |
|--------------|------------------------------------|------------------------------|
| `/downloads` | `sites/downloads/files`          | downloads.itproxima.com      |
| `/uploads`   | `sites/uploads/files`            | uploads.itproxima.com        |
| `/archive`   | `utility/storage/archive`          | (bulk; OneDrive migration)   |

These are the **same** dirs bind-mounted into the web vault at `/config/vault/storage/*`.

## Bring up
```bash
docker compose -f docker-compose.yml up -d
```

## Mount on the desktop (so it lands inside the vault tree)
The mount must attach at a **subfolder** of the vault (`<vault>/storage`) — a mount can't merge
into the vault root without hiding your local notes.

- **Windows:** Map network drive → `https://dav.itproxima.com` → user `mian` + password.
  (Then point a vault symlink/junction `storage` at it, or open the drive as the storage folder.)
- **macOS:** Finder → Go → Connect to Server → `https://dav.itproxima.com`.
- **Linux:** `davfs2` →
  ```bash
  sudo mount -t davfs https://dav.itproxima.com "<vault>/storage"
  ```
- **rclone (any OS):** `rclone mount dav: "<vault>/storage" --vfs-cache-mode writes`
  (remote: `rclone config create dav webdav url=https://dav.itproxima.com vendor=other user=mian pass=...`)

LiveSync is set to **ignore `storage/`** (vault-root `.gitignore`) so none of this replicates
through CouchDB.
