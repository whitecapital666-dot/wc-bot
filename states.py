"""
FSM-состояния диалога.
Aiogram 3.x использует StatesGroup + State.
"""
from aiogram.fsm.state import State, StatesGroup


class SellerStates(StatesGroup):
    """Ветка «Хочу продать / оценить бизнес»"""
    waiting_niche    = State()   # Ниша бизнеса
    waiting_revenue  = State()   # Годовая выручка
    waiting_city     = State()   # Город
    waiting_horizon  = State()   # Когда планирует выход
    done             = State()


class BuyerStates(StatesGroup):
    """Ветка «Ищу объект для покупки»"""
    waiting_budget   = State()   # Объём инвестиций
    waiting_niche    = State()   # Сфера интересов
    waiting_goal     = State()   # Цель (пассивный доход / экспансия)
    done             = State()
