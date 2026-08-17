/**
 * Murshed — WhatsApp Marketing Agent
 * ==================================
 * Turned a single-shot auto-reply bot into a full marketing engine:
 *
 *  - Multi-lead outreach from leads.json (no more argv-only targets)
 *  - Lead pipeline: new → sent → replied → interested → demo_booked → won/lost
 *  - Follow-up scheduler (day 3, day 7) for silent leads
 *  - Rate limiting (delays between sends, quiet hours)
 *  - Intent detection (interested / not interested / question) via keywords + LLM
 *  - Owner alerts on demo bookings (forward hot leads to your number)
 *  - JSONL conversation log + JSON state (survives restarts)
 *  - OmniRoute gateway with model fallbacks (fixed: openai/gpt-4o-mini had no credentials)
 *
 * Usage:
 *   node agent.js <num1,num2,...>   # add extra targets for this run
 *   node agent.js                   # just use leads.json
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const path = require('path');
const core = require('./core');

const DIR = __dirname;
const read = (f, fallback = '') => { try { return fs.readFileSync(path.join(DIR, f), 'utf8').trim() || fallback; } catch { return fallback; } };
const readJSON = (f, fallback) => { try { return JSON.parse(fs.readFileSync(path.join(DIR, f), 'utf8')); } catch { return fallback; } };

// ---- Config ----
const CONFIG = readJSON('config.json', {});
const MODEL = CONFIG.model || 'openrouter/google/gemini-2.5-flash';
const FALLBACKS = CONFIG.modelFallbacks || [];
const AI_ENDPOINT = CONFIG.aiEndpoint || 'http://127.0.0.1:20128/v1/chat/completions';
const SEND_DELAY = (CONFIG.sendDelayMs ?? 25000);
const MAX_BATCH = CONFIG.maxSendsPerBatch ?? 12;
const FOLLOW_UP_DAYS = CONFIG.followUpDays || [3, 7];
// Temporarily shortened quiet hours to allow 5 AM testing
const QUIET = CONFIG.quietHours || { start: 23, end: 4 };
const OWNER = CONFIG.ownerNumber || '';
const WEBHOOK_URL = CONFIG.webhookUrl || '';
// QR watchdog: if the browser stops producing QRs while unauthenticated,
// the session is stuck (memory pressure / CDP drop). Restart the process and
// let systemd + ExecStartPre bring it back cleanly.
const QR_GRACE_MS = CONFIG.qrGraceMs ?? 120000;   // no QR for this long = stuck
const QR_CHECK_MS = CONFIG.qrCheckMs ?? 30000;    // check interval
let lastQrAt = null;
let authenticated = false;

const LEADS_FILE = path.join(DIR, CONFIG.leadsFile || 'leads.json');
const STATE_FILE = path.join(DIR, CONFIG.stateFile || 'state.json');
const LOG_FILE = path.join(DIR, CONFIG.logFile || 'outreach.log.jsonl');

// ---- Persona + templates ----
const PERSONA = read('ai_persona.txt');
const PITCH = read('product_pitch.txt');
const FOLLOW_UPS = {
  3: read('followup_3.txt', ''),
  7: read('followup_7.txt', ''),
};
const DEMO_REPLY = read('demo_reply.txt', '');
const BOOKING_REPLY = read('booking_reply.txt', '');
const OBJECTIONS = read('objections.txt', '');

// ---- Leads DB ----
function loadLeads() {
  try { return JSON.parse(fs.readFileSync(LEADS_FILE, 'utf8')); } catch { return []; }
}
function saveLeads(leads) {
  fs.writeFileSync(LEADS_FILE, JSON.stringify(leads, null, 2));
}
function getLead(leads, num) {
  return leads.find(l => l.number === num);
}
function touchLead(leads, num, patch) {
  let l = getLead(leads, num);
  if (!l) { l = { number: num, status: 'new', createdAt: new Date().toISOString(), followUps: 0, lastMsg: null }; leads.push(l); }
  Object.assign(l, patch, { updatedAt: new Date().toISOString() });
  return l;
}

// ---- State (sent timestamps, per-run dedup) ----
function loadState() { try { return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8')); } catch { return { sent: {} }; } }
function saveState(s) { fs.writeFileSync(STATE_FILE, JSON.stringify(s, null, 2)); }

// ---- Logging ----
function logEvent(ev) {
  const line = JSON.stringify({ at: new Date().toISOString(), ...ev });
  fs.appendFileSync(LOG_FILE, line + '\n');
  console.log(line);
}
function notifyOwner(text) {
  if (OWNER) {
    client.sendMessage(`${OWNER}@c.us`, text).catch(() => {});
  }
}

// ---- Helpers ----
const isQuietHours = () => core.isQuietHours(QUIET);
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function callAI(messages) {
  const lastErr = [];
  for (const model of [MODEL, ...FALLBACKS]) {
    try {
      const res = await fetch(AI_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model, messages, max_tokens: 300 }),
      });
      if (!res.ok) { lastErr.push(`${model}: HTTP ${res.status}`); continue; }
      const data = await res.json();
      if (data.choices && data.choices[0]?.message?.content) return data.choices[0].message.content.trim();
      lastErr.push(`${model}: no content`);
    } catch (e) { lastErr.push(`${model}: ${e.message}`); }
  }
  throw new Error('All AI models failed: ' + lastErr.join('; '));
}

// ---- Intent detection (pure logic lives in core.js — tested) ----
const detectIntent = (text) => core.detectIntent(text, CONFIG);

// ---- Sending with rate limiting ----
let sendQueue = Promise.resolve();
function queueSend(fn) {
  sendQueue = sendQueue.then(async () => { await fn(); await sleep(SEND_DELAY); });
  return sendQueue;
}
async function sendToNumber(num, text, label) {
  try {
    const id = await client.getNumberId(num);
    if (!id) { logEvent({ type: 'send_failed', to: num, label, reason: 'not_registered' }); return false; }
    await client.sendMessage(id._serialized, text);
    logEvent({ type: 'sent', to: num, label });
    return true;
  } catch (e) { logEvent({ type: 'send_failed', to: num, label, reason: e.message }); return false; }
}

// ---- Main flow ----
const argvTargets = (process.argv[2] || '').split(',').map(s => s.trim()).filter(Boolean);
const state = loadState();

const client = new Client({
  authStrategy: new LocalAuth(),
  puppeteer: { headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] },
});

client.on('qr', (qr) => {
  lastQrAt = Date.now();
  console.log('\n⚠️  Scan this QR with WhatsApp → Linked Devices:\n');
  qrcode.generate(qr, { small: true });
  // Also write a scannable PNG so the QR is visible without the terminal
  try { require('qrcode').toFile(path.join(DIR, 'qr.png'), qr, { width: 300, margin: 2 }); } catch (e) { /* qrcode pkg optional */ }
  logEvent({ type: 'qr' });
});

