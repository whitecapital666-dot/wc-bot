"""
База данных SQLite для хранения лидов и ответов пользователей.
Используем aiosqlite для async I/O.

Схема:
  users        — основная таблица пользователей/лидов
  answers      — все ответы на квалификационные вопросы (EAV-модель)
  hot_leads    — горячие лиды (выручка > 30M или бюджет > 10M)
"""

import aiosqlite
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/whitecapital.db")


CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id           INTEGER UNIQUE NOT NULL,         -- Telegram user_id
    username        TEXT,                             -- @username (может отсутствовать)
    full_name       TEXT,                             -- Имя из профиля TG
    role            TEXT CHECK(role IN ('seller','buyer','unknown')),
    is_hot          INTEGER DEFAULT 0,               -- 1 = горячий лид
    score           INTEGER DEFAULT 0,               -- скоринговый балл
    created_at      TEXT DEFAULT (datetime('now','localtime')),
    updated_at      TEXT DEFAULT (datetime('now','localtime'))
);
"""

CREATE_ANSWERS = """
CREATE TABLE IF NOT EXISTS answers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(tg_id) ON DELETE CASCADE,
    question    TEXT NOT NULL,   -- ключ вопроса: 'niche', 'revenue', 'city', ...
    answer      TEXT NOT NULL,   -- ответ пользователя (всегда текст)
    created_at  TEXT DEFAULT (datetime('now','localtime'))
);
"""

CREATE_HOT_LEADS = """
CREATE TABLE IF NOT EXISTS hot_leads (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(tg_id),
    role            TEXT,
    financial_key   TEXT,        -- 'revenue' или 'budget'
    financial_value INTEGER,     -- числовое значение для сортировки
    niche           TEXT,
    city            TEXT,
    horizon         TEXT,        -- когда планирует выход (для продавца)
    goal            TEXT,        -- цель покупки (для покупателя)
    notified        INTEGER DEFAULT 0,  -- 1 = уведомление отправлено владельцу
    created_at      TEXT DEFAULT (datetime('now','localtime'))
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_users_tg_id ON users(tg_id);",
    "CREATE INDEX IF NOT EXISTS idx_answers_user ON answers(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_hot_leads_user ON hot_leads(user_id);",
]


async def init_db():
    """Создаём БД и таблицы при первом запуске."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_USERS)
        await db.execute(CREATE_ANSWERS)
        await db.execute(CREATE_HOT_LEADS)
        for idx in CREATE_INDEXES:
            await db.execute(idx)
        await db.commit()


async def upsert_user(tg_id: int, username: str, full_name: str, role: str = "unknown"):
    """Создать или обновить пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (tg_id, username, full_name, role, updated_at)
            VALUES (?, ?, ?, ?, datetime('now','localtime'))
            ON CONFLICT(tg_id) DO UPDATE SET
                username   = excluded.username,
                full_name  = excluded.full_name,
                role       = excluded.role,
                updated_at = excluded.updated_at
        """, (tg_id, username, full_name, role))
        await db.commit()


async def save_answer(user_id: int, question: str, answer: str):
    """Сохранить один ответ пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO answers (user_id, question, answer) VALUES (?, ?, ?)",
            (user_id, question, answer)
        )
        await db.commit()


async def get_answers(user_id: int) -> dict:
    """Получить все ответы пользователя в виде словаря {question: answer}."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT question, answer FROM answers WHERE user_id = ?", (user_id,)
        )
        rows = await cursor.fetchall()
    return {row["question"]: row["answer"] for row in rows}


async def mark_hot_lead(user_id: int, role: str, financial_key: str,
                        financial_value: int, niche: str, city: str = "",
                        horizon: str = "", goal: str = ""):
    """Записать горячий лид и поставить флаг в таблице users."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_hot = 1, score = score + 100 WHERE tg_id = ?",
            (user_id,)
        )
        await db.execute("""
            INSERT INTO hot_leads
                (user_id, role, financial_key, financial_value, niche, city, horizon, goal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, role, financial_key, financial_value, niche, city, horizon, goal))
        await db.commit()


async def mark_notified(user_id: int):
    """Пометить что уведомление владельцу отправлено."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE hot_leads SET notified = 1 WHERE user_id = ?", (user_id,)
        )
        await db.commit()


async def get_all_leads(limit: int = 50) -> list[dict]:
    """Получить последние N лидов для экспорта/анализа."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT u.tg_id, u.username, u.full_name, u.role,
                   u.is_hot, u.score, u.created_at,
                   h.financial_key, h.financial_value, h.niche,
                   h.city, h.horizon, h.goal
            FROM users u
            LEFT JOIN hot_leads h ON u.tg_id = h.user_id
            ORDER BY u.created_at DESC
            LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]
