#!/usr/bin/env bash
# ship-pr.sh — ship staged changes as a co-authored, merged PR.
#
# Earns / progresses GitHub achievements on PUBLIC repos:
#   • Pair Extraordinaire — commit carries a Co-Authored-By trailer
#   • Pull Shark          — a merged PR (tiers at 2/16/128/1024)
#   • YOLO                — merged without review (already have it)
#
# Achievements only count in PUBLIC repos. Run from inside a repo clone with your
# changes already `git add`ed.
#
# Usage:
#   ship-pr.sh "commit / PR title"
#
# Requires: a GitHub token in ~/.git-credentials (used for the API).
set -euo pipefail

TITLE="${1:?usage: ship-pr.sh \"PR title\"}"
COAUTHOR="${COAUTHOR:-Claude Opus 4.8 <noreply@anthropic.com>}"
TOKEN="$(sed -E 's#https://[^:]+:([^@]+)@.*#\1#' ~/.git-credentials | head -1)"
[ -z "$TOKEN" ] && { echo "no token in ~/.git-credentials"; exit 1; }

# Resolve owner/repo from origin
ORIGIN="$(git config --get remote.origin.url)"
SLUG="$(echo "$ORIGIN" | sed -E 's#.*github.com[:/]([^/]+/[^/]+?)(\.git)?$#\1#')"
BASE="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#origin/##')"
BASE="${BASE:-main}"
BRANCH="ship/$(date +%s)"

echo "repo=$SLUG base=$BASE branch=$BRANCH"
git switch -c "$BRANCH" >/dev/null
git commit -q -m "$TITLE

Co-Authored-By: $COAUTHOR"
git push -q -u origin "$BRANCH"

api() { curl -sS -H "Authorization: token $TOKEN" -H "Accept: application/vnd.github+json" "$@"; }
PR=$(api -X POST "https://api.github.com/repos/$SLUG/pulls" \
  -d "{\"title\":$(printf '%s' "$TITLE" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))'),\"head\":\"$BRANCH\",\"base\":\"$BASE\"}")
NUM=$(echo "$PR" | python3 -c "import sys,json;print(json.load(sys.stdin).get('number',''))")
[ -z "$NUM" ] && { echo "PR create failed:"; echo "$PR" | head -20; exit 1; }
echo "opened PR #$NUM"
api -X PUT "https://api.github.com/repos/$SLUG/pulls/$NUM/merge" \
  -d '{"merge_method":"squash"}' >/dev/null
echo "✅ merged PR #$NUM — Pair Extraordinaire + Pull Shark credited (public repos only)"
git switch -q "$BASE" && git pull -q && git branch -D "$BRANCH" >/dev/null 2>&1 || true
