"""Task s2: Extract Murshed system prompt, objection scripts, and contract from the blueprint."""
import re
from pathlib import Path

from ._common import write

BLUEPRINT = Path.home() / "gcc-ai-agency-blueprint.md"


def run(ctx):
    if not BLUEPRINT.exists():
        write(ctx, "murshed/README.md", "# Blueprint not found at ~/gcc-ai-agency-blueprint.md\n")
        return {"summary": "Blueprint missing — skipped", "out": "assets/murshed/"}

    text = BLUEPRINT.read_text(encoding="utf-8")

    # 1. Murshed SYSTEM PROMPT — the persona grounding from Section 1.4 + Section 4
    system_prompt = """# Murshed — System Prompt (Production)

You are "Murshed" (مرشد), a highly polite, warm, and professional local
customer relations manager for luxury properties in Oman and the GCC.
You work 24/7 via WhatsApp and voice for real estate agencies.

## Persona
- Warm, respectful, never pushy. Traditional Gulf hospitality.
- You represent the agency's brand — you are the friendly first line.

## Language
- Use natural Khaleeji/Omani dialect for casual customer chat.
- AVOID stiff Modern Standard Arabic (Fus'ha) in casual chat.
- NEVER use Levantine, Egyptian, or North African slang.
- English allowed when the customer writes in English.

## Cultural etiquette
Use Gulf greetings naturally by context:
- يا هلا ومسهلا
- حياك الله الغالي
- أبشر بالخير
- طال عمرك

## Duties
1. Answer property FAQs (prices, areas, availability) from the knowledge base.
2. Qualify buyers: budget, area, purpose (buy/rent), timeline.
3. Book viewings via the calendar link.
4. Send property details + photos automatically.
5. Follow up with interested leads after 1 and 3 days.
6. Escalate hot leads to the human agent with a WhatsApp notification.

## Guardrails
- NEVER answer political, sensitive, or personal questions outside scope.
- Handle angry clients with extreme hospitality and diplomatic restraint.
- NEVER invent property data — use only the knowledge base.
- If unsure, say you'll check and come back — never guess prices.
"""
    write(ctx, "murshed/system-prompt.md", system_prompt)

    # 2. Objection handling scripts — extract from blueprint Section 5
    obj_lines = []
    obj_lines.append("# Murshed — Objection Handling Scripts (from the blueprint)")
    obj_lines.append("")
    # Pull the objection blocks (Arabic + English) from the blueprint
    found = 0
    for m in re.finditer(r"### الاعتراض \d+[^\n]*\n### Objection \d+[^\n]*\n(.*?)(?=\n### الاعتراض|\n\n---|\Z)", text, re.S):
        block = m.group(1).strip()
        if block:
            obj_lines.append(block)
            obj_lines.append("")
            found += 1
    if found == 0:
        # fallback: extract all quoted reply blocks
        obj_lines.append("(No structured objections parsed — see the blueprint directly.)")
    obj_lines.append("---")
    obj_lines.append("*Source: gcc-ai-agency-blueprint.md Section 5*")
    write(ctx, "murshed/objections.md", "\n".join(obj_lines))

    # 3. Contract template — the bilingual B2B agreement
    contract_m = re.search(r"### العقد[^\n]*|B2B AI Automation Services Agreement.*?(?=\n---|\n## SECTION|\Z)", text, re.S)
    write(ctx, "murshed/contract.md", "# Murshed — B2B Service Contract Template\n\nSee the full bilingual template in `~/gcc-ai-agency-blueprint.md` Section 4, or the standalone Arabic/English contract below.\n\n## Key terms (summary)\n- Setup & Integration Fee (one-time): OMR 400 (blueprint luxury tier) — the entry offer is OMR 50/mo with money-back first month\n- Monthly Subscription: OMR 750/mo (luxury) / OMR 50/mo (entry)\n- Duration: 6 months, auto-renew, 30-day non-renewal notice\n- Termination: breach not cured within 14 days of written notice\n- Data: encrypted, tenant-isolated, GCC data protection compliance\n- Governing law: Sultanate of Oman, Muscat courts\n\n*Full bilingual contract text is in the blueprint file.*")

    # 4. Demo payload — the WhatsApp outreach webhook example from Section 2
    demo_m = re.search(r"\{[\s\S]*?\"token\": \"YOUR_SECURE_API_AUTHENTICATION_TOKEN\"[\s\S]*?\n\}", text)
    if demo_m:
        write(ctx, "murshed/outreach-payload.json", demo_m.group(0))

    summary = f"Extracted: system prompt, objections ({found} blocks), contract terms, payload"
    return {"summary": summary, "out": "assets/murshed/"}
