# 🍺 tavern.itproxima.com — SillyTavern (supped-up)

A tuned SillyTavern fronted by the shared `bobo-prime` Cloudflare Tunnel on the
`drawbridge` network. Public access is gated by **Cloudflare Access**
(email allowlist `mianfaizanxgp@gmail.com`), managed by
`/opt/homelab/utility/cloudflared/deploy-tunnel.sh`.

## Layout
```
docker-compose.yml                  # SillyTavern on drawbridge, no published host port
volumes/config/config.yaml         # tuned: listen mode, CSRF off (CF Access gates), SSRF filter on
volumes/data/default-user/
  secrets.json                     # OpenRouter API key (pre-seeded, never in git)
  settings.json                    # main_api=openai, source=openrouter, 64k ctx unlocked, tuned samplers
  OpenAI Settings/Spicy Pro.json   # sharp deep-RP prompt preset (main + NSFW + post-history)
  characters/Lyra Voss.json        # deep-RP starter character
```

## Connection (already wired — just open the URL)
1. Go to **https://tavern.itproxima.com/** → log in with the allowlisted email.
2. API Connections panel → **Chat Completion** → source **OpenRouter** (key is pre-filled).
3. Preset **Spicy Pro** is selected by default. Default model **sao10k/l3.3-euryale-70b**.

## Switching models
Spicy / RP-friendly picks currently on OpenRouter (2026):
- `sao10k/l3.3-euryale-70b` — default, the spicy-RP legend (131k ctx)
- `sao10k/l3.1-euryale-70b` — alt Euryale
- `anthropic/claude-sonnet-4.6` / `claude-opus-4.8` — top prose quality
- `anthracite-org/magnum-v4-72b` — strong RP
- `nousresearch/hermes-3-llama-3.1-405b` — big creative brain
- `x-ai/grok-4.20` — high context, low censorship
- `deepseek/deepseek-v3.2` / `deepseek-r1` — cheap & sharp
- `meta-llama/llama-3.3-70b-instruct` — solid open baseline

## Operating
```
docker compose -f /opt/homelab/sites/tavern/docker-compose.yml up -d     # start
docker compose -f /opt/homelab/sites/tavern/docker-compose.yml logs -f   # logs
docker compose -f /opt/homelab/sites/tavern/docker-compose.yml pull && \
docker compose -f /opt/homelab/sites/tavern/docker-compose.yml up -d      # upgrade
```
To re-publish the tunnel route (e.g. after adding hosts): run `deploy-tunnel.sh`
in `/opt/homelab/utility/cloudflared/`, then `docker restart cloudflared`.
