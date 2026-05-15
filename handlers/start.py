import logging
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import TEXTS, GUIDE_SELLER, GUIDE_BUYER
from keyboards.inline import kb_role, kb_niche_seller, kb_budget
from states import SellerStates, BuyerStates

logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    try:
        from db.database import upsert_user
        await upsert_user(tg_id=message.from_user.id, username=message.from_user.username or "", full_name=message.from_user.full_name or "")
    except Exception as e:
        logger.warning(f"DB error: {e}")
    await message.answer(TEXTS["welcome"], reply_markup=kb_role())

@router.callback_query(F.data == "role:seller")
async def on_seller(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(SellerStates.waiting_niche)
    await call.message.edit_text(TEXTS["seller_intro"])
    try:
        from aiogram.types import FSInputFile
        await call.message.answer_document(FSInputFile(GUIDE_SELLER), caption="PDF")
    except:
        await call.message.answer("https://white-capital.online/Oshibki-pri-prodazhe-biznesa.pdf")
    await call.message.answer("1. Ниша?", reply_markup=kb_niche_seller())

@router.callback_query(F.data == "role:buyer")
async def on_buyer(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(BuyerStates.waiting_budget)
    await call.message.edit_text(TEXTS["buyer_intro"])
    try:
        from aiogram.types import FSInputFile
        await call.message.answer_document(FSInputFile(GUIDE_BUYER), caption="PDF")
    except:
        await call.message.answer("https://white-capital.online/strategiya-pokupki.pdf")
    await call.message.answer("1. Бюджет?", reply_markup=kb_budget())
