# ♾️ The Immortal — autonomous work session log

**Started:** 2026-06-29 ~23:30 CEST (≈ 2026-06-30 02:30 PKT) · _formerly "Midnight Oil"_
**Why:** Load-shedding. Built to work autonomously for hours and survive power/SSH
drops. This file is the **resume point** — if a session dies, a fresh `immortal`
session reads this and continues from "NEXT".

> Reattach The Immortal from any terminal (incl. phone):  **`immortal`**
> Fresh clean session: **`immortal new`** · Detach (leave running): `Ctrl-b` then `d`.

---

## Key facts about this box (so a cold session has context)

- This is a **cloud VPS** (`vmi3391102`, QEMU/KVM) — **never loses power.** Only
  Faizan's laptop SSH link dies during load-shedding.
- Homelab monorepo: **`/opt/homelab`** → `github.com/faizanxgp/homelab` (push works,
  creds in `/root/.git-credentials`). Commit as `faizanxgp / mianfaizanxgp@gmail.com`.
- Obsidian: **web vault** (editable in `obsidian.itproxima.com`) lives at
  `/opt/homelab/sites/obsidian/volumes/config/vault/`. A cron mirrors `*.md`
  from there to **`/opt/obsidian-vault`** → `github.com/faizanxgp/Obsidian`
  (`vault-to-github.sh`, Mon & Thu 09:00 Asia/Karachi).
