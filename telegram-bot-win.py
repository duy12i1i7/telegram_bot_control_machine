#!/usr/bin/env python3
"""Telegram Bot - Nhận lệnh từ Telegram và thực thi trên máy."""

import json
import subprocess
import urllib.request
import urllib.parse
import time
import os
import glob
import sys
import codecs
import html as html_mod

# Sửa lỗi UnicodeEncodeError trên Windows khi in ra console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')



BOT_TOKEN = "<YOUR_BOT_TOKEN_HERE>"
ALLOWED_CHAT_IDS = ["<YOUR_CHAT_ID_HERE>"] # VD: ["123456", "-987654321"]
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Nhận diện OS
OS_NAME = "Windows"
OS_EMOJI = "🪟"

# ============================================================
# CẤU HÌNH LỆNH - Thêm lệnh mới ở đây
# ============================================================
COMMANDS = {
    # Thêm lệnh mới theo mẫu:
    # "/tenlenhcuamay": {
    #     "description": "Mô tả lệnh",
    #     "cmd": "lenh_can_chay",
    #     "gui": False,  # True = mở gnome-terminal
    # },
}

# ============================================================


def send_message(chat_id, text, parse_mode="Markdown"):
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }).encode()
    try:
        req = urllib.request.Request(f"{API_URL}/sendMessage", data=data)
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"[ERROR] Gửi tin nhắn thất bại: {e}")
        # Retry không format nếu HTML/Markdown lỗi
        if parse_mode:
            try:
                data2 = urllib.parse.urlencode({
                    "chat_id": chat_id,
                    "text": text,
                }).encode()
                req2 = urllib.request.Request(f"{API_URL}/sendMessage", data=data2)
                urllib.request.urlopen(req2, timeout=10)
            except Exception:
                pass



def run_background(cmd, description):
    """Chạy lệnh ngầm bằng PowerShell, trả về output."""
    try:
        # Trên Windows, chạy bằng PowerShell
        result = subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True, text=True, timeout=60, encoding='utf-8', errors='replace'
        )
        output = result.stdout.strip() or result.stderr.strip() or "(không có output)"
        # Giới hạn output
        if len(output) > 3000:
            output = output[:3000] + "\n... (cắt bớt)"
        return f"✅ *{description}*\n```\n{output}\n```"
    except subprocess.TimeoutExpired:
        return f"⏰ Lệnh *{description}* chạy quá 60s, đã bị dừng."
    except Exception as e:
        return f"❌ Lỗi: `{e}`"


