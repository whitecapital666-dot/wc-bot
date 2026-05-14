"""
White Capital — Анализатор Telegram-каналов для закупки рекламы.

Алгоритм:
1. Загружает список каналов из TGStat по тематикам
2. Фильтрует по ERR, приросту, признакам накрутки
3. Выводит финальный рейтинг каналов

Требования:
    pip install requests pandas tabulate python-dotenv

Использование:
    python tgstat_analyzer.py
    python tgstat_analyzer.py --min-subs 5000 --min-err 10 --export channels.xlsx
"""

import os
import time
import argparse
import requests
import pandas as pd
from dataclasses import dataclass, field, asdict
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

TGSTAT_TOKEN = os.getenv("TGSTAT_TOKEN", "ВСТАВЬ_ТОКЕН_TGSTAT")
BASE_URL = "https://api.tgstat.ru"

# ── Тематики каналов (коды TGStat) ───────────────────────────────────────────
# Целевая аудитория: владельцы бизнеса, инвесторы, топ-менеджмент
TARGET_CATEGORIES = {
    "business":       "Бизнес",
    "investments":    "Инвестиции",
    "realestate":     "Недвижимость",
    "economics":      "Экономика / финансы",
    "law":            "Право / юриспруденция",
    "management":     "Менеджмент",
    "startups":       "Стартапы / венчур",
    "franchise":      "Франшизы",
    "manufacturing":  "Производство / промышленность",
    "retail":         "Торговля / ритейл",
}

# Вручную проверенные каналы где сидит целевая аудитория
MANUAL_SEED_CHANNELS = [
    "@flenin_official",     # Топовый бизнес-блог
    "@business_ru",
    "@opora_russia",        # ОПОРА РОССИЯ
    "@rbc_russia",          # РБК
    "@kommersant",
    "@vedomosti",
    "@forbes_russia",
    "@skolkovo_live",
    "@investfunds",
    "@buyvend",             # Купля-продажа бизнеса
    "@biznes_ru",
    "@mabusiness",          # M&A тематика
    "@naumen_news",
    "@retailer_ru",
]


@dataclass
class ChannelMetrics:
    username: str
    title: str
    subscribers: int
    avg_views: int
    err: float                    # Engagement Rate by Reach (%)
    err24: float                  # ERR за последние 24ч
    post_frequency: float         # постов в неделю
    growth_30d: int               # прирост подписчиков за 30 дней
    growth_percent: float         # % прироста
    ads_count_30d: int            # количество рекламных постов за 30 дней
    mention_count: int            # упоминания канала другими
    is_verified: bool
    category: str
    # Вычисляемые флаги
    fraud_flag: bool = False
    fraud_reason: str = ""
    score: float = 0.0            # итоговый скоринговый балл


def tgstat_request(endpoint: str, params: dict = None) -> Optional[dict]:
    """Базовый запрос к TGStat API с retry."""
    url = f"{BASE_URL}{endpoint}"
    p = {"token": TGSTAT_TOKEN}
    if params:
        p.update(params)

    for attempt in range(3):
        try:
            r = requests.get(url, params=p, timeout=10)
            r.raise_for_status()
            data = r.json()
            if data.get("status") == "error":
                print(f"  API error: {data.get('error')}")
                return None
            return data
        except requests.RequestException as e:
            print(f"  Request failed (attempt {attempt+1}): {e}")
            time.sleep(2 ** attempt)
    return None


def get_channel_stat(username: str) -> Optional[dict]:
    """Получаем статистику одного канала."""
    username = username.lstrip("@")
    data = tgstat_request("/channels/stat", {"channelId": f"@{username}"})
    return data.get("response") if data else None


def get_channels_by_category(category: str, limit: int = 50) -> list[dict]:
    """Получаем топ каналов по категории."""
    data = tgstat_request("/channels/search", {
        "category":   category,
        "country":    "ru",
        "language":   "ru",
        "sort":       "subscribers",
        "limit":      limit,
    })
    if not data:
        return []
    return data.get("response", {}).get("items", [])


