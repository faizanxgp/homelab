#!/usr/bin/env python3
"""Generate homelab Grafana dashboards bound to the 'prometheus' datasource.
All metric names used here were verified live against the running exporters."""
import json, os

DS = {"type": "prometheus", "uid": "prometheus"}
OUT = "/opt/homelab/observatory/monitoring/grafana/dashboards"

PG_INSTANCES = [("n8n-postgres", "n8n"), ("evo-postgres", "evolution"), ("postgres-automation", "automation")]
REDIS_INSTANCES = [("n8n-redis", "n8n"), ("evo-redis", "evolution"), ("textbee-redis", "textbee")]

_id = 0
def nid():
    global _id; _id += 1; return _id

def tgt(expr, legend="", ref="A", instant=False):
    return {"datasource": DS, "expr": expr, "legendFormat": legend, "refId": ref, "instant": instant}

def gp(x, y, w, h): return {"x": x, "y": y, "w": w, "h": h}

def _fields(unit=None, decimals=None, mappings=None, thresholds=None, color_mode=None):
    cfg = {"color": {"mode": color_mode or "palette-classic"}, "custom": {}}
    if unit: cfg["unit"] = unit
    if decimals is not None: cfg["decimals"] = decimals
    if mappings: cfg["mappings"] = mappings
    if thresholds:
        cfg["thresholds"] = {"mode": "absolute", "steps": thresholds}
    else:
        cfg["thresholds"] = {"mode": "absolute", "steps": [{"color": "green", "value": None}]}
    return cfg

def ts(title, targets, x, y, w=12, h=8, unit="short", stack=False, fill=10, legend_table=False):
    leg = {"displayMode": "table", "placement": "bottom", "calcs": ["lastNotNull", "max", "mean"]} if legend_table \
          else {"displayMode": "list", "placement": "bottom", "calcs": []}
    return {
        "id": nid(), "type": "timeseries", "title": title, "datasource": DS,
        "gridPos": gp(x, y, w, h), "targets": targets,
        "fieldConfig": {"defaults": {**_fields(unit=unit), "custom": {
            "drawStyle": "line", "lineInterpolation": "smooth", "lineWidth": 2,
            "fillOpacity": fill, "gradientMode": "opacity", "showPoints": "never",
            "stacking": {"mode": "normal" if stack else "none", "group": "A"},
            "axisPlacement": "auto"}}, "overrides": []},
        "options": {"tooltip": {"mode": "multi", "sort": "desc"}, "legend": leg},
    }

def stat(title, targets, x, y, w=6, h=4, unit="short", mappings=None, thresholds=None, color_mode="thresholds", graph=False, decimals=None):
    return {
        "id": nid(), "type": "stat", "title": title, "datasource": DS,
        "gridPos": gp(x, y, w, h), "targets": targets,
        "fieldConfig": {"defaults": _fields(unit=unit, decimals=decimals, mappings=mappings, thresholds=thresholds, color_mode=color_mode), "overrides": []},
        "options": {"reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "orientation": "auto", "colorMode": "value", "graphMode": "area" if graph else "none",
                    "justifyMode": "auto", "textMode": "auto"},
    }

