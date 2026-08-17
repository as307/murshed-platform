#!/bin/bash
# Launch Murshed Console (Electron). Uses --no-sandbox because the SUID
# sandbox needs root on this machine.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
exec node_modules/.bin/electron --no-sandbox .
