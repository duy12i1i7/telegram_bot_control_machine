#!/bin/bash
# notify-boot.sh - Send Telegram notification on boot

BOT_TOKEN="<YOUR_BOT_TOKEN_HERE>"
ALLOWED_CHAT_IDS=("<YOUR_CHAT_ID_HERE>") # VD: ("123456" "-987654321")

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

for chat_id in "${ALLOWED_CHAT_IDS[@]}"; do
    curl -fsS -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
         -d "chat_id=${chat_id}" \
         -d "parse_mode=Markdown" \
         -d "text=${MESSAGE}"
done