- Public routing via cloudflared tunnel: `utility/cloudflared/deploy-tunnel.sh`.
- Commit trailers required (see CLAUDE/Bash policy):
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` + `Claude-Session:` line.
- Use Opus for everything (user's explicit preference). Commit & push after EVERY step.

---

## Task board

| # | Task | Status |
|---|------|--------|
| 1 | Always-on Claude (tmux+systemd `oil`) | ✅ DONE — `fe7c7a2` |
| 2 | This resume log + frequent updates | 🔄 ongoing |
| 3 | `git-push-pull.md` green-commit cron | ✅ DONE — `5a0a48b` |
| 4 | Expose Claude Code files in Obsidian | ✅ DONE — `a53124a` |
| 5 | Finish Uptime Kuma no-endpoint container monitors | ✅ CODE DONE — `b6bcbfa` (run to apply) |
| 6 | Deploy Postiz + marketing brief for Giant Group interview (Wed) | ✅ DONE — `f6e29be` |
| 7 | Hermes agent web UI + docker interactivity | ✅ DONE — `3aae645` |
| 8 | GitHub badges plan (`github.com/faizanxgp`) | ✅ DONE — `174b8bb` |

### Round 2 (power held — Faizan awake)
| # | Task | Status |
|---|------|--------|
| 9 | Rename Midnight Oil → **The Immortal** (+run) | ✅ DONE — `ba77bd7` |
| 10 | Create Postiz admin account (needed Temporal+ES fix) | ✅ DONE — `b2265d1` |
| 11 | Apply Kuma monitors live (83 total) + Postiz/Hermes | ✅ DONE — `ea131a7` |
| 12 | Postiz pg+redis exporters → Prometheus + Grafana | ✅ DONE — `e49134a` |
| 13 | Collect all READMEs → downloads/Homelab-Docs | ✅ DONE — `6db5026` |

**ALL TASKS COMPLETE.** Postiz login: `mianfaizanxgp@gmail.com` (registration locked).
Kuma/Postiz creds were provided live and are NOT stored in git.

---

## Done so far

### ✅ #1 Always-on Claude — the immortal session
- **Root cause of the "it hung / press any key to reconnect / lost 40 min" bug:**
  `claude` was a child of `sshd` (`systemd→sshd→bash→claude`). SSH drop → SIGHUP →
  claude killed. Server never lost power; only the client link did.
- **Fix shipped:** `utility/claude-code/` — `oil.sh` (launch/attach/status/new/ensure),
  `claude-oil.service` (systemd, boot-persistent), `README.md`.
- tmux server parented to `systemd` (PID1), socket `/tmp/tmux-0/default`.
- Gotchas solved: (a) systemd cgroup reaping → `KillMode=process`; (b) nvm not on
  systemd PATH → resolve node bin via glob `/root/.nvm/versions/node/*/bin`.
- `oil` alias added to `~/.bashrc`. Service `enabled`. **Verified Claude UI live.**

---

### ✅ #3 Green-commit streak keeper
- `git-push-pull.md` ledger created in web vault; `vault-to-github.sh` appends a
  row (run# · date · time · comment) every run → guaranteed green square Mon & Thu.
- Manual override: `vault-to-github.sh "custom comment"`.
- **⚠️ PRIVACY (told Faizan):** vault has ~65 personal `Claudy-Therapy/` notes.
  The mirror script pushed to `github.com/faizanxgp/Obsidian`. I **hard-excluded
  `Claudy-Therapy/`** from the mirror (`5a0a48b`). Last real sync predated these
  notes so nothing leaked yet. **ACTION for Faizan:** confirm the Obsidian repo is
  PRIVATE; decide if therapy notes should sync anywhere (separate private/encrypted
  repo?). `gh` CLI is not installed on the box — couldn't verify visibility.

### ✅ #4 Claude Code files in Obsidian
- `sites/obsidian/docker-compose.yml`: bind-mounted `/root/.claude/{agents,memory,
  settings*,statusline}` (rw) + `projects` chat-logs (ro) → `/config/vault/Claude-Code/`.
- Verified present inside container. Container-only mounts → never hit GitHub mirror.

### ✅ #5 Uptime Kuma container monitors (CODE done; apply pending)
- `provision-monitors.py` now adds a `🐳 Containers (no endpoint)` group with `DOCKER`
  monitors for promtail, cloudflared, node-exporter, cadvisor + 8 exporters, via a
  `local-socket` Docker host (auto-created). Idempotent. Compiles clean.
- **ACTION for Faizan (needs the Kuma admin password, not stored):**
  `cd /opt/homelab/utility/uptime-kuma && python3 -m venv venv && ./venv/bin/pip install uptime-kuma-api && ./venv/bin/python provision-monitors.py 'YOUR_PW'`

## NEXT (resume here)
- **#6** Deploy Postiz at `marketing/postiz` → `postiz.itproxima.com` (follow cloudflared
  tunnel + drawbridge/observatory pattern). Write the marketing-analytics brief for the
  Giant Group interview (Wed). Postiz needs Postgres+Redis+JWT secret; social posting
  needs his OAuth app creds (document, don't fabricate).
- Then #7 Hermes web UI → #8 GitHub badges plan.
- Update this file + push after each step.

## Open decisions to surface to Faizan (don't block on them — pick sane default)
- Postiz at `postiz.itproxima.com`: will provision behind the existing cloudflared
  tunnel pattern; needs DB + env. Default: deploy internal-first, expose when verified.
- Hermes "web UI": locate the existing Hermes agent first; pick a chat UI
  (Open WebUI / Lobe Chat) wired to its tools.

---

## Round 3 (2026-06-30, overnight) — big reorg + new stacks + achievements

**Mode:** code-only via merged PRs; live containers left running except the explicit
shutdowns below. Nothing new was started (RAM). Every compose validated with
`docker compose config` (all 34 stacks OK via `ops/homelab.sh config`).

### Decommissioned (stopped, volumes preserved — reversible)
`postiz · hermes · obsidian · uploads · downloads · apk-server · sillytavern ·
db-viewer · couchdb · snippetbox · dashy · glance · homepage`
→ freed ~3.8 GB RAM (was 0.65 GB free, now ~5–7 GB free).

### Renames (code-only; apply with `docker compose up -d` to recreate)
- `postgres-automation` → `automation-postgres`
- `textbee-db` → `textbee-mongo` (compose is vendored/gitignored — edited on disk)
- `temporal-postgresql` → `temporal-postgres` (+ new pg & ES exporters)

### Moves / structure
- Flattened `observatory/monitoring/*` → `observatory/` (pinned `name: monitoring`;
  repointed `/etc/cron.d/container-metrics`).
- `utility/postiz` → `marketing/postiz`; `utility/{obsidian,uploads,downloads,apk-server}`
  → `sites/`; `utility/hermes` → `ai-agents/hermes`. Live crons repointed.
- New external networks created: `marketing`, `sites`, `agents`.

### New stacks (defined, STOPPED — review before `up`)
- **marketing/**: listmonk, umami, matomo, metabase, typebot, chatwoot, plausible, posthog
- **ai-agents/**: flowise, langflow, librechat, anythingllm, dify
- **observatory/dozzle**, **dashboards/beszel**
- All exporters wired into Prometheus + Grafana (gen_dashboards now 41 dashboards,
  incl. MySQL + ClickHouse; promtool-validated).

### Uptime Kuma
- `provision-monitors.py` rewritten: full-topology monitors + a boxed, per-stack
  **status page** (`/homelab`) with custom CSS. Run with the admin password to apply.

### GitHub achievements (repo now public)
- **24 PRs** merged this session (all co-authored → Pair Extraordinaire; Pull Shark silver).
- **9 Q&A discussions** posted with self-accepted answers (→ Galaxy Brain silver).
  Mirrored in `discussions/`.

### NEXT for Faizan
- Review this transcript; decide which new stacks to actually run (start light ones
  first: umami, listmonk, metabase, flowise, langflow, anythingllm).
- Apply renames (`automation-postgres`, `textbee-mongo`, `temporal-postgres`) when
  ready — each is a recreate, data preserved.
- Run `provision-monitors.py 'KUMA_PW'` to apply the new monitors + status page.
- Add cloudflared ingress + DNS for any new public hosts you enable.
