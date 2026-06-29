#!/usr/bin/env bash
# BoBo Prime — Cloudflare Tunnel deployer (Phase H).
# Idempotent: safe to re-run. Needs a CF API token with:
#   Account > Cloudflare Tunnel: Edit
#   Account > Access: Apps and Policies: Edit
#   Zone   > DNS: Edit        (itproxima.com)
#   Zone   > Zone: Read
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZONE_NAME="itproxima.com"
TUNNEL_NAME="bobo-prime"
ACCESS_EMAIL="${ACCESS_EMAIL:-mianfaizanxgp@gmail.com}"   # who may reach Postgres via Access

# --- token ---------------------------------------------------------------
TOKEN="${CF_API_TOKEN:-}"
[ -z "$TOKEN" ] && [ -f "$DIR/.cf_api_token" ] && TOKEN="$(tr -d ' \t\r\n' < "$DIR/.cf_api_token")"
if [ -z "$TOKEN" ]; then echo "ERROR: no API token (set CF_API_TOKEN or create $DIR/.cf_api_token)" >&2; exit 1; fi
command -v jq >/dev/null || { echo "ERROR: jq not installed" >&2; exit 1; }

API="https://api.cloudflare.com/client/v4"
api() { # method path [json-body]
  local m="$1" p="$2" d="${3:-}"
  if [ -n "$d" ]; then
    curl -sS -X "$m" "$API$p" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data "$d"
  else
    curl -sS -X "$m" "$API$p" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json"
  fi
}
ok() { echo "$1" | jq -e '.success == true' >/dev/null 2>&1; }
die() { echo "ERROR: $1"; echo "$2" | jq '.errors' 2>/dev/null || echo "$2"; exit 1; }

# --- hostname -> service map --------------------------------------------
# "host service [path-regex]"  -- optional 3rd field routes only matching paths
# (ordered: more specific path rules MUST come before the host catch-all)
ROUTES=(
  "n8n.$ZONE_NAME            http://n8n-main:5678"
  "evolution.$ZONE_NAME      http://evolution-api:8080"
  "text.$ZONE_NAME           http://textbee-api:3001    ^/api/v1"
  "text.$ZONE_NAME           http://textbee-web:3000"
  "home.$ZONE_NAME           http://homepage:3000"
  "dash.$ZONE_NAME           http://dashy:8080"
  "glance.$ZONE_NAME         http://glance:8080"
  "grafana.$ZONE_NAME        http://grafana:3000"
  "uptime.$ZONE_NAME         http://uptime-kuma:3001"
  "snippets.$ZONE_NAME       http://snippetbox:5000"
  "db.$ZONE_NAME             tcp://postgres-automation:5432"
  "tavern.$ZONE_NAME         http://sillytavern:8000"
  "apk.$ZONE_NAME            http://apk-server:80"
  "downloads.$ZONE_NAME      http://downloads:80"
  "uploads.$ZONE_NAME        http://uploads:80"
  "obsidian.$ZONE_NAME       http://obsidian:3000"
  "couch.$ZONE_NAME          http://couchdb:5984"
  "dav.$ZONE_NAME            http://webdav:6065"
  "postiz.$ZONE_NAME         http://postiz:5000"
  "hermes.$ZONE_NAME         http://hermes:8080"
)
# NOTE: postiz is intentionally NOT in ACCESS_HOSTS — it has its own auth, and a
# Cloudflare Access gate would break social-platform OAuth callbacks to /api/*.

# Hostnames that get an email-allowlist Cloudflare Access gate in front of them.
# (db is tcp so its app is self_hosted; tavern is http so http is fine.)
ACCESS_HOSTS=(
  "db.$ZONE_NAME"
  "tavern.$ZONE_NAME"
  "uploads.$ZONE_NAME"
  "obsidian.$ZONE_NAME"
  "hermes.$ZONE_NAME"
)

echo "==> Resolving account + zone"
ZRESP="$(api GET "/zones?name=$ZONE_NAME")"
ZONE_ID="$(echo "$ZRESP" | jq -r '.result[0].id // empty')"
ACCT_ID="$(echo "$ZRESP" | jq -r '.result[0].account.id // empty')"   # derive acct from zone (token can't list /accounts)
[ -z "$ZONE_ID" ] && die "zone $ZONE_NAME not found for this token" "$ZRESP"
[ -z "$ACCT_ID" ] && die "could not derive account id from zone" "$ZRESP"
echo "    account=$ACCT_ID zone=$ZONE_ID"

# --- tunnel (create or reuse) -------------------------------------------
echo "==> Tunnel '$TUNNEL_NAME'"
TRESP="$(api GET "/accounts/$ACCT_ID/cfd_tunnel?name=$TUNNEL_NAME&is_deleted=false")"
TUNNEL_ID="$(echo "$TRESP" | jq -r '.result[0].id // empty')"
if [ -z "$TUNNEL_ID" ]; then
  SECRET="$(openssl rand -base64 32)"
  CRESP="$(api POST "/accounts/$ACCT_ID/cfd_tunnel" \
    "$(jq -nc --arg n "$TUNNEL_NAME" --arg s "$SECRET" '{name:$n,tunnel_secret:$s,config_src:"cloudflare"}')")"
  ok "$CRESP" || die "tunnel create failed" "$CRESP"
  TUNNEL_ID="$(echo "$CRESP" | jq -r '.result.id')"
  echo "    created $TUNNEL_ID"
else
  echo "    reusing $TUNNEL_ID"
