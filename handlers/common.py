"""
Общие хэндлеры: fallback на неожиданные сообщения.
"""
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()


@router.message(Command("restart"))
async def cmd_restart(message: Message):
    """Перезапуск диалога."""
    from aiogram.fsm.context import FSMContext
    await message.answer(
        "🔄 Диалог сброшен. Напишите /start чтобы начать заново."
    )


@router.message()
async def fallback(message: Message):
    """Обрабатываем любые непредусмотренные сообщения."""
    await message.answer(
        "Используйте кнопки для ответов, или нажмите /start чтобы начать заново."
    )
