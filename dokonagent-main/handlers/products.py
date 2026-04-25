from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import (
    add_product,
    delete_product,
    get_firm_by_telegram,
    get_product_by_id,
    get_products_by_firm,
    get_firm_stats,
    toggle_product,
)
from keyboards import ikb_product_manage, kb_agent_menu, kb_product_actions_reply, kb_skip_cancel, kb_units
from states import AddProduct
from utils import is_float

router = Router()
VALID_UNITS = {"dona", "korobka", "kg", "litr"}


@router.message(F.text == "📦 Mahsulotlar")
async def products_menu(message: Message):
    firm = await get_firm_by_telegram(message.from_user.id)
    if not firm:
        await message.answer("Firma topilmadi.")
        return
    products = await get_products_by_firm(firm["id"], active_only=False)
    await message.answer("Mahsulotlar ro'yxati:", reply_markup=kb_product_actions_reply())
    if not products:
        await message.answer("Mahsulotlar yo'q.")
        return
    for p in products:
        txt = (
            f"📦 <b>{p['name']}</b>\n"
            f"Birlik: {p['unit']}\n"
            f"Min: {p['min_qty']}\n"
            f"Narx: {p['price'] or '-'}"
        )
        await message.answer(txt, reply_markup=ikb_product_manage(p["id"], bool(p["is_active"])))


@router.message(F.text == "🔙 Orqaga")
async def back_to_agent(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Agent paneliga qaytdingiz.", reply_markup=kb_agent_menu())


@router.message(F.text == "➕ Mahsulot qo'shish")
async def add_start(message: Message, state: FSMContext):
    await state.set_state(AddProduct.waiting_name)
    await message.answer("Mahsulot nomini kiriting:")


@router.message(F.text == "⚡ Tez qo'shish")
async def add_quick_start(message: Message, state: FSMContext):
    await state.set_state(AddProduct.waiting_quick_input)
    await message.answer(
        "Bir qatorda kiriting:\n"
        "<code>nom; birlik; min_miqdor; narx; izoh</code>\n\n"
        "Misol:\n"
        "<code>Cola 1L; dona; 5; 12000; sovutilgan</code>\n\n"
        "Izoh ixtiyoriy."
    )


@router.message(AddProduct.waiting_quick_input)
async def add_quick_finish(message: Message, state: FSMContext):
    parts = [p.strip() for p in message.text.split(";")]
    if len(parts) < 2:
        await message.answer("Format xato. Kamida: <code>nom; narx</code> bo'lsin.")
        return
    name = parts[0]
    price_raw = parts[1]
    unit = (parts[2] if len(parts) > 2 and parts[2] else "dona").lower()
    min_qty_raw = parts[3] if len(parts) > 3 and parts[3] else "1"
    description = parts[4] if len(parts) > 4 else ""
    if unit not in VALID_UNITS:
        await message.answer("Birlik noto'g'ri. Faqat: dona, korobka, kg, litr.")
        return
    if not is_float(min_qty_raw):
        await message.answer("Minimal miqdor musbat son bo'lishi kerak.")
        return
    price = None
    if price_raw and price_raw != "-":
        if not is_float(price_raw):
            await message.answer("Narx musbat son bo'lishi kerak yoki '-' kiriting.")
            return
        price = float(price_raw)

    firm = await get_firm_by_telegram(message.from_user.id)
    if not firm:
        await state.clear()
        await message.answer("Firma topilmadi.", reply_markup=kb_agent_menu())
        return
    await add_product(
        firm_id=firm["id"],
        name=name,
        description=description,
        unit=unit,
        min_qty=float(min_qty_raw),
        price=price,
    )
    await state.clear()
    await message.answer("✅ Mahsulot tezkor qo'shildi!", reply_markup=kb_agent_menu())


@router.message(AddProduct.waiting_name)
async def add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddProduct.waiting_description)
    await message.answer("Tavsif kiriting yoki o'tkazib yuboring:", reply_markup=kb_skip_cancel())


@router.message(AddProduct.waiting_description)
async def add_description(message: Message, state: FSMContext):
    desc = "" if message.text == "⏭ O'tkazib yuborish" else message.text.strip()
    await state.update_data(description=desc)
    await state.set_state(AddProduct.waiting_unit)
    await message.answer("Birlik tanlang:", reply_markup=kb_units())


