from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import (
    confirm_order,
    get_firm_by_telegram,
    get_order_by_id,
    get_order_items,
    get_orders_for_firm,
    get_store_by_id,
    reject_order,
)
from keyboards import ikb_order_actions, ikb_order_delivered
from states import AgentOrderAction
from utils import format_order_summary, validate_date

router = Router()


@router.message(F.text == "📨 Yangi zakazlar")
async def new_orders(message: Message):
    firm = await get_firm_by_telegram(message.from_user.id)
    if not firm or not firm["is_approved"]:
        await message.answer("Tasdiqlangan firma profili topilmadi.")
        return
    orders = await get_orders_for_firm(firm["id"], status="new")
    if not orders:
        await message.answer("Yangi zakaz yo'q.")
        return
    for order in orders:
        store = await get_store_by_id(order["store_id"])
        items = await get_order_items(order["id"])
        txt = format_order_summary(
            store_name=store["name"] if store else "-",
            firm_name=firm["name"],
            items=items,
            note=order.get("store_note") or "",
            order_id=order["id"],
            status=order["status"],
            created_at=order["created_at"],
        )
        await message.answer(txt, reply_markup=ikb_order_actions(order["id"]))


@router.callback_query(F.data.startswith("accept:"))
async def accept_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    order_id = int(callback.data.split(":")[1])
    firm = await get_firm_by_telegram(callback.from_user.id)
    order = await get_order_by_id(order_id)
    if not firm or not order or order["firm_id"] != firm["id"] or order["status"] != "new":
        await callback.message.answer("Bu zakazni qabul qila olmaysiz.")
        return
    await state.set_state(AgentOrderAction.entering_delivery_date)
    await state.update_data(order_id=order_id)
    await callback.message.answer("Yetkazib berish sanasini kiriting (DD.MM.YYYY):")


@router.message(AgentOrderAction.entering_delivery_date)
async def accept_finish(message: Message, state: FSMContext):
    if not validate_date(message.text.strip()):
        await message.answer("Sana noto'g'ri. DD.MM.YYYY kiriting.")
        return
    data = await state.get_data()
    order = await get_order_by_id(data["order_id"])
    firm = await get_firm_by_telegram(message.from_user.id)
    if not order or not firm or order["firm_id"] != firm["id"]:
        await state.clear()
        await message.answer("Zakaz topilmadi.")
        return
    await confirm_order(order["id"], message.text.strip())
    await state.clear()
    await message.answer(f"✅ Zakaz #{order['id']} tasdiqlandi!")

    store = await get_store_by_id(order["store_id"])
    items = await get_order_items(order["id"])
    text = "✅ <b>Zakazingiz tasdiqlandi!</b>\n\n" + format_order_summary(
        store_name=store["name"],
        firm_name=firm["name"],
        items=items,
        note=order.get("store_note") or "",
        delivery_date=message.text.strip(),
        order_id=order["id"],
        status="confirmed",
    )
    try:
        await message.bot.send_message(store["telegram_id"], text, reply_markup=ikb_order_delivered(order["id"]))
    except Exception:
        pass


@router.callback_query(F.data.startswith("reject:"))
async def reject_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    order_id = int(callback.data.split(":")[1])
    firm = await get_firm_by_telegram(callback.from_user.id)
    order = await get_order_by_id(order_id)
    if not firm or not order or order["firm_id"] != firm["id"] or order["status"] != "new":
        await callback.message.answer("Bu zakazni rad qila olmaysiz.")
        return
    await state.set_state(AgentOrderAction.entering_rejection_reason)
    await state.update_data(order_id=order_id)
    await callback.message.answer("Rad etish sababini kiriting:")


@router.message(AgentOrderAction.entering_rejection_reason)
async def reject_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    order = await get_order_by_id(data["order_id"])
    firm = await get_firm_by_telegram(message.from_user.id)
    if not order or not firm or order["firm_id"] != firm["id"]:
        await state.clear()
        await message.answer("Zakaz topilmadi.")
        return
    reason = message.text.strip()
    await reject_order(order["id"], reason)
    await state.clear()
    await message.answer(f"❌ Zakaz #{order['id']} rad etildi.")
    store = await get_store_by_id(order["store_id"])
    try:
        await message.bot.send_message(
            store["telegram_id"],
            f"❌ <b>Zakazingiz rad etildi.</b>\nSabab: <i>{reason}</i>",
        )
    except Exception:
        pass


@router.message(F.text == "📋 Barcha zakazlar")
async def all_orders(message: Message):
    firm = await get_firm_by_telegram(message.from_user.id)
    if not firm:
        await message.answer("Firma topilmadi.")
        return
    orders = await get_orders_for_firm(firm["id"], status=None, limit=30)
    if not orders:
        await message.answer("Zakazlar yo'q.")
        return
    for order in orders:
        store = await get_store_by_id(order["store_id"])
        items = await get_order_items(order["id"])
        await message.answer(
            format_order_summary(
                store_name=store["name"] if store else "-",
                firm_name=firm["name"],
                items=items,
                note=order.get("store_note") or "",
                delivery_date=order.get("delivery_date") or "",
                order_id=order["id"],
                status=order["status"],
                agent_note=order.get("agent_note") or "",
                created_at=order["created_at"],
            )
        )