def handle_command(text, chat_id):
    """Xử lý lệnh từ Telegram."""
    # Lấy phần lệnh (bỏ @botname nếu có)
    cmd_text = text.split("@")[0].strip().lower()

    if cmd_text == "/getid":
        send_message(chat_id, f"🆔 Chat ID của nhóm/user này là: `{chat_id}`")
        return

    # Từ đây trở đi, kiểm tra quyền truy cập
    if chat_id not in ALLOWED_CHAT_IDS:
        print(f"[WARN] Từ chối truy cập từ Chat ID lạ: {chat_id}")
        return

    if cmd_text in COMMANDS:
        conf = COMMANDS[cmd_text]
        result = run_background(conf["cmd"], conf["description"])
        send_message(chat_id, result)
        return

    if cmd_text.startswith("/svc"):
        parts = text.strip().split()
        if len(parts) < 3:
            send_message(chat_id,
                "⚙️ *Cú pháp:* `/svc <hành_động> <tên_service>`\n\n"
                "*Hành động:*\n"
                "▶️ `start` \u2014 Khởi động\n"
                "⏹ `stop` \u2014 Dừng\n"
                "🔄 `restart` \u2014 Khởi động lại\n"
                "✅ `enable` \u2014 Bật tự khởi động\n"
                "❌ `disable` \u2014 Tắt tự khởi động\n"
                "📝 `log` \u2014 Xem 30 dòng log gần nhất\n"
                "📊 `info` \u2014 Xem chi tiết service\n\n"
                "*Ví dụ:* `/svc restart docker`"
            )
            return

        action = parts[1].lower()
        svc_name = parts[2]

        valid_actions = {
            "start":   ("▶️", f"Start-Service -Name {svc_name}"),
            "stop":    ("⏹", f"Stop-Service -Name {svc_name}"),
            "restart": ("🔄", f"Restart-Service -Name {svc_name}"),
            "enable":  ("✅", f"Set-Service -Name {svc_name} -StartupType Automatic"),
            "disable": ("❌", f"Set-Service -Name {svc_name} -StartupType Disabled"),
        }

        if action == "log":
            # Event Viewer cho Windows Service thay vì journalctl
            output = subprocess.getoutput(
                f'powershell -Command "Get-EventLog -LogName System -Source \\"Service Control Manager\\" -Newest 30 | Where-Object Message -match \\"{svc_name}\\" | Select-Object TimeGenerated, Message | Format-Table -Wrap -AutoSize"'
            )
            if len(output) > 3500:
                output = output[-3500:]
            send_message(chat_id,
                f"📝 *Log: {svc_name}*\n```\n{output}\n```"
            )
            return

        if action == "info":
            output = subprocess.getoutput(
                f'powershell -Command "Get-Service -Name {svc_name} | Select-Object *" '
            )
            if len(output) > 3500:
                output = output[-3500:]
            send_message(chat_id,
                f"📊 *Info: {svc_name}*\n```\n{output}\n```"
            )
            return

        if action not in valid_actions:
            send_message(chat_id,
                f"❌ Hành động `{action}` không hợp lệ.\n"
                "Dùng: `start`, `stop`, `restart`, `enable`, `disable`, `log`, `info`"
            )
            return

        emoji, cmd = valid_actions[action]
        result = subprocess.getoutput(f"powershell -Command \"{cmd}\" 2>&1")

        # Kiểm tra trạng thái sau khi thực hiện
        status_info = subprocess.getoutput(
            f'powershell -Command "Get-Service -Name {svc_name} | Select-Object Status, StartType | ConvertTo-Json"'
        )
        try:
            status_dict = json.loads(status_info)
            status_after = str(status_dict.get("Status", "Unknown"))
            enabled_after = str(status_dict.get("StartType", "Unknown"))
        except:
            status_after = "Unknown"
            enabled_after = "Unknown"

        status_emoji = "🟢" if "Running" in status_after else "🔴" if "Stopped" in status_after else "⚫"

        msg = (
            f"{emoji} *{action.upper()}* `{svc_name}`\n\n"
            f"{status_emoji} Trạng thái: *{status_after}*\n"
            f"🔧 Auto-start: *{enabled_after}*"
        )
        if result.strip():
            msg += f"\n\n```\n{result[:1000]}\n```"
        send_message(chat_id, msg)
        return

    if cmd_text == "/services":
        try:
            raw = subprocess.getoutput(
                'powershell -Command "Get-Service | Select-Object Status, Name | ConvertTo-Json"'
            )
            try:
                services_list = json.loads(raw)
                if isinstance(services_list, dict):
                    services_list = [services_list]
            except:
                services_list = []

            status_map = {
                "Running": ("🟢", []),
                "Stopped": ("⚪", []),
                "Paused":  ("🟡", []),
                "other":   ("🔵", []),
            }
            
            for svc in services_list:
                status = str(svc.get("Status", "other"))
                name = str(svc.get("Name", "Unknown"))
                
                # Match .NET Enum to string equivalent if it comes back as int (Running = 4, Stopped = 1)
                if status == "4" or status == "Running":
                    status_map["Running"][1].append(name)
                elif status == "1" or status == "Stopped":
                    status_map["Stopped"][1].append(name)
                elif status == "7" or status == "Paused":
                    status_map["Paused"][1].append(name)
                else:
                    status_map["other"][1].append(name)

            messages = []
            current = "📋 <b>Danh sách Services</b>\n"

            for status, (emoji, names) in status_map.items():
                if not names:
                    continue
                header = f"\n{emoji} <b>{status.upper()}</b> ({len(names)})\n"
                # Nếu header không vừa, tách tin nhắn mới
                if len(current) + len(header) > 2000:
                    messages.append(current)
                    current = "📋 <b>Services (tiếp)</b>\n"
                current += header

                for n in names:
                    item = f"  • <code>{html_mod.escape(n)}</code>\n"
                    if len(current) + len(item) > 2000:
                        messages.append(current)
                        current = f"📋 <b>Services (tiếp)</b>\n\n{emoji} <b>{status.upper()} (tt)</b>\n"
                    current += item

            messages.append(current)
            for msg in messages:
                send_message(chat_id, msg, parse_mode="HTML")
                time.sleep(0.3)  # Tránh rate limit
        except Exception as e:
            send_message(chat_id, f"❌ Lỗi: `{e}`")
        return

    if cmd_text == "/reboot":
        hostname = subprocess.getoutput("hostname")
        send_message(chat_id, f"🔄 Đang khởi động lại máy *{hostname}*...")
        subprocess.Popen(["shutdown", "/r", "/t", "0"])
        return

    if cmd_text == "/shutdown":
        hostname = subprocess.getoutput("hostname")
        send_message(chat_id, f"🔌 Đang tắt máy *{hostname}*...")
        subprocess.Popen(["shutdown", "/s", "/t", "0"])
        return

    if cmd_text == "/switch_to_win":
        send_message(chat_id, "❌ Lệnh này chỉ dành cho Ubuntu. Máy đã ở Windows rồi!")
        return

    if cmd_text == "/switch_to_linux":
        send_message(chat_id, "🔄 *Đang chuyển sang Ubuntu...*")
        subprocess.run('powershell -Command "bcdedit /set \\"{fwbootmgr}\\" bootsequence \\"{8a6ef682-5faa-11f1-ad70-806e6f6e6963}\\"; shutdown.exe /r /t 0"', shell=True)
        return

    if cmd_text == "/lock":
        # Khoá màn hình Windows bằng quyền Interactive User (Cách B)
        subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
        send_message(chat_id, "🔒 *Màn hình đã được khoá an toàn!*")
        return



    if cmd_text == "/status":
        hostname = subprocess.getoutput("hostname")
        uptime_str = subprocess.getoutput('powershell -Command "$ts = (Get-Date) - (gcim Win32_OperatingSystem).LastBootUpTime; Write-Output \\"up $($ts.Days) days, $($ts.Hours) hours, $($ts.Minutes) minutes\\""')
        
        ip = subprocess.getoutput('powershell -Command "Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias Tailscale* | Select-Object -ExpandProperty IPAddress"')
        if not ip:
            ip = subprocess.getoutput('powershell -Command "Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch \'Loopback\' } | Select-Object -ExpandProperty IPAddress | Select-Object -First 1"')
            
        cpu = subprocess.getoutput('powershell -Command "(Get-WmiObject Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average"') + "%"
        
        mem_raw = subprocess.getoutput('powershell -Command "$cs = Get-CimInstance Win32_OperatingSystem; $total = [math]::Round($cs.TotalVisibleMemorySize / 1MB, 2); $free = [math]::Round($cs.FreePhysicalMemory / 1MB, 2); $used = [math]::Round($total - $free, 2); $percent = [math]::Round(($used/$total)*100, 0); Write-Output \\"${used}GB / ${total}GB (${percent}%)\\""')
        mem = mem_raw.split('\n')[-1] if '\n' in mem_raw else mem_raw
        
        disk_raw = subprocess.getoutput('powershell -Command "$d = Get-WmiObject Win32_LogicalDisk -Filter \\"DeviceID=\'C:\'\\"; $total = [math]::Round($d.Size / 1GB, 2); $free = [math]::Round($d.FreeSpace / 1GB, 2); $used = [math]::Round($total - $free, 2); $percent = [math]::Round(($used/$total)*100, 0); Write-Output \\"${used}GB / ${total}GB (${percent}%)\\""')
        disk = disk_raw.split('\n')[-1] if '\n' in disk_raw else disk_raw

        # GPU info
        gpu_info = ""
        try:
            gpu_raw = subprocess.getoutput("nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits 2>nul")
            if gpu_raw and "not recognized" not in gpu_raw.lower():
                for i, line in enumerate(gpu_raw.strip().split("\n")):
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 5:
                        name, util, mem_used, mem_total, temp = parts[:5]
                        gpu_info += f"\n🎮 GPU{i}: *{name}*\n"
                        gpu_info += f"    ⚡ Sử dụng: {util}% | 🌡 {temp}°C\n"
                        gpu_info += f"    📦 VRAM: {mem_used}M / {mem_total}M"
        except Exception:
            pass

        if not gpu_info:
            gpu_info = "\n🎮 GPU: _không phát hiện_"

        msg = (
            f"{OS_EMOJI} *Status máy {hostname}* ({OS_NAME})\n"
            f"🌐 IP: `{ip}`\n"
            f"⏱ {uptime_str}\n"
            f"💻 CPU: {cpu}\n"
            f"🧠 RAM: {mem}\n"
            f"💾 Disk: {disk}"
            f"{gpu_info}"
        )
        send_message(chat_id, msg)
        return

    if cmd_text in ("/help", "/start"):
        lines = [f"{OS_EMOJI} *Danh sách lệnh ({OS_NAME}):*\n"]
        for name, conf in COMMANDS.items():
            emoji = "🖥" if conf.get("gui") else "⚙️"
            lines.append(f"{emoji} `{name}` — {conf['description']}")
        lines.append(f"📋 `/services` — Xem tất cả services")
        lines.append(f"⚙️ `/svc <action> <name>` — Điều khiển service")
        lines.append(f"    _VD: /svc restart docker_")
        lines.append(f"    _Actions: start, stop, restart, enable, disable, log, info_")
        lines.append(f"🔒 `/lock` — Khóa màn hình")
        lines.append(f"📊 `/status` — Xem trạng thái máy")
        lines.append(f"🔄 `/reboot` — Khởi động lại máy")
        lines.append(f"🔌 `/shutdown` — Tắt máy tính")
        if OS_NAME == "Ubuntu":
            lines.append(f"🪟 `/switch_to_win` — Chuyển sang Windows")
        else:
            lines.append(f"🐧 `/switch_to_linux` — Chuyển sang Ubuntu")
        lines.append(f"❓ `/help` — Hiện danh sách lệnh")
        lines.append(f"🆔 `/getid` — Lấy Chat ID hiện tại")
        send_message(chat_id, "\n".join(lines))
        return