def gauge(title, targets, x, y, w=6, h=6, unit="percent", thresholds=None, mx=100):
    return {
        "id": nid(), "type": "gauge", "title": title, "datasource": DS,
        "gridPos": gp(x, y, w, h), "targets": targets,
        "fieldConfig": {"defaults": {**_fields(unit=unit, color_mode="thresholds",
            thresholds=thresholds or [{"color":"green","value":None},{"color":"yellow","value":70},{"color":"red","value":90}]),
            "min": 0, "max": mx}, "overrides": []},
        "options": {"reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False}, "showThresholdLabels": False, "showThresholdMarkers": True},
    }

def table(title, targets, x, y, w=12, h=8, unit="short"):
    return {
        "id": nid(), "type": "table", "title": title, "datasource": DS,
        "gridPos": gp(x, y, w, h), "targets": [{**t, "instant": True, "format": "table"} for t in targets],
        "fieldConfig": {"defaults": _fields(unit=unit), "overrides": []},
        "options": {"showHeader": True}, "transformations": [{"id": "organize", "options": {}}],
    }

def row(title, y):
    return {"id": nid(), "type": "row", "title": title, "collapsed": False, "gridPos": gp(0, y, 24, 1), "panels": []}

UP_MAP = [{"type": "value", "options": {"0": {"text": "DOWN", "color": "red"}, "1": {"text": "UP", "color": "green"}}}]
UP_TH = [{"color": "red", "value": None}, {"color": "green", "value": 1}]

def var_query(name, query, label=None, multi=True, allv=True):
    return {"name": name, "type": "query", "datasource": DS, "label": label or name,
            "query": {"qryType": 1, "query": query, "refId": "var"}, "definition": query,
            "includeAll": allv, "multi": multi, "refresh": 2, "sort": 1,
            "current": {"text": "All", "value": "$__all"} if allv else {}}

def dashboard(title, uid, tags, panels, variables=None, refresh="30s"):
    return {
        "uid": uid, "title": title, "tags": tags, "schemaVersion": 39, "version": 1,
        "editable": True, "graphTooltip": 1, "time": {"from": "now-6h", "to": "now"},
        "refresh": refresh, "timezone": "browser",
        "templating": {"list": variables or []},
        "annotations": {"list": [{"builtIn": 1, "datasource": {"type": "grafana", "uid": "-- Grafana --"},
                                  "enable": True, "hide": True, "name": "Annotations & Alerts", "type": "dashboard"}]},
        "panels": panels,
    }

def write(folder, fname, dash):
    d = os.path.join(OUT, folder); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, fname), "w") as f:
        json.dump(dash, f, indent=2)
    print(f"  {folder}/{fname}")

# ============================================================ POSTGRES
def pg_panels(sel):
    """sel = instance label matcher fragment, e.g. '=~\"$instance\"' or '=\"n8n-postgres\"'"""
    f = lambda m: f'{{instance{sel}}}' if not m else f'{{instance{sel},{m}}}'
    L = "{{instance}}"
    p = []
    p.append(stat("Up", [tgt(f'pg_up{f("")}', L)], 0, 1, 4, 4, unit="none", mappings=UP_MAP, thresholds=UP_TH))
    p.append(stat("Postgres Version", [tgt(f'pg_static{f("")}', L)], 4, 1, 4, 4, unit="none"))
    p.append(stat("Backends (connections)", [tgt(f'sum by(instance)(pg_stat_database_numbackends{f("")})', L)], 8, 1, 4, 4, unit="short", graph=True, color_mode="value"))
    p.append(stat("Max Connections", [tgt(f'pg_settings_max_connections{f("")}', L)], 12, 1, 4, 4, unit="short"))
    p.append(stat("DB Size (sum)", [tgt(f'sum by(instance)(pg_database_size_bytes{f("")})', L)], 16, 1, 4, 4, unit="bytes", graph=True, color_mode="value"))
    p.append(stat("Deadlocks (sum)", [tgt(f'sum by(instance)(pg_stat_database_deadlocks{f("")})', L)], 20, 1, 4, 4, unit="short", color_mode="value", thresholds=[{"color":"green","value":None},{"color":"red","value":1}]))
    p.append(row("Connections & Throughput", 5))
    p.append(ts("Active Backends", [tgt(f'sum by(instance)(pg_stat_database_numbackends{f("")})', L)], 0, 6, 12, 8, legend_table=True))
    p.append(ts("Connection Utilisation %", [tgt(f'100 * sum by(instance)(pg_stat_database_numbackends{f("")}) / on(instance) group_left max by(instance)(pg_settings_max_connections{f("")})', L)], 12, 6, 12, 8, unit="percent"))
    p.append(ts("Commits / sec", [tgt(f'sum by(instance)(rate(pg_stat_database_xact_commit{f("")}[5m]))', L)], 0, 14, 12, 8, unit="ops"))
    p.append(ts("Rollbacks / sec", [tgt(f'sum by(instance)(rate(pg_stat_database_xact_rollback{f("")}[5m]))', L)], 12, 14, 12, 8, unit="ops"))
    p.append(row("Tuples & Cache", 22))
    p.append(ts("Tuples Fetched/Returned/sec", [
        tgt(f'sum by(instance)(rate(pg_stat_database_tup_fetched{f("")}[5m]))', "fetched {{instance}}"),
        tgt(f'sum by(instance)(rate(pg_stat_database_tup_returned{f("")}[5m]))', "returned {{instance}}", "B")], 0, 23, 12, 8, unit="ops"))
    p.append(ts("Tuples Ins/Upd/Del per sec", [
        tgt(f'sum by(instance)(rate(pg_stat_database_tup_inserted{f("")}[5m]))', "insert {{instance}}"),
        tgt(f'sum by(instance)(rate(pg_stat_database_tup_updated{f("")}[5m]))', "update {{instance}}", "B"),
        tgt(f'sum by(instance)(rate(pg_stat_database_tup_deleted{f("")}[5m]))', "delete {{instance}}", "C")], 12, 23, 12, 8, unit="ops"))
    p.append(ts("Cache Hit Ratio %", [tgt(f'100 * sum by(instance)(rate(pg_stat_database_blks_hit{f("")}[5m])) / (sum by(instance)(rate(pg_stat_database_blks_hit{f("")}[5m])) + sum by(instance)(rate(pg_stat_database_blks_read{f("")}[5m])) > 0)', L)], 0, 31, 12, 8, unit="percent"))
    p.append(ts("Disk Block Reads / sec", [tgt(f'sum by(instance)(rate(pg_stat_database_blks_read{f("")}[5m]))', L)], 12, 31, 12, 8, unit="ops"))
    p.append(row("Database Sizes & Locks", 39))
    p.append(ts("Database Size", [tgt(f'pg_database_size_bytes{f("")}', "{{instance}} / {{datname}}")], 0, 40, 12, 8, unit="bytes"))
    p.append(ts("Locks", [tgt(f'sum by(instance, mode)(pg_locks_count{f("")})', "{{instance}} {{mode}}")], 12, 40, 12, 8, unit="short"))
    p.append(ts("Temp Bytes / sec", [tgt(f'sum by(instance)(rate(pg_stat_database_temp_bytes{f("")}[5m]))', L)], 0, 48, 12, 8, unit="Bps"))
    p.append(ts("Conflicts / Rollback ratio %", [tgt(f'100 * sum by(instance)(rate(pg_stat_database_xact_rollback{f("")}[5m])) / (sum by(instance)(rate(pg_stat_database_xact_commit{f("")}[5m])) + sum by(instance)(rate(pg_stat_database_xact_rollback{f("")}[5m])) > 0)', L)], 12, 48, 12, 8, unit="percent"))
    return p

