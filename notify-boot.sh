#!/bin/bash
# notify-boot.sh - Send Telegram notification on boot

BOT_TOKEN="<YOUR_BOT_TOKEN_HERE>"
CHAT_ID="<YOUR_CHAT_ID_HERE>"

# Đợi network sẵn sàng
sleep 5

HOSTNAME=$(hostname)
IP=$(tailscale ip -4 2>/dev/null || hostname -I 2>/dev/null | grep -oE '100\.[0-9]+\.[0-9]+\.[0-9]+')
UPTIME=$(uptime -p 2>/dev/null || uptime)
BOOT_TIME=$(date '+%Y-%m-%d %H:%M:%S')

MESSAGE="🟢 Máy *${HOSTNAME}* đã khởi động!
🕐 Thời gian: ${BOOT_TIME}
🌐 IP: ${IP}
⏱ Uptime: ${UPTIME}"

curl -fsS -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
     -d "chat_id=${CHAT_ID}" \
     -d "parse_mode=Markdown" \
     -d "text=${MESSAGE}"
