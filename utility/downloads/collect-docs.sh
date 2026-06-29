#!/usr/bin/env bash
# Gather all homelab READMEs + key docs into downloads/files/Homelab-Docs/ with
# clear, human names — so they're browsable at downloads.itproxima.com AND visible
# in Obsidian (the downloads dir is bind-mounted into the vault at storage/downloads).
#
# Re-run anytime to refresh. Output is gitignored (served file drop); this script
# is the tracked source of truth.
set -euo pipefail

REPO="/opt/homelab"
OUT="$REPO/utility/downloads/files/Homelab-Docs"
rm -rf "$OUT"; mkdir -p "$OUT"

# title-case a dir slug: "uptime-kuma" -> "Uptime Kuma"
titlecase() { echo "$1" | sed 's/[-_]/ /g' | awk '{for(i=1;i<=NF;i++)$i=toupper(substr($i,1,1)) substr($i,2)}1'; }

copy() { # src  nicename
  local src="$1" name="$2"
  [ -f "$src" ] || return 0
  { echo "> 📄 Source: \`${src#$REPO/}\` — auto-collected $(date +%Y-%m-%d). Edit the source, then re-run collect-docs.sh."; echo; cat "$src"; } > "$OUT/$name"
}

# ── Tonight's headline docs (numbered so they sort first) ───────────────────
copy "$REPO/THE-IMMORTAL.md"                       "00 - The Immortal (session log).md"
copy "$REPO/utility/claude-code/README.md"         "01 - The Immortal - always-on Claude (how-to).md"
copy "$REPO/utility/postiz/README.md"              "02 - Postiz (social scheduler).md"
copy "$REPO/utility/postiz/marketing-arsenal.md"   "03 - Marketing Analytics Arsenal (interview brief).md"
copy "$REPO/utility/hermes/README.md"              "04 - Hermes (AI agent web UI).md"
copy "$REPO/utility/uptime-kuma/README.md"         "05 - Uptime Kuma (monitors).md"
copy "$REPO/COOL-STACK-IDEAS.md"                   "06 - Cool Stack Ideas (what to add next).md"
copy "$REPO/GITHUB-BADGES.md"                      "07 - GitHub Badges (farming plan).md"
copy "$REPO/README.md"                             "08 - Homelab (overview).md"

# ── Every other service README, auto-named by its folder ────────────────────
for d in "$REPO"/utility/*/ "$REPO"/automation/*/ "$REPO"/observatory/*/ "$REPO"/dashboards/ "$REPO"/sites/*/; do
  [ -f "${d}README.md" ] || continue
  slug="$(basename "$d")"
  case "$slug" in claude-code|postiz|hermes|uptime-kuma) continue ;; esac   # already added above
  copy "${d}README.md" "$(titlecase "$slug") - README.md"
done

# ── Index ───────────────────────────────────────────────────────────────────
{
  echo "# 🗂️ Homelab Docs — index"
  echo
  echo "All homelab READMEs + key docs, auto-collected by \`utility/downloads/collect-docs.sh\`."
  echo "Browse/download at **downloads.itproxima.com/Homelab-Docs/** or open in Obsidian."
  echo
  ( cd "$OUT" && for f in *.md; do [ "$f" = "INDEX.md" ] && continue; echo "- [$f](<$f>)"; done )
} > "$OUT/INDEX.md"

echo "Collected $(ls "$OUT" | wc -l) docs into $OUT"
ls "$OUT"