write("PostgreSQL", "pg-overview.json", dashboard(
    "PostgreSQL — Fleet Overview", "pg-fleet", ["postgres", "homelab"],
    pg_panels('=~"$instance"'),
    variables=[var_query("instance", "label_values(pg_up, instance)", "PG instance")]))

for inst, friendly in PG_INSTANCES:
    write("PostgreSQL", f"pg-{friendly}.json", dashboard(
        f"PostgreSQL — {friendly} ({inst})", f"pg-{friendly}", ["postgres", "homelab", friendly],
        pg_panels(f'="{inst}"')))

# ============================================================ REDIS
def redis_panels(sel):
    f = lambda: f'{{instance{sel}}}'
    L = "{{instance}}"
    p = []
    p.append(stat("Up", [tgt(f'redis_up{f()}', L)], 0, 1, 4, 4, unit="none", mappings=UP_MAP, thresholds=UP_TH))
    p.append(stat("Connected Clients", [tgt(f'sum by(instance)(redis_connected_clients{f()})', L)], 4, 1, 4, 4, unit="short", graph=True, color_mode="value"))
    p.append(stat("Memory Used", [tgt(f'sum by(instance)(redis_memory_used_bytes{f()})', L)], 8, 1, 4, 4, unit="bytes", graph=True, color_mode="value"))
    p.append(stat("Keys (total)", [tgt(f'sum by(instance)(redis_db_keys{f()})', L)], 12, 1, 4, 4, unit="short", color_mode="value"))
    p.append(stat("Ops / sec", [tgt(f'sum by(instance)(rate(redis_commands_processed_total{f()}[5m]))', L)], 16, 1, 4, 4, unit="ops", graph=True, color_mode="value", decimals=1))
    p.append(stat("Uptime", [tgt(f'max by(instance)(redis_uptime_in_seconds{f()})', L)], 20, 1, 4, 4, unit="s", color_mode="value"))
    p.append(row("Throughput & Clients", 5))
    p.append(ts("Commands Processed / sec", [tgt(f'sum by(instance)(rate(redis_commands_processed_total{f()}[5m]))', L)], 0, 6, 12, 8, unit="ops", legend_table=True))
    p.append(ts("Connected / Blocked Clients", [
        tgt(f'sum by(instance)(redis_connected_clients{f()})', "connected {{instance}}"),
        tgt(f'sum by(instance)(redis_blocked_clients{f()})', "blocked {{instance}}", "B")], 12, 6, 12, 8, unit="short"))
    p.append(row("Memory", 14))
    p.append(ts("Memory Used", [
        tgt(f'sum by(instance)(redis_memory_used_bytes{f()})', "used {{instance}}"),
        tgt(f'sum by(instance)(redis_memory_max_bytes{f()} > 0)', "max {{instance}}", "B")], 0, 15, 12, 8, unit="bytes"))
    p.append(ts("Memory Fragmentation Ratio", [tgt(f'avg by(instance)(redis_mem_fragmentation_ratio{f()})', L)], 12, 15, 12, 8, unit="short"))
    p.append(row("Keyspace & Hit Rate", 23))
    p.append(ts("Keyspace Hit Ratio %", [tgt(f'100 * sum by(instance)(rate(redis_keyspace_hits_total{f()}[5m])) / (sum by(instance)(rate(redis_keyspace_hits_total{f()}[5m])) + sum by(instance)(rate(redis_keyspace_misses_total{f()}[5m])) > 0)', L)], 0, 24, 12, 8, unit="percent"))
    p.append(ts("Keys per DB", [tgt(f'redis_db_keys{f()}', "{{instance}} {{db}}")], 12, 24, 12, 8, unit="short"))
    p.append(ts("Expired / Evicted Keys / sec", [
        tgt(f'sum by(instance)(rate(redis_expired_keys_total{f()}[5m]))', "expired {{instance}}"),
        tgt(f'sum by(instance)(rate(redis_evicted_keys_total{f()}[5m]))', "evicted {{instance}}", "B")], 0, 32, 12, 8, unit="ops"))
    p.append(ts("Network I/O", [
        tgt(f'sum by(instance)(rate(redis_net_input_bytes_total{f()}[5m]))', "in {{instance}}"),
        tgt(f'sum by(instance)(rate(redis_net_output_bytes_total{f()}[5m]))', "out {{instance}}", "B")], 12, 32, 12, 8, unit="Bps"))
    return p

