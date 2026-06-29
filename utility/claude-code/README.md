# 🛢️ Midnight Oil — the always-on Claude Code session

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
systemd ── tmux-server ── claude
```

Now an SSH drop **cannot** reach Claude. The work keeps running on the VPS. You
reconnect from your phone, re-attach, and you're back exactly where you were —
the timer never even paused.

## Install (already done once on this box)

```bash
cp utility/claude-code/claude-oil.service /etc/systemd/system/claude-oil.service
systemctl daemon-reload
systemctl enable --now claude-oil.service
```

The service guarantees a tmux session named **`oil`** running Claude exists at
all times and is recreated on every reboot.

## Daily use

```bash
oil            # attach to the always-on session (alias for oil.sh)
oil status     # is it alive? (without attaching)
oil new        # restart claude fresh inside the session
```

**To leave it running (detach):** press `Ctrl-b` then `d`. Claude keeps working.

### From your phone

1. SSH into the VPS with any mobile terminal (Termius, Blink, JuiceSSH).
2. Run `oil`.
3. You're attached to the same long-lived Claude session. Type, then detach with
   `Ctrl-b d` whenever you want — it never stops.

> The Claude **mobile app**'s remote sessions are tied to the lifetime of the
> underlying `claude` process. Because `oil` keeps that process alive on the
> server, the session stays reachable instead of getting archived after a drop.

## Files

| File | Purpose |
|---|---|
| `oil.sh` | idempotent launcher / attach / status |
| `claude-oil.service` | systemd unit that keeps the `oil` session alive across reboots |
