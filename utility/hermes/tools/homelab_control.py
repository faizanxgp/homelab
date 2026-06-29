"""
title: Homelab Control
author: Hermes
description: Let Hermes inspect and operate the homelab's Docker containers and probe internal service health.
required_open_webui_version: 0.4.0
requirements: docker, requests
version: 0.1.0
"""

# HOW TO INSTALL
#   Open Hermes (https://hermes.itproxima.com) > Workspace > Tools > "+" >
#   paste this file > Save. Then enable the tool inside a chat (the wrench icon).
#   Requires /var/run/docker.sock mounted into the hermes container (it is, by
#   default in docker-compose.yml). docker control is root-equivalent — that's
#   why Hermes sits behind Cloudflare Access + its own login.

import docker
import requests
from pydantic import Field


class Tools:
    def __init__(self):
        self.client = docker.from_env()  # talks to /var/run/docker.sock

    def list_containers(self) -> str:
        """List every container with its status, image, and published ports."""
        out = []
        for c in sorted(self.client.containers.list(all=True), key=lambda x: x.name):
            image = c.image.tags[0] if c.image.tags else c.image.short_id
            out.append(f"{c.name:28} {c.status:10} {image}")
        return "NAME                         STATUS     IMAGE\n" + "\n".join(out)

    def container_logs(
        self,
        name: str = Field(..., description="Container name, e.g. 'n8n-main'"),
        lines: int = Field(60, description="How many trailing log lines to return"),
    ) -> str:
        """Return the last N log lines of a container by name."""
        try:
            c = self.client.containers.get(name)
        except docker.errors.NotFound:
            return f"No container named '{name}'."
        return c.logs(tail=lines).decode("utf-8", "replace")

    def container_stats(
        self, name: str = Field(..., description="Container name to read CPU/RAM for")
    ) -> str:
        """Return a one-shot CPU% and memory usage for a container."""
        try:
            c = self.client.containers.get(name)
        except docker.errors.NotFound:
            return f"No container named '{name}'."
        s = c.stats(stream=False)
        try:
            cpu_d = s["cpu_stats"]["cpu_usage"]["total_usage"] - s["precpu_stats"]["cpu_usage"]["total_usage"]
            sys_d = s["cpu_stats"]["system_cpu_usage"] - s["precpu_stats"]["system_cpu_usage"]
            ncpu = s["cpu_stats"].get("online_cpus", 1)
            cpu = (cpu_d / sys_d) * ncpu * 100 if sys_d > 0 else 0.0
            mem = s["memory_stats"]["usage"] / 1048576
            lim = s["memory_stats"]["limit"] / 1048576
            return f"{name}: CPU {cpu:.1f}%  MEM {mem:.0f}MiB / {lim:.0f}MiB"
        except (KeyError, ZeroDivisionError):
            return f"{name}: stats unavailable (container may be stopped)."

    def restart_container(
        self, name: str = Field(..., description="Container name to restart")
    ) -> str:
        """Restart a container by name. Use with care."""
        try:
            c = self.client.containers.get(name)
        except docker.errors.NotFound:
            return f"No container named '{name}'."
        c.restart()
        return f"Restarted '{name}'. New status: {self.client.containers.get(name).status}"

    def http_health(
        self,
        url: str = Field(..., description="Internal URL, e.g. http://n8n-main:5678/healthz"),
    ) -> str:
        """HTTP GET an internal service URL and report the status code + snippet."""
        try:
            r = requests.get(url, timeout=8)
            return f"{url} -> HTTP {r.status_code}\n{r.text[:300]}"
        except Exception as e:
            return f"{url} -> ERROR: {e}"
