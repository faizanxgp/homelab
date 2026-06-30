# Why does moving a Compose folder cause 'container name already in use' on up?

> Posted as a Q&A discussion: https://github.com/faizanxgp/homelab/discussions/31

## Question

I moved a Docker Compose stack to a new directory. Now `docker compose up -d` from the new path tries to create fresh containers and collides with the running ones ("container name already in use"). The data and config are fine — it's purely that Compose doesn't recognise the existing stack. Why?
## Answer

Compose identifies a stack by its **project name**, and the default project name is the **basename of the directory** you launch from. Move `monitoring/` -> `observatory/` and the project silently changes from `monitoring` to `observatory`. Compose then looks for containers labelled `com.docker.compose.project=observatory`, finds none, and tries to create them — but your fixed `container_name:`s already exist, so it errors.

Fix: pin the project name so it's independent of the directory.

```yaml
# top of docker-compose.yml
name: monitoring
```

Now from the new path Compose reconciles the existing `monitoring` project in place. (Equivalent: always pass `-p monitoring`, or set `COMPOSE_PROJECT_NAME`.) It may still recreate containers if a bind-mount source path changed, but it updates the existing stack instead of duplicating it.
