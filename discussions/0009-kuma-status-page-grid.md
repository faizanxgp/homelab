# How do I script Uptime Kuma into a grouped, card-grid status page?

> Posted as a Q&A discussion: https://github.com/faizanxgp/homelab/discussions/34

## Question

Uptime Kuma's status page is one long flat list of monitors. Can I script it via the API to group monitors into sections and make it look like a grid of cards instead?
## Answer

Yes — both the grouping and the styling are scriptable through `save_status_page` (e.g. via `uptime-kuma-api`). Two levers:

**1. Sections** — `publicGroupList` is independent of the monitor tree, so group however you like:
```python
api.save_status_page(
    "homelab", title="Homelab Status", theme="dark", published=True,
    publicGroupList=[
        {"name": "Marketing", "weight": 1,
         "monitorList": [{"id": 12}, {"id": 13}]},
        {"name": "AI Agents", "weight": 2,
         "monitorList": [{"id": 20}, {"id": 21}]},
    ],
    customCSS=CSS,
)
```

**2. Card grid** — `customCSS` turns the flat `.monitor-list` into a responsive grid:
```css
.monitor-list { display:grid;
  grid-template-columns:repeat(auto-fill, minmax(230px,1fr)); gap:14px; }
.monitor-list .item { border-radius:16px; padding:14px 16px;
  background:#161b2e; border:1px solid rgba(124,92,255,.18);
  transition:transform .15s; }
.monitor-list .item:hover { transform:translateY(-3px); }
```

Collect each monitor's `id` after creating it, bucket the ids into your sections, and one `save_status_page` call rebuilds the whole board — boxes, gradient header and all.
