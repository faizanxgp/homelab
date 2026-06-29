#!/usr/bin/env bash
# container-metrics.sh — per-container resource metrics for Prometheus, read straight
# from cgroup v2 files. This exists because cAdvisor cannot label containers on this
# host: Docker 29 uses the containerd image store (Storage Driver: overlayfs), and
# cAdvisor's docker handler aborts on every container trying to read a legacy
# image/overlay2/layerdb rw-layer that no longer exists ("failed to identify the
# read-write layer ID"). So we bypass cAdvisor entirely for container resources.
#
# Output is an atomically-written .prom file in node-exporter's textfile collector dir.
# Memory is exact bytes (memory.current); CPU is the cumulative cgroup counter
# (cpu.stat usage_usec) exposed as *_seconds_total so Grafana rate() gives cores used.
#
# Schedule: /etc/cron.d/container-metrics (every minute). Logs to /var/log/homelab.
set -euo pipefail

TEXTFILE_DIR="/var/lib/node_exporter/textfile_collector"
OUT="${TEXTFILE_DIR}/container_metrics.prom"
TMP="${OUT}.$$"
CGROOT="/sys/fs/cgroup/system.slice"

mkdir -p "$TEXTFILE_DIR"

# id(64hex) -> name map, single docker call
declare -A NAME COMPOSE
while read -r id nm proj; do
  NAME["$id"]="$nm"
  COMPOSE["$id"]="${proj:-}"
done < <(docker ps --no-trunc \
  --format '{{.ID}} {{.Names}} {{.Label "com.docker.compose.project"}}')

{
  echo "# HELP homelab_container_memory_bytes Container memory usage (cgroup memory.current)."
  echo "# TYPE homelab_container_memory_bytes gauge"
  echo "# HELP homelab_container_memory_anon_bytes Container anonymous (non-reclaimable) memory."
  echo "# TYPE homelab_container_memory_anon_bytes gauge"
  echo "# HELP homelab_container_memory_max_bytes Container memory limit (cgroup memory.max; 0 = unlimited)."
  echo "# TYPE homelab_container_memory_max_bytes gauge"
  echo "# HELP homelab_container_cpu_usage_seconds_total Cumulative CPU time (cgroup cpu.stat usage_usec)."
  echo "# TYPE homelab_container_cpu_usage_seconds_total counter"
  echo "# HELP homelab_container_pids Current number of processes/threads in the container."
  echo "# TYPE homelab_container_pids gauge"
  echo "# HELP homelab_container_up 1 if the container cgroup is present and readable."
  echo "# TYPE homelab_container_up gauge"

  for scope in "$CGROOT"/docker-*.scope; do
    [ -d "$scope" ] || continue
    id="${scope##*/docker-}"; id="${id%.scope}"
    name="${NAME[$id]:-${id:0:12}}"
    proj="${COMPOSE[$id]:-}"
    lbl="name=\"${name}\",project=\"${proj}\",id=\"${id:0:12}\""

    mem=$(cat "$scope/memory.current" 2>/dev/null || echo 0)
    anon=$(awk '/^anon /{print $2}' "$scope/memory.stat" 2>/dev/null || echo 0)
    max=$(cat "$scope/memory.max" 2>/dev/null || echo max)
    [ "$max" = "max" ] && max=0
    pids=$(cat "$scope/pids.current" 2>/dev/null || echo 0)
    usec=$(awk '/^usage_usec /{print $2}' "$scope/cpu.stat" 2>/dev/null || echo 0)
    cpu_sec=$(awk -v u="$usec" 'BEGIN{printf "%.6f", u/1000000}')

    printf 'homelab_container_memory_bytes{%s} %s\n' "$lbl" "${mem:-0}"
    printf 'homelab_container_memory_anon_bytes{%s} %s\n' "$lbl" "${anon:-0}"
    printf 'homelab_container_memory_max_bytes{%s} %s\n' "$lbl" "${max:-0}"
    printf 'homelab_container_cpu_usage_seconds_total{%s} %s\n' "$lbl" "$cpu_sec"
    printf 'homelab_container_pids{%s} %s\n' "$lbl" "${pids:-0}"
    printf 'homelab_container_up{%s} 1\n' "$lbl"
  done

  echo "# HELP homelab_container_metrics_last_run_seconds Unix time of last successful scrape build."
  echo "# TYPE homelab_container_metrics_last_run_seconds gauge"
  echo "homelab_container_metrics_last_run_seconds $(date +%s)"
} > "$TMP"

mv -f "$TMP" "$OUT"
