/**
 * Murshed — core logic (pure, testable)
 * Everything here is deterministic given inputs; no WhatsApp/network side effects.
 */
const DAY_MS = 86400000;

/** Merge argv targets + leads.json into a de-duplicated list of {number, source}. */
function mergeTargets(leads, argvTargets) {
  const out = new Map();
  for (const l of leads) out.set(l.number, l);
  for (const num of argvTargets) {
    if (!out.has(num)) out.set(num, { number: num, status: 'new' });
  }
  return [...out.values()];
}

/** Quiet hours check. Supports overnight windows (start > end). */
function isQuietHours(quiet, now = new Date()) {
  if (!quiet) return false;
  const h = now.getHours();
  const { start, end } = quiet;
  if (start <= end) return h >= start && h < end;
  return h >= start || h < end; // overnight window
}

/**
 * Determine if a lead is due for a follow-up.
 * Returns the day number to send (e.g. 3 or 7) or null.
 */
function dueFollowUp(lead, followUpDays, now = Date.now()) {
  if (!lead || lead.status !== 'sent' || !lead.sentAt) return null;
  if (!Array.isArray(followUpDays) || followUpDays.length === 0) return null;
  const sentAt = new Date(lead.sentAt).getTime();
  const days = Math.floor((now - sentAt) / DAY_MS);
  const idx = lead.followUps || 0;
  const targetDay = followUpDays[idx];
  if (targetDay == null) return null;
  return days >= targetDay ? targetDay : null;
}

/** Intent classification from an incoming message body. */
function detectIntent(text, config = {}) {
  const t = String(text || '').toLowerCase();
  const neg = (config.markNotInterestedKeywords || []).map(k => k.toLowerCase());
  const pos = (config.markInterestedKeywords || []).map(k => k.toLowerCase());

  // Booking / demo words — highest priority
  if (/(ديمو|demo|معاينة|viewing|موعد|booking|appointment|نتصل|نكلم|call me|اتصل|مكالمة)/i.test(t)) return 'booking';
  // Price questions
  if (/(كم |سعر|اسعار|price|cost|how much|بكم)/i.test(t)) return 'question';
  // Clear negatives first (avoid "لا بأس" / "ما شاء الله" false positives)
  if (neg.some(k => k && t.includes(k))) return 'not_interested';
  if (pos.some(k => k && t.includes(k))) return 'interested';
  return 'unknown';
}

/** Next status in the pipeline given an event. */
function nextStatus(current, intent) {
  const map = {
    'new': { default: 'sent', booking: 'demo_booked', not_interested: 'lost', interested: 'interested' },
    'sent': { default: 'sent', booking: 'demo_booked', not_interested: 'lost', interested: 'interested' },
    'interested': { default: 'interested', booking: 'demo_booked', not_interested: 'lost' },
  };
  const row = map[current] || { default: current };
  return row[intent] || row.default || current;
}

/** Should we attempt sends right now? */
function canSend(quiet, now = new Date()) {
  return !isQuietHours(quiet, now);
}

/** Rate limiting: how many sends are allowed this batch. */
function batchCap(count, max) {
  return Math.min(count, max);
}

module.exports = {
  DAY_MS,
  mergeTargets,
  isQuietHours,
  dueFollowUp,
  detectIntent,
  nextStatus,
  canSend,
  batchCap,
};
