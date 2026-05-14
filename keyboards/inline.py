"""
Клавиатуры для всех шагов диалога.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def kb_role() -> InlineKeyboardMarkup:
    """Выбор роли на старте."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Хочу продать / оценить бизнес",
                              callback_data="role:seller")],
        [InlineKeyboardButton(text="🔍 Ищу объект для покупки",
                              callback_data="role:buyer")],
    ])


def kb_niche_seller() -> InlineKeyboardMarkup:
    """Быстрый выбор ниши для продавца."""
    niches = [
        ("🍽 Общепит / HoReCa",   "niche:horeca"),
        ("💇 Красота / SPA",       "niche:beauty"),
        ("🏭 Производство",        "niche:production"),
        ("🛒 Ритейл / торговля",   "niche:retail"),
        ("🚗 Авто / сервис",       "niche:auto"),
        ("🏥 Медицина / клиники",  "niche:medicine"),
        ("💻 IT / digital",        "niche:it"),
        ("📦 Другое",              "niche:other"),
    ]
    rows = []
    for i in range(0, len(niches), 2):
        row = [InlineKeyboardButton(text=niches[i][0], callback_data=niches[i][1])]
        if i + 1 < len(niches):
            row.append(InlineKeyboardButton(text=niches[i+1][0], callback_data=niches[i+1][1]))
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_revenue() -> InlineKeyboardMarkup:
    """Диапазоны годовой выручки."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="До 10 млн ₽",       callback_data="revenue:5000000")],
        [InlineKeyboardButton(text="10 — 30 млн ₽",     callback_data="revenue:20000000")],
        [InlineKeyboardButton(text="30 — 100 млн ₽",    callback_data="revenue:65000000")],
        [InlineKeyboardButton(text="100 — 300 млн ₽",   callback_data="revenue:200000000")],
        [InlineKeyboardButton(text="Более 300 млн ₽",   callback_data="revenue:400000000")],
    ])


def kb_horizon() -> InlineKeyboardMarkup:
    """Горизонт выхода для продавца."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="В течение 3 месяцев",  callback_data="horizon:3m")],
        [InlineKeyboardButton(text="3–6 месяцев",          callback_data="horizon:6m")],
        [InlineKeyboardButton(text="6–12 месяцев",         callback_data="horizon:12m")],
        [InlineKeyboardButton(text="Более года / думаю",   callback_data="horizon:thinking")],
    ])


def kb_budget() -> InlineKeyboardMarkup:
    """Бюджет покупателя."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="До 10 млн ₽",        callback_data="budget:5000000")],
        [InlineKeyboardButton(text="10 — 30 млн ₽",      callback_data="budget:20000000")],
        [InlineKeyboardButton(text="30 — 100 млн ₽",     callback_data="budget:65000000")],
        [InlineKeyboardButton(text="100 — 300 млн ₽",    callback_data="budget:200000000")],
        [InlineKeyboardButton(text="Более 300 млн ₽",    callback_data="budget:400000000")],
    ])


def kb_niche_buyer() -> InlineKeyboardMarkup:
    """Сфера интересов покупателя."""
    niches = [
        ("🍽 Общепит / HoReCa",   "niche:horeca"),
        ("💇 Красота / SPA",       "niche:beauty"),
        ("🏭 Производство",        "niche:production"),
        ("🛒 Ритейл",              "niche:retail"),
        ("🚗 Авто / сервис",       "niche:auto"),
        ("🏥 Медицина",            "niche:medicine"),
        ("💻 IT / digital",        "niche:it"),
        ("🌐 Любая прибыльная",   "niche:any"),
    ]
    rows = []
    for i in range(0, len(niches), 2):
        row = [InlineKeyboardButton(text=niches[i][0], callback_data=niches[i][1])]
        if i + 1 < len(niches):
            row.append(InlineKeyboardButton(text=niches[i+1][0], callback_data=niches[i+1][1]))
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_goal() -> InlineKeyboardMarkup:
    """Цель покупки бизнеса."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Пассивный доход",
                              callback_data="goal:passive")],
        [InlineKeyboardButton(text="🚀 Экспансия / масштабирование сети",
                              callback_data="goal:expansion")],
        [InlineKeyboardButton(text="🔄 Диверсификация портфеля",
                              callback_data="goal:diversification")],
        [InlineKeyboardButton(text="💡 Стратегическое поглощение (M&A)",
                              callback_data="goal:ma")],
    ])


def kb_book_call(calendly_link: str) -> InlineKeyboardMarkup:
    """Кнопка записи на встречу для горячего лида."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📅 Записаться на стратегическую сессию",
            url=calendly_link
        )],
    ])
