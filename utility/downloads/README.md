# Downloads — Public File Drop

A read-only nginx file server. Drop files into `./files/` on the host and they're immediately downloadable at `downloads.yourdomain.com`. No auth, no UI — just files over HTTPS.

## Use cases

- Sharing files publicly without a cloud storage account
- Hosting assets referenced by n8n workflows
- Making Android APKs or configs available to devices
- The `files/` directory is bind-mounted into the Obsidian web vault at `vault/storage/downloads` — files appear in the vault without copying

## Bring up

```bash
docker compose up -d
```

Drop files into `utility/downloads/files/`. They're served immediately. Directory listing is enabled by default in `nginx.conf`.

## Networks

`drawbridge` (public URL) + `observatory` (monitoring).

## Note on APKs

For Android app distribution specifically, the dedicated `apk-server` stack has a better nginx config with correct MIME types for `.apk` files. Use `downloads` for general file sharing.
