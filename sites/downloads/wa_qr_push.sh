#!/usr/bin/env bash
# Push a LIVE WhatsApp QR for an Evolution instance into the public downloads drop.
#
#   wa_qr_push.sh <instance> <slug> [loop_seconds]
#   e.g.  wa_qr_push.sh mian_one wa_qr1 600
#
# Creates the instance if it doesn't exist, then refreshes <slug>.png every few
# seconds (writing an auto-refreshing <slug>.html wrapper) until the instance
# reports "open" (linked) or loop_seconds elapses. Reusable for every number.
set -uo pipefail

INST="${1:?usage: wa_qr_push.sh <instance> <slug> [loop_seconds]}"
SLUG="${2:?usage: wa_qr_push.sh <instance> <slug> [loop_seconds]}"
LOOP="${3:-600}"

API="http://127.0.0.1:8080"
KEY="$(grep -E '^EVO_API_KEY=' /opt/homelab/automation/evoapi/.env | cut -d= -f2- | tr -d ' \r\n')"
OUT="/opt/homelab/sites/downloads/files"
PNG="$OUT/$SLUG.png"
HTML="$OUT/$SLUG.html"

hdr=(-H "apikey: $KEY")

write_html() { # $1 = state line
  cat > "$HTML" <<EOF
<!doctype html><html><head><meta charset="utf-8">
<title>WhatsApp QR — $INST</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
 body{font-family:system-ui,sans-serif;background:#0b141a;color:#e9edef;text-align:center;margin:0;padding:32px}
 h1{font-weight:600;font-size:20px} .meta{color:#8696a0;font-size:14px;margin-bottom:18px}
 img{width:300px;height:300px;background:#fff;border-radius:12px;padding:10px}
 .ok{color:#25d366;font-size:22px;font-weight:600}
</style></head><body>
<h1>Link WhatsApp — <code>$INST</code></h1>
<div class="meta">$1</div>
<div id="box"><img id="qr" src="$SLUG.png?t=0" alt="QR"></div>
<p class="meta">WhatsApp &rarr; Settings &rarr; Linked Devices &rarr; Link a Device</p>
<script>
 // reload the QR image every 8s; reload whole page every 60s to pick up state changes
 setInterval(function(){document.getElementById('qr').src='$SLUG.png?t='+Date.now();},8000);
 setTimeout(function(){location.reload();},60000);
</script>
</body></html>
EOF
}

# ensure instance exists (ignore "already in use")
curl -s -m 25 -X POST "$API/instance/create" "${hdr[@]}" -H "Content-Type: application/json" \
  -d "{\"instanceName\":\"$INST\",\"integration\":\"WHATSAPP-BAILEYS\",\"qrcode\":true}" >/dev/null 2>&1

write_html "Generating QR…"
echo "[wa_qr_push] $INST -> $SLUG  (downloads.itproxima.com/$SLUG)"

start=$(date +%s)
while :; do
  state="$(curl -s -m 10 "${hdr[@]}" "$API/instance/connectionState/$INST" | python3 -c 'import json,sys;print((json.load(sys.stdin).get("instance") or {}).get("state","?"))' 2>/dev/null)"
  if [ "$state" = "open" ]; then
    write_html "&#10003; LINKED — this number is connected."
    sed -i 's#<img id="qr"[^>]*>#<div class="ok">&#10003; Connected</div>#' "$HTML"
    echo "[wa_qr_push] $INST is LINKED (state=open). Done."
    break
  fi
  # pull a fresh QR
  b64="$(curl -s -m 12 "${hdr[@]}" "$API/instance/connect/$INST" | python3 -c 'import json,sys;d=json.load(sys.stdin);b=d.get("base64") or "";print(b.split(",",1)[1] if "," in b else b)' 2>/dev/null)"
  if [ -n "$b64" ]; then
    echo "$b64" | base64 -d > "$PNG.tmp" 2>/dev/null && mv "$PNG.tmp" "$PNG"
    write_html "Live QR — refreshes automatically. State: $state"
  fi
  now=$(date +%s); [ $((now-start)) -ge "$LOOP" ] && { echo "[wa_qr_push] timeout after ${LOOP}s (state=$state)"; break; }
  # short wait between refreshes (curl latency + this) keeps QR fresh
  python3 -c 'import time;time.sleep(6)'
done
