#!/usr/bin/env bash
# Obsidian vault -> GitHub (faizanxgp/Obsidian), NOTES ONLY.
#
# Mirrors *.md (folder structure preserved) from the web vault into a dedicated
# git repo and pushes. Deliberately excludes .obsidian/ (themes, community plugins,
# and the LiveSync data.json which holds the CouchDB password + E2E passphrase),
# the 50GB storage/ mount, .trash/, and every non-markdown file.
#
# Run by cron every Monday & Thursday (see utility/obsidian/cron/obsidian-vault).
set -euo pipefail

VAULT="/opt/homelab/utility/obsidian/volumes/config/vault"   # the web vault (LiveSync target)
MIRROR="/opt/obsidian-vault"                                  # dedicated git mirror (outside the homelab repo)
REMOTE="https://github.com/faizanxgp/Obsidian.git"
BRANCH="main"
LOG="/var/log/homelab/vault-push.log"

mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1
echo "===== $(date -Is) :: vault -> github sync ====="

if [ ! -d "$VAULT" ]; then echo "vault not found at $VAULT — aborting"; exit 1; fi

# First-run init of the mirror repo
if [ ! -d "$MIRROR/.git" ]; then
  echo "initialising mirror repo at $MIRROR"
  mkdir -p "$MIRROR"
  git -C "$MIRROR" init -q -b "$BRANCH"
  git -C "$MIRROR" remote add origin "$REMOTE"
fi
git -C "$MIRROR" config user.name  "faizanxgp"
git -C "$MIRROR" config user.email "mianfaizanxgp@gmail.com"

# Regenerated repo README (protected from the --delete sweep below)
cat > "$MIRROR/README.md" <<'MD'
# 📓 Obsidian Vault

Notes only (`.md`), auto-synced from the homelab every **Monday & Thursday**.

Attachments, themes, community plugins, the LiveSync config, and the bulk
`storage/` mount are intentionally excluded — this repo is just the writing.
MD

# Mirror ONLY markdown, preserving folders. Excluded paths are also protected
# from --delete, so .git/ and README.md survive.
rsync -a --delete --prune-empty-dirs \
  --exclude='.git/' \
  --exclude='/README.md' \
  --exclude='.obsidian/' \
  --exclude='.trash/' \
  --exclude='storage/' \
  --include='*/' \
  --include='*.md' \
  --exclude='*' \
  "$VAULT/" "$MIRROR/"

cd "$MIRROR"
git add -A
if git diff --cached --quiet; then
  echo "no note changes — nothing to commit"
  exit 0
fi

ADDED=$(git diff --cached --name-status | grep -c '^A' || true)
MODIFIED=$(git diff --cached --name-status | grep -c '^M' || true)
DELETED=$(git diff --cached --name-status | grep -c '^D' || true)
TOTAL=$(find . -name '*.md' -not -path './.git/*' | wc -l | tr -d ' ')
MSG="📓 Vault sync — $(date +%A) $(date +%Y-%m-%d) · +${ADDED} new, ${MODIFIED} edited, ${DELETED} removed (${TOTAL} notes)"

git commit -q -m "$MSG"
git push -q -u origin "$BRANCH"
echo "pushed: $MSG"