// --- QR watchdog: self-heal if the browser stalls ---
setInterval(() => {
  if (core.qrStuck(lastQrAt, Date.now(), QR_GRACE_MS, authenticated)) {
    logEvent({ type: 'watchdog_restart', reason: `no QR for ${QR_GRACE_MS}ms while unauthenticated` });
    console.error('⚠️ Watchdog: QR stale — restarting browser process');
    // Exit hard; systemd Restart=always + ExecStartPre (stale-browser kill)
    // bring the agent back with a fresh browser.
    process.exit(1);
  }
}, QR_CHECK_MS);

client.on('ready', async () => {
  authenticated = true;
  console.log(`\n✅ Murshed is LIVE. Targets in leads.json + argv: ${[...new Set([...loadLeads().map(l=>l.number), ...argvTargets])].join(', ')}`);
  logEvent({ type: 'ready' });
  
  // Run the outreach cycle immediately on boot
  await runOutreach();

  // Run the outreach cycle every 1 hour (3600000 ms) to automatically process day 3 / day 7 follow-ups 
  // without needing to restart the script manually.
  setInterval(async () => {
    console.log('🔄 Running scheduled outreach cycle...');
    await runOutreach();
  }, 3600000);
});

// --- Outreach: send pitch to new leads, follow-ups to silent ones ---
async function runOutreach() {
  let leads = loadLeads();

  // Add argv targets as new leads
  for (const num of argvTargets) {
    if (!getLead(leads, num)) touchLead(leads, num, { status: 'new' });
  }
  saveLeads(leads);

  // Only work during non-quiet hours
  if (isQuietHours()) { console.log('🌙 Quiet hours — skipping sends'); return; }

  const now = Date.now();
  const dayMs = 86400000;
  let batch = 0;

  for (const lead of leads) {
    if (batch >= MAX_BATCH) { console.log('⏸ Batch limit reached this run'); break; }

    // 1) New lead → send pitch
    if (lead.status === 'new') {
      const ok = await sendToNumber(lead.number, PITCH, 'pitch');
      if (ok) {
        touchLead(leads, lead.number, { status: 'sent', sentAt: new Date().toISOString(), lastMsg: 'pitch' });
        saveLeads(leads);
        batch++;
      }
      continue;
    }

    // 2) Silent lead → follow-ups on day 3 / day 7
    if (lead.status === 'sent' && lead.sentAt) {
      const sentAt = new Date(lead.sentAt).getTime();
      const days = Math.floor((now - sentAt) / dayMs);
      const nextIdx = lead.followUps || 0;
      const targetDay = FOLLOW_UP_DAYS[nextIdx];
      if (targetDay && days >= targetDay) {
        const text = FOLLOW_UPS[targetDay];
        if (!text) { continue; }
        const ok = await sendToNumber(lead.number, text, `followup_day${targetDay}`);
        if (ok) {
          touchLead(leads, lead.number, { followUps: (lead.followUps || 0) + 1, lastMsg: `followup_day${targetDay}` });
          saveLeads(leads);
          batch++;
        }
      }
    }
  }
}