@router.message(AddProduct.waiting_unit)
async def add_unit(message: Message, state: FSMContext):
    if message.text not in VALID_UNITS:
        await message.answer("Faqat taklif qilingan birlikni tanlang.")
        return
    await state.update_data(unit=message.text)
    await state.set_state(AddProduct.waiting_min_qty)
    await message.answer("Minimal miqdorni kiriting:")


@router.message(AddProduct.waiting_min_qty)
async def add_min_qty(message: Message, state: FSMContext):
    if not is_float(message.text):
        await message.answer("Musbat son kiriting.")
        return
    await state.update_data(min_qty=float(message.text))
    await state.set_state(AddProduct.waiting_price)
    await message.answer("Narx kiriting yoki o'tkazib yuboring:", reply_markup=kb_skip_cancel())


@router.message(AddProduct.waiting_price)
async def add_price(message: Message, state: FSMContext):
    if ";" in message.text:
        parts = [p.strip() for p in message.text.split(";")]
        if len(parts) >= 2:
            name = parts[0]
            price_raw = parts[1]
            unit = (parts[2] if len(parts) > 2 and parts[2] else "dona").lower()
            min_qty_raw = parts[3] if len(parts) > 3 and parts[3] else "1"
            description = parts[4] if len(parts) > 4 else ""
            if unit in VALID_UNITS and is_float(min_qty_raw) and is_float(price_raw):
                firm = await get_firm_by_telegram(message.from_user.id)
                await add_product(
                    firm_id=firm["id"],
                    name=name,
                    description=description,
                    unit=unit,
                    min_qty=float(min_qty_raw),
                    price=float(price_raw),
                )
                await state.clear()
                await message.answer("✅ Mahsulot shortcut bilan qo'shildi!", reply_markup=kb_agent_menu())
                return
        await message.answer("Format: <code>nom; narx; birlik; min; izoh</code>")
        return

    if message.text == "⏭ O'tkazib yuborish":
        price = None
    else:
        if not is_float(message.text):
            await message.answer("Narx uchun musbat son kiriting.")
            return
        price = float(message.text)
    data = await state.get_data()
    firm = await get_firm_by_telegram(message.from_user.id)
    await add_product(
        firm_id=firm["id"],
        name=data["name"],
        description=data["description"],
        unit=data["unit"],
        min_qty=data["min_qty"],
        price=price,
    )
    await state.clear()
    await message.answer("✅ Mahsulot qo'shildi!", reply_markup=kb_agent_menu())


@router.callback_query(F.data.startswith("ptoggle:"))
async def toggle(callback: CallbackQuery):
    await callback.answer()
    product_id = int(callback.data.split(":")[1])
    product = await get_product_by_id(product_id)
    firm = await get_firm_by_telegram(callback.from_user.id)
    if not product or not firm or product["firm_id"] != firm["id"]:
        await callback.message.answer("Ruxsat yo'q.")
        return
    await toggle_product(product_id)
    await callback.message.answer("Mahsulot holati yangilandi.")


@router.callback_query(F.data.startswith("pdelete:"))
async def delete(callback: CallbackQuery):
    await callback.answer()
    product_id = int(callback.data.split(":")[1])
    product = await get_product_by_id(product_id)
    firm = await get_firm_by_telegram(callback.from_user.id)
    if not product or not firm or product["firm_id"] != firm["id"]:
        await callback.message.answer("Ruxsat yo'q.")
        return
    await delete_product(product_id)
    await callback.message.answer("🗑 Mahsulot o'chirildi.")


@router.message(F.text == "📊 Hisobot")
async def report(message: Message):
    firm = await get_firm_by_telegram(message.from_user.id)
    if not firm:
        await message.answer("Firma topilmadi.")
        return
    stats = await get_firm_stats(firm["id"])
    await message.answer(
        "📊 <b>Hisobot</b>\n"
        f"Jami: <b>{stats['total']}</b>\n"
        f"Yangi: <b>{stats['new']}</b>\n"
        f"Tasdiqlangan: <b>{stats['confirmed']}</b>\n"
        f"Yetkazilgan: <b>{stats['delivered']}</b>"
    )