def get_updates(offset=None):
    url = f"{API_URL}/getUpdates?timeout=30&allowed_updates=[\"message\"]"
    if offset is not None:
        url += f"&offset={offset}"
    try:
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req, timeout=35)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f"[ERROR] getUpdates: {e}")
        return None


def register_bot_commands():
    """Đăng ký menu lệnh cho bot trên Telegram."""
    commands = []
    for name, conf in COMMANDS.items():
        commands.append({"command": name.lstrip("/"), "description": conf["description"]})
    commands.append({"command": "services", "description": "Xem tất cả services"})
    commands.append({"command": "svc", "description": "Điều khiển service (start/stop/restart/...)" })
    commands.append({"command": "lock", "description": "Khóa màn hình (Windows)"})
    commands.append({"command": "status", "description": "Xem trạng thái máy"})
    commands.append({"command": "reboot", "description": "Khởi động lại máy"})
    commands.append({"command": "shutdown", "description": "Tắt máy tính"})
    commands.append({"command": "switch_to_linux", "description": "Chuyển sang Ubuntu"})
    commands.append({"command": "help", "description": "Hiện danh sách lệnh"})
    commands.append({"command": "getid", "description": "Lấy Chat ID"})

    data = json.dumps({"commands": commands}).encode()
    req = urllib.request.Request(
        f"{API_URL}/setMyCommands",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=10)
        print("[INFO] Đã đăng ký menu lệnh bot.")
    except Exception as e:
        print(f"[WARN] Không đăng ký được menu: {e}")