write("Redis", "redis-overview.json", dashboard(
    "Redis — Fleet Overview", "redis-fleet", ["redis", "homelab"],
    redis_panels('=~"$instance"'),
    variables=[var_query("instance", "label_values(redis_up, instance)", "Redis instance")]))

for inst, friendly in REDIS_INSTANCES:
    write("Redis", f"redis-{friendly}.json", dashboard(
        f"Redis — {friendly} ({inst})", f"redis-{friendly}", ["redis", "homelab", friendly],
        redis_panels(f'="{inst}"')))

# ============================================================ MONGODB
m = []
m.append(stat("Up", [tgt('mongodb_up', "textbee-db")], 0, 1, 4, 4, unit="none", mappings=UP_MAP, thresholds=UP_TH))
m.append(stat("Uptime", [tgt('mongodb_instance_uptime_seconds')], 4, 1, 4, 4, unit="s", color_mode="value"))
m.append(stat("Current Connections", [tgt('mongodb_connections{state="current"}')], 8, 1, 4, 4, unit="short", graph=True, color_mode="value"))
m.append(stat("Available Connections", [tgt('mongodb_connections{state="available"}')], 12, 1, 4, 4, unit="short", color_mode="value"))
m.append(stat("Resident Memory (MB)", [tgt('mongodb_memory{type="resident"}')], 16, 1, 4, 4, unit="decmbytes", color_mode="value"))
m.append(stat("Virtual Memory (MB)", [tgt('mongodb_memory{type="virtual"}')], 20, 1, 4, 4, unit="decmbytes", color_mode="value"))
m.append(row("Operations", 5))
m.append(ts("Operations / sec by type", [tgt('rate(mongodb_op_counters_total[5m])', "{{type}}")], 0, 6, 12, 8, unit="ops", legend_table=True))
m.append(ts("Document Metrics / sec", [tgt('rate(mongodb_metrics_document_total[5m])', "{{state}}")], 12, 6, 12, 8, unit="ops"))
m.append(row("Connections & Memory", 14))
m.append(ts("Connections by state", [tgt('mongodb_connections', "{{state}}")], 0, 15, 12, 8, unit="short"))
m.append(ts("Memory (MB)", [tgt('mongodb_memory', "{{type}}")], 12, 15, 12, 8, unit="decmbytes"))
m.append(row("Network & Asserts", 23))
m.append(ts("Network Requests / sec", [tgt('rate(mongodb_network_metrics_num_requests_total[5m])', "requests")], 0, 24, 12, 8, unit="ops"))
m.append(ts("Asserts / sec", [tgt('rate(mongodb_asserts_total[5m])', "{{type}}")], 12, 24, 12, 8, unit="ops"))
m.append(ts("Page Faults / sec", [tgt('rate(mongodb_extra_info_page_faults_total[5m])', "page faults")], 0, 32, 12, 8, unit="ops"))
m.append(ts("WiredTiger Cache Bytes", [tgt('mongodb_mongod_wiredtiger_cache_bytes', "{{type}}")], 12, 32, 12, 8, unit="bytes"))
write("MongoDB", "mongodb-textbee.json", dashboard(
    "MongoDB — textbee", "mongodb-textbee", ["mongodb", "homelab", "textbee"], m))

