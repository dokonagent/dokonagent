from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from config import settings
from database import (
    create_order,
    get_approved_firms,
    get_firm_by_id,
    get_order_items,
    get_orders_for_store,
    get_product_by_id,
    get_products_by_firm,
    get_store_by_telegram,
)
from keyboards import (
    ikb_confirm_order,
    ikb_firms,
    ikb_order_status_store,
    ikb_products,
    kb_store_menu,
)
from states import NewOrder
from utils import format_cart, format_order_summary, is_float, validate_date

router = Router()


@router.message(F.text == "📦 Yangi zakaz")
async def new_order(message: Message, state: FSMContext):
    firms = await get_approved_firms()
    if not firms:
        await message.answer("Hozircha tasdiqlangan firmalar yo'q.")
        return
    await state.clear()
    await state.set_state(NewOrder.selecting_firm)
    await state.update_data(cart={})
    await message.answer("Firmani tanlang:", reply_markup=ikb_firms(firms))


@router.callback_query(F.data == "order_cancel")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.answer("Zakaz bekor qilindi.", reply_markup=kb_store_menu())


@router.callback_query(F.data.startswith("firm:"))
async def choose_firm(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    firm_id = int(callback.data.split(":")[1])
    products = await get_products_by_firm(firm_id, active_only=True)
    if not products:
        await callback.message.answer("Bu firmada faol mahsulotlar yo'q.")
        return
    data = await state.get_data()
    cart = data.get("cart", {})
    await state.update_data(firm_id=firm_id)
    await state.set_state(NewOrder.selecting_product)
    await callback.message.answer("Mahsulotlarni tanlang:", reply_markup=ikb_products(products, cart))


@router.callback_query(F.data.startswith("prod:"))
async def choose_product(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    product_id = int(callback.data.split(":")[1])
    product = await get_product_by_id(product_id)
    if not product:
        await callback.message.answer("Mahsulot topilmadi.")
        return
    await state.update_data(selected_product_id=product_id)
    await state.set_state(NewOrder.entering_quantity)
    await callback.message.answer(
        f"<b>{product['name']}</b> uchun miqdor kiriting.\nMinimal: <code>{product['min_qty']}</code> {product['unit']}"
    )


@router.message(NewOrder.entering_quantity)
async def enter_qty(message: Message, state: FSMContext):
    if not is_float(message.text):
        await message.answer("Miqdor noto'g'ri. Musbat son kiriting.")
        return
    qty = float(message.text)
    data = await state.get_data()
    product = await get_product_by_id(data["selected_product_id"])
    if qty < float(product["min_qty"]):
        await message.answer(f"Minimal miqdor {product['min_qty']} {product['unit']}.")
        return
    cart = data.get("cart", {})
    cart[str(product["id"])] = {
        "product_id": product["id"],
        "name": product["name"],
        "qty": qty,
        "unit": product["unit"],
    }
    await state.update_data(cart=cart)
    await state.set_state(NewOrder.selecting_product)
    products = await get_products_by_firm(data["firm_id"], active_only=True)
    await message.answer(f"{format_cart(cart)}\n\nYana mahsulot tanlang yoki davom eting.", reply_markup=ikb_products(products, cart))


@router.callback_query(F.data == "order_next")
async def order_next(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    cart = data.get("cart", {})
    if not cart:
        await callback.message.answer("Savat bo'sh.")
        return
    await state.set_state(NewOrder.entering_date)
    await callback.message.answer("Yetkazib berish sanasini kiriting (DD.MM.YYYY):")


@router.message(NewOrder.entering_date)
async def enter_date(message: Message, state: FSMContext):
    if not validate_date(message.text.strip()):
        await message.answer("Sana noto'g'ri. Masalan: 25.05.2026")
        return
    await state.update_data(delivery_date=message.text.strip())
    await state.set_state(NewOrder.entering_note)
    await message.answer("Izoh qoldiring yoki \"⏭ O'tkazib yuborish\" deb yozing.")


@router.message(NewOrder.entering_note)
async def enter_note(message: Message, state: FSMContext):
    note = "" if message.text.strip() == "⏭ O'tkazib yuborish" else message.text.strip()
    await state.update_data(note=note)
    data = await state.get_data()
    store = await get_store_by_telegram(message.from_user.id)
    firm = await get_firm_by_id(data["firm_id"])
    items = list(data["cart"].values())
    summary = format_order_summary(store["name"], firm["name"], items, note=note, delivery_date=data["delivery_date"])
    await state.set_state(NewOrder.confirming)
    await message.answer(summary, reply_markup=ikb_confirm_order())


@router.callback_query(F.data == "order_confirm")
async def confirm(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    store = await get_store_by_telegram(callback.from_user.id)
    order_id = await create_order(store["id"], data["firm_id"], data.get("note", ""), list(data["cart"].values()))
    await state.clear()
    await callback.message.answer(f"✅ Zakaz <b>#{order_id}</b> yuborildi!", reply_markup=kb_store_menu())

    firm = await get_firm_by_id(data["firm_id"])
    from keyboards import ikb_order_actions

    order_items = await get_order_items(order_id)
    text = "🔔 <b>Yangi zakaz keldi!</b>\n\n" + format_order_summary(
        store_name=store["name"],
        firm_name=firm["name"],
        items=order_items,
        note=data.get("note", ""),
        delivery_date=data.get("delivery_date", ""),
        order_id=order_id,
    )
    try:
        await callback.bot.send_message(firm["telegram_id"], text, reply_markup=ikb_order_actions(order_id))
    except Exception:
        pass


@router.message(F.text == "📋 Zakazlarim")
async def my_orders(message: Message):
    store = await get_store_by_telegram(message.from_user.id)
    if not store:
        await message.answer("Avval dokon sifatida ro'yxatdan o'ting.")
        return
    orders = await get_orders_for_store(store["id"], limit=10)
    if not orders:
        await message.answer("Zakazlar topilmadi.")
        return
    for order in orders:
        items = await get_order_items(order["id"])
        firm = await get_firm_by_id(order["firm_id"])
        txt = format_order_summary(
            store_name=store["name"],
            firm_name=firm["name"] if firm else "-",
            items=items,
            note=order.get("store_note") or "",
            delivery_date=order.get("delivery_date") or "",
            order_id=order["id"],
            status=order["status"],
            agent_note=order.get("agent_note") or "",
            created_at=order["created_at"],
        )
        await message.answer(txt, reply_markup=ikb_order_status_store(order["id"], order["status"]))


@router.message(F.text == "👤 Profil")
async def profile(message: Message):
    store = await get_store_by_telegram(message.from_user.id)
    if not store:
        await message.answer("Profil topilmadi.")
        return
    await message.answer(
        f"👤 <b>Profil</b>\nNomi: <b>{store['name']}</b>\nManzil: {store['address']}\nTel: <code>{store['phone']}</code>"
    )


@router.message(F.text == "🌐 Mini App")
async def open_mini_app(message: Message):
    store = await get_store_by_telegram(message.from_user.id)
    if not store:
        await message.answer("Avval dokon sifatida ro'yxatdan o'ting.")
        return
    if not settings.WEBAPP_URL:
        await message.answer("Mini App URL sozlanmagan. ADMIN: WEBAPP_URL env qo'shing.")
        return
    url = f"{settings.WEBAPP_URL.rstrip('/')}/miniapp?tg_id={message.from_user.id}"
    markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🛒 Mini App ochish", web_app=WebAppInfo(url=url))]]
    )
    await message.answer("Mini App orqali firma va mahsulotlarni qulay ko'ring:", reply_markup=markup)


@router.callback_query(F.data.startswith("delivered:"))
async def delivered(callback: CallbackQuery):
    await callback.answer()
    from database import get_order_by_id, mark_delivered

    order_id = int(callback.data.split(":")[1])
    order = await get_order_by_id(order_id)
    if not order:
        await callback.message.answer("Zakaz topilmadi.")
        return
    store = await get_store_by_telegram(callback.from_user.id)
    if not store or store["id"] != order["store_id"]:
        await callback.message.answer("Bu zakaz sizga tegishli emas.")
        return
    await mark_delivered(order_id)
    await callback.message.answer("📦 Zakaz yetkazildi deb belgilandi!")
