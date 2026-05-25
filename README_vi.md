# Telegram Bot Control Machine

[English](README.md)

Bot Telegram dùng để quản lý và điều khiển máy tính Linux từ xa một cách tiện lợi và bảo mật.

## Tính năng
- **Bảo mật:** Chỉ phản hồi lệnh từ `CHAT_ID` mà bạn thiết lập.
- **Quản lý Service:** Khởi động, dừng, xem trạng thái, log của các systemd services trực tiếp từ Telegram (`/svc`, `/services`).
- **Khoá/Mở Khoá:** Dễ dàng khoá/mở khoá màn hình (Hỗ trợ GNOME/loginctl).
- **Trạng Thái:** Xem nhanh IP, uptime, CPU, RAM, Disk, và thông tin GPU (`/status`).
- **Khởi Động:** Thông báo tự động gửi về Telegram mỗi khi máy khởi động xong.

## Yêu cầu
- Máy tính chạy Linux (đã test trên Ubuntu).
- Cài đặt `python3`, `curl`.

## Cách Cài Đặt

### Bước 1: Chuẩn bị thông tin Bot
1. Lấy **Bot Token** từ [@BotFather](https://t.me/BotFather) trên Telegram.
2. Lấy **Chat ID** của bạn thông qua bot [@userinfobot](https://t.me/userinfobot) (hoặc bất kỳ bot lấy ID nào).

### Bước 2: Tải code
```bash
git clone https://github.com/duy12i1i7/telegram_bot_control_machine.git
cd telegram_bot_control_machine
```

### Bước 3: Điền thông tin
Bạn cần mở các file code và thay thế `<YOUR_BOT_TOKEN_HERE>` và `<YOUR_CHAT_ID_HERE>` bằng Token và ID bạn vừa lấy:

1. Trong file `notify-boot.sh`:
```bash
BOT_TOKEN="<YOUR_BOT_TOKEN_HERE>"
CHAT_ID="<YOUR_CHAT_ID_HERE>"
```

2. Trong file `telegram-bot.py`:
```python
BOT_TOKEN = "<YOUR_BOT_TOKEN_HERE>"
CHAT_ID = "<YOUR_CHAT_ID_HERE>"
```

*(Lưu ý: Không đẩy các file chứa token thật của bạn lên GitHub!)*

### Bước 4: Deploy lên hệ thống
Chạy các lệnh sau với quyền root/sudo (thay đổi `User=avis` trong `telegram-bot.service` và các script đường dẫn nếu tài khoản hệ thống của bạn khác `avis`):

```bash
# 1. Cài đặt script notify-boot
sudo cp notify-boot.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/notify-boot.sh
sudo cp notify-boot.service /etc/systemd/system/

# 2. Cài đặt script telegram-bot
sudo cp telegram-bot.py /usr/local/bin/
sudo chmod +x /usr/local/bin/telegram-bot.py
sudo cp telegram-bot.service /etc/systemd/system/

# 3. Cấp quyền sudo (Không yêu cầu mật khẩu) cho bot
# Mở file sudoers bằng: sudo visudo -f /etc/sudoers.d/telegram-bot
# Thêm dòng sau (đổi 'avis' thành tên user của bạn):
# avis ALL=(ALL) NOPASSWD: /usr/bin/systemctl, /usr/sbin/reboot, /usr/bin/loginctl

# 4. Kích hoạt và khởi chạy các dịch vụ
sudo systemctl daemon-reload
sudo systemctl enable notify-boot.service
sudo systemctl enable telegram-bot.service
sudo systemctl start telegram-bot.service
```

Xong! Mở Telegram chat với bot của bạn, gõ `/start` hoặc `/help` để xem danh sách lệnh.