// --- Incoming messages ---
client.on('message_create', async (msg) => {
  if (msg.fromMe) return;
  if (!msg.body || !msg.body.trim()) return;

  const contact = await msg.getContact().catch(() => null);
  const senderNumber = (contact && contact.number) || msg.from.replace(/@.*$/, '');
  let leads = loadLeads();
  const lead = getLead(leads, senderNumber);
  const isTarget = lead || argvTargets.includes('any') || argvTargets.some(n => senderNumber.includes(n) || msg.from.includes(n));

  if (!isTarget) { logEvent({ type: 'ignored', from: senderNumber, body: msg.body.slice(0, 60) }); return; }

  logEvent({ type: 'incoming', from: senderNumber, body: msg.body.slice(0, 120) });

  // Load context (last 10 messages)
  const chat = await msg.getChat().catch(() => null);
  let history = [];
  if (chat) {
    const fetched = await chat.fetchMessages({ limit: 10 }).catch(() => []);
    for (const m of fetched) if (m.body) history.push({ role: m.fromMe ? 'assistant' : 'user', content: m.body });
    history = history.reverse();
  }

  const intent = detectIntent(msg.body);

  // Booking intent → mark demo_booked, notify owner
  if (intent === 'booking') {
    touchLead(leads, senderNumber, { status: 'demo_booked', demoAt: new Date().toISOString() });
    saveLeads(leads);
    logEvent({ type: 'demo_booked', from: senderNumber, body: msg.body.slice(0, 120) });
    if (BOOKING_REPLY) await sendToNumber(senderNumber, BOOKING_REPLY, 'booking_reply');
    notifyOwner(`🎯 DEMO BOOKED from +${senderNumber}:\n"${msg.body.slice(0, 150)}"\n→ Call them today. Script: ~/Life/agents/assets/outreach/pack.md`);
    return;
  }

  // Not interested → mark lost, stop follow-ups
  if (intent === 'not_interested') {
    touchLead(leads, senderNumber, { status: 'lost', lostAt: new Date().toISOString() });
    saveLeads(leads);
    logEvent({ type: 'lost', from: senderNumber });
    notifyOwner(`😔 Lead +${senderNumber} said not interested:\n"${msg.body.slice(0, 120)}"`);
    return;
  }

  // Interested / question / unknown → AI reply
  if (intent === 'interested') {
    touchLead(leads, senderNumber, { status: 'interested' });
    saveLeads(leads);
  }

  try {
    const aiReply = await callAI([
      { role: 'system', content: `${PERSONA}\n\nProduct pitch we sent: ${PITCH}\n\nIf they ask about price: say OMR 50/month, first month money-back. If they agree, suggest a 15-min demo call and ask for a time.` },
      ...history,
    ]);
    await sendToNumber(senderNumber, aiReply, 'ai_reply');
    logEvent({ type: 'replied', from: senderNumber, reply: aiReply.slice(0, 120) });
    if (intent === 'interested' && DEMO_REPLY) {
      // Keep the demo close handy — send once per conversation
      const l = getLead(loadLeads(), senderNumber);
      if (l && !l.demoReplySent) {
        await sleep(SEND_DELAY / 2);
        await sendToNumber(senderNumber, DEMO_REPLY, 'demo_reply');
        l.demoReplySent = true;
        saveLeads(loadLeads());
      }
    }
  } catch (e) {
    logEvent({ type: 'ai_error', from: senderNumber, error: e.message });
    await sendToNumber(senderNumber, 'أهلاً! لحظة — فريقنا يرد عليك قريبًا جدًا. 🤝', 'fallback');
  }
});

client.initialize();
