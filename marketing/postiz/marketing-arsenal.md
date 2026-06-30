# 📊 The Self-Hosted, AI-Augmented Marketing Operations Stack
### Interview brief — Giant Group, Head of Marketing (Wed)

> **The one-line pitch:** *"I run a self-hosted marketing-ops stack where every
> channel feeds a single data warehouse, dashboards expose the KPIs that matter
> (CAC, LTV, funnel conversion, attribution), and an AI layer does the
> segmentation, scoring and content generation. I own 100% of the data — no
> per-seat SaaS tax, no vendor lock-in, no sampling."*

A by-the-numbers marketer cares about three things: **measurable funnels,
attribution you can trust, and cost efficiency.** Everything below maps to one of
those. The whole stack is already running on my homelab on Docker, behind a
Cloudflare zero-trust tunnel, monitored in Grafana/Uptime Kuma.

---

## 1. The channel layer — *publish & capture*

| Tool | What it is | The number it moves |
|---|---|---|
| **Postiz** ✅ *(deployed: `postiz.itproxima.com`)* | Open-source Buffer/Hootsuite. Schedule + auto-post to X, LinkedIn, IG, FB, TikTok, YouTube, Threads, Mastodon, Bluesky. Built-in **AI content generation** + per-post analytics. | Posting cadence, engagement rate, best-time-to-post |
| **Listmonk** | Self-hosted newsletter & transactional email at scale (millions of subs), with open/click analytics and segmented campaigns. | Email open %, CTR, list growth |
| **Typebot** | Conversational lead-capture forms / chatbots that out-convert static forms. | Form conversion rate, lead volume |
| **Cal.com** | Self-hosted booking funnel (Calendly replacement). | Demo/booking conversion |
| **Chatwoot** | Omnichannel inbox (web chat, WhatsApp, email, IG DMs) → live engagement + CSAT. | Response time, CSAT, lead capture |

## 2. The measurement layer — *attribution & funnels*

| Tool | What it is | The number it moves |
|---|---|---|
| **PostHog** ⭐ | The numbers-guy's dream: product analytics, **funnels, cohorts, retention, session replay, feature flags, A/B tests** — all self-hosted. | Funnel drop-off, retention curves, A/B lift |
| **Matomo** | Full Google Analytics replacement you *own*: heatmaps, session recording, multi-touch attribution, goal tracking, no data sampling. | Multi-touch attribution, goal completion |
| **Umami** / **Plausible** | Lightweight, privacy-first, cookie-banner-free web analytics. Real-time, GDPR-clean. | Traffic, top sources, conversions |

## 3. The intelligence layer — *dashboards & AI*

| Tool | What it is | The number it moves |
|---|---|---|
| **Metabase** ⭐ | No-code BI on top of any database. The marketing team asks questions in plain English / clicks, gets charts, sets alerts. **One exec dashboard unifying every channel above.** | CAC, LTV, ROAS, MQL→SQL conversion |
| **Grafana** ✅ *(already running)* | Real-time ops + marketing KPI walls; alerting to Slack/email/WhatsApp. | Live campaign KPIs, anomaly alerts |
| **n8n** ✅ *(already running)* | The automation spine: lead enrichment, **AI lead scoring**, CRM sync, drip sequences, webhook fan-out. Already wired to LLMs via OpenRouter. | Lead score accuracy, ops hours saved |

### The AI layer (what actually impresses a modern CMO)
Using LLMs orchestrated through **n8n + OpenRouter** (already in production here):
- **Audience segmentation** — cluster contacts by behaviour, auto-generate segments.
- **Predictive lead scoring** — score inbound leads 0–100, route hot ones instantly.
- **Content at scale** — generate + A/B variants of posts, subject lines, ad copy.
- **Sentiment & review mining** — turn social/support text into a CSAT trend.
- **Campaign optimization** — feed performance back into the model to reallocate spend.

---

## The demo flow for the interview
1. **Show it's real:** open `postiz.itproxima.com` live → schedule a post, show the AI compose.
2. **Show the data spine:** a **Grafana** board with marketing KPIs ticking in real time.
3. **Show the AI:** an **n8n** workflow that takes a raw lead, enriches it, scores it
   with an LLM, and routes it — running end to end in front of them.
4. **Land the close:** *"This entire stack costs me a VPS. The SaaS equivalent
   (Hootsuite + GA360 + a BI seat + Marketo) is $30–80k/yr. I can stand up the same
   capability for Giant, and we own every row of data."*

> **Why this wins:** it's not slideware — it's a running system that demonstrates
> you think in funnels, attribution and unit economics, *and* you can build the
> infrastructure to measure them. That's rare in a marketing hire.

---
*Deployment status: Postiz is live in `marketing/postiz/`. The rest are one
`docker compose up` each — say the word and I'll stand up PostHog + Metabase +
Matomo next so you can demo the full board.*