# ============================================================ N8N
NL = "{{instance}}"
def n8n_inst(): return 'job="n8n"'
# --- Overview
o = []
o.append(stat("Instances Up", [tgt('count(up{job="n8n"} == 1)')], 0, 1, 4, 4, unit="none", color_mode="value", thresholds=UP_TH))
o.append(stat("Main Up", [tgt('up{job="n8n",instance="n8n-main"}')], 4, 1, 4, 4, unit="none", mappings=UP_MAP, thresholds=UP_TH))
o.append(stat("Worker Up", [tgt('up{job="n8n",instance="n8n-worker"}')], 8, 1, 4, 4, unit="none", mappings=UP_MAP, thresholds=UP_TH))
o.append(stat("Active Workflows", [tgt('max(n8n_active_workflow_count)')], 12, 1, 4, 4, unit="short", color_mode="value"))
o.append(stat("Leader Elected", [tgt('max(n8n_instance_role_leader)')], 16, 1, 4, 4, unit="none", mappings=[{"type":"value","options":{"0":{"text":"no"},"1":{"text":"yes","color":"green"}}}], thresholds=UP_TH))
o.append(stat("Jobs Waiting", [tgt('max(n8n_scaling_mode_queue_jobs_waiting)')], 20, 1, 4, 4, unit="short", color_mode="value", thresholds=[{"color":"green","value":None},{"color":"yellow","value":5},{"color":"red","value":25}]))
o.append(row("Cache & Activity", 5))
o.append(ts("Cache Hit Ratio % (main+worker)", [tgt('100 * sum(rate(n8n_cache_hits_total[5m])) / (sum(rate(n8n_cache_hits_total[5m])) + sum(rate(n8n_cache_misses_total[5m])) > 0)', "hit ratio")], 0, 6, 12, 8, unit="percent"))
o.append(ts("Seconds Since Last Activity", [tgt('time() - max(n8n_last_activity)', "idle seconds")], 12, 6, 12, 8, unit="s"))
o.append(row("Resource Usage (per instance)", 14))
o.append(ts("CPU Usage", [tgt('rate(n8n_process_cpu_seconds_total{job="n8n"}[5m])', NL)], 0, 15, 12, 8, unit="percentunit", legend_table=True))
o.append(ts("Resident Memory", [tgt('n8n_process_resident_memory_bytes{job="n8n"}', NL)], 12, 15, 12, 8, unit="bytes", legend_table=True))
write("n8n", "n8n-overview.json", dashboard(
    "n8n — Overview", "n8n-overview", ["n8n", "homelab"], o))

# --- Queue & Scaling
q = []
q.append(stat("Jobs Waiting", [tgt('max(n8n_scaling_mode_queue_jobs_waiting)')], 0, 1, 6, 4, unit="short", color_mode="value", graph=True, thresholds=[{"color":"green","value":None},{"color":"yellow","value":5},{"color":"red","value":25}]))
q.append(stat("Jobs Active", [tgt('max(n8n_scaling_mode_queue_jobs_active)')], 6, 1, 6, 4, unit="short", color_mode="value", graph=True))
q.append(stat("Completed (total)", [tgt('max(n8n_scaling_mode_queue_jobs_completed)')], 12, 1, 6, 4, unit="short", color_mode="value"))
q.append(stat("Failed (total)", [tgt('max(n8n_scaling_mode_queue_jobs_failed)')], 18, 1, 6, 4, unit="short", color_mode="value", thresholds=[{"color":"green","value":None},{"color":"red","value":1}]))
q.append(row("Queue Depth", 5))
q.append(ts("Jobs Waiting vs Active", [
    tgt('max(n8n_scaling_mode_queue_jobs_waiting)', "waiting"),
    tgt('max(n8n_scaling_mode_queue_jobs_active)', "active", "B")], 0, 6, 24, 8, unit="short"))
