from datetime import datetime
from typing import Dict

STATUS_EMOJI = {"new": "🕐", "confirmed": "✅", "rejected": "❌", "delivered": "📦"}
STATUS_TEXT = {
    "new": "Kutilmoqda",
    "confirmed": "Tasdiqlangan",
    "rejected": "Rad etilgan",
    "delivered": "Yetkazildi",
}


def format_order_summary(
    store_name,
    firm_name,
    items,
    note="",
    delivery_date="",
    order_id=None,
    status="new",
    agent_note="",
    created_at="",
) -> str:
    header = f"📋 <b>Zakaz #{order_id}</b>\n" if order_id else "📋 <b>Zakaz</b>\n"
    text = [header]
    text.append(f"🏪 <b>Dokon:</b> {store_name}")
    text.append(f"🏢 <b>Firma:</b> {firm_name}")
    if created_at:
        text.append(f"📅 <b>Sana:</b> {created_at}")
    text.append("\n<b>Mahsulotlar:</b>")
    for item in items:
        text.append(f"  • {item.get('product_name') or item.get('name')} — {item['quantity']} {item['unit']}")
    if note:
        text.append(f"\n💬 <b>Izoh:</b> {note}")
    if delivery_date:
        text.append(f"🚚 <b>Yetkazish sanasi:</b> {delivery_date}")
    if agent_note and status == "rejected":
        text.append(f"📝 <b>Rad sababi:</b> {agent_note}")
    text.append(f"📌 <b>Holat:</b> {STATUS_EMOJI.get(status, 'ℹ️')} {STATUS_TEXT.get(status, status)}")
    return "\n".join(text)


def format_cart(cart: Dict[int, dict]) -> str:
    if not cart:
        return "🛒 <b>Savat bo'sh.</b>"
    lines = ["🛒 <b>Savat:</b>"]
    for item in cart.values():
        lines.append(f"  • {item['name']} — {item['qty']} {item['unit']}")
    return "\n".join(lines)


def validate_date(date_str: str) -> bool:
    try:
        parsed = datetime.strptime(date_str, "%d.%m.%Y")
        return parsed.date() >= datetime.now().date()
    except ValueError:
        return False


def is_float(value: str) -> bool:
    try:
        numeric = float(value)
        return numeric > 0
    except (ValueError, TypeError):
        return False


def normalize_phone(phone: str) -> str:
    cleaned = phone.strip().replace(" ", "").replace("-", "")
    if cleaned.startswith("998"):
        cleaned = f"+{cleaned}"
    if not cleaned.startswith("+"):
        cleaned = f"+{cleaned}"
    return cleaned
