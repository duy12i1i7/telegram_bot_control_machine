#!/usr/bin/env python3
"""Telegram Bot - Nhận lệnh từ Telegram và thực thi trên máy."""

import json
import subprocess
import urllib.request
import urllib.parse
import time
import os
import glob
import html as html_mod

BOT_TOKEN = "<YOUR_BOT_TOKEN_HERE>"
CHAT_ID = "<YOUR_CHAT_ID_HERE>"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

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


def get_gui_env():
    """Lấy biến môi trường DISPLAY và DBUS để chạy GUI app."""
    env = os.environ.copy()

    # Tìm DISPLAY từ session đang chạy
    try:
        # Thử lấy từ process gnome-session hoặc Xorg
        for proc_name in ["gnome-session", "Xorg", "Xwayland", "gdm"]:
            result = subprocess.run(
                ["pgrep", "-a", proc_name],
                capture_output=True, text=True, timeout=5
            )
            if result.stdout.strip():
                # Lấy PID đầu tiên
                pid = result.stdout.strip().split("\n")[0].split()[0]
                env_file = f"/proc/{pid}/environ"
                if os.path.exists(env_file):
                    try:
                        with open(env_file, "r") as f:
                            proc_env = f.read()
                        for var in proc_env.split("\0"):
                            if var.startswith("DISPLAY="):
                                env["DISPLAY"] = var.split("=", 1)[1]
                            elif var.startswith("XAUTHORITY="):
                                env["XAUTHORITY"] = var.split("=", 1)[1]
                            elif var.startswith("DBUS_SESSION_BUS_ADDRESS="):
                                env["DBUS_SESSION_BUS_ADDRESS"] = var.split("=", 1)[1]
                            elif var.startswith("WAYLAND_DISPLAY="):
                                env["WAYLAND_DISPLAY"] = var.split("=", 1)[1]
                    except PermissionError:
                        pass
                if "DISPLAY" in env:
                    break
    except Exception:
        pass

    # Fallback
    if "DISPLAY" not in env:
        env["DISPLAY"] = ":0"

    # Fallback cho DBUS
    if "DBUS_SESSION_BUS_ADDRESS" not in env:
        try:
            uid = subprocess.getoutput("id -u")
            bus_path = f"/run/user/{uid}/bus"
            if os.path.exists(bus_path):
                env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={bus_path}"
        except Exception:
            pass

    # Fallback XAUTHORITY
    if "XAUTHORITY" not in env:
        # Tìm Xwayland auth file
        auth_files = glob.glob("/run/user/*/.*Xwaylandauth*")
        if auth_files:
            env["XAUTHORITY"] = auth_files[0]
        else:
            home = os.path.expanduser("~")
            xauth = os.path.join(home, ".Xauthority")
            if os.path.exists(xauth):
                env["XAUTHORITY"] = xauth

    return env


def run_in_terminal(cmd, description):
    """Mở gnome-terminal và chạy lệnh."""
    env = get_gui_env()
    try:
        subprocess.Popen(
            [
                "gnome-terminal", "--",
                "bash", "-c", f"{cmd}; echo ''; echo '--- Nhấn Enter để đóng ---'; read"
            ],
            env=env,
            start_new_session=True,
        )
        return f"✅ Đã mở terminal và chạy: *{description}*"
    except Exception as e:
        return f"❌ Lỗi mở terminal: `{e}`"


