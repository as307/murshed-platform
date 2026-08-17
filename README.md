# Murshed Platform — OmanAI

The complete, ready-to-run Murshed WhatsApp marketing stack. Built by autonomous agents, deployed as systemd services, controlled from a desktop console.

## Repo layout

| Directory | What it is | Status |
|---|---|---|
| `murshed-agent/` | WhatsApp marketing engine (whatsapp-web.js + AI replies via OmniRoute) | ✅ deployed, 20/20 tests |
| `murshed-app/` | Electron console — live dashboard, QR display, service controls | ✅ deployed |
| `freebuff-agents/` | Autonomous GTM agent system (leads, Gumroad product, Fiverr gig, outreach) | ✅ runs end-to-end |
| `war-room.html` | NEXUS War Room — project tracker + launch pad (open in browser) | ✅ improved |

## Quick start

```bash
# 1. Agent
cd murshed-agent && npm install && npm test
bash deploy.sh          # installs systemd service, auto-restart

# 2. Console (desktop dashboard)
cd murshed-app && npm install
npm start               # or: bash run.sh

# 3. Autonomous GTM agents
cd freebuff-agents && python3 run_agent.py
```

## Services (systemd, user-level)

```bash
systemctl --user status murshed-agent   # WhatsApp agent (scan QR to link)
systemctl --user status murshed-app     # Electron console
tail -f ~/logs/murshed-agent.log        # agent log
bash murshed-agent/show-qr.sh           # open fresh QR to scan
```

## The AI brain

Agent replies route through **OmniRoute** (the free AI gateway: 271 providers, ~1.4B free tokens/mo) at `http://127.0.0.1:20128/v1/chat/completions`, model `openrouter/google/gemini-2.5-flash` with fallbacks. If OmniRoute is down, replies degrade gracefully instead of failing.

## Config

`murshed-agent/config.json` — model, fallbacks, rate limits, quiet hours, follow-up cadence, owner alert number (set `ownerNumber` to get a ping on demo bookings).

---
© OmanAI — Murshed. Built with Codebuff.
