const { test } = require('node:test');
const assert = require('node:assert');
const {
  DAY_MS,
  mergeTargets,
  isQuietHours,
  dueFollowUp,
  detectIntent,
  nextStatus,
  canSend,
  batchCap,
} = require('../core');

// ---------- mergeTargets ----------
test('mergeTargets dedupes argv + leads', () => {
  const leads = [
    { number: '96872542766', status: 'sent' },
    { number: '96897130999', status: 'new' },
  ];
  const merged = mergeTargets(leads, ['96897130999', '96812345678']);
  assert.strictEqual(merged.length, 3);
  assert.ok(merged.find(l => l.number === '96897130999' && l.status === 'new')); // existing lead wins
  assert.ok(merged.find(l => l.number === '96812345678' && l.status === 'new')); // argv added
});

test('mergeTargets empty argv keeps leads only', () => {
  const merged = mergeTargets([{ number: '1' }], []);
  assert.strictEqual(merged.length, 1);
});

// ---------- isQuietHours ----------
test('isQuietHours daytime = not quiet', () => {
  const q = { start: 22, end: 9 };
  assert.strictEqual(isQuietHours(q, new Date('2026-08-17T14:00:00')), false);
});

test('isQuietHours night = quiet', () => {
  const q = { start: 22, end: 9 };
  assert.strictEqual(isQuietHours(q, new Date('2026-08-17T23:30:00')), true);
  assert.strictEqual(isQuietHours(q, new Date('2026-08-17T03:00:00')), true);
});

test('isQuietHours boundary: start hour inclusive, end exclusive', () => {
  const q = { start: 22, end: 9 };
  assert.strictEqual(isQuietHours(q, new Date('2026-08-17T22:00:00')), true);
  assert.strictEqual(isQuietHours(q, new Date('2026-08-17T09:00:00')), false);
});

test('isQuietHours same-day window (9-18)', () => {
  const q = { start: 9, end: 18 };
  assert.strictEqual(isQuietHours(q, new Date('2026-08-17T12:00:00')), true);
  assert.strictEqual(isQuietHours(q, new Date('2026-08-17T19:00:00')), false);
});

test('isQuietHours null config = never quiet', () => {
  assert.strictEqual(isQuietHours(null), false);
});

// ---------- dueFollowUp ----------
function lead(sentDaysAgo, followUps = 0, status = 'sent') {
  return {
    status,
    sentAt: new Date(Date.now() - sentDaysAgo * DAY_MS).toISOString(),
    followUps,
  };
}

test('dueFollowUp: day 3 due after 3+ days, not before', () => {
  assert.strictEqual(dueFollowUp(lead(2.5), [3, 7]), null);
  assert.strictEqual(dueFollowUp(lead(3), [3, 7]), 3);
  assert.strictEqual(dueFollowUp(lead(5), [3, 7]), 3);
});

test('dueFollowUp: day 7 after first follow-up', () => {
  assert.strictEqual(dueFollowUp(lead(5, 1), [3, 7]), null);
  assert.strictEqual(dueFollowUp(lead(7, 1), [3, 7]), 7);
});

test('dueFollowUp: exhausted follow-ups return null', () => {
  assert.strictEqual(dueFollowUp(lead(30, 2), [3, 7]), null);
});

test('dueFollowUp: non-sent or missing sentAt returns null', () => {
  assert.strictEqual(dueFollowUp(lead(5, 0, 'interested'), [3, 7]), null);
  assert.strictEqual(dueFollowUp({ status: 'sent' }, [3, 7]), null);
});

// ---------- detectIntent ----------
const KW = {
  markNotInterestedKeywords: ['لا', 'شكرا', 'مش مهتم', 'no', 'not interested'],
  markInterestedKeywords: ['نعم', 'ممتاز', 'حاب', 'ابي', 'ok', 'yes', 'تمام', 'كم', 'سعر', 'بكم'],
};

test('detectIntent: booking words win', () => {
  assert.strictEqual(detectIntent('ابي حجز موعد معاينة', KW), 'booking');
  assert.strictEqual(detectIntent('نعم نبي نكلمكم', KW), 'booking');
  assert.strictEqual(detectIntent('can we book a demo', KW), 'booking');
});

test('detectIntent: price questions', () => {
  assert.strictEqual(detectIntent('كم السعر؟', KW), 'question');
  assert.strictEqual(detectIntent('بكم الشهر', KW), 'question');
});

test('detectIntent: not interested beats interested for clear negatives', () => {
  assert.strictEqual(detectIntent('لا شكرا مش مهتم', KW), 'not_interested');
  assert.strictEqual(detectIntent('شكرا ما نبي', KW), 'not_interested');
});

test('detectIntent: positives', () => {
  assert.strictEqual(detectIntent('نعم حاب أعرف أكثر', KW), 'interested');
  assert.strictEqual(detectIntent('تمام يهمني', KW), 'interested');
});

test('detectIntent: unknown falls through', () => {
  assert.strictEqual(detectIntent('من وين انتوا؟', KW), 'unknown');
  assert.strictEqual(detectIntent('', KW), 'unknown');
});

test('detectIntent: no false positive on common Arabic negation-adjacent phrases', () => {
  // "ما شاء الله" contains "ما" but not our negative keywords as whole phrases
  assert.strictEqual(detectIntent('ما شاء الله', KW), 'unknown');
});

// ---------- nextStatus ----------
test('nextStatus pipeline transitions', () => {
  assert.strictEqual(nextStatus('new', 'default'), 'sent');
  assert.strictEqual(nextStatus('new', 'interested'), 'interested');
  assert.strictEqual(nextStatus('new', 'booking'), 'demo_booked');
  assert.strictEqual(nextStatus('new', 'not_interested'), 'lost');
  assert.strictEqual(nextStatus('sent', 'booking'), 'demo_booked');
  assert.strictEqual(nextStatus('interested', 'not_interested'), 'lost');
  assert.strictEqual(nextStatus('lost', 'interested'), 'lost'); // terminal
  assert.strictEqual(nextStatus('demo_booked', 'not_interested'), 'demo_booked'); // terminal
});

// ---------- canSend / batchCap ----------
test('canSend respects quiet hours', () => {
  assert.strictEqual(canSend({ start: 22, end: 9 }, new Date('2026-08-17T14:00:00')), true);
  assert.strictEqual(canSend({ start: 22, end: 9 }, new Date('2026-08-17T23:00:00')), false);
});

test('batchCap caps batch size', () => {
  assert.strictEqual(batchCap(50, 12), 12);
  assert.strictEqual(batchCap(5, 12), 5);
});
