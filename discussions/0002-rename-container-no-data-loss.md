# How do I rename a long-lived Postgres container without losing its data?

> Posted as a Q&A discussion: https://github.com/faizanxgp/homelab/discussions/27

## Question

I have a Postgres container that's been running for weeks with real data in a bind-mounted volume. I want to rename it (e.g. `postgres-automation` -> `automation-postgres`) for naming consistency. Does renaming the container risk the data, and what exactly has to change so dependent services don't break?
## Answer

Renaming is safe for the **data** as long as the **volume** stays put — the data lives in the bind mount (`./volumes/postgres:/var/lib/postgresql/data`), not in the container. What you're really changing is `container_name:` plus the DNS name other services use to reach it.

The trap is **referential**: a container name is also its network hostname. Every place that resolves the old name must change *together*, or the next `up` connects to nothing:

1. `container_name:` and the service's own `depends_on:` / exporter `DATA_SOURCE_NAME` host.
2. Anything that dials it by hostname: other compose files, an exporter, a tunnel ingress (`tcp://postgres-automation:5432`), Prometheus `instance` labels, Grafana dashboard `instance="..."` filters, and uptime monitors.

Do it as one atomic change (a single grep-driven rename across the repo), keep the volume path identical, then `docker compose up -d` to recreate. The container is replaced; the volume — and your data — is reattached untouched. There's a few seconds of downtime during the recreate, nothing more.
