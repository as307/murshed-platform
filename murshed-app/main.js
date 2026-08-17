const { app, BrowserWindow, ipcMain } = require('electron');
const { execFile, exec } = require('child_process');
const fs = require('fs');
const path = require('path');

const AGENT_DIR = path.join(__dirname, '..', 'murshed-agent');
const LEADS_FILE = path.join(AGENT_DIR, 'leads.json');
const LOG_FILE = path.join(AGENT_DIR, 'outreach.log.jsonl');
const QR_FILE = path.join(AGENT_DIR, 'qr.png');
const SVC_LOG = '/home/yaman/logs/murshed-agent.log';

let win = null;

function createWindow() {
  win = new BrowserWindow({
    width: 1100,
    height: 760,
    backgroundColor: '#070b12',
    title: 'Murshed — WhatsApp Marketing Console',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  win.loadFile('index.html');
}

// ---- Data reads (all sandboxed: no writes from renderer) ----
function readJSON(p, fallback) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch { return fallback; }
}

function serviceStatus(cb) {
  exec('systemctl --user is-active murshed-agent', (e, out) => {
    cb((out || '').trim() === 'active');
  });
}

function collectStats() {
  const leads = readJSON(LEADS_FILE, []);
  const events = [];
  try {
    const raw = fs.readFileSync(LOG_FILE, 'utf8');
    for (const line of raw.split('\n').filter(Boolean)) {
      try { events.push(JSON.parse(line)); } catch {}
    }
  } catch {}

  const count = t => events.filter(e => e.type === t).length;
  const lastBookings = events.filter(e => e.type === 'demo_booked').slice(-5).reverse();
  const lastEvents = events.slice(-8).reverse();

  const byStatus = {};
  for (const l of leads) byStatus[l.status] = (byStatus[l.status] || 0) + 1;

  const qr = fs.existsSync(QR_FILE) ? 'file://' + QR_FILE : null;

  return {
    leads,
    byStatus,
    stats: {
      sent: count('sent'),
      sendFailed: count('send_failed'),
      incoming: count('incoming'),
      replied: count('replied'),
      demoBooked: count('demo_booked'),
      lost: count('lost'),
    },
    lastBookings,
    lastEvents,
    qr,
    updatedAt: new Date().toISOString(),
  };
}

ipcMain.handle('dashboard:stats', async () => collectStats());
ipcMain.handle('dashboard:service', async () => new Promise(res => serviceStatus(res)));
ipcMain.handle('dashboard:log', async () => {
  try { return fs.readFileSync(SVC_LOG, 'utf8').split('\n').slice(-60).join('\n'); } catch { return '(no service log yet)'; }
});
ipcMain.handle('dashboard:restart', async () => {
  exec('systemctl --user restart murshed-agent');
  await new Promise(r => setTimeout(r, 1200));
  return new Promise(res => serviceStatus(res));
});
ipcMain.handle('dashboard:reveal', async (_e, file) => {
  const target = file === 'leads' ? LEADS_FILE : file === 'log' ? LOG_FILE : AGENT_DIR;
  exec(`xdg-open "${path.dirname(target)}"`);
  return true;
});

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
