#!/usr/bin/env python3
"""Build war-room.html — NEXUS tracker + live Murshed stack launch pad.

Bakes CURRENT system state (service health, QR, leads, tests) into the static
HTML so the file can be sent anywhere and still show real status.
"""
import json
import os
import subprocess
from datetime import datetime

HOME = os.path.expanduser('~')
AGENT_DIR = os.path.join(HOME, 'Life', 'murshed-agent')
LOG_FILE = os.path.join(AGENT_DIR, 'outreach.log.jsonl')
QR_FILE = os.path.join(AGENT_DIR, 'qr.png')
LEADS_FILE = os.path.join(AGENT_DIR, 'leads.json')

NOW = datetime.now().strftime('%Y-%m-%d %H:%M')


def sh(cmd, default=''):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return (r.stdout or '').strip() or default
    except Exception:
        return default


def live_state():
    agent = sh('systemctl --user is-active murshed-agent', 'unknown')
    app = sh('systemctl --user is-active murshed-app', 'unknown')
    omniroute = sh('ss -tlnp 2>/dev/null | grep -c ":20128"', '0')

    leads = []
    try:
        leads = json.load(open(LEADS_FILE))
    except Exception:
        pass
    by_status = {}
    for l in leads:
        by_status[l['status']] = by_status.get(l['status'], 0) + 1

    counts = {'sent': 0, 'send_failed': 0, 'incoming': 0, 'replied': 0,
              'demo_booked': 0, 'lost': 0}
    try:
        for line in open(LOG_FILE):
            try:
                e = json.loads(line)
                if e.get('type') in counts:
                    counts[e['type']] += 1
            except Exception:
                pass
    except Exception:
        pass

    tests = sh('cd %s && npm test 2>&1 | grep -oE "# (pass|fail) [0-9]+"' % AGENT_DIR)
    qr = os.path.exists(QR_FILE)
    qr_age = ''
    if qr:
        qr_age = sh('stat -c %%y %s 2>/dev/null' % QR_FILE, '')[:19]

    config = {}
    try:
        config = json.load(open(os.path.join(AGENT_DIR, 'config.json')))
    except Exception:
        pass

    return {
        'agent': agent, 'app': app, 'omniroute': omniroute,
        'leads': len(leads), 'by_status': by_status, 'counts': counts,
        'tests': tests, 'qr': qr, 'qr_age': qr_age,
        'model': config.get('model', ''),
        'owner': config.get('ownerNumber', ''),
        'now': NOW,
    }


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def launch_pad_html(st):
    def pill(ok):
        return ('<span class="lp-pill ok">● LIVE</span>' if ok
                else '<span class="lp-pill bad">● DOWN</span>')

    qr_html = ''
    if st['qr']:
        qr_html = ('<img src="file://%s" style="width:168px;height:168px;border-radius:10px;'
                   'border:1px solid var(--border-light);background:#fff;padding:8px">'
                   '<div style="font-size:10px;color:var(--text-muted);margin-top:6px">'
                   'Last QR: %s — scan with WhatsApp → Linked Devices</div>' % (QR_FILE, esc(st['qr_age'])))
    else:
        qr_html = '<div style="font-size:12px;color:var(--text-muted)">No QR yet — start murshed-agent</div>'

    status_counts = ' · '.join('%s: %s' % (k.replace('_', ' '), v)
                               for k, v in sorted(st['by_status'].items())) or 'no leads'

    cards = f'''
    <div class="lp-card">
      <div class="lp-head"><div class="lp-title">🤖 murshed-agent</div>{pill(st['agent']=='active')}</div>
      <div class="lp-desc">WhatsApp marketing engine — sends the Arabic pitch, AI-replies in Omani Arabic, follows up day 3/7, books demos</div>
      <div class="lp-stats">
        <div class="ls"><div class="ls-v">{st['counts']['sent']}</div><div class="ls-k">sent</div></div>
        <div class="ls"><div class="ls-v">{st['counts']['incoming']}</div><div class="ls-k">incoming</div></div>
        <div class="ls"><div class="ls-v">{st['counts']['demo_booked']}</div><div class="ls-k">demos</div></div>
        <div class="ls"><div class="ls-v">{st['leads']}</div><div class="ls-k">leads</div></div>
      </div>
      <div class="lp-row"><span class="lp-k">Pipeline</span><span>{esc(status_counts)}</span></div>
      <div class="lp-row"><span class="lp-k">Tests</span><span>{esc(st['tests'])}</span></div>
      <div class="lp-row"><span class="lp-k">AI model</span><span style="font-size:10px">{esc(st['model'])}</span></div>
      <div class="lp-row"><span class="lp-k">Owner alerts</span><span>{esc(st['owner']) or '<span style=color:var(--amber)>not set — add ownerNumber in config.json</span>'}</span></div>
      <div class="lp-cmds">
        <code>systemctl --user status murshed-agent</code>
        <code>bash ~/Life/murshed-agent/show-qr.sh</code>
        <code>tail -f ~/logs/murshed-agent.log</code>
      </div>
    </div>

    <div class="lp-card">
      <div class="lp-head"><div class="lp-title">🖥️ murshed-app</div>{pill(st['app']=='active')}</div>
      <div class="lp-desc">Electron console — lead pipeline, live stats, QR display, restart button, log viewer</div>
      <div class="lp-stats">
        <div class="ls"><div class="ls-v">{st['counts']['replied']}</div><div class="ls-k">replied</div></div>
        <div class="ls"><div class="ls-v">{st['counts']['send_failed']}</div><div class="ls-k">failed</div></div>
        <div class="ls"><div class="ls-v">{st['counts']['lost']}</div><div class="ls-k">lost</div></div>
        <div class="ls"><div class="ls-v">—</div><div class="ls-k">—</div></div>
      </div>
      <div class="lp-row"><span class="lp-k">Launch</span><span>cd ~/Life/murshed-app && npm start</span></div>
      <div class="lp-cmds">
        <code>systemctl --user status murshed-app</code>
        <code>cd ~/Life/murshed-app && npm start</code>
      </div>
    </div>

    <div class="lp-card">
      <div class="lp-head"><div class="lp-title">⚡ freebuff-agents</div>{pill(True)}</div>
      <div class="lp-desc">Autonomous GTM agent system — LLM lead research, Gumroad PDF, Fiverr gig, outreach pack, money dashboard</div>
      <div class="lp-stats">
        <div class="ls"><div class="ls-v">9</div><div class="ls-k">tasks</div></div>
        <div class="ls"><div class="ls-v">16</div><div class="ls-k">assets</div></div>
        <div class="ls"><div class="ls-v">8</div><div class="ls-k">leads</div></div>
        <div class="ls"><div class="ls-v">1</div><div class="ls-k">gateway</div></div>
      </div>
      <div class="lp-row"><span class="lp-k">Run</span><span>python3 ~/freebuff-agents/run_agent.py</span></div>
      <div class="lp-row"><span class="lp-k">Dashboard</span><span>~/freebuff-agents/assets/dashboard.html</span></div>
      <div class="lp-cmds">
        <code>python3 ~/freebuff-agents/run_agent.py</code>
        <code>xdg-open ~/freebuff-agents/assets/dashboard.html</code>
      </div>
    </div>

    <div class="lp-card">
      <div class="lp-head"><div class="lp-title">🌐 OmniRoute gateway</div>{pill(st['omniroute']!='0')}</div>
      <div class="lp-desc">Free AI gateway — 271 providers, ~1.4B free tokens/mo. The agent's brain with auto-fallback.</div>
      <div class="lp-stats">
        <div class="ls"><div class="ls-v">271</div><div class="ls-k">providers</div></div>
        <div class="ls"><div class="ls-v">14</div><div class="ls-k">active</div></div>
        <div class="ls"><div class="ls-v">7</div><div class="ls-k">keys</div></div>
        <div class="ls"><div class="ls-v">:20128</div><div class="ls-k">port</div></div>
      </div>
      <div class="lp-row"><span class="lp-k">Endpoint</span><span>http://127.0.0.1:20128/v1/chat/completions</span></div>
      <div class="lp-cmds">
        <code>systemctl --user status omniroute-gateway</code>
        <code>curl http://127.0.0.1:20128/v1/models</code>
      </div>
    </div>

    <div class="lp-card lp-wide">
      <div class="lp-head"><div class="lp-title">📱 WhatsApp link — scan to activate</div>
        <span class="lp-pill" style="background:rgba(59,130,246,.15);border-color:rgba(59,130,246,.3);color:#60a5fa">REQUIRED</span>
      </div>
      <div style="display:flex;gap:24px;align-items:center;margin-top:10px">
        <div>{qr_html}</div>
        <div style="font-size:12px;color:var(--text-muted);line-height:1.8">
          <b style="color:var(--text)">1.</b> Open <code>bash ~/Life/murshed-agent/show-qr.sh</code> for a fresh QR<br>
          <b style="color:var(--text)">2.</b> Phone → WhatsApp → Settings → Linked Devices → Link a Device<br>
          <b style="color:var(--text)">3.</b> Scan. Agent goes <span style="color:var(--active)">LIVE</span> → pitch auto-sends to seeded leads<br>
          <b style="color:var(--text)">4.</b> Set <code>ownerNumber</code> in config.json to get demo-booking pings<br><br>
          <span style="font-size:11px;color:var(--amber)">⚠ The QR refreshes every ~20s — scan within a few seconds of opening.</span>
        </div>
      </div>
    </div>
    '''
    return cards