def get_post_frequency(username: str, days: int = 30) -> float:
    """Считаем среднее количество постов в неделю за последние N дней."""
    username = username.lstrip("@")
    data = tgstat_request("/channels/posts", {
        "channelId": f"@{username}",
        "limit": 200,
    })
    if not data:
        return 0.0
    posts = data.get("response", {}).get("items", [])
    return round(len(posts) / (days / 7), 1) if posts else 0.0


def detect_fraud(ch: ChannelMetrics) -> tuple[bool, str]:
    """
    Эвристики определения накрутки.
    Возвращает (is_fraud, reason).
    """
    reasons = []

    # 1. Очень низкий ERR при большой аудитории → накрутка подписчиков
    if ch.subscribers > 10_000 and ch.err < 3.0:
        reasons.append(f"ERR={ch.err}% слишком низкий для {ch.subscribers:,} подписчиков")

    # 2. Аномальный прирост — возможна покупка подписчиков
    if ch.growth_percent > 50 and ch.growth_30d > 5_000:
        reasons.append(f"Подозрительный прирост: +{ch.growth_percent}% за 30 дней")

    # 3. Слишком редкие посты — канал «мёртвый»
    if ch.post_frequency < 1.0:
        reasons.append(f"Менее 1 поста/нед → низкая активность")

    # 4. Слишком много рекламы → аудитория выгорела
    if ch.ads_count_30d > 30:
        reasons.append(f"Много рекламы: {ch.ads_count_30d} постов/мес")

    # 5. ERR24 аномально отличается от среднего ERR
    if ch.err > 0 and ch.err24 > 0:
        ratio = ch.err24 / ch.err
        if ratio > 5 or ratio < 0.1:
            reasons.append(f"ERR24 аномален: {ch.err24}% vs средний {ch.err}%")

    is_fraud = len(reasons) > 0
    return is_fraud, " | ".join(reasons) if reasons else ""


def calc_score(ch: ChannelMetrics) -> float:
    """
    Скоринг канала от 0 до 100.
    Учитывает: ERR, размер, прирост, частоту постов, упоминания.
    """
    if ch.fraud_flag:
        return 0.0

    score = 0.0

    # ERR (вес 40%)
    err_score = min(ch.err / 30 * 40, 40)   # 30% ERR = максимум
    score += err_score

    # Размер аудитории (вес 20%) — оптимум 20-100к
    if 20_000 <= ch.subscribers <= 100_000:
        score += 20
    elif 10_000 <= ch.subscribers < 20_000:
        score += 15
    elif 100_000 < ch.subscribers <= 500_000:
        score += 10
    elif ch.subscribers > 500_000:
        score += 5   # очень крупные каналы дороже и менее таргетированы

    # Органический прирост (вес 15%)
    if 0 < ch.growth_percent <= 20:
        score += 15
    elif 20 < ch.growth_percent <= 40:
        score += 8

    # Частота постов (вес 15%) — оптимум 3-7 в неделю
    if 3 <= ch.post_frequency <= 7:
        score += 15
    elif 1 <= ch.post_frequency < 3:
        score += 8
    elif ch.post_frequency > 7:
        score += 5

    # Упоминания = органический охват (вес 10%)
    mention_score = min(ch.mention_count / 50 * 10, 10)
    score += mention_score

    return round(score, 1)


