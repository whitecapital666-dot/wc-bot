"""
Стартовый хэндлер: /start и выбор роли.
"""
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import TEXTS, GUIDE_SELLER, GUIDE_BUYER
from keyboards.inline import kb_role, kb_niche_seller, kb_budget
from states import SellerStates, BuyerStates
from db.database import upsert_user

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Приветствие и выбор роли."""
    await state.clear()

    user = message.from_user
    await upsert_user(
        tg_id=user.id,
        username=user.username or "",
        full_name=user.full_name or "",
    )

    await message.answer(
        TEXTS["welcome"],
        reply_markup=kb_role(),
    )


@router.callback_query(F.data == "role:seller")
async def on_seller(call: CallbackQuery, state: FSMContext):
    """Пользователь выбрал «Продать»."""
    await call.answer()
    user = call.from_user
    await upsert_user(
        tg_id=user.id,
        username=user.username or "",
        full_name=user.full_name or "",
        role="seller",
    )
    await state.set_state(SellerStates.waiting_niche)

    # Редактируем приветственное сообщение
    await call.message.edit_text(TEXTS["seller_intro"])

    # Отправляем PDF-гайд
    try:
        from aiogram.types import FSInputFile
        await call.message.answer_document(
            FSInputFile(GUIDE_SELLER),
            caption="📄 <b>«12 ошибок при продаже бизнеса»</b>\n\nСохраните — пригодится!"
        )
    except FileNotFoundError:
        await call.message.answer(
            "📄 <b>Гайд «12 ошибок при продаже бизнеса»</b>\n"
            "Ссылка на скачивание: https://white-capital.online/Oshibki-pri-prodazhe-biznesa.pdf"
        )

    # Первый вопрос
    await call.message.answer(
        "1️⃣ <b>В какой нише ваш бизнес?</b>",
        reply_markup=kb_niche_seller(),
    )


@router.callback_query(F.data == "role:buyer")
async def on_buyer(call: CallbackQuery, state: FSMContext):
    """Пользователь выбрал «Купить»."""
    await call.answer()
    user = call.from_user
    await upsert_user(
        tg_id=user.id,
        username=user.username or "",
        full_name=user.full_name or "",
        role="buyer",
    )
    await state.set_state(BuyerStates.waiting_budget)

    await call.message.edit_text(TEXTS["buyer_intro"])

    # Отправляем PDF-гайд покупателя
    try:
        from aiogram.types import FSInputFile
        await call.message.answer_document(
            FSInputFile(GUIDE_BUYER),
            caption="📄 <b>«Стратегия поиска активов»</b>\n\nОбязательно к прочтению!"
        )
    except FileNotFoundError:
        await call.message.answer(
            "📄 <b>Гайд «Стратегия поиска активов»</b>\n"
            "Ссылка: https://white-capital.online/strategiya-pokupki.pdf"
        )

    # Первый вопрос
    await call.message.answer(
        "1️⃣ <b>Каков ваш инвестиционный бюджет на покупку бизнеса?</b>",
        reply_markup=kb_budget(),
    )
