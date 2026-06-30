# Why does adding one Grafana dashboard renumber panel IDs in all the others?

> Posted as a Q&A discussion: https://github.com/faizanxgp/homelab/discussions/28

## Question

I generate my Grafana dashboards from a Python script. I added ONE new dashboard, regenerated, and `git diff` shows changes in a dozen *unrelated* dashboards — their panel `id` fields all shifted by some offset. The panels are otherwise identical. Why, and should I worry?
## Answer

Almost certainly your generator hands out panel ids from a **single global counter** (`_id += 1; return _id`) that increments as panels are emitted, in order, across *all* dashboards in one run. Insert a new dashboard (or extra panels) early in the sequence and every panel generated *after* it gets bumped by the same offset — hence the cascade of `id`-only diffs downstream.

Should you worry? No — panel ids only need to be unique **within a dashboard**; Grafana doesn't care about their absolute values. The diffs are pure renumbering noise.

Two ways to handle it:
- **Embrace it** (what I do): the generator is the source of truth, so commit the whole regenerated set. The invariant "running the generator produces exactly the committed files" is worth more than a tidy diff.
- **Avoid it**: reset the counter per-dashboard (seed `_id = 0` at the start of each dashboard) so ids are stable and local. Then a new dashboard only touches its own file.
