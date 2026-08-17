const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

const STATUS_META = {
  new: 'new', sent: 'sent', replied: 'replied', interested: 'interested',
  demo_booked: 'demo_booked', lost: 'lost',
};

async function refresh() {
  try {
    const d = await window.murshed.stats();
    $('updated').textContent = 'Updated ' + new Date(d.updatedAt).toLocaleTimeString();

    // Stats
    const s = d.stats;
    $('stats').innerHTML = [
      ['Sent', s.sent, 'var(--amber)'],
      ['Replies', s.replied, 'var(--green)'],
      ['Demo Booked', s.demoBooked, '#a78bfa'],
      ['Lost', s.lost, 'var(--red)'],
      ['Incoming', s.incoming, 'var(--blue)'],
      ['Send Failed', s.sendFailed, s.sendFailed ? 'var(--red)' : 'var(--muted)'],
    ].map(([k, v, c]) =>
      `<div class="stat"><div class="v" style="color:${c}">${v}</div><div class="k">${k}</div></div>`
    ).join('');

    // Leads table
    $('leadsBody').innerHTML = d.leads.length
      ? d.leads.map(l => `<tr>
          <td>+${esc(l.number)}</td>
          <td>${esc(l.name || '—')}</td>
          <td><span class="tag ${STATUS_META[l.status] || 'new'}">${esc(l.status)}</span></td>
        </tr>`).join('')
      : '<tr><td colspan="3" class="empty">No leads yet — add numbers to leads.json</td></tr>';

    // Bookings
    $('bookings').innerHTML = d.lastBookings.length
      ? d.lastBookings.map(b =>
          `<div class="ev">🎯 <b>+${esc(b.from)}</b> booked — ${esc((b.body || '').slice(0, 80))}</div>`).join('')
      : '<div class="empty">No demo bookings yet. They appear here instantly.</div>';

    // QR
    if (d.qr) {
      $('qrBox').innerHTML = `
        <img src="${d.qr}?t=${Date.now()}">
        <div class="qr-note">Scan with <b>WhatsApp → Linked Devices</b>. Refreshes every ~20s while unlinked.</div>`;
    } else {
      $('qrBox').innerHTML = '<div class="qr-note">No QR yet — agent may already be linked. Check service log.</div>';
    }
  } catch (e) {
    $('updated').textContent = 'Error loading: ' + e.message;
  }
}

async function refreshService() {
  try {
    const on = await window.murshed.service();
    $('svcDot').className = 'dot ' + (on ? 'on' : 'off');
    $('svcText').textContent = on ? 'active' : 'inactive';
  } catch {}
}

async function refreshLog() {
  try { $('svcLog').textContent = await window.murshed.log(); } catch {}
}

$('restartBtn').onclick = async () => {
  $('restartBtn').textContent = 'Restarting…';
  await window.murshed.restart();
  setTimeout(() => { $('restartBtn').textContent = 'Restart'; refreshService(); refresh(); }, 1500);
};
$('openLeads').onclick = () => window.murshed.reveal('leads');
$('openAgent').onclick = () => window.murshed.reveal('agent');
$('logBtn').onclick = () => window.murshed.reveal('log');

refresh(); refreshService(); refreshLog();
setInterval(() => { refresh(); refreshService(); }, 10000);
setInterval(refreshLog, 15000);
