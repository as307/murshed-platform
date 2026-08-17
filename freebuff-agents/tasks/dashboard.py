"""Generate dashboard.html — the money-machine status view from plan + state."""
import json
import time
from pathlib import Path

from ._common import write

ICONS = {"auto": "🤖", "gate": "👤"}
KINDS = {
    "approve+send": "send", "reply": "reply", "call": "call", "billing": "billing",
    "signup": "signup", "publish": "publish", "setup": "setup",
}


def run(ctx):
    root = ctx["root"]
    plan = json.loads((root / "plan.json").read_text())
    state = ctx["state"]

    tracks_html = []
    total_done = total_all = 0
    for track in plan["tracks"]:
        steps = track["steps"]
        done = sum(1 for s in steps if state["done"].get(s["id"]))
        total_done += done
        total_all += len(steps)
        pct = round(done / len(steps) * 100) if steps else 0

        rows = ""
        for s in steps:
            d = state["done"].get(s["id"])
            if d:
                cls = "done"
                badge = "✓ done"
                extra = f'<div class="step-out">{d.get("summary", "")}</div>'
            elif s["type"] == "gate":
                cls = "gate"
                badge = f'⛔ {s.get("kind", "human")}'
                extra = f'<div class="step-out">→ {s.get("instructions", "")[:120]}</div>'
            else:
                cls = "pending"
                badge = "🤖 auto"
                extra = ""
            rows += f"""
            <div class="step {cls}">
              <div class="step-top"><span class="step-id">{s['id']}</span><span class="step-title">{s['title']}</span><span class="step-badge">{badge}</span></div>
              {extra}
            </div>"""

        tracks_html.append(f"""
        <div class="track">
          <div class="track-hdr">
            <span class="track-name">{track['name']}</span>
            <span class="track-pct">{done}/{len(steps)} · {pct}%</span>
          </div>
          <div class="track-bar"><div class="track-fill" style="width:{pct}%"></div></div>
          {rows}
        </div>""")

    overall = round(total_done / total_all * 100) if total_all else 0
    now = time.strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FREEBUFF-AGENTS — Money Machine</title>
<style>
  :root {{ --bg:#070b12; --card:#0d1117; --card2:#141b24; --border:#1e2d3d;
    --text:#e2e8f4; --muted:#637080; --green:#22c55e; --amber:#f59e0b; --red:#ef4444; --blue:#3b82f6; }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:'SF Pro Text','Segoe UI',system-ui,sans-serif; background:var(--bg); color:var(--text); padding:24px; }}
  .hdr {{ display:flex; align-items:center; gap:14px; margin-bottom:20px; }}
  .hdr h1 {{ font-size:20px; font-weight:800; letter-spacing:-.5px; }}
  .hdr .sub {{ font-size:11px; color:var(--muted); }}
  .overall {{ margin-left:auto; text-align:right; }}
  .overall .pct {{ font-size:26px; font-weight:800; color:var(--green); }}
  .overall .lbl {{ font-size:10px; color:var(--muted); text-transform:uppercase; letter-spacing:.6px; }}
  .mission {{ background:linear-gradient(135deg,rgba(59,130,246,.1),rgba(34,197,94,.08));
    border:1px solid rgba(59,130,246,.25); border-radius:12px; padding:14px 18px; margin-bottom:20px; font-size:13px; line-height:1.5; }}
  .track {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:14px; margin-bottom:14px; }}
  .track-hdr {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }}
  .track-name {{ font-size:13px; font-weight:700; }}
  .track-pct {{ font-size:11px; color:var(--muted); }}
  .track-bar {{ height:4px; background:var(--border); border-radius:2px; overflow:hidden; margin-bottom:10px; }}
  .track-fill {{ height:100%; background:var(--blue); border-radius:2px; transition:width .4s; }}
  .step {{ border:1px solid var(--border); border-radius:8px; padding:9px 12px; margin-bottom:6px; background:var(--card2); }}
  .step.done {{ opacity:.55; }}
  .step.gate {{ border-color:rgba(245,158,11,.4); }}
  .step-top {{ display:flex; align-items:center; gap:10px; }}
  .step-id {{ font-size:10px; font-weight:700; color:var(--muted); background:var(--bg); border:1px solid var(--border); border-radius:4px; padding:2px 6px; }}
  .step-title {{ font-size:12px; font-weight:600; flex:1; }}
  .step-badge {{ font-size:9px; padding:2px 8px; border-radius:10px; background:var(--bg); border:1px solid var(--border); color:var(--muted); flex-shrink:0; }}
  .step.done .step-badge {{ color:var(--green); border-color:var(--green); }}
  .step.gate .step-badge {{ color:var(--amber); border-color:var(--amber); }}
  .step-out {{ font-size:10px; color:var(--muted); margin-top:5px; }}
  .foot {{ text-align:center; color:var(--muted); font-size:10px; margin-top:16px; }}
</style>
</head>
<body>
  <div class="hdr">
    <div>
      <h1>🤖 FREEBUFF-AGENTS</h1>
      <div class="sub">Master Money Machine · last run {now}</div>
    </div>
    <div class="overall"><div class="pct">{overall}%</div><div class="lbl">{total_done}/{total_all} steps</div></div>
  </div>
  <div class="mission">{plan['mission']}</div>
  {''.join(tracks_html)}
  <div class="foot">Re-run: python3 ~/freebuff-agents/run_agent.py — idempotent, resumes where it stopped</div>
</body>
</html>"""

    p = write(ctx, "dashboard.html", html)
    return {"summary": f"Dashboard generated ({overall}% complete)", "out": "assets/dashboard.html"}
