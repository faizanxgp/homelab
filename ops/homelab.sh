#!/usr/bin/env bash
# homelab.sh — discover and manage every Compose stack in the monorepo.
#
#   ops/homelab.sh list              # every stack + running/stopped
#   ops/homelab.sh config            # `docker compose config -q` on all (validate)
#   ops/homelab.sh ps                # running containers
#   ops/homelab.sh up   <dir>        # bring one stack up   (e.g. marketing/umami)
#   ops/homelab.sh down <dir>        # bring one stack down (keeps volumes)
#
# Stacks are auto-discovered from docker-compose.yml files, so new ones are picked
# up automatically. Vendored/venv/volume paths are skipped.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

discover() {
  find . -name docker-compose.yml \
    -not -path '*/volumes/*' -not -path '*/venv/*' \
    -not -path '*/node_modules/*' -not -path './.git/*' \
    | sed 's#/docker-compose.yml##; s#^\./##' | sort
}

cmd="${1:-list}"
case "$cmd" in
  list)
    printf '%-28s %s\n' "STACK (dir)" "STATE"
    for d in $(discover); do
      proj=$(grep -m1 '^name:' "$d/docker-compose.yml" 2>/dev/null | awk '{print $2}')
      proj="${proj:-$(basename "$d")}"
      n=$(docker compose --project-directory "$d" -f "$d/docker-compose.yml" ps -q 2>/dev/null | wc -l)
      [ "$n" -gt 0 ] && state="● up ($n)" || state="○ stopped"
      printf '%-28s %s\n' "$d" "$state"
    done
    ;;
  config)
    fail=0
    for d in $(discover); do
      if docker compose -f "$d/docker-compose.yml" --project-directory "$d" config -q 2>/tmp/cfgerr; then
        echo "OK   $d"
      else
        echo "FAIL $d"; sed 's/^/       /' /tmp/cfgerr; fail=1
      fi
    done
    exit $fail
    ;;
  ps)   docker ps --format 'table {{.Names}}\t{{.Status}}' ;;
  up)   d="${2:?usage: up <dir>}";   docker compose --project-directory "$d" -f "$d/docker-compose.yml" up -d ;;
  down) d="${2:?usage: down <dir>}"; docker compose --project-directory "$d" -f "$d/docker-compose.yml" down ;;
  *)    echo "unknown command: $cmd"; sed -n '3,12p' "$0"; exit 2 ;;
esac
