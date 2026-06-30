# How do you auth mysqld_exporter 0.15+ in Compose without a .my.cnf file?

> Posted as a Q&A discussion: https://github.com/faizanxgp/homelab/discussions/30

## Question

Older `mysqld_exporter` examples set `DATA_SOURCE_NAME=user:pass@(host:3306)/`. With the current image that env var seems ignored. How do you authenticate mysqld_exporter ≥ 0.15 in Docker Compose without mounting a `.my.cnf` file?
## Answer

Right — `mysqld_exporter` **dropped `DATA_SOURCE_NAME` in 0.15**. It now wants either a `--config.my-cnf` file or the split flags/env. The file-free, env-based way that works in Compose:

```yaml
mysqld-exporter:
  image: prom/mysqld-exporter:v0.15.1
  environment:
    MYSQLD_EXPORTER_PASSWORD: "${DB_PASSWORD}"   # read automatically
  command:
    - "--mysqld.username=exporter"
    - "--mysqld.address=db-host:3306"
```

Key points:
- The password comes **only** from the `MYSQLD_EXPORTER_PASSWORD` env var (don't put it on the command line).
- Username and address go on flags.
- The user needs `PROCESS`, `REPLICATION CLIENT` and `SELECT` for full coverage; an app user gets you most server-status metrics.

No mounted config file, no secret baked into the image layer.
