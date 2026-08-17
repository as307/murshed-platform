# 🤖 FREEBUFF-AGENTS — Your Money Machine

One autonomous agent system that **gathers everything** (Claude work, Antigravity,
your files) into a single orchestrator that runs every task it can and stops only
at **human gates** — signin, signup, billing, sending, approval.

## What was gathered (KNOWLEDGE.md)

- **oman-lead-bot** — deployed Convex product (WhatsApp lead bot), keys pending
- **gcc-ai-agency-blueprint.md** — Murshed persona, objections, contract
- **marketing-automation-system** — 12-agent marketing company (D1+D2)
- **ai_company** — 50+ agent system (Gemini/Groq/OpenRouter keys)
- **Life/agents** — the GTM agent (products, copy, posts, packs)
- **Antigravity** — odoo19-wholesale + the GTM exec summary
- **voice-agent-app**, **ultimate-autopilot** — voice + autopilot
- **OmniRoute** — the LLM gateway (RUNNING on :20128, 14 providers, free tiers, auto-fallback) — now the agent's default LLM route

## Run it

```bash
python3 ~/freebuff-agents/run_agent.py           # run auto tasks + show gates
python3 ~/freebuff-agents/run_agent.py --status  # progress
python3 ~/freebuff-agents/run_agent.py --gates   # human to-do queue
xdg-open ~/freebuff-agents/assets/dashboard.html # money dashboard
```

Idempotent — re-run anytime, it skips completed work.

## What the agents produce (all verified)

| Task | Output | Money value |
|---|---|---|
| `llm_leads` | 8 fresh leads (Gemini) + 6 known | outreach targets |
| `gumroad_product` | 50-prompt Arabic kit PDF | $19/product |
| `fiverr_gig` | gig package + cover image | $50-200/order |
| `blueprint_assets` | Murshed system prompt, 7 objection scripts, contract, payload | the actual product |
| `product_demo` | live 3-test demo script | closes clients |
| `promo_posts` | LinkedIn EN/AR + WhatsApp + tech posts | free traffic |
| `leadbot_status` | deployment health check | knows what's broken |
| `onboard_brief` | client delivery plan | first client |
| `dashboard` | money-machine status page | see it all |

## Human gates (only you)

1. **Send outreach** — test number first (+968 7254 2766), then verified leads
2. **Gumroad signup → upload the kit at $19**
3. **Fiverr signup → publish the gig**
4. **Paste WHATSAPP_TOKEN + PHONE_NUMBER_ID** into oman-lead-bot Settings → Keys
5. **Demo calls + collect payment** (thawani / bank)

## System health (as of last run)

- oman-lead-bot site **reachable** (`ideal-boar-193.convex.site`), tests pass
- ⚠️ 3 keys not set: `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN` (gate D1)
- ✅ **OmniRoute gateway live on :20128** — LLM calls route through it (14 providers, auto-fallback). The dead OpenRouter key is no longer a blocker.

## Extending

Add a task: drop a `tasks/mytask.py` with a `run(ctx)` function returning
`{"summary": "...", "out": "..."}`, then add a step to `plan.json`.
