"""
White Capital — Telegram-бот квалификации лидов
Библиотека: aiogram 3.x
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers.start import router as start_router
from handlers.seller import router as seller_router
from handlers.buyer import router as buyer_router
from handlers.common import router as common_router
from db.database import init_db
from config import BOT_TOKEN

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    # Инициализация БД
    await init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрируем роутеры в правильном порядке
dp.include_router(start_router)
dp.include_router(seller_router)
dp.include_router(buyer_router)
dp.include_router(common_router)

    logger.info("White Capital Bot запущен")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