fi
TOKEN_RESP="$(api GET "/accounts/$ACCT_ID/cfd_tunnel/$TUNNEL_ID/token")"
TUNNEL_TOKEN="$(echo "$TOKEN_RESP" | jq -r '.result')"
[ "$TUNNEL_TOKEN" = "null" ] && die "could not fetch tunnel token" "$TOKEN_RESP"

# --- ingress config ------------------------------------------------------
echo "==> Pushing ingress config"
ING="[]"
for r in "${ROUTES[@]}"; do
  h="$(echo "$r" | awk '{print $1}')"; s="$(echo "$r" | awk '{print $2}')"; p="$(echo "$r" | awk '{print $3}')"
  if [ -n "$p" ]; then
    ING="$(echo "$ING" | jq -c --arg h "$h" --arg s "$s" --arg p "$p" '. + [{hostname:$h, service:$s, path:$p}]')"
  else
    ING="$(echo "$ING" | jq -c --arg h "$h" --arg s "$s" '. + [{hostname:$h, service:$s}]')"
  fi
done
ING="$(echo "$ING" | jq -c '. + [{service:"http_status:404"}]')"
CFG="$(jq -nc --argjson ing "$ING" '{config:{ingress:$ing}}')"
CRESP="$(api PUT "/accounts/$ACCT_ID/cfd_tunnel/$TUNNEL_ID/configurations" "$CFG")"
ok "$CRESP" || die "ingress config failed" "$CRESP"
echo "    $(echo "$ING" | jq 'length') ingress rules set"

# --- DNS CNAMEs (upsert, proxied) ---------------------------------------
echo "==> DNS records -> $TUNNEL_ID.cfargotunnel.com"
TARGET="$TUNNEL_ID.cfargotunnel.com"
seen_hosts=""
for r in "${ROUTES[@]}"; do
  h="$(echo "$r" | awk '{print $1}')"
  case " $seen_hosts " in *" $h "*) continue ;; esac   # one DNS record per host (skip path-rule dupes)
  seen_hosts="$seen_hosts $h"
  body="$(jq -nc --arg n "$h" --arg c "$TARGET" '{type:"CNAME",name:$n,content:$c,proxied:true}')"
  ex="$(api GET "/zones/$ZONE_ID/dns_records?type=CNAME&name=$h")"
  rid="$(echo "$ex" | jq -r '.result[0].id // empty')"
  if [ -n "$rid" ]; then
    out="$(api PATCH "/zones/$ZONE_ID/dns_records/$rid" "$body")"; verb="updated"
  else
    out="$(api POST "/zones/$ZONE_ID/dns_records" "$body")"; verb="created"
  fi
  ok "$out" && echo "    $verb  $h" || die "DNS $h failed" "$out"
done

# --- Access gates (email allowlist) for sensitive hosts ----------------
echo "==> Cloudflare Access gates"
APPS="$(api GET "/accounts/$ACCT_ID/access/apps")"
polbody="$(jq -nc --arg e "$ACCESS_EMAIL" '{name:"allow-owner",decision:"allow",include:[{email:{email:$e}}]}')"

for d in "${ACCESS_HOSTS[@]}"; do
  case "$d" in
    db.*)   appname="Postgres (BoBo Prime)"; apptype="self_hosted" ;;
    tavern.*) appname="SillyTavern (BoBo Prime)"; apptype="self_hosted" ;;
    uploads.*) appname="Uploads (BoBo Prime)"; apptype="self_hosted" ;;
    obsidian.*) appname="Obsidian (BoBo Prime)"; apptype="self_hosted" ;;
    *)      appname="$d"; apptype="self_hosted" ;;
  esac

  APP_ID="$(echo "$APPS" | jq -r --arg d "$d" '.result[]? | select(.domain==$d) | .id' | head -1)"
  appbody="$(jq -nc --arg d "$d" --arg n "$appname" --arg t "$apptype" '{name:$n,domain:$d,type:$t,session_duration:"24h"}')"
  if [ -z "$APP_ID" ]; then
    AR="$(api POST "/accounts/$ACCT_ID/access/apps" "$appbody")"; ok "$AR" || die "access app create failed ($d)" "$AR"
    APP_ID="$(echo "$AR" | jq -r '.result.id')"; echo "    app created $APP_ID  ($d)"
  else
    echo "    app exists $APP_ID  ($d)"
  fi
  POLS="$(api GET "/accounts/$ACCT_ID/access/apps/$APP_ID/policies")"
  POL_ID="$(echo "$POLS" | jq -r '.result[]? | select(.name=="allow-owner") | .id' | head -1)"
  if [ -z "$POL_ID" ]; then
    PR="$(api POST "/accounts/$ACCT_ID/access/apps/$APP_ID/policies" "$polbody")"; ok "$PR" || die "policy create failed ($d)" "$PR"
    echo "    policy created (allow $ACCESS_EMAIL)  ($d)"
  else
    PR="$(api PUT "/accounts/$ACCT_ID/access/apps/$APP_ID/policies/$POL_ID" "$polbody")"; ok "$PR" || die "policy update failed ($d)" "$PR"
    echo "    policy updated (allow $ACCESS_EMAIL)  ($d)"
  fi
done

# --- write connector token + bring up -----------------------------------
echo "==> Writing .env"
umask 077
printf 'TUNNEL_TOKEN=%s\n' "$TUNNEL_TOKEN" > "$DIR/.env"
echo "    wrote $DIR/.env (TUNNEL_TOKEN set)"

echo
echo "DONE. Now:  docker compose -f $DIR/docker-compose.yml up -d"
echo "Tunnel ID:  $TUNNEL_ID"
