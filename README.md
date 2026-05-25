# Telegram Bot Control Machine

[Tiếng Việt](README_vi.md)

A Telegram Bot to conveniently and securely manage and control your Linux machine remotely.

## Features
- **Security:** Only responds to commands from the specific `CHAT_ID` you configure.
- **Service Management:** Start, stop, check the status, and view logs of systemd services directly from Telegram (`/svc`, `/services`).
- **Lock/Unlock:** Easily lock/unlock your screen (Supports GNOME/loginctl).
- **System Status:** Quickly view IP, uptime, CPU, RAM, Disk usage, and GPU information (`/status`).
- **Boot Notification:** Automatically sends a Telegram message when the machine finishes booting.

## Requirements
- A machine running Linux (tested on Ubuntu).
- `python3` and `curl` installed.

## Installation Guide

### Step 1: Prepare Bot Information
1. Get a **Bot Token** from [@BotFather](https://t.me/BotFather) on Telegram.
2. Get your **Chat ID** from the [@userinfobot](https://t.me/userinfobot) (or any other bot that provides your Telegram ID).

### Step 2: Download Code
```bash
git clone https://github.com/duy12i1i7/telegram_bot_control_machine.git
cd telegram_bot_control_machine
```

### Step 3: Configure Information
Open the code files and replace `<YOUR_BOT_TOKEN_HERE>` and `<YOUR_CHAT_ID_HERE>` with your actual Token and Chat ID:

1. In `notify-boot.sh`:
```bash
BOT_TOKEN="<YOUR_BOT_TOKEN_HERE>"
CHAT_ID="<YOUR_CHAT_ID_HERE>"
```

2. In `telegram-bot.py`:
```python
BOT_TOKEN = "<YOUR_BOT_TOKEN_HERE>"
CHAT_ID = "<YOUR_CHAT_ID_HERE>"
```

*(Note: Do NOT push your actual tokens to GitHub!)*

### Step 4: Deploy to System
Run the following commands with root/sudo privileges (change `User=avis` in `telegram-bot.service` and the script paths if your system username is not `avis`):

```bash
# 1. Install notify-boot script
sudo cp notify-boot.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/notify-boot.sh
sudo cp notify-boot.service /etc/systemd/system/

# 2. Install telegram-bot script
sudo cp telegram-bot.py /usr/local/bin/
sudo chmod +x /usr/local/bin/telegram-bot.py
sudo cp telegram-bot.service /etc/systemd/system/

# 3. Grant sudo privileges (No password required) to the bot
# Open the sudoers file using: sudo visudo -f /etc/sudoers.d/telegram-bot
# Add the following line (replace 'avis' with your actual username):
# avis ALL=(ALL) NOPASSWD: /usr/bin/systemctl, /usr/sbin/reboot, /usr/bin/loginctl

# 4. Enable and start the services
sudo systemctl daemon-reload
sudo systemctl enable notify-boot.service
sudo systemctl enable telegram-bot.service
sudo systemctl start telegram-bot.service
```

Done! Open the Telegram chat with your bot and send `/start` or `/help` to view the list of commands.
