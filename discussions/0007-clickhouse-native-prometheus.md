# Can ClickHouse expose Prometheus metrics without a separate exporter?

> Posted as a Q&A discussion: https://github.com/faizanxgp/homelab/discussions/32

## Question

I run ClickHouse as the events store for a self-hosted analytics app. I'd like Prometheus to scrape it, but I don't want to run a separate clickhouse-exporter sidecar. Does ClickHouse expose Prometheus metrics natively?
## Answer

Yes — ClickHouse has a **built-in Prometheus endpoint**; no sidecar needed. Drop a config file into `config.d/`:

```xml
<!-- /etc/clickhouse-server/config.d/prometheus.xml -->
<clickhouse>
    <prometheus>
        <endpoint>/metrics</endpoint>
        <port>9363</port>
        <metrics>true</metrics>
        <events>true</events>
        <asynchronous_metrics>true</asynchronous_metrics>
        <status_info>true</status_info>
    </prometheus>
</clickhouse>
```

Mount it (`./clickhouse/config.d:/etc/clickhouse-server/config.d:ro`), put the container on your monitoring network, and scrape `clickhouse-host:9363`. You get `ClickHouseMetrics_*` (gauges like active `Query`, `MemoryTracking`), `ClickHouseProfileEvents_*` (counters — `Query`, `InsertedRows`, `SelectedRows`) and `ClickHouseAsyncMetrics_*` (`Uptime`, `LoadAverage1`). While you're in there, set `<logger><level>warning</level></logger>` and drop `query_log` to keep the events DB quiet.
