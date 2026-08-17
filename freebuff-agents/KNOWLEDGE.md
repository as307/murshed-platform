# 🧠 FREEBUFF-AGENTS — Consolidated Knowledge Base
*Gathered from: Claude sessions, Antigravity work, and Yaman's files — August 17, 2026*

---

## 1. THE PRODUCT: Murshed (OmanAI)

**What it is:** An Arabic (Khaleeji/Omani dialect) AI WhatsApp assistant for real estate agencies in Oman.
Handles client inquiries, qualifies leads, books viewings, follows up 24/7.

### The codebase — `~/oman-lead-bot/`
- **Status:** Production-ready, committed on `main` (`b75e9ac`), all 31 tests pass
- **Stack:** Convex (backend + DB), React/Vite frontend, Meta WhatsApp Business Cloud API (direct — NO Twilio)
- **Env vars configured:** `.env.local` has `CONVEX_DEPLOYMENT`, `VITE_CONVEX_URL`, `VITE_CONVEX_SITE_URL`, `VERCEL_OIDC_TOKEN`
- **WhatsApp keys needed:** `WHATSAPP_TOKEN` + `WHATSAPP_PHONE_NUMBER_ID` (Meta system-user token + phone number ID) + `WHATSAPP_VERIFY_TOKEN` — user has registered the number in Meta ✅
- **Webhook:** `WHATSAPP_VERIFY_TOKEN` + subscribe to `messages` at `<site-url>/whatsapp-webhook`
- **Docs:** `README.md` has full Oman setup walkthrough; `docs/DEPLOY.md` has the deploy runbook

### The Murshed persona (from `gcc-ai-agency-blueprint.md`)
- Persona: "Murshed" — polite, warm, professional local customer relations manager for luxury properties
- Dialect: natural Khaleeji/Omani, NOT stiff Fus'ha; no Levantine/Egyptian slang
- Etiquette: يا هلا ومسهلا، حياك الله الغالي، أبشر بالخير، طال عمرك
- Guardrails: no politics/sensitive topics; handle angry clients with hospitality
- **7 objection-handling scripts** exist in the blueprint (AR+EN) — data-security, dialect doubt, "we have staff", "no time", "clients prefer humans", "no proof", "contract lock-in"

### Business model (blueprint contract)
- Setup fee: OMR 400 one-time (blueprint) / OMR 50-100/mo (Revenue Agent plan)
- Monthly: OMR 750/mo (blueprint luxury) / OMR 50/mo (Revenue Agent entry)
- Contract: 6 months, auto-renew, 14-day cure period, Omani law/Muscat courts

---

## 2. THE MONEY PLAN (from Antigravity exec summary + revenue-agent.html)

**Mission:** First paying Murshed client (OMR 50/mo = $130) within 7 days. $30 budget.

### Track A — Direct Sales (Murshed → Real Estate)
- **6 leads** (AI-scraped): MK Muscat +968 7222 9999, Vista +968 9338 9810, Red Skyline +968 9344 3544, Maqar +968 9126 0908, Next Home +968 9513 2812, Wave Homes +968 9506 4803
- **TEST number (user-confirmed):** Ahmad Basha +968 7254 2766
- Outreach script (`~/Life/murshed_bot.py`) opens WhatsApp Web pre-filled; human clicks Send
- Demo reply / call script / follow-ups / objection replies → in `~/Life/agents/assets/outreach/pack.md`

### Track B — Fiverr (AI Services Gig)
- Gig: "I will build an Arabic AI chatbot for your WhatsApp Business" — $50/$100/$200
- Full package → `~/Life/agents/assets/fiverr/gig-package.md` + cover image PNG

### Track C — Digital Product (Gumroad)
- Arabic AI Business Prompt Kit — 50 prompts, 8 categories, bilingual, $19
- Product built → `~/Life/agents/assets/gumroad/arabic-ai-prompt-kit.pdf` (8 pages) + HTML
- Listing copy → `~/Life/agents/assets/gumroad/product-copy.md`

### Payment rails
- thawani.om (free for CR holders) — Omani payment links
- Bank transfer (simplest for first client)
- Gumroad → Payoneer/bank for international

---

## 3. THE AGENT INFRASTRUCTURE (what Claude/Antigravity built)

### `~/marketing-automation-system/` (Aug 9) — 12-agent marketing company
- D1 Prospecting: Lead Researcher (200+/day), Email Verifier
- D2 Content: Strategist, Copywriter (5 variants), LinkedIn Generator
- D3-D6 planned: Outreach, Sales, Analytics, Finance
- SQL schema: 8 tables + 4 views; autonomy tiers 1/2/3
- **Status:** D1+D2 implemented; rest is scaffolding