def run_background(cmd, description):
    """Chạy lệnh ngầm, trả về output."""
    try:
        result = subprocess.run(
            ["bash", "-c", cmd],
            capture_output=True, text=True, timeout=60
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

    if cmd_text in COMMANDS:
        conf = COMMANDS[cmd_text]
        if conf.get("gui"):
            result = run_in_terminal(conf["cmd"], conf["description"])
        else:
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
        # Thêm .service nếu chưa có
        if not svc_name.endswith(".service"):
            svc_name_full = svc_name + ".service"
        else:
            svc_name_full = svc_name
            svc_name = svc_name.replace(".service", "")

        valid_actions = {
            "start":   ("▶️", f"sudo systemctl start {svc_name_full}"),
            "stop":    ("⏹", f"sudo systemctl stop {svc_name_full}"),
            "restart": ("🔄", f"sudo systemctl restart {svc_name_full}"),
            "enable":  ("✅", f"sudo systemctl enable {svc_name_full}"),
            "disable": ("❌", f"sudo systemctl disable {svc_name_full}"),
        }

        if action == "log":
            output = subprocess.getoutput(
                f"journalctl -u {svc_name_full} --no-pager -n 30 2>&1"
            )
            if len(output) > 3500:
                output = output[-3500:]
            send_message(chat_id,
                f"📝 *Log: {svc_name}*\n```\n{output}\n```"
            )
            return

        if action == "info":
            output = subprocess.getoutput(
                f"systemctl status {svc_name_full} --no-pager 2>&1"
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
        result = subprocess.getoutput(cmd + " 2>&1")

        # Kiểm tra trạng thái sau khi thực hiện
        status_after = subprocess.getoutput(
            f"systemctl is-active {svc_name_full} 2>&1"
        ).strip()
        enabled_after = subprocess.getoutput(
            f"systemctl is-enabled {svc_name_full} 2>&1"
        ).strip()

        status_emoji = "🟢" if status_after == "active" else "🔴" if status_after == "failed" else "⚫"

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
                "systemctl list-units --type=service --all --no-pager --no-legend"
            )
            status_map = {
                "running": ("🟢", []),
                "exited":  ("⚪", []),
                "dead":    ("⚫", []),
                "failed":  ("🔴", []),
                "waiting": ("🟡", []),
                "other":   ("🔵", []),
            }
            for line in raw.strip().split("\n"):
                # Bỏ ký tự ● đầu dòng (systemctl dùng cho service lỗi)
                line = line.replace("●", "").strip()
                parts = line.split()
                if len(parts) >= 4 and ".service" in parts[0]:
                    name = parts[0].replace(".service", "")
                    sub_state = parts[3]
                    if sub_state in status_map:
                        status_map[sub_state][1].append(name)
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
        subprocess.Popen(["sudo", "reboot"])
        return

    if cmd_text == "/shutdown":
        hostname = subprocess.getoutput("hostname")
        send_message(chat_id, f"🔌 Đang tắt máy *{hostname}*...")
        subprocess.Popen(["sudo", "systemctl", "poweroff"])
        return

    if cmd_text == "/lock":
        subprocess.Popen(["sudo", "loginctl", "lock-sessions"])
        send_message(chat_id, "🔒 *Màn hình đã được khoá an toàn!*")
        return

    if cmd_text == "/unlock":
        subprocess.Popen(["sudo", "loginctl", "unlock-sessions"])
        send_message(chat_id, "🔓 *Màn hình đã được mở khoá!*")
        return

    if cmd_text == "/status":
        hostname = subprocess.getoutput("hostname")
        uptime_str = subprocess.getoutput("uptime -p 2>/dev/null || uptime")
        ip = subprocess.getoutput(
            "tailscale ip -4 2>/dev/null || hostname -I | grep -oE '100\\.[0-9]+\\.[0-9]+\\.[0-9]+'"
        )
        cpu = subprocess.getoutput(
            "top -bn1 | grep '%Cpu' | awk '{printf \"%.1f%%\", 100 - $8}'"
        )
        mem = subprocess.getoutput(
            "free -h | awk '/Mem:/{printf \"%s / %s (%.0f%%)\", $3, $2, $3/$2*100}'"
        )
        disk = subprocess.getoutput(
            "df -h / | awk 'NR==2{printf \"%s / %s (%s)\", $3, $2, $5}'"
        )

        # GPU info
        gpu_info = ""
        try:
            gpu_raw = subprocess.getoutput(
                "nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu "
                "--format=csv,noheader,nounits 2>/dev/null"
            )
            if gpu_raw and "NVIDIA-SMI" not in gpu_raw and "not found" not in gpu_raw:
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
            f"📊 *Status máy {hostname}*\n"
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
        lines = ["🤖 *Danh sách lệnh:*\n"]
        for name, conf in COMMANDS.items():
            emoji = "🖥" if conf.get("gui") else "⚙️"
            lines.append(f"{emoji} `{name}` — {conf['description']}")
        lines.append(f"📋 `/services` — Xem tất cả services")
        lines.append(f"⚙️ `/svc <action> <name>` — Điều khiển service")
        lines.append(f"    _VD: /svc restart docker_")
        lines.append(f"    _Actions: start, stop, restart, enable, disable, log, info_")
        lines.append(f"🔒 `/lock` — Khóa màn hình máy tính")
        lines.append(f"🔓 `/unlock` — Mở khóa màn hình máy tính")
        lines.append(f"📊 `/status` — Xem trạng thái máy")
        lines.append(f"🔄 `/reboot` — Khởi động lại máy")
        lines.append(f"🔌 `/shutdown` — Tắt máy tính")
        lines.append(f"❓ `/help` — Hiện danh sách lệnh")
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
    commands.append({"command": "lock", "description": "Khóa màn hình"})
    commands.append({"command": "unlock", "description": "Mở khóa màn hình"})
    commands.append({"command": "status", "description": "Xem trạng thái máy"})
    commands.append({"command": "reboot", "description": "Khởi động lại máy"})
    commands.append({"command": "shutdown", "description": "Tắt máy tính"})
    commands.append({"command": "help", "description": "Hiện danh sách lệnh"})

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
    send_message(CHAT_ID, "🤖 Bot đã khởi động và sẵn sàng nhận lệnh!\nGõ /help để xem danh sách lệnh.")

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

                if not text or chat_id != CHAT_ID:
                    continue

                if text.startswith("/"):
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
