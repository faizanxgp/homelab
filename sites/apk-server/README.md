# APK Server — Android App Distribution

Self-hosted nginx server for distributing Android APKs. Serves files from `./files/` at `apk.yourdomain.com` with correct MIME types so Android devices can download and install directly.

## Why self-host APK distribution?

- Internal/beta apps that shouldn't go on the Play Store
- Distributing builds to testers without Play Console overhead
- Hosting modified APKs for personal devices
- Pinned versions of apps that auto-update to worse versions

## nginx config

The `nginx.conf` sets `application/vnd.android.package-archive` as the MIME type for `.apk` files, which triggers Android's package installer on download rather than a generic file save.

## Bring up

```bash
docker compose up -d
```

Drop `.apk` files into `sites/apk-server/files/`. They're served at `apk.yourdomain.com/filename.apk`. Directory listing lets you browse available APKs.

## On the device

Install from unknown sources must be enabled for the browser or file manager doing the install. For a smoother experience, the download URL can be shared as a QR code.

## Networks

`drawbridge` (public URL) + `observatory` (monitoring).
