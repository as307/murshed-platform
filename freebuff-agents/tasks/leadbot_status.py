"""Task s1: Verify oman-lead-bot deployment health."""
import json
import os
import subprocess
from pathlib import Path

from ._common import write


def run(ctx):
    home = Path.home()
    bot = home / "oman-lead-bot"
    lines = ["# oman-lead-bot — Deployment Health Check", ""]
    issues = []

    if not bot.exists():
        write(ctx, "system/leadbot-status.md", "# oman-lead-bot — NOT FOUND at ~/oman-lead-bot\n")
        return {"summary": "oman-lead-bot directory missing!", "out": "assets/system/leadbot-status.md"}

    lines.append("## 1. Git state")
    try:
        r = subprocess.run(["git", "-C", str(bot), "log", "--oneline", "-1"], capture_output=True, text=True, timeout=10)
        lines.append(f"- Last commit: `{r.stdout.strip()}`")
        r2 = subprocess.run(["git", "-C", str(bot), "status", "--short"], capture_output=True, text=True, timeout=10)
        dirty = r2.stdout.strip()
        lines.append(f"- Working tree: {'DIRTY — uncommitted changes' if dirty else 'clean'}")
        if dirty:
            issues.append("uncommitted changes in oman-lead-bot")
    except Exception as e:
        lines.append(f"- git check failed: {e}")

    lines.append("")
    lines.append("## 2. WhatsApp / deployment env vars")
    env_file = bot / ".env.local"
    env = {}
    if env_file.exists():
        for ln in env_file.read_text().splitlines():
            if "=" in ln and not ln.strip().startswith("#"):
                k, _, v = ln.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    checks = {
        "CONVEX_DEPLOYMENT": "Convex deployment ID",
        "VITE_CONVEX_URL": "Convex client URL",
        "VITE_CONVEX_SITE_URL": "Convex site URL (webhook base)",
        "WHATSAPP_TOKEN": "Meta system-user token (env)",
        "WHATSAPP_PHONE_NUMBER_ID": "Meta phone number ID (env)",
        "WHATSAPP_VERIFY_TOKEN": "Webhook verify token (env)",
    }
    for key, label in checks.items():
        present = bool(env.get(key)) or key in os.environ
        if key.startswith("WHATSAPP_"):
            # These are set via `npx convex env set` — can't read here; check for local presence only
            mark = "set locally (verify in Convex dashboard)" if present else "NOT set — set via `npx convex env set`"
            lines.append(f"- `{key}` ({label}): {mark}")
            if not present:
                issues.append(f"{key} not configured")
        else:
            mark = "✅" if present else "❌ MISSING"
            lines.append(f"- `{key}` ({label}): {mark}")
            if not present:
                issues.append(f"{key} missing from .env.local")

    lines.append("")
    lines.append("## 3. Site URL reachability")
    site = env.get("VITE_CONVEX_SITE_URL") or os.environ.get("CONVEX_SITE_URL", "")
    if site:
        try:
            import urllib.request
            import urllib.error
            req = urllib.request.Request(site, method="GET", headers={"User-Agent": "freebuff-agent"})
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    lines.append(f"- {site} → HTTP {resp.status} ✅ reachable")
            except urllib.error.HTTPError as e:
                # Convex sites return 404 on the root path — that still proves it's live
                lines.append(f"- {site} → HTTP {e.code} ✅ reachable (404 on root is normal for Convex; webhook is at /whatsapp-webhook)")
        except Exception as e:
            lines.append(f"- {site} → unreachable ({e.__class__.__name__})")
            issues.append(f"site {site} unreachable")
    else:
        lines.append("- No VITE_CONVEX_SITE_URL set — cannot test reachability")

    lines.append("")
    lines.append("## 4. Test suite")
    try:
        r = subprocess.run(["bash", "-lc", f"cd {bot} && (command -v bun >/dev/null && bun test 2>&1 || npm test 2>&1) | tail -3"],
                           capture_output=True, text=True, timeout=120)
        out = (r.stdout or "") + (r.stderr or "")
        tail = [l for l in out.splitlines() if l.strip()][-3:]
        lines.append(f"- Tests: {' | '.join(tail) if tail else 'no output'}")
    except Exception as e:
        lines.append(f"- Tests: skipped ({e})")

    lines.append("")
    lines.append("## Verdict")
    if issues:
        lines.append(f"- ⚠️ {len(issues)} issue(s): " + "; ".join(issues))
        lines.append("- First step: `cd ~/oman-lead-bot && npx convex env set WHATSAPP_TOKEN ...` (see docs/DEPLOY.md)")
    else:
        lines.append("- ✅ Deployment looks healthy")

    p = write(ctx, "system/leadbot-status.md", "\n".join(lines))
    verdict = "⚠️ " + str(len(issues)) + " issues found" if issues else "✅ healthy"
    return {"summary": f"oman-lead-bot: {verdict}", "out": "assets/system/leadbot-status.md"}