def main():
    print("[INFO] Bot đang khởi động...")
    register_bot_commands()

    offset = None

    # Bỏ qua tin nhắn cũ khi mới start
    print("[INFO] Bỏ qua tin nhắn cũ...")
    updates = get_updates(-1)
    if updates and updates.get("ok") and updates.get("result"):
        offset = updates["result"][-1]["update_id"] + 1

    print("[INFO] Bot sẵn sàng, đang lắng nghe lệnh...")
    for chat_id in ALLOWED_CHAT_IDS:
        send_message(chat_id, "🤖 Bot đã khởi động và sẵn sàng nhận lệnh!\nGõ /help để xem danh sách lệnh.")

    while True:
        try:
            updates = get_updates(offset)
            if not updates or not updates.get("ok"):
                time.sleep(5)
                continue

            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                message = update.get("message", {})
                text = message.get("text", "")
                chat_id = str(message.get("chat", {}).get("id", ""))

                if not text:
                    continue

                if text.startswith("/"):
                    # Check /getid FIRST before enforcing chat_id
                    cmd_text = text.split("@")[0].strip().lower()
                    if cmd_text == "/getid":
                        send_message(chat_id, f"🆔 Chat ID của nhóm/user này là: `{chat_id}`")
                        continue

                    if chat_id not in ALLOWED_CHAT_IDS:
                        print(f"[WARN] Từ chối truy cập từ Chat ID lạ: {chat_id}")
                        continue

                    print(f"[CMD] {text} from {chat_id}")
                    handle_command(text, chat_id)

        except KeyboardInterrupt:
            print("\n[INFO] Bot dừng.")
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
