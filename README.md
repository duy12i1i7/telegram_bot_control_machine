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
Open the code files and replace `<YOUR_BOT_TOKEN_HERE>` and `<YOUR_CHAT_ID_HERE>` with your actual Token and Chat ID. You can add multiple Chat IDs (e.g. for groups) by separating them with commas.

To get a Group Chat ID, add the bot to the group and send `/getid` to it.

1. In `notify-boot.sh` (Ubuntu):
```bash
BOT_TOKEN="<YOUR_BOT_TOKEN_HERE>"
ALLOWED_CHAT_IDS=("<YOUR_CHAT_ID_HERE>" "-100123456789")
```

2. In `telegram-bot.py` (Ubuntu) / `telegram-bot-win.py` (Windows):
```python
BOT_TOKEN = "<YOUR_BOT_TOKEN_HERE>"
ALLOWED_CHAT_IDS = ["<YOUR_CHAT_ID_HERE>", "-100123456789"]
```

*(Note: Do NOT push your actual tokens to GitHub!)*

## Installation (Ubuntu)

1. Copy files to appropriate directories:
```bash
sudo cp telegram-bot.py /usr/local/bin/telegram-bot.py
sudo chmod +x /usr/local/bin/telegram-bot.py

sudo cp notify-boot.sh /usr/local/bin/notify-boot.sh
sudo chmod +x /usr/local/bin/notify-boot.sh

sudo cp telegram-bot.service /etc/systemd/system/
sudo cp notify-boot.service /etc/systemd/system/
```

2. Set up sudo permissions (IMPORTANT for safe reboot/services control):
Create a file `/etc/sudoers.d/avis-bot`:
```bash
avis ALL=(ALL) NOPASSWD: /usr/bin/systemctl, /usr/sbin/reboot, /usr/bin/loginctl, /usr/sbin/grub-reboot
```

3. Enable and start services:
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot.service
sudo systemctl start telegram-bot.service
sudo systemctl enable notify-boot.service
```

## Installation (Windows)

1. Install Python 3 on Windows.
2. Open PowerShell as Admin and install `requests`:
```powershell
pip install requests
```
3. Create folder `C:\Bot` and copy `telegram-bot-win.py` into it.
4. Set up Task Scheduler to run at startup:
```powershell
$action = New-ScheduledTaskAction -Execute "C:\Program Files\Python312\pythonw.exe" -Argument "C:\Bot\telegram-bot-win.py"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\SYSTEM" -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName "TelegramBot" -Action $action -Trigger $trigger -Principal $principal -Force
```

Done! Open the Telegram chat with your bot and send `/start` or `/help` to view the list of commands.
