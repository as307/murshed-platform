#!/bin/bash
# Send the Murshed build summary to as@omanai.co via Gmail SMTP (app password).
# Usage: GMAIL_USER=you@gmail.com GMAIL_APP_PASS=xxxx bash send-email.sh
set -euo pipefail

GMAIL_USER="${GMAIL_USER:?Set GMAIL_USER (the gmail address that owns the app password)}"
GMAIL_APP_PASS="${GMAIL_APP_PASS:?Set GMAIL_APP_PASS (16-char app password, no spaces)}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Build a full RFC822 message: headers + body (the body file has a Subject line to strip)
{
  printf 'From: Murshed <"'"$GMAIL_USER"'">\r\n'
  printf 'To: as@omanai.co\r\n'
  sed -n '1s/^Subject: //p' "$DIR/email_body.txt" | sed 's/$/\r/'
  printf 'MIME-Version: 1.0\r\n'
  printf 'Content-Type: text/plain; charset=UTF-8\r\n'
  printf 'Content-Transfer-Encoding: 8bit\r\n'
  printf '\r\n'
  sed '1d' "$DIR/email_body.txt"
} > "$DIR/email_ready.eml"

# Send via Gmail SMTP over TLS. No extra deps — use python3's smtplib.
python3 - "$GMAIL_USER" "$GMAIL_APP_PASS" "$DIR/email_ready.eml" <<'PYEOF'
import smtplib, sys
user, app_pass, path = sys.argv[1], sys.argv[2], sys.argv[3]
msg = open(path, 'rb').read()
s = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
s.ehlo()
s.starttls()
s.ehlo()
s.login(user, app_pass)
s.sendmail(user, ['as@omanai.co'], msg)
s.quit()
print('✅ Email sent to as@omanai.co')
PYEOF
