"""
Скоринг лидов и отправка уведомлений владельцу.
"""
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError

from config import (
    OWNER_TELEGRAM_ID,
    HOT_LEAD_SELLER_REVENUE,
    HOT_LEAD_BUYER_BUDGET,
    CALENDLY_LINK,
    TEXTS,
)
from keyboards.inline import kb_book_call
from db.database import mark_hot_lead, mark_notified

logger = logging.getLogger(__name__)

# Метки ниш для человекочитаемого вывода
NICHE_LABELS = {
    "horeca":      "Общепит / HoReCa",
    "beauty":      "Красота / SPA",
    "production":  "Производство",
    "retail":      "Ритейл / торговля",
    "auto":        "Авто / сервис",
    "medicine":    "Медицина / клиники",
    "it":          "IT / digital",
    "other":       "Другое",
    "any":         "Любая прибыльная",
}

HORIZON_LABELS = {
    "3m":       "В течение 3 месяцев",
    "6m":       "3–6 месяцев",
    "12m":      "6–12 месяцев",
    "thinking": "Более года / ещё думает",
}

GOAL_LABELS = {
    "passive":        "Пассивный доход",
    "expansion":      "Экспансия / масштабирование",
    "diversification":"Диверсификация портфеля",
    "ma":             "Стратегическое поглощение (M&A)",
}


def parse_int(value: str) -> int:
    """Безопасно парсим число из строки типа '65000000'."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def format_money(amount: int) -> str:
    """Форматируем число в читаемый вид: 65000000 → '65 млн ₽'."""
    if amount >= 1_000_000_000:
        return f"{amount / 1_000_000_000:.1f} млрд ₽"
    if amount >= 1_000_000:
        return f"{amount // 1_000_000} млн ₽"
    return f"{amount:,} ₽".replace(",", " ")


async def score_seller(
    bot: Bot,
    user_id: int,
    username: str,
    full_name: str,
    niche: str,
    revenue_raw: str,
    city: str,
    horizon: str,
) -> bool:
    """
    Скоринг для продавца.
    Возвращает True, если лид горячий (выручка > 30 млн).
    """
    revenue = parse_int(revenue_raw)
    is_hot = revenue >= HOT_LEAD_SELLER_REVENUE

    if is_hot:
        await mark_hot_lead(
            user_id=user_id,
            role="seller",
            financial_key="revenue",
            financial_value=revenue,
            niche=NICHE_LABELS.get(niche, niche),
            city=city,
            horizon=HORIZON_LABELS.get(horizon, horizon),
        )
        await _notify_owner(
            bot=bot,
            user_id=user_id,
            username=username,
            full_name=full_name,
            role="🏭 ПРОДАВЕЦ",
            financial_label="Годовая выручка",
            financial_value=format_money(revenue),
            niche=NICHE_LABELS.get(niche, niche),
            city=city,
            horizon=HORIZON_LABELS.get(horizon, horizon),
            goal="—",
        )
        await _notify_hot_user(bot, user_id)

    return is_hot


async def score_buyer(
    bot: Bot,
    user_id: int,
    username: str,
    full_name: str,
    budget_raw: str,
    niche: str,
    goal: str,
) -> bool:
    """
    Скоринг для покупателя.
    Возвращает True, если лид горячий (бюджет > 10 млн).
    """
    budget = parse_int(budget_raw)
    is_hot = budget >= HOT_LEAD_BUYER_BUDGET

    if is_hot:
        await mark_hot_lead(
            user_id=user_id,
            role="buyer",
            financial_key="budget",
            financial_value=budget,
            niche=NICHE_LABELS.get(niche, niche),
            goal=GOAL_LABELS.get(goal, goal),
        )
        await _notify_owner(
            bot=bot,
            user_id=user_id,
            username=username,
            full_name=full_name,
            role="💼 ПОКУПАТЕЛЬ",
            financial_label="Бюджет покупки",
            financial_value=format_money(budget),
            niche=NICHE_LABELS.get(niche, niche),
            city="—",
            horizon="—",
            goal=GOAL_LABELS.get(goal, goal),
        )
        await _notify_hot_user(bot, user_id)

    return is_hot


async def _notify_owner(bot: Bot, user_id: int, username: str,
                         full_name: str, role: str, financial_label: str,
                         financial_value: str, niche: str, city: str,
                         horizon: str, goal: str):
    """Отправляем уведомление владельцу бота."""
    if not OWNER_TELEGRAM_ID:
        logger.warning("OWNER_TELEGRAM_ID не задан — уведомление не отправлено")
        return

    text = TEXTS["hot_lead_owner"].format(
        name=full_name,
        username=username or "нет",
        role=role,
        financial_label=financial_label,
        financial_value=financial_value,
        niche=niche,
        city=city,
        horizon=horizon,
        goal=goal,
        user_id=user_id,
    )
    try:
        await bot.send_message(OWNER_TELEGRAM_ID, text)
        await mark_notified(user_id)
        logger.info(f"Уведомление о горячем лиде отправлено для user_id={user_id}")
    except TelegramForbiddenError:
        logger.error("Владелец заблокировал бота — не можем отправить уведомление")
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления: {e}")


async def _notify_hot_user(bot: Bot, user_id: int):
    """Предлагаем горячему лиду записаться на сессию."""
    try:
        await bot.send_message(
            user_id,
            TEXTS["hot_lead_user"],
            reply_markup=kb_book_call(CALENDLY_LINK),
        )
    except Exception as e:
        logger.error(f"Ошибка отправки приглашения пользователю: {e}")
