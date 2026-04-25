from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

remove_kb = ReplyKeyboardRemove()


def kb_role_select() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏪 Dokon sifatida kirish")],
            [KeyboardButton(text="🏢 Firma sifatida ro'yxatdan o'tish")],
        ],
        resize_keyboard=True,
    )


def kb_phone_request() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Kontakt ulashish", request_contact=True)],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True,
    )


def kb_store_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Yangi zakaz"), KeyboardButton(text="📋 Zakazlarim")],
            [KeyboardButton(text="🌐 Mini App"), KeyboardButton(text="👤 Profil")],
        ],
        resize_keyboard=True,
    )


def kb_agent_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📨 Yangi zakazlar"), KeyboardButton(text="📋 Barcha zakazlar")],
            [KeyboardButton(text="📦 Mahsulotlar"), KeyboardButton(text="📊 Hisobot")],
        ],
        resize_keyboard=True,
    )


def kb_admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏢 Kutayotgan firmalar")],
            [KeyboardButton(text="🏪 Dokonlar"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="🧪 Demo Mini App")],
        ],
        resize_keyboard=True,
    )


def kb_cancel() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Bekor qilish")]], resize_keyboard=True)


def kb_skip_cancel() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⏭ O'tkazib yuborish"), KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True,
    )


def kb_units() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="dona"), KeyboardButton(text="korobka")],
            [KeyboardButton(text="kg"), KeyboardButton(text="litr")],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True,
    )


def kb_product_actions_reply() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Mahsulot qo'shish"), KeyboardButton(text="⚡ Tez qo'shish")],
            [KeyboardButton(text="🔙 Orqaga")],
        ],
        resize_keyboard=True,
    )


def ikb_firms(firms: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for firm in firms:
        builder.button(text=firm["name"], callback_data=f"firm:{firm['id']}")
    builder.button(text="❌ Bekor qilish", callback_data="order_cancel")
    builder.adjust(1)
    return builder.as_markup()


def ikb_products(products: list, cart: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for product in products:
        key = str(product["id"])
        checked = "✅ " if key in cart else ""
        builder.button(text=f"{checked}{product['name']}", callback_data=f"prod:{product['id']}")
    builder.button(text="➡️ Zakaz berish", callback_data="order_next")
    builder.button(text="❌ Bekor qilish", callback_data="order_cancel")
    builder.adjust(1)
    return builder.as_markup()


def ikb_confirm_order() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="order_confirm"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="order_cancel"),
            ]
        ]
    )


def ikb_order_actions(order_id) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"accept:{order_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject:{order_id}"),
            ]
        ]
    )


def ikb_order_delivered(order_id) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="📦 Yetkazildi", callback_data=f"delivered:{order_id}")]]
    )


def ikb_approve_firm(firm_id) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"afirm:{firm_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"rfirm:{firm_id}"),
            ]
        ]
    )


def ikb_product_manage(product_id, is_active) -> InlineKeyboardMarkup:
    toggle_text = "🔴 O'chirish" if is_active else "🟢 Yoqish"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=toggle_text, callback_data=f"ptoggle:{product_id}"),
                InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"pdelete:{product_id}"),
            ]
        ]
    )


def ikb_order_status_store(order_id, status) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Zakaz #{order_id} holati: {status}", callback_data=f"noop:{order_id}")]
        ]
    )