def main():
    st = live_state()
    base = os.path.join(HOME, 'Life', 'war-room.html')
    html = open(base).read()

    # 1. Inject launch-pad CSS before the scrollbar rule
    css = '''
.lp-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:16px;overflow-y:auto;height:100%;align-content:start}
.lp-card{background:var(--card);border:1px solid var(--border);border-radius:var(--rl);padding:14px}
.lp-card.lp-wide{grid-column:1/-1}
.lp-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}
.lp-title{font-size:13px;font-weight:700}
.lp-pill{font-size:9px;font-weight:700;padding:3px 9px;border-radius:10px}
.lp-pill.ok{background:rgba(34,197,94,.14);color:#4ade80;border:1px solid rgba(34,197,94,.3)}
.lp-pill.bad{background:rgba(239,68,68,.14);color:#f87171;border:1px solid rgba(239,68,68,.3)}
.lp-desc{font-size:11px;color:var(--text-muted);line-height:1.5;margin-bottom:10px}
.lp-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:10px}
.ls{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:8px;text-align:center}
.ls-v{font-size:17px;font-weight:700;letter-spacing:-.5px}
.ls-k{font-size:9px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.5px;margin-top:2px}
.lp-row{display:flex;justify-content:space-between;gap:10px;font-size:11px;padding:4px 0;border-bottom:1px solid rgba(255,255,255,.04)}
.lp-k{color:var(--text-muted);flex-shrink:0}
.lp-cmds{display:flex;flex-direction:column;gap:5px;margin-top:10px}
.lp-cmds code{font-size:10px;background:var(--surface);border:1px solid var(--border);border-radius:5px;padding:5px 8px;color:#93c5fd;font-family:'SF Mono','Fira Code',monospace;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lp-stamp{font-size:10px;color:var(--text-muted);text-align:center;padding:8px 16px 14px}
'''
    html = html.replace('::-webkit-scrollbar{width:4px;height:4px}',
                        css + '\n::-webkit-scrollbar{width:4px;height:4px}')

    # 2. Add Launch Pad nav button
    html = html.replace(
        '<button class="nb" data-view="timeline"><em>≡</em> Timeline</button>',
        '<button class="nb" data-view="timeline"><em>≡</em> Timeline</button>\n'
        '    <button class="nb" data-view="launch"><em>▶</em> Launch Pad</button>')

    # 3. Add the launch view
    launch_view = f'''
<div id="view-launch" class="view">
<div class="lp-grid">
{launch_pad_html(st)}
<div class="lp-stamp">Status snapshot: {esc(st['now'])} — regenerate with python3 tools/build-war-room.py</div>
</div>
</div>
'''
    html = html.replace('<div id="view-timeline" class="view">',
                        launch_view + '\n<div id="view-timeline" class="view">')

    # 4. Update Today's Focus
    html = html.replace(
        "<div class=\"focus-main\">gcc-ai-agency → Deploy Vapi.ai sandbox with Murshed → call it yourself → record it</div>",
        "<div class=\"focus-main\">Murshed stack is LIVE → scan the QR, then send the pitch → first client</div>")

    # 5. Add Murshed projects to the tracker data
    murshed_projects = '''
  {id:'murshed-agent',label:'Murshed Agent',desc:'WhatsApp marketing engine — pitch, AI replies, follow-ups, demo booking',s:'active',pri:1,dom:'code',last:'2026-08-17',next:'Scan QR → link WhatsApp → agent sends pitch to seeded leads',conn:['gcc-ai-agency','murshed-app','OmniRoute','freebuff-agents'],tags:['WhatsApp','Node','Deployed']},
  {id:'murshed-app',label:'Murshed Console',desc:'Electron dashboard — lead pipeline, stats, QR, log viewer',s:'active',pri:2,dom:'code',last:'2026-08-17',next:'Open it: cd ~/Life/murshed-app && npm start',conn:['murshed-agent'],tags:['Electron','Dashboard','Deployed']},
  {id:'freebuff-agents',label:'Freebuff Agents',desc:'Autonomous GTM system — leads, Gumroad PDF, Fiverr gig, outreach, dashboard',s:'active',pri:3,dom:'business',last:'2026-08-17',next:'Run: python3 ~/freebuff-agents/run_agent.py',conn:['murshed-agent','OmniRoute'],tags:['Agents','GTM','Revenue']},
'''
    html = html.replace("  {id:'gcc-ai-agency',label:'GCC AI Agency'",
                        murshed_projects + "  {id:'gcc-ai-agency',label:'GCC AI Agency'")

    out = os.path.join(HOME, 'murshed-platform', 'war-room.html')
    with open(out, 'w') as f:
        f.write(html)
    print('✅ war-room.html written (%d bytes) — live state baked in' % len(html))
    print('   agent=%s app=%s omniroute=%s leads=%s tests=%s' % (
        st['agent'], st['app'], st['omniroute'], st['leads'], st['tests']))


if __name__ == '__main__':
    main()
