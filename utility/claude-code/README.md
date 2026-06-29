# ♾️ The Immortal — the always-on Claude Code session

A Claude Code instance that **never dies when your SSH tunnel drops**, so
load-shedding, a tripped laptop, or a flaky ISP can't cost you tokens, context,
or hours of work.

## The problem it solves

This homelab runs on a **cloud VPS** — it never loses power. But when you SSH in
from your laptop and run `claude` directly, the process tree looks like this:

```
systemd ── sshd ── bash ── claude
```

Claude is a *child of the SSH connection*. The moment load-shedding kills your
laptop/router, the tunnel drops, `sshd` dies, and the kernel sends `SIGHUP` down
the chain — **killing Claude mid-task**. That's the "it hung, the timer froze,
then it said *press any key to reconnect* and I lost 40 minutes" bug. It was
never a token or Anthropic problem.

## The fix

Run Claude inside **tmux**. tmux's server is parented to `systemd` (PID 1), not
to `sshd`:

```
systemd ── tmux-server ── claude   ← The Immortal
```

Now an SSH drop **cannot** reach Claude. The work keeps running on the VPS. You
reconnect from your phone, re-attach, and you're back exactly where you were —
the timer never even paused.

## Install (already done once on this box)

```bash
cp utility/claude-code/claude-immortal.service /etc/systemd/system/claude-immortal.service
systemctl daemon-reload
systemctl enable --now claude-immortal.service
```

The service guarantees a tmux session named **`immortal`** running Claude exists
at all times and is recreated on every reboot.

## Daily use

```bash
immortal           # attach to The Immortal (raises it if needed)
immortal status    # is it alive? (without attaching)
immortal new       # restart claude FRESH inside the session (clean slate)
```

**To leave it running (detach):** press `Ctrl-b` then `d`. Claude keeps working.

### From your phone

1. SSH into the VPS with any mobile terminal (Termius, Blink, JuiceSSH) — or the
   Claude mobile app's terminal.
2. Run `immortal`.
3. You're attached to the same long-lived Claude session. Type, then detach with
   `Ctrl-b d` whenever you want — it never stops.

> The Claude **mobile app**'s remote sessions are tied to the lifetime of the
> underlying `claude` process. Because The Immortal keeps that process alive on
> the server, the session stays reachable instead of getting archived after a drop.

## Resetting context (new night / too much context)

The mobile app can't type slash-commands like `/compact` or `/clear`. So:

- **From any SSH (incl. mobile terminal):** `immortal new` kills the old claude and
  raises a **fresh** one with clean context. Continuity is preserved because the
  fresh session reads `/opt/homelab/THE-IMMORTAL.md` (the resume log).
- **From a desktop SSH attach:** `immortal`, then run `/compact` (summarise + keep
  going) or `/clear` (wipe context) inside the TUI as normal.

## Files

| File | Purpose |
|---|---|
| `immortal.sh` | launcher / attach / status / new / ensure |
| `claude-immortal.service` | systemd unit that keeps the session alive across reboots |
| `ship-pr.sh` | ship staged changes as a merged co-authored PR (GitHub badges) |
