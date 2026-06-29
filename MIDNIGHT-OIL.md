# 🛢️ Midnight Oil — autonomous work session log

**Started:** 2026-06-29 ~23:30 CEST (≈ 2026-06-30 02:30 PKT)
**Why:** Load-shedding (power out ~03:10 PKT). Faizan is asleep; Claude works
autonomously for 3–4 h. This file is the **resume point** — if the SSH session
dies, a fresh `oil` session reads this and continues from "NEXT".

> Reattach the always-on session from any terminal (incl. phone):  **`oil`**
> Detach (leave it running): `Ctrl-b` then `d`.

---

## Key facts about this box (so a cold session has context)

- This is a **cloud VPS** (`vmi3391102`, QEMU/KVM) — **never loses power.** Only
  Faizan's laptop SSH link dies during load-shedding.
- Homelab monorepo: **`/opt/homelab`** → `github.com/faizanxgp/homelab` (push works,
  creds in `/root/.git-credentials`). Commit as `faizanxgp / mianfaizanxgp@gmail.com`.
- Obsidian: **web vault** (editable in `obsidian.itproxima.com`) lives at
  `/opt/homelab/utility/obsidian/volumes/config/vault/`. A cron mirrors `*.md`
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
| 1 | Always-on Claude (tmux+systemd `oil`) | ✅ DONE — committed `fe7c7a2` |
| 2 | This resume log + frequent updates | 🔄 in progress |
| 3 | `git-push-pull.md` green-commit cron | ⏳ next |
| 4 | Expose Claude Code files in Obsidian | ⏳ |
| 5 | Finish Uptime Kuma no-endpoint container monitors | ⏳ |
| 6 | Deploy Postiz + marketing brief for Giant Group interview (Wed) | ⏳ |
| 7 | Hermes agent web UI + docker interactivity | ⏳ |
| 8 | GitHub badges plan (`github.com/faizanxgp`) | ⏳ |

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

## NEXT (resume here)
- **#3** Add `git-push-pull.md` to the web vault; modify `vault-to-github.sh` to append
  a timestamped row (date · time · run-id · comment) every run so there's always a diff
  → guaranteed green commit Mon & Thu. Commit to homelab repo.
- Then #4 → #8 in order. Update this file + push after each.

## Open decisions to surface to Faizan (don't block on them — pick sane default)
- Postiz at `postiz.itproxima.com`: will provision behind the existing cloudflared
  tunnel pattern; needs DB + env. Default: deploy internal-first, expose when verified.
- Hermes "web UI": locate the existing Hermes agent first; pick a chat UI
  (Open WebUI / Lobe Chat) wired to its tools.
