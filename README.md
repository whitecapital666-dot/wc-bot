# White Capital — Telegram-бот квалификации лидов

## Архитектура

```
whitecapital_bot/
├── main.py                  # Точка входа, запуск polling
├── config.py                # Все настройки и тексты
├── states.py                # FSM-состояния диалога
├── requirements.txt
├── .env.example             # Шаблон переменных окружения
│
├── handlers/
│   ├── start.py             # /start, выбор роли, отправка гайдов
│   ├── seller.py            # Ветка продавца (4 вопроса)
│   ├── buyer.py             # Ветка покупателя (3 вопроса)
│   └── common.py            # Fallback, /restart
│
├── keyboards/
│   └── inline.py            # Все inline-клавиатуры
│
├── states.py                # SellerStates, BuyerStates
│
├── db/
│   └── database.py          # SQLite через aiosqlite
│
├── utils/
│   └── scoring.py           # Скоринг лидов + уведомления
│
├── guides/
│   ├── 12_oshibok_prodavtsa.pdf      # Гайд для продавцов
│   └── strategiya_pokupki.pdf        # Гайд для покупателей
│
├── data/
│   └── whitecapital.db      # SQLite база (создаётся автоматически)
│
├── tgstat_analyzer.py       # Скрипт поиска каналов для рекламы
└── ad_posts.md              # Шаблоны рекламных постов
```

---

## Схема диалога

```
/start
  └── Выбор роли
        ├── ПРОДАТЬ
        │     ├── Отправить PDF «12 ошибок»
        │     ├── Q1: Ниша (кнопки)
        │     ├── Q2: Выручка (кнопки)
        │     ├── Q3: Город (свободный текст)
        │     └── Q4: Горизонт выхода (кнопки)
        │           └── СКОРИНГ
        │                 ├── выручка < 30 млн → стандартное завершение
        │                 └── выручка ≥ 30 млн → 🔥 уведомить владельца
        │                                        + предложить встречу
        │
        └── КУПИТЬ
              ├── Отправить PDF «Стратегия поиска»
              ├── Q1: Бюджет (кнопки)
              ├── Q2: Сфера интересов (кнопки)
              └── Q3: Цель (кнопки)
                    └── СКОРИНГ
                          ├── бюджет < 10 млн → стандартное завершение
                          └── бюджет ≥ 10 млн → 🔥 уведомить владельца
                                               + предложить встречу
```

---

## Схема БД (SQLite)

```sql
-- Пользователи и их роли
users (tg_id, username, full_name, role, is_hot, score, created_at, updated_at)

-- Все ответы пользователей (EAV — гибко расширяется)
answers (id, user_id → users.tg_id, question, answer, created_at)

-- Горячие лиды с финансовыми показателями
hot_leads (id, user_id, role, financial_key, financial_value,
           niche, city, horizon, goal, notified, created_at)
```

---

## Установка и запуск

```bash
# 1. Клонировать / скопировать папку
cd whitecapital_bot

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Настроить переменные
cp .env.example .env
# Заполнить WC_BOT_TOKEN и WC_OWNER_ID в .env

# 4. Положить PDF-гайды в папку guides/

# 5. Запустить
python main.py
```

---

## Запуск в production (systemd)

```ini
# /etc/systemd/system/whitecapital_bot.service
[Unit]
Description=White Capital Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/whitecapital_bot
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10
EnvironmentFile=/opt/whitecapital_bot/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable whitecapital_bot
sudo systemctl start whitecapital_bot
sudo journalctl -u whitecapital_bot -f  # логи
```

---

## Анализатор каналов (TGStat)

```bash
# Установить дополнительные зависимости
pip install pandas tabulate openpyxl

# Базовый запуск
python tgstat_analyzer.py

# С фильтрами и экспортом
python tgstat_analyzer.py --min-subs 10000 --min-err 10 --export channels.xlsx
```

Получить токен TGStat: https://api.tgstat.ru — бесплатный план 1000 запросов/сутки.

---

## Целевые тематики каналов (где сидит ЦА)

| Тематика | Почему работает |
|---|---|
| Бизнес-новости / аналитика | Предприниматели следят за рынком |
| Инвестиции / фондовый рынок | Ищут альтернативные активы |
| Недвижимость | Диверсификация портфеля |
| Право / налоги | Собственники решают юр. вопросы |
| Франшизы | Готовы к покупке готового бизнеса |
| HoReCa / ритейл / авто | Отраслевые владельцы |
| Форумы РСПП, ТПП, ОПОРА | Крупный и средний бизнес |
| Executive / топ-менеджмент | Принимают решения об инвестициях |

---

## Скоринговая модель (calc_score)

| Критерий | Макс. балл | Логика |
|---|---|---|
| ERR% | 40 | 30%+ ERR = максимум |
| Размер аудитории | 20 | Оптимум 20–100к |
| Органический прирост | 15 | 0–20% в месяц |
| Частота постов | 15 | 3–7 постов/неделю |
| Упоминания | 10 | Органический охват |
| Итого | 100 | ≥70 = горячий канал |

---

## Что настроить перед запуском

1. **WC_BOT_TOKEN** в `.env` — токен от @BotFather
2. **WC_OWNER_ID** в `.env` — твой Telegram user_id (узнать через @userinfobot)
3. **CALENDLY_LINK** в `config.py` — ссылка на твоё расписание
4. **CHANNEL_LINK** в `config.py` — ссылка на Telegram-канал White Capital
5. Положить PDF-файлы в `guides/`
6. **TGSTAT_TOKEN** — токен от api.tgstat.ru для анализатора каналов
