#!/bin/bash
# White Capital Bot — автоматический деплой на Ubuntu 20.04/22.04
# Запуск: bash deploy.sh

set -e
echo "============================================"
echo "  White Capital Bot — Деплой"
echo "============================================"

BOT_DIR="/opt/whitecapital_bot"
BOT_USER="ubuntu"
SERVICE_NAME="whitecapital_bot"

# 1. Обновляем систему и ставим Python
echo "→ Устанавливаем зависимости..."
sudo apt-get update -qq
sudo apt-get install -y python3 python3-pip python3-venv unzip curl

# 2. Создаём директорию бота
echo "→ Создаём директорию $BOT_DIR..."
sudo mkdir -p $BOT_DIR
sudo chown $BOT_USER:$BOT_USER $BOT_DIR

# 3. Копируем файлы (предполагаем что архив уже на сервере)
echo "→ Разворачиваем файлы бота..."
cp -r /tmp/whitecapital_bot/* $BOT_DIR/
cd $BOT_DIR

# 4. Создаём виртуальное окружение
echo "→ Создаём venv и ставим зависимости..."
python3 -m venv venv
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 5. Создаём .env из примера (если нет)
if [ ! -f "$BOT_DIR/.env" ]; then
    cp $BOT_DIR/.env.example $BOT_DIR/.env
    echo ""
    echo "⚠️  ВАЖНО: отредактируй $BOT_DIR/.env если нужно изменить токены"
fi

# 6. Создаём папки для данных и гайдов
mkdir -p $BOT_DIR/data $BOT_DIR/guides

# 7. Создаём systemd-сервис
echo "→ Создаём systemd-сервис..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << SERVICE
[Unit]
Description=White Capital Telegram Bot
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=$BOT_USER
WorkingDirectory=$BOT_DIR
ExecStart=$BOT_DIR/venv/bin/python main.py
Restart=always
RestartSec=5
EnvironmentFile=$BOT_DIR/.env
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

# 8. Запускаем сервис
echo "→ Запускаем бота..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

sleep 3
STATUS=$(sudo systemctl is-active $SERVICE_NAME)

echo ""
echo "============================================"
if [ "$STATUS" = "active" ]; then
    echo "  ✅ Бот запущен успешно!"
    echo "  Логи: sudo journalctl -u $SERVICE_NAME -f"
    echo "  Стоп: sudo systemctl stop $SERVICE_NAME"
    echo "  Рестарт: sudo systemctl restart $SERVICE_NAME"
else
    echo "  ❌ Что-то пошло не так. Смотри логи:"
    echo "  sudo journalctl -u $SERVICE_NAME -n 50"
fi
echo "============================================"
