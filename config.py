"""
Конфигурация бота White Capital
Переменные читаются из окружения (Railway / .env файл)
"""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BOT_TOKEN = os.getenv("WC_BOT_TOKEN", "")
OWNER_TELEGRAM_ID = int(os.getenv("WC_OWNER_ID", "7978253994"))

HOT_LEAD_SELLER_REVENUE = 30_000_000
HOT_LEAD_BUYER_BUDGET   = 10_000_000

CALENDLY_LINK = "https://calendly.com/sheluhin-kirill/30min"
CHANNEL_LINK  = "https://t.me/kirillbusinesss"

GUIDE_SELLER = "guides/12_oshibok_prodavtsa.pdf"
GUIDE_BUYER  = "guides/strategiya_pokupki.pdf"

TEXTS = {
    "welcome": (
        "👋 <b>Добро пожаловать в White Capital!</b>\n\n"
        "Мы — M&A платформа полного цикла: покупка и продажа готового бизнеса "
        "в Москве и России (чек от 30 до 500 млн ₽).\n\n"
        "Выберите, что вас интересует:"
    ),
    "seller_intro": (
        "📋 <b>Вы хотите продать или оценить бизнес</b>\n\n"
        "Отлично! Держите бесплатный гайд:\n"
        "<b>«12 ошибок при продаже бизнеса»</b> 👇\n\n"
        "Это поможет не потерять 20–40% стоимости на переговорах."
    ),
    "buyer_intro": (
        "🔍 <b>Вы ищете объект для покупки</b>\n\n"
        "Держите гайд:\n"
        "<b>«Стратегия поиска активов: как не купить кота в мешке»</b> 👇\n\n"
        "83% ошибок при покупке совершаются ещё на этапе поиска."
    ),
    "hot_lead_owner": (
        "🔥 <b>ГОРЯЧИЙ ЛИД!</b>\n\n"
        "👤 {name} (@{username})\n"
        "📊 Роль: {role}\n"
        "💰 {financial_label}: {financial_value}\n"
        "🏭 Ниша/Сфера: {niche}\n"
        "🏙 Город: {city}\n"
        "⏰ Горизонт: {horizon}\n"
        "🎯 Цель: {goal}\n\n"
        "Telegram ID: <code>{user_id}</code>"
    ),
    "hot_lead_user": (
        "✅ <b>Отличные показатели!</b>\n\n"
        "Ваш запрос — в приоритетной очереди White Capital.\n"
        "Запишитесь на бесплатную 30-минутную стратегическую сессию с Кириллом:"
    ),
    "done": (
        "✅ <b>Спасибо, данные получены!</b>\n\n"
        "Наш брокер свяжется с вами в течение 24 часов.\n\n"
        "📌 Подпишитесь на канал — там закрытые объекты и аналитика:\n"
        "{channel}"
    ),
}
