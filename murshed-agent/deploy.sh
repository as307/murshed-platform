#!/bin/bash
# Murshed agent deploy — installs a systemd user service with auto-restart.
# Usage: bash deploy.sh   (or: npm run deploy)
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NODE_BIN="$(command -v node)"
SERVICE_NAME="murshed-agent"
UNIT="$HOME/.config/systemd/user/${SERVICE_NAME}.service"
LOGDIR="$HOME/logs"

mkdir -p "$LOGDIR"

cat > "$UNIT" <<EOF
[Unit]
Description=Murshed WhatsApp marketing agent
After=network-online.target omniroute-gateway.service
Wants=network-online.target

[Service]
Type=simple
Environment=PATH=/home/yaman/.nvm/versions/node/v22.23.1/bin:/home/yaman/.local/bin:/usr/local/bin:/usr/bin:/bin
# Stale Chromium processes survive crashes and hold the session lock, making
# the next start fail with "browser is already running". Kill them, then clear
# the singleton lock files, before every start.
ExecStartPre=/bin/sh -c 'pkill -f "wwebjs_auth/[s]ession" 2>/dev/null || true; sleep 1; rm -f ${DIR}/.wwebjs_auth/[s]ession/Singleton* ${DIR}/.wwebjs_auth/[s]ession/DevToolsActivePort'
ExecStart=${NODE_BIN} ${DIR}/agent.js
WorkingDirectory=${DIR}
Restart=always
RestartSec=10
TimeoutStopSec=30
KillSignal=SIGTERM
StandardOutput=append:${LOGDIR}/murshed-agent.log
StandardError=append:${LOGDIR}/murshed-agent.log

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable "${SERVICE_NAME}.service"
systemctl --user restart "${SERVICE_NAME}.service"

echo "✅ Deployed: systemctl --user status ${SERVICE_NAME}"
echo "   Logs: tail -f ${LOGDIR}/murshed-agent.log"
echo "   Stop:  systemctl --user stop ${SERVICE_NAME}"