### `~/ai_company/` (Apex) — 50+ agent self-building company
- 5 revenue streams, 11 pods, RAG knowledge base, dashboard, self-improvement
- **Env keys available:** `OPENROUTER_API_KEY`, `GROQ_API_KEY`, `GOOGLE_API_KEY`, `TWILIO_*` in `~/ai_company/.env`
- Docs: AUTOPILOT_SERVICE.md, PERSONAS.md, PROJECT_PLAN.md, ENHANCEMENT_REPORT.md

### `~/voice-agent-app/` (AURA) — voice agent (port 3000)
- Node.js + Express voice agent app; built Aug 15-16, not currently running

### `~/ultimate-autopilot/` — autopilot scripts + systemd service
- `autopilot.sh`, `run.sh`, `ultimate-autopilot.service`

### `~/OmniRoute/` — THE FREE AI GATEWAY ⭐ (the LLM router)
- **What:** Aggregates 271 providers / 90+ free tiers / ~1.4B free tokens/mo behind one endpoint with auto-fallback + token compression
- **Status:** RUNNING NOW — v16.2.12 serving on `localhost:20128` (`omniroute serve --no-open --port 20128`)
- **Configured providers (14 active):** gemini, openrouter, freeaiapikey, cerebras, huggingchat, claude, antigravity, devin, github, opencode, trae, mimocode, gitlawb, devin-cli
- **API keys (7 enabled):** cerebras, devin, freeaiapikey, gemini, gitlawb, huggingchat, openrouter
- **Endpoint:** `http://localhost:20128/v1/chat/completions` (OpenAI-compatible, no auth needed locally)
- **Why it matters for freebuff-agents:** the direct OpenRouter key in ai_company hit its monthly budget — OmniRoute is the working replacement (routes to Gemini/cerebras/free tiers with auto-fallback)
- **Model slugs that work:** `openrouter/google/gemini-2.5-flash`, `openrouter/google/gemini-2.0-flash`
- **CLI:** `omniroute providers list`, `omniroute keys list`, `omniroute test <id>`

### Antigravity projects (`~/Documents/antigravity/`)
- `elegant-shannon/odoo19-wholesale/` — Odoo 19 wholesale ERP + Tally connector (client work)
- `epic-lavoisier/`, `amazing-bell/` — empty scaffolds
- Exec summary (GTM strategy) is the source of the money plan

### Life OS (`~/Life/`)
- `revenue-agent.html` — the money dashboard (tracks A/B/C + budget + leads)
- `war-room.html`, `weekly-review.html`, `briefing.sh` — daily ops
- `murshed_bot.py` — outreach bot (now has test number)
- `agents/` — the GTM agent system (plan.json, run_agent.py, 8 auto tasks)

---

## 4. KEY ASSETS INVENTORY (ready to use NOW)

| Asset | Path | Money value |
|---|---|---|
| Prompt kit PDF (50 prompts) | `~/Life/agents/assets/gumroad/arabic-ai-prompt-kit.pdf` | $19 × sales |
| Fiverr gig package + cover | `~/Life/agents/assets/fiverr/` | $50-200/order |
| Outreach pack (all scripts) | `~/Life/agents/assets/outreach/pack.md` | OMR 50/mo client |
| Client onboarding brief | `~/Life/agents/assets/outreach/client-brief.md` | delivery plan |
| Lead verification report | `~/Life/agents/assets/leads/verified.md` | outreach quality |
| LinkedIn/WhatsApp posts | `~/Life/agents/assets/posts/` | free traffic |
| oman-lead-bot (product) | `~/oman-lead-bot/` | OMR 50-750/mo/client |
| Murshed blueprint | `~/gcc-ai-agency-blueprint.md` | system prompts + contract |
| Marketing automation | `~/marketing-automation-system/` | scalable lead gen |

---

## 5. THE ONE-PAGE STRATEGY

```
FASTEST CASH (this week):
  1. Send outreach to test number + verified leads (Track A) → demo call → OMR 50/mo
  2. Publish Gumroad product ($19 kit — already built) → passive international sales
  3. Publish Fiverr gig (already written) → GCC AI services demand

THE PRODUCT (post-first-payment):
  4. Onboard client with oman-lead-bot (already deployed, 90% done)
  5. Use marketing-automation-system for scalable lead gen
  6. Voice agent (AURA) as upsell

SCALING:
  7. ai_company autopilot for self-improvement
  8. odoo19-wholesale as separate client track
```

---

## 6. GAPS / NEXT ACTIONS (things the agents will do)

1. **Verify oman-lead-bot deployment** is actually live (env vars, site URL, webhook) — leadbot_status task
2. **Extract blueprint assets** (Murshed system prompt, objection scripts, contract) into ready files — blueprint_assets task
3. **Find fresh leads** beyond the 6 (LLM research via OmniRoute gateway) — llm_leads task
4. **Generate all sales collateral** from the blueprint into the agent's asset folder
5. **Run the money tracks** with human gates (send, signup, billing)
6. **DONE:** OmniRoute wired in as the LLM routing layer (`tasks/_llm.py` — OmniRoute first, direct Gemini fallback)
