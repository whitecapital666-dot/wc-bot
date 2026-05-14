"""
Ветка «Продавец» — полная цепочка квалификационных вопросов.
Нниша → Выручка → Город → Горизонт → Скоринг → Финал
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states import SellerStates
from keyboards.inline import kb_revenue, kb_horizon
from db.database import save_answer
from utils.scoring import score_seller
from config import TEXTS, CHANNEL_LINK

router = Router()


# ─── 1. Ниша ──────────────────────────────────────────────────────────────────
@router.callback_query(SellerStates.waiting_niche, F.data.startswith("niche:"))
async def seller_niche(call: CallbackQuery, state: FSMContext):
    niche = call.data.split(":")[1]
    await call.answer()
    await save_answer(call.from_user.id, "niche", niche)
    await state.update_data(niche=niche)
    await state.set_state(SellerStates.waiting_revenue)

    await call.message.edit_text(
        "2️⃣ <b>Какова годовая выручка вашего бизнеса?</b>\n\n"
        "<i>Выручка — ключевой мультипликатор оценки. "
        "Укажите максимально точно.</i>"
    )
    await call.message.answer("Выберите диапазон:", reply_markup=kb_revenue())


# ─── 2. Выручка ───────────────────────────────────────────────────────────────
@router.callback_query(SellerStates.waiting_revenue, F.data.startswith("revenue:"))
async def seller_revenue(call: CallbackQuery, state: FSMContext):
    revenue = call.data.split(":")[1]
    await call.answer()
    await save_answer(call.from_user.id, "revenue", revenue)
    await state.update_data(revenue=revenue)
    await state.set_state(SellerStates.waiting_city)

    await call.message.edit_text(
        "3️⃣ <b>В каком городе / регионе находится бизнес?</b>\n\n"
        "<i>Напишите ответ в свободной форме: например, «Москва», «СПб», «Краснодар».</i>"
    )


# ─── 3. Город (свободный текст) ───────────────────────────────────────────────
@router.message(SellerStates.waiting_city)
async def seller_city(message: Message, state: FSMContext):
    city = message.text.strip()
    await save_answer(message.from_user.id, "city", city)
    await state.update_data(city=city)
    await state.set_state(SellerStates.waiting_horizon)

    await message.answer(
        "4️⃣ <b>Когда планируете выход из бизнеса?</b>",
        reply_markup=kb_horizon(),
    )


# ─── 4. Горизонт → Скоринг → Финал ───────────────────────────────────────────
@router.callback_query(SellerStates.waiting_horizon, F.data.startswith("horizon:"))
async def seller_horizon(call: CallbackQuery, state: FSMContext):
    horizon = call.data.split(":")[1]
    await call.answer()
    await save_answer(call.from_user.id, "horizon", horizon)

    data = await state.get_data()
    await state.set_state(SellerStates.done)

    user = call.from_user
    is_hot = await score_seller(
        bot=call.bot,
        user_id=user.id,
        username=user.username or "",
        full_name=user.full_name or "",
        niche=data.get("niche", ""),
        revenue_raw=data.get("revenue", "0"),
        city=data.get("city", ""),
        horizon=horizon,
    )

    if not is_hot:
        # Обычный лид — стандартное завершение
        await call.message.edit_text(
            TEXTS["done"].format(channel=CHANNEL_LINK)
        )
    # Если is_hot — горячему лиду уже отправлено предложение из scoring.py
