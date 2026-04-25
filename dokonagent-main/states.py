from aiogram.fsm.state import State, StatesGroup


class StoreRegistration(StatesGroup):
    waiting_name = State()
    waiting_address = State()
    waiting_phone = State()


class FirmRegistration(StatesGroup):
    waiting_name = State()
    waiting_inn = State()
    waiting_address = State()
    waiting_phone = State()


class NewOrder(StatesGroup):
    selecting_firm = State()
    selecting_product = State()
    entering_quantity = State()
    entering_date = State()
    entering_note = State()
    confirming = State()


class AddProduct(StatesGroup):
    waiting_name = State()
    waiting_description = State()
    waiting_unit = State()
    waiting_min_qty = State()
    waiting_price = State()
    waiting_quick_input = State()


class AgentOrderAction(StatesGroup):
    entering_delivery_date = State()
    entering_rejection_reason = State()
