"""Task b2: Generate Fiverr gig cover image (HTML → PNG via headless Chromium)."""
import subprocess
from pathlib import Path

from ._common import out_path

HTML = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><style>
  body { margin:0; width:1280px; height:720px; font-family:'Noto Naskh Arabic','DejaVu Sans',sans-serif;
         background:linear-gradient(135deg,#0f172a 0%,#134e4a 60%,#0f766e 100%); color:#fff; display:flex;
         align-items:center; justify-content:center; text-align:center; }
  .inner { max-width:1000px; }
  .badge { display:inline-block; background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.3);
           border-radius:30px; padding:10px 26px; font-size:26px; letter-spacing:2px; margin-bottom:30px; }
  h1 { font-size:64px; margin:0 0 16px; line-height:1.2; }
  h2 { font-size:34px; font-weight:400; opacity:.92; margin:0 0 10px; }
  .sub { font-size:24px; opacity:.75; }
  .pill { display:inline-block; margin-top:36px; background:#22c55e; color:#052e16; font-weight:700;
          font-size:26px; padding:14px 40px; border-radius:40px; }
</style></head>
<body>
  <div class="inner">
    <div class="badge">🇴🇲 OMANAI</div>
    <h1>مساعد ذكاء اصطناعي لواتساب بالعربي</h1>
    <h2>Arabic AI WhatsApp Chatbot for Your Business</h2>
    <div class="sub">24/7 replies • Lead capture • Khaleeji Arabic + English</div>
    <div class="pill">7-DAY DELIVERY — ORDER NOW</div>
  </div>
</body>
</html>"""


def run(ctx):
    html_path = out_path(ctx, "fiverr/gig-cover.html")
    png_path = out_path(ctx, "fiverr/gig-cover.png")
    html_path.write_text(HTML, encoding="utf-8")

    import shutil
    browser = None
    for c in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        if shutil.which(c):
            browser = c
            break
    if not browser:
        return {"summary": "Cover HTML generated (no chromium for PNG)", "out": "assets/fiverr/gig-cover.html"}

    cmd = [browser, "--headless", "--disable-gpu", "--no-sandbox",
           "--window-size=1280,720", f"--screenshot={png_path}", f"file://{html_path}"]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        ok = png_path.exists() and png_path.stat().st_size > 1000
    except Exception:
        ok = False
    if not ok:
        return {"summary": "Cover HTML generated (PNG render failed)", "out": "assets/fiverr/gig-cover.html"}
    return {"summary": "Gig cover image rendered (1280x720 PNG)", "out": "assets/fiverr/gig-cover.png"}
