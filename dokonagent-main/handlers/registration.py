from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Contact, Message

from config import settings
from database import (
    create_firm,
    create_store,
    get_firm_by_telegram,
    get_store_by_telegram,
    get_user,
    update_user_role,
)
from keyboards import kb_cancel, kb_phone_request, kb_role_select, kb_store_menu
from states import FirmRegistration, StoreRegistration
from utils import normalize_phone

router = Router()


@router.message(F.text == "❌ Bekor qilish")
async def cancel_flow(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=kb_role_select())


@router.message(F.text == "🏪 Dokon sifatida kirish")
async def register_store(message: Message, state: FSMContext):
    existing = await get_store_by_telegram(message.from_user.id)
    if existing:
        await message.answer("Siz allaqachon dokon sifatida ro'yxatdan o'tgansiz.", reply_markup=kb_store_menu())
        return
    await state.set_state(StoreRegistration.waiting_name)
    await message.answer("Dokon nomini kiriting (kamida 2 harf):", reply_markup=kb_cancel())


@router.message(StoreRegistration.waiting_name)
async def store_name(message: Message, state: FSMContext):
    if len(message.text.strip()) < 2:
        await message.answer("Noto'g'ri nom. Qayta kiriting.")
        return
    await state.update_data(store_name=message.text.strip())
    await state.set_state(StoreRegistration.waiting_address)
    await message.answer("Dokon manzilini kiriting:")


@router.message(StoreRegistration.waiting_address)
async def store_address(message: Message, state: FSMContext):
    await state.update_data(store_address=message.text.strip())
    await state.set_state(StoreRegistration.waiting_phone)
    await message.answer("Telefon raqamini kiriting yoki kontakt ulashing:", reply_markup=kb_phone_request())


@router.message(StoreRegistration.waiting_phone, F.contact)
async def store_phone_contact(message: Message, state: FSMContext):
    await _complete_store_registration(message, state, message.contact.phone_number)


@router.message(StoreRegistration.waiting_phone)
async def store_phone_text(message: Message, state: FSMContext):
    await _complete_store_registration(message, state, message.text)


async def _complete_store_registration(message: Message, state: FSMContext, phone_raw: str):
    phone = normalize_phone(phone_raw)
    if not phone.startswith("+"):
        await message.answer("Telefon + bilan boshlanishi kerak.")
        return
    data = await state.get_data()
    user = await get_user(message.from_user.id)
    await create_store(user["id"], message.from_user.id, data["store_name"], data["store_address"], phone)
    await update_user_role(message.from_user.id, "store", phone=phone)
    await state.clear()
    await message.answer("✅ Muvaffaqiyatli ro'yxatdan o'tdingiz!", reply_markup=kb_store_menu())

    admin_text = (
        "🆕 <b>Yangi dokon ro'yxatdan o'tdi</b>\n"
        f"Nomi: <b>{data['store_name']}</b>\n"
        f"Manzil: {data['store_address']}\n"
        f"Tel: <code>{phone}</code>\n"
        f"Telegram ID: <code>{message.from_user.id}</code>"
    )
    for admin_id in settings.ADMIN_IDS:
        try:
            await message.bot.send_message(admin_id, admin_text)
        except Exception:
            continue


@router.message(F.text == "🏢 Firma sifatida ro'yxatdan o'tish")
async def register_firm(message: Message, state: FSMContext):
    existing = await get_firm_by_telegram(message.from_user.id)
    if existing:
        await message.answer("Siz allaqachon firma ariza topshirgansiz.")
        return
    await state.set_state(FirmRegistration.waiting_name)
    await message.answer("Firma nomini kiriting:", reply_markup=kb_cancel())


@router.message(FirmRegistration.waiting_name)
async def firm_name(message: Message, state: FSMContext):
    await state.update_data(firm_name=message.text.strip())
    await state.set_state(FirmRegistration.waiting_inn)
    await message.answer("INN/STIR kiriting (yoki '-'):")


@router.message(FirmRegistration.waiting_inn)
async def firm_inn(message: Message, state: FSMContext):
    await state.update_data(firm_inn=message.text.strip())
    await state.set_state(FirmRegistration.waiting_address)
    await message.answer("Firma manzilini kiriting:")


@router.message(FirmRegistration.waiting_address)
async def firm_address(message: Message, state: FSMContext):
    await state.update_data(firm_address=message.text.strip())
    await state.set_state(FirmRegistration.waiting_phone)
    await message.answer("Telefon raqami yoki kontakt:", reply_markup=kb_phone_request())


@router.message(FirmRegistration.waiting_phone, F.contact)
async def firm_phone_contact(message: Message, state: FSMContext):
    await _complete_firm_registration(message, state, message.contact.phone_number)


@router.message(FirmRegistration.waiting_phone)
async def firm_phone_text(message: Message, state: FSMContext):
    await _complete_firm_registration(message, state, message.text)


async def _complete_firm_registration(message: Message, state: FSMContext, phone_raw: str):
    phone = normalize_phone(phone_raw)
    if not phone.startswith("+"):
        await message.answer("Telefon + bilan boshlanishi kerak.")
        return
    data = await state.get_data()
    user = await get_user(message.from_user.id)
    firm_id = await create_firm(
        user["id"],
        message.from_user.id,
        data["firm_name"],
        data["firm_inn"],
        data["firm_address"],
        phone,
    )
    await update_user_role(message.from_user.id, "firm_pending", phone=phone)
    await state.clear()
    await message.answer("✅ Arizangiz qabul qilindi! Admin tekshirib chiqadi.", reply_markup=kb_role_select())

    txt = (
        "🆕 <b>Yangi firma arizasi</b>\n"
        f"ID: <code>{firm_id}</code>\n"
        f"Nomi: <b>{data['firm_name']}</b>\n"
        f"INN: <code>{data['firm_inn']}</code>\n"
        f"Manzil: {data['firm_address']}\n"
        f"Tel: {phone}"
    )
    from keyboards import ikb_approve_firm

    for admin_id in settings.ADMIN_IDS:
        try:
            await message.bot.send_message(admin_id, txt, reply_markup=ikb_approve_firm(firm_id))
        except Exception:
            continue
