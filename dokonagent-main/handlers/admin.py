from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from config import settings
from database import (
    approve_firm,
    get_all_stores,
    get_all_users_count,
    get_firm_by_id,
    get_pending_firms,
    reject_firm,
    update_user_role,
)
from keyboards import ikb_approve_firm, kb_admin_menu, kb_agent_menu

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


@router.message(Command("admin"))
async def admin_cmd(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ruxsat yo'q.")
        return
    await update_user_role(message.from_user.id, "admin")
    await message.answer("🛠 <b>Admin panel</b>", reply_markup=kb_admin_menu())


@router.message(Command("owner"))
async def owner_cmd(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ruxsat yo'q.")
        return
    await update_user_role(message.from_user.id, "admin")
    await message.answer(
        "👑 <b>Owner panel</b>\nSiz tasdiqlash va monitoringni shu yerdan boshqarasiz.",
        reply_markup=kb_admin_menu(),
    )


@router.message(F.text == "🏢 Kutayotgan firmalar")
async def pending_firms(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ruxsat yo'q.")
        return
    firms = await get_pending_firms()
    if not firms:
        await message.answer("Kutayotgan firmalar yo'q.")
        return
    for firm in firms:
        await message.answer(
            f"🏢 <b>{firm['name']}</b>\nINN: <code>{firm['inn']}</code>\nTel: <code>{firm['phone']}</code>",
            reply_markup=ikb_approve_firm(firm["id"]),
        )


@router.callback_query(F.data.startswith("afirm:"))
async def approve(callback: CallbackQuery):
    await callback.answer()
    if not is_admin(callback.from_user.id):
        await callback.message.answer("⛔ Ruxsat yo'q.")
        return
    firm_id = int(callback.data.split(":")[1])
    firm = await get_firm_by_id(firm_id)
    if not firm:
        await callback.message.answer("Firma topilmadi.")
        return
    await approve_firm(firm_id)
    await callback.message.answer("✅ Firma tasdiqlandi.")
    try:
        await callback.bot.send_message(
            firm["telegram_id"],
            "✅ <b>Firmangiz tasdiqlandi!</b>",
            reply_markup=kb_agent_menu(),
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("rfirm:"))
async def reject(callback: CallbackQuery):
    await callback.answer()
    if not is_admin(callback.from_user.id):
        await callback.message.answer("⛔ Ruxsat yo'q.")
        return
    firm_id = int(callback.data.split(":")[1])
    firm = await get_firm_by_id(firm_id)
    if not firm:
        await callback.message.answer("Firma topilmadi.")
        return
    await reject_firm(firm_id)
    await callback.message.answer("❌ Firma rad etildi.")
    try:
        await callback.bot.send_message(firm["telegram_id"], "❌ <b>Firmangiz rad etildi.</b>")
    except Exception:
        pass


@router.message(F.text == "📊 Statistika")
async def stats(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ruxsat yo'q.")
        return
    c = await get_all_users_count()
    await message.answer(
        "📊 <b>Statistika</b>\n"
        f"Jami users: <b>{c['total']}</b>\n"
        f"Dokonlar: <b>{c['stores']}</b>\n"
        f"Tasdiqlangan firmalar: <b>{c['firms']}</b>\n"
        f"Kutayotganlar: <b>{c['pending']}</b>"
    )


@router.message(F.text == "🏪 Dokonlar")
async def all_stores(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ruxsat yo'q.")
        return
    stores = await get_all_stores()
    if not stores:
        await message.answer("Dokonlar yo'q.")
        return
    for s in stores:
        await message.answer(
            f"🏪 <b>{s['name']}</b>\nManzil: {s['address']}\nTel: <code>{s['phone']}</code>"
        )


@router.message(F.text == "🧪 Demo Mini App")
async def demo_mini_app(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ruxsat yo'q.")
        return
    if not settings.WEBAPP_URL:
        await message.answer("WEBAPP_URL sozlanmagan.")
        return
    url = f"{settings.WEBAPP_URL.rstrip('/')}/miniapp?tg_id={message.from_user.id}"
    markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🛒 Demo Mini App ochish", web_app=WebAppInfo(url=url))]]
    )
    await message.answer(
        "Demo store va demo firmalar seed qilingan bo'lsa, Mini App shu tugma orqali ochiladi.",
        reply_markup=markup,
    )
