"""Task a1: Research fresh leads via Gemini (with OpenRouter fallback)."""
from ._common import write
from ._llm import ask

# Known leads from the Revenue Agent dashboard (fallback + seed)
KNOWN = [
    ("96872229999", "MK Muscat", "real-estate"),
    ("96893389810", "Vista Real Estate", "real-estate"),
    ("96893443544", "Red Skyline Real Estate", "real-estate"),
    ("96891260908", "Maqar Real Estate Advisors", "real-estate"),
    ("96895132812", "Next Home Oman", "real-estate"),
    ("96895064803", "Wave Homes", "real-estate"),
]

PROMPT = """You are a market researcher for Oman. Produce a JSON array of 8 real business leads in Muscat, Oman that would benefit from an Arabic AI WhatsApp assistant.

Cover these sectors: real estate agencies (2), hotels/boutique hospitality (2), retail/e-commerce (2), clinics (2).

For each lead output exactly this JSON shape:
{"name": "Business Name", "sector": "real-estate|hospitality|retail|clinic", "city": "Muscat", "notes": "one line on why they'd buy"}

CRITICAL: Do NOT invent phone numbers. Put "unlisted" for phone unless you are confident.
Output ONLY the JSON array, no other text."""


def run(ctx):
    lines = ["# LLM-Researched Leads — Oman", ""]
    llm_leads = []
    used = ""

    try:
        print("     calling LLM (OmniRoute → Gemini)...")
        llm_leads, used = ask(PROMPT, want_json_array=True)
    except Exception as e:
        lines.append(f"- ⚠️ LLM call failed: {e}")

    if llm_leads:
        lines.append(f"**{len(llm_leads)} fresh leads via {used}:**")
        lines.append("")
        lines.append("| Business | Sector | City | Notes |")
        lines.append("|---|---|---|---|")
        for lead in llm_leads:
            name = lead.get("name", "?")
            sector = lead.get("sector", "?")
            city = lead.get("city", "?")
            notes = lead.get("notes", "").replace("|", "/")
            lines.append(f"| {name} | {sector} | {city} | {notes} |")
    else:
        lines.append("- No working LLM key — using known leads only.")

    lines.append("")
    lines.append("## Known leads (Revenue Agent dashboard)")
    lines.append("")
    lines.append("| Business | WhatsApp | Sector | Status |")
    lines.append("|---|---|---|---|")
    for num, name, sector in KNOWN:
        lines.append(f"| {name} | +{num} | {sector} | needs manual verification |")
    lines.append("")
    lines.append("## Verification")
    lines.append("LLM-generated phone numbers are unreliable. Verify each via")
    lines.append("https://wa.me/<number> before adding to the outreach bot.")
    lines.append("")

    p = write(ctx, "leads/llm-leads.md", "\n".join(lines))
    n = len(llm_leads)
    return {"summary": f"Leads: {n} new via LLM + 6 known (verify before send)", "out": "assets/leads/llm-leads.md"}
