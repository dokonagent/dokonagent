from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import settings
from database import create_user, get_firm_by_telegram, get_user
from keyboards import kb_admin_menu, kb_agent_menu, kb_role_select, kb_store_menu

router = Router()


@router.message(CommandStart())
async def start_cmd(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await create_user(message.from_user.id, message.from_user.full_name)
        user = await get_user(message.from_user.id)

    if message.from_user.id in settings.ADMIN_IDS:
        from database import update_user_role

        if user.get("role") != "admin":
            await update_user_role(message.from_user.id, "admin")
        await message.answer("🛠 <b>Owner/Admin panel</b>", reply_markup=kb_admin_menu())
        return

    role = user.get("role")
    if role == "store":
        await message.answer("🏪 <b>Dokon paneli</b>", reply_markup=kb_store_menu())
    elif role == "firm":
        firm = await get_firm_by_telegram(message.from_user.id)
        if firm and firm["is_approved"]:
            await message.answer("🏢 <b>Firma agent paneli</b>", reply_markup=kb_agent_menu())
        else:
            await message.answer("⌛ <b>Arizangiz hali tasdiqlanmagan.</b>")
    elif role == "admin":
        await message.answer("🛠 <b>Admin panel</b>", reply_markup=kb_admin_menu())
    else:
        await message.answer("Rolni tanlang:", reply_markup=kb_role_select())
