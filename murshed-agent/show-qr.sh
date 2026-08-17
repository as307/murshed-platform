#!/bin/bash
# Open the latest QR code image (refreshes every ~20s while unlinked).
# Usage: bash show-qr.sh   (or: xdg-open ~/Life/murshed-agent/qr.png)
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec xdg-open "$DIR/qr.png"
