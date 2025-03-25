#!/bin/bash

# Đường dẫn đến thư mục dự án
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_DIR"

# Kích hoạt môi trường ảo nếu chưa được kích hoạt
if [[ -z "${VIRTUAL_ENV}" ]]; then
    source venv/bin/activate
fi

# Kiểm tra và cài đặt dependencies nếu cần
pip install -r requirements.txt >/dev/null 2>&1

# Kill các process cũ nếu có
pkill -f "python.*\(master\|proxy\|slave\).py"
sleep 2

echo "Khởi động Slave..."
# Khởi động slave trong terminal mới với log
gnome-terminal --title="Slave" -- bash -c "cd '$PROJECT_DIR' && source venv/bin/activate && python -u slave.py 2>&1 | tee slave.log; exec bash"

# Đợi 2 giây để slave khởi động
sleep 2

echo "Khởi động Proxy..."
# Khởi động proxy trong terminal mới với log
gnome-terminal --title="Proxy" -- bash -c "cd '$PROJECT_DIR' && source venv/bin/activate && python -u proxy.py 2>&1 | tee proxy.log; exec bash"

# Đợi 2 giây để proxy khởi động
sleep 2

echo "Khởi động Master..."
# Khởi động master trong terminal mới với log
gnome-terminal --title="Master" -- bash -c "cd '$PROJECT_DIR' && source venv/bin/activate && python -u master.py 2>&1 | tee master.log; exec bash"

echo "Hệ thống đã được khởi động trong các terminal riêng biệt."
echo "Kiểm tra log trong các file: slave.log, proxy.log, master.log"
