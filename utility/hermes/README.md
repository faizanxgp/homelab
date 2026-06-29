# Hermes — the homelab AI agent (web UI)

A polished multi-model AI chat (**Open WebUI**) that talks to the OpenRouter
frontier models and — via an imported tool — can **inspect and operate the other
containers**. Messenger of the homelab.

**Live:** https://hermes.itproxima.com (gated by Cloudflare Access — email OTP to
`mianfaizanxgp@gmail.com`, then Hermes' own login).

## First-run
1. Open the URL → pass the Cloudflare email OTP.
2. Create the **admin** account (first signup becomes admin).
3. Edit `docker-compose.yml`: set `ENABLE_SIGNUP: "false"`, then `docker compose up -d`.
4. Add models: **Settings → Connections → OpenAI API** →
   base `https://openrouter.ai/api/v1`, paste your **OpenRouter key**
   (or set `OPENROUTER_API_KEY` in `.env` and recreate). Pick models (Claude Opus
   4.8, etc.) and start chatting.

## Give Hermes hands on the homelab (the cool part)
Import the tool so Hermes can list/inspect/restart containers and probe service health:

1. **Workspace → Tools → +** → paste `tools/homelab_control.py` → Save.
2. In a chat, click the wrench and enable **Homelab Control**.
3. Ask: *"list the containers"*, *"show me the last 50 logs of n8n-main"*,
   *"is evolution-api healthy?"*, *"restart sillytavern"*.

The tool uses the mounted `/var/run/docker.sock`. That is **root-equivalent on the
host**, which is exactly why Hermes lives behind Cloudflare Access + its own login.
To disable docker control entirely, remove the `docker.sock` volume in the compose.

## Manage
```bash
cd /opt/homelab/utility/hermes
docker compose ps
docker compose logs -f hermes
docker compose up -d
```

## See also
`/opt/homelab/COOL-STACK-IDEAS.md` — curated next services to add (Vaultwarden,
Dozzle, NocoDB, Coolify, Ntfy, Immich, SearXNG/Perplexica, Flowise…).
