"""
Ветка «Покупатель» — полная цепочка квалификационных вопросов.
Бюджет → Ниша → Цель → Скоринг → Финал
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from states import BuyerStates
from keyboards.inline import kb_niche_buyer, kb_goal
from db.database import save_answer
from utils.scoring import score_buyer
from config import TEXTS, CHANNEL_LINK

router = Router()


# ─── 1. Бюджет ────────────────────────────────────────────────────────────────
@router.callback_query(BuyerStates.waiting_budget, F.data.startswith("budget:"))
async def buyer_budget(call: CallbackQuery, state: FSMContext):
    budget = call.data.split(":")[1]
    await call.answer()
    await save_answer(call.from_user.id, "budget", budget)
    await state.update_data(budget=budget)
    await state.set_state(BuyerStates.waiting_niche)

    await call.message.edit_text(
        "2️⃣ <b>Какая сфера вас интересует?</b>\n\n"
        "<i>Можно выбрать несколько направлений — мы подберём варианты под ваш профиль.</i>"
    )
    await call.message.answer("Выберите сферу:", reply_markup=kb_niche_buyer())


# ─── 2. Ниша ──────────────────────────────────────────────────────────────────
@router.callback_query(BuyerStates.waiting_niche, F.data.startswith("niche:"))
async def buyer_niche(call: CallbackQuery, state: FSMContext):
    niche = call.data.split(":")[1]
    await call.answer()
    await save_answer(call.from_user.id, "niche", niche)
    await state.update_data(niche=niche)
    await state.set_state(BuyerStates.waiting_goal)

    await call.message.edit_text(
        "3️⃣ <b>Какова ваша основная цель покупки бизнеса?</b>\n\n"
        "<i>Это поможет нам предложить объекты с нужным профилем доходности.</i>"
    )
    await call.message.answer("Выберите цель:", reply_markup=kb_goal())


# ─── 3. Цель → Скоринг → Финал ───────────────────────────────────────────────
@router.callback_query(BuyerStates.waiting_goal, F.data.startswith("goal:"))
async def buyer_goal(call: CallbackQuery, state: FSMContext):
    goal = call.data.split(":")[1]
    await call.answer()
    await save_answer(call.from_user.id, "goal", goal)

    data = await state.get_data()
    await state.set_state(BuyerStates.done)

    user = call.from_user
    is_hot = await score_buyer(
        bot=call.bot,
        user_id=user.id,
        username=user.username or "",
        full_name=user.full_name or "",
        budget_raw=data.get("budget", "0"),
        niche=data.get("niche", ""),
        goal=goal,
    )

    if not is_hot:
        await call.message.edit_text(
            TEXTS["done"].format(channel=CHANNEL_LINK)
        )
    # Горячим лидам предложение уже отправлено из scoring.py