def analyze_channels(
    min_subscribers: int = 5_000,
    min_err: float = 8.0,
    max_ads_per_month: int = 25,
) -> list[ChannelMetrics]:
    """
    Основная функция анализа.
    1. Собирает каналы из категорий + ручного списка
    2. Получает метрики
    3. Фильтрует и скорит
    """
    print("=" * 60)
    print("White Capital — Анализатор Telegram-каналов")
    print("=" * 60)

    all_usernames = set(MANUAL_SEED_CHANNELS)

    # Собираем каналы из категорий TGStat
    for cat_id, cat_name in TARGET_CATEGORIES.items():
        print(f"  Загружаю категорию: {cat_name}...")
        channels = get_channels_by_category(cat_id, limit=30)
        for ch in channels:
            username = ch.get("username")
            if username:
                all_usernames.add(f"@{username}")
        time.sleep(0.5)  # rate limit

    print(f"\n  Всего найдено каналов: {len(all_usernames)}")
    print("  Получаю метрики...\n")

    results = []
    for i, username in enumerate(sorted(all_usernames)):
        print(f"  [{i+1}/{len(all_usernames)}] {username}...", end=" ")
        stat = get_channel_stat(username)
        if not stat:
            print("нет данных")
            continue

        subs = stat.get("participants_count", 0)
        if subs < min_subscribers:
            print(f"мало подписчиков ({subs:,})")
            continue

        avg_views = stat.get("avg_post_reach", 0)
        err       = stat.get("err", 0.0)
        err24     = stat.get("err24", 0.0)

        # Прирост
        members_growth = stat.get("members_growth", {})
        growth_30d = members_growth.get("day30", 0)
        growth_pct = round(growth_30d / subs * 100, 1) if subs else 0

        freq = get_post_frequency(username)
        ads  = stat.get("adv_posts_count_30", 0)

        ch = ChannelMetrics(
            username=username,
            title=stat.get("title", ""),
            subscribers=subs,
            avg_views=avg_views,
            err=round(err, 2),
            err24=round(err24, 2),
            post_frequency=freq,
            growth_30d=growth_30d,
            growth_percent=growth_pct,
            ads_count_30d=ads,
            mention_count=stat.get("mention_count", 0),
            is_verified=stat.get("is_verified", False),
            category=stat.get("category", ""),
        )

        ch.fraud_flag, ch.fraud_reason = detect_fraud(ch)
        ch.score = calc_score(ch)

        if ch.err < min_err:
            print(f"низкий ERR ({ch.err}%)")
            continue
        if ch.ads_count_30d > max_ads_per_month:
            print(f"много рекламы ({ch.ads_count_30d}/мес)")
            continue

        results.append(ch)
        status = "🔥 HOT" if ch.score >= 70 else ("✅ OK" if not ch.fraud_flag else "⚠️  FRAUD")
        print(f"score={ch.score} {status}")
        time.sleep(0.3)

    results.sort(key=lambda x: x.score, reverse=True)
    return results


def print_report(channels: list[ChannelMetrics]):
    """Красивый вывод результатов в терминал."""
    if not channels:
        print("\nНет каналов, прошедших фильтрацию.")
        return

    print(f"\n{'=' * 80}")
    print(f"ФИНАЛЬНЫЙ РЕЙТИНГ — {len(channels)} каналов")
    print(f"{'=' * 80}")

    df = pd.DataFrame([asdict(c) for c in channels])
    cols = ["username", "title", "subscribers", "err", "post_frequency",
            "growth_percent", "ads_count_30d", "score", "fraud_flag", "fraud_reason"]
    df = df[cols].rename(columns={
        "username":       "Канал",
        "title":          "Название",
        "subscribers":    "Подписчики",
        "err":            "ERR%",
        "post_frequency": "Постов/нед",
        "growth_percent": "Прирост%",
        "ads_count_30d":  "Реклам/мес",
        "score":          "Балл",
        "fraud_flag":     "Накрутка?",
        "fraud_reason":   "Причина",
    })

    try:
        from tabulate import tabulate
        print(tabulate(df.head(20), headers="keys", tablefmt="rounded_outline",
                       showindex=False, floatfmt=".1f"))
    except ImportError:
        print(df.head(20).to_string(index=False))


def export_excel(channels: list[ChannelMetrics], path: str):
    """Экспорт в Excel."""
    df = pd.DataFrame([asdict(c) for c in channels])
    df.to_excel(path, index=False)
    print(f"\n  ✅ Экспортировано в {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="White Capital TGStat Analyzer")
    parser.add_argument("--min-subs",  type=int,   default=5_000,  help="Мин. подписчиков")
    parser.add_argument("--min-err",   type=float, default=8.0,    help="Мин. ERR%")
    parser.add_argument("--max-ads",   type=int,   default=25,     help="Макс. реклам/мес")
    parser.add_argument("--export",    type=str,   default="",     help="Путь для Excel")
    args = parser.parse_args()

    channels = analyze_channels(
        min_subscribers=args.min_subs,
        min_err=args.min_err,
        max_ads_per_month=args.max_ads,
    )
    print_report(channels)

    if args.export:
        export_excel(channels, args.export)
