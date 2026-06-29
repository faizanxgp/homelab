#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  immortal.sh — "The Immortal": an always-on Claude Code session that cannot be
#  killed by an SSH drop / load-shedding / a dead laptop.
#
#  WHY
#  Claude launched from an SSH shell is a child of sshd:
#         systemd ── sshd ── bash ── claude
#  When the tunnel drops, sshd dies, the kernel SIGHUPs the chain, and claude is
#  killed mid-thought — losing tokens, context and up to ~40 min of work.
#
#  THE FIX
#  Run claude inside tmux. The tmux server is parented to systemd (PID 1):
#         systemd ── tmux-server ── claude   ← The Immortal
#  An SSH drop can't touch it. The VPS never loses power, so the work keeps
#  running. You re-attach from your phone and pick up exactly where you were.
#
#  USAGE
#    immortal           # attach to The Immortal (creating + launching it if needed)
#    immortal new       # restart claude FRESH inside the session (clean slate)
#    immortal status    # is it alive? (without attaching)
#    immortal ensure    # guarantee it exists, no attach (used by systemd)
#
#  DETACH (leave it running):  press  Ctrl-b  then  d
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SESSION="immortal"
WORKDIR="/opt/homelab"
SOCKET="/tmp/tmux-0/default"           # explicit so systemd + ssh share one server

# Resolve the nvm node bin dir by filesystem glob (newest version), so this works
# under systemd's bare environment too — nvm is NOT sourced for the non-interactive
# shells systemd uses. Prepending it to PATH makes both `node` and `claude` resolve.
NODE_BIN="$(ls -d /root/.nvm/versions/node/*/bin 2>/dev/null | sort -V | tail -1)"
if [ -n "$NODE_BIN" ]; then export PATH="$NODE_BIN:$PATH"; fi
export HOME="${HOME:-/root}"
CLAUDE_CMD="exec env IS_SANDBOX=1 claude --dangerously-skip-permissions"

tmux="tmux -S ${SOCKET}"

ensure_session() {
  if ! $tmux has-session -t "$SESSION" 2>/dev/null; then
    $tmux new-session -d -s "$SESSION" -c "$WORKDIR" "$CLAUDE_CMD"
    sleep 1
  fi
}

case "${1:-attach}" in
  status)
    if $tmux has-session -t "$SESSION" 2>/dev/null; then
      echo "✅ THE IMMORTAL is ALIVE (parented to systemd, survives SSH drops)."
      $tmux list-panes -t "$SESSION" -F '   pane #{pane_index}: #{pane_current_command}' 2>/dev/null || true
    else
      echo "❌ The Immortal is NOT running. Run 'immortal' to raise it."
    fi
    ;;
  ensure)
    ensure_session
    echo "The Immortal ensured."
    ;;
  new)
    $tmux kill-session -t "$SESSION" 2>/dev/null || true
    ensure_session
    echo "Raised a FRESH Immortal (clean context). Attaching…"
    [ -t 1 ] && exec $tmux attach -t "$SESSION"
    ;;
  attach|*)
    ensure_session
    if [ -t 1 ]; then
      exec $tmux attach -t "$SESSION"
    else
      echo "The Immortal ensured (no TTY to attach to)."
    fi
    ;;
esac
