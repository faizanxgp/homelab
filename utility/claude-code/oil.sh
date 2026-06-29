#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  oil.sh — the "Midnight Oil" always-on Claude Code session.
#
#  WHY THIS EXISTS
#  Claude Code, when launched from an interactive SSH shell, is a child of that
#  shell which is a child of sshd:
#         systemd ── sshd ── bash ── claude
#  When load-shedding kills the laptop/router, the SSH tunnel drops, sshd dies,
#  the kernel SIGHUPs the chain, and the claude process is killed mid-thought —
#  losing tokens, context and up to ~40 min of work ("press any key to reconnect").
#
#  THE FIX
#  Run claude inside tmux. The tmux *server* is parented to systemd (PID 1), not
#  to sshd:
#         systemd ── tmux-server ── claude
#  Now an SSH drop cannot kill claude. The work keeps running on the VPS (which
#  never loses power). You simply re-attach from your phone and pick up exactly
#  where you left off — the timer never even paused.
#
#  USAGE
#    oil.sh            # attach to the 'oil' session (creating + launching claude
#                      # if it isn't running yet)
#    oil.sh new        # start claude fresh inside the session (kills the old pane)
#    oil.sh status     # show whether the session is alive, without attaching
#
#  DETACH (leave it running):  press  Ctrl-b  then  d
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SESSION="oil"
WORKDIR="/opt/homelab"
SOCKET="/tmp/tmux-0/default"           # explicit so systemd + ssh share one server

# Resolve the nvm node bin dir by filesystem glob (newest version), so this works
# under systemd's bare environment too — `.bashrc`/nvm is NOT sourced for the
# non-interactive shells systemd uses, so we must not rely on it. Prepending this
# dir to PATH makes both `node` and `claude` resolve.
NODE_BIN="$(ls -d /root/.nvm/versions/node/*/bin 2>/dev/null | sort -V | tail -1)"
if [ -n "$NODE_BIN" ]; then export PATH="$NODE_BIN:$PATH"; fi
export HOME="${HOME:-/root}"
CLAUDE_CMD="exec env IS_SANDBOX=1 claude --dangerously-skip-permissions"

tmux="tmux -S ${SOCKET}"

ensure_session() {
  if ! $tmux has-session -t "$SESSION" 2>/dev/null; then
    # New tmux server inherits this script's PATH (with NODE_BIN), so the pane
    # finds claude. -d = detached (lives independent of any terminal).
    $tmux new-session -d -s "$SESSION" -c "$WORKDIR" "$CLAUDE_CMD"
    sleep 1
  fi
}

case "${1:-attach}" in
  status)
    if $tmux has-session -t "$SESSION" 2>/dev/null; then
      echo "✅ 'oil' session is ALIVE (parented to systemd, survives SSH drops)."
      $tmux list-panes -t "$SESSION" -F '   pane #{pane_index}: #{pane_current_command}' 2>/dev/null || true
    else
      echo "❌ 'oil' session is NOT running. Run 'oil.sh' to start it."
    fi
    ;;
  ensure)
    # Non-interactive: just guarantee the session exists (used by systemd).
    ensure_session
    echo "'oil' session ensured."
    ;;
  new)
    $tmux kill-session -t "$SESSION" 2>/dev/null || true
    ensure_session
    echo "Relaunched claude in 'oil'. Attaching…"
    [ -t 1 ] && exec $tmux attach -t "$SESSION"
    ;;
  attach|*)
    ensure_session
    if [ -t 1 ]; then
      exec $tmux attach -t "$SESSION"
    else
      echo "'oil' session ensured (no TTY to attach to)."
    fi
    ;;
esac