q.append(row("Throughput", 14))
q.append(ts("Jobs Completed / sec", [tgt('sum(rate(n8n_scaling_mode_queue_jobs_completed[5m]))', "completed/s")], 0, 15, 12, 8, unit="ops"))
q.append(ts("Jobs Failed / sec", [tgt('sum(rate(n8n_scaling_mode_queue_jobs_failed[5m]))', "failed/s")], 12, 15, 12, 8, unit="ops"))
write("n8n", "n8n-queue.json", dashboard(
    "n8n — Queue & Scaling Mode", "n8n-queue", ["n8n", "homelab", "queue"], q, refresh="10s"))

# --- Runtime: Process & Memory
r = []
r.append(ts("CPU Usage (user/system)", [
    tgt('rate(n8n_process_cpu_user_seconds_total{job="n8n"}[5m])', "user {{instance}}"),
    tgt('rate(n8n_process_cpu_system_seconds_total{job="n8n"}[5m])', "system {{instance}}", "B")], 0, 1, 12, 8, unit="percentunit", legend_table=True))
r.append(ts("Resident Memory", [tgt('n8n_process_resident_memory_bytes{job="n8n"}', NL)], 12, 1, 12, 8, unit="bytes", legend_table=True))
r.append(row("Node.js Heap", 9))
r.append(ts("Heap Used vs Total", [
    tgt('n8n_nodejs_heap_size_used_bytes{job="n8n"}', "used {{instance}}"),
    tgt('n8n_nodejs_heap_size_total_bytes{job="n8n"}', "total {{instance}}", "B")], 0, 10, 12, 8, unit="bytes"))
r.append(ts("Heap Space Used", [tgt('n8n_nodejs_heap_space_size_used_bytes{job="n8n"}', "{{instance}} {{space}}")], 12, 10, 12, 8, unit="bytes"))
r.append(row("Handles & GC", 18))
r.append(ts("Active Handles", [tgt('n8n_nodejs_active_handles_total{job="n8n"}', NL)], 0, 19, 12, 8, unit="short"))
r.append(ts("Active Requests", [tgt('n8n_nodejs_active_requests_total{job="n8n"}', NL)], 12, 19, 12, 8, unit="short"))
write("n8n", "n8n-runtime-process.json", dashboard(
    "n8n — Runtime: Process & Memory", "n8n-runtime-process", ["n8n", "homelab", "runtime"], r))

# --- Runtime: Event Loop & Cache
e = []
e.append(ts("Event Loop Lag (mean)", [tgt('n8n_nodejs_eventloop_lag_mean_seconds{job="n8n"}', NL)], 0, 1, 12, 8, unit="s", legend_table=True))
e.append(ts("Event Loop Lag percentiles (p50/p90/p99)", [
    tgt('n8n_nodejs_eventloop_lag_p50_seconds{job="n8n"}', "p50 {{instance}}"),
    tgt('n8n_nodejs_eventloop_lag_p90_seconds{job="n8n"}', "p90 {{instance}}", "B"),
    tgt('n8n_nodejs_eventloop_lag_p99_seconds{job="n8n"}', "p99 {{instance}}", "C")], 12, 1, 12, 8, unit="s"))
e.append(row("Cache", 9))
e.append(ts("Cache Hits / Misses per sec", [
    tgt('sum(rate(n8n_cache_hits_total[5m]))', "hits"),
    tgt('sum(rate(n8n_cache_misses_total[5m]))', "misses", "B")], 0, 10, 12, 8, unit="ops"))
e.append(ts("Cache Updates / sec", [tgt('sum(rate(n8n_cache_updates_total[5m]))', "updates")], 12, 10, 12, 8, unit="ops"))
e.append(row("Event Loop Max & StdDev", 18))
e.append(ts("Event Loop Lag (max)", [tgt('n8n_nodejs_eventloop_lag_max_seconds{job="n8n"}', NL)], 0, 19, 12, 8, unit="s"))
e.append(ts("Event Loop Lag (stddev)", [tgt('n8n_nodejs_eventloop_lag_stddev_seconds{job="n8n"}', NL)], 12, 19, 12, 8, unit="s"))
write("n8n", "n8n-runtime-eventloop.json", dashboard(
    "n8n — Runtime: Event Loop & Cache", "n8n-runtime-eventloop", ["n8n", "homelab", "runtime"], e))

print("\nDone.")
