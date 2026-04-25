from typing import List, Optional

import aiosqlite
from config import settings

DB_PATH = settings.DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id BIGINT UNIQUE NOT NULL,
                full_name TEXT,
                phone TEXT,
                role TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS firms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                telegram_id BIGINT,
                name TEXT NOT NULL,
                inn TEXT,
                address TEXT,
                phone TEXT,
                is_approved INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS stores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                telegram_id BIGINT,
                name TEXT NOT NULL,
                address TEXT,
                phone TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                firm_id INTEGER REFERENCES firms(id),
                name TEXT NOT NULL,
                description TEXT,
                image_url TEXT,
                unit TEXT DEFAULT 'dona',
                min_qty REAL DEFAULT 1,
                price REAL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER REFERENCES stores(id),
                firm_id INTEGER REFERENCES firms(id),
                status TEXT DEFAULT 'new',
                delivery_date TEXT,
                agent_note TEXT,
                store_note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER REFERENCES orders(id),
                product_id INTEGER REFERENCES products(id),
                quantity REAL NOT NULL,
                product_name TEXT,
                unit TEXT
            );
            """
        )
        for statement in (
            "ALTER TABLE products ADD COLUMN image_url TEXT",
            "ALTER TABLE orders ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ):
            try:
                await db.execute(statement)
            except aiosqlite.OperationalError:
                pass
        await db.commit()


async def _fetchone(query: str, params=()) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(query, params)
        row = await cur.fetchone()
        return dict(row) if row else None


async def _fetchall(query: str, params=()) -> List[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(query, params)
        rows = await cur.fetchall()
        return [dict(row) for row in rows]


async def get_user(telegram_id: int) -> Optional[dict]:
    return await _fetchone("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))


async def create_user(telegram_id: int, full_name: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "INSERT INTO users (telegram_id, full_name) VALUES (?, ?)",
            (telegram_id, full_name),
        )
        await db.commit()
        return cur.lastrowid


async def ensure_user(telegram_id: int, full_name: str, role: Optional[str] = None, phone: Optional[str] = None) -> int:
    user = await get_user(telegram_id)
    if user:
        if role or phone:
            await update_user_role(telegram_id, role or user.get("role") or "", phone=phone)
        return user["id"]
    user_id = await create_user(telegram_id, full_name)
    if role or phone:
        await update_user_role(telegram_id, role or "", phone=phone)
    return user_id


async def update_user_role(telegram_id: int, role: str, phone: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if phone:
            await db.execute("UPDATE users SET role = ?, phone = ? WHERE telegram_id = ?", (role, phone, telegram_id))
        else:
            await db.execute("UPDATE users SET role = ? WHERE telegram_id = ?", (role, telegram_id))
        await db.commit()


async def get_all_users_count() -> dict:
    total = await _fetchone("SELECT COUNT(*) as c FROM users")
    stores = await _fetchone("SELECT COUNT(*) as c FROM stores WHERE is_active = 1")
    firms = await _fetchone("SELECT COUNT(*) as c FROM firms WHERE is_approved = 1 AND is_active = 1")
    pending = await _fetchone("SELECT COUNT(*) as c FROM firms WHERE is_approved = 0 AND is_active = 1")
    return {"total": total["c"], "stores": stores["c"], "firms": firms["c"], "pending": pending["c"]}


async def create_store(user_id, telegram_id, name, address, phone) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "INSERT INTO stores (user_id, telegram_id, name, address, phone) VALUES (?, ?, ?, ?, ?)",
            (user_id, telegram_id, name, address, phone),
        )
        await db.commit()
        return cur.lastrowid


async def ensure_store(user_id, telegram_id, name, address, phone) -> int:
    store = await get_store_by_telegram(telegram_id)
    if store:
        return store["id"]
    return await create_store(user_id, telegram_id, name, address, phone)


async def get_store_by_telegram(telegram_id) -> Optional[dict]:
    return await _fetchone("SELECT * FROM stores WHERE telegram_id = ? AND is_active = 1", (telegram_id,))


async def get_store_by_id(store_id) -> Optional[dict]:
    return await _fetchone("SELECT * FROM stores WHERE id = ?", (store_id,))


async def get_all_stores() -> List[dict]:
    return await _fetchall("SELECT * FROM stores WHERE is_active = 1 ORDER BY id DESC")


async def create_firm(user_id, telegram_id, name, inn, address, phone) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "INSERT INTO firms (user_id, telegram_id, name, inn, address, phone) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, telegram_id, name, inn, address, phone),
        )
        await db.commit()
        return cur.lastrowid


async def ensure_firm(user_id, telegram_id, name, inn, address, phone, approved=True) -> int:
    firm = await get_firm_by_telegram(telegram_id)
    if firm:
        return firm["id"]
    firm_id = await create_firm(user_id, telegram_id, name, inn, address, phone)
    if approved:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE firms SET is_approved = 1 WHERE id = ?", (firm_id,))
            await db.execute("UPDATE users SET role = 'firm' WHERE id = ?", (user_id,))
            await db.commit()
    return firm_id


async def get_firm_by_telegram(telegram_id) -> Optional[dict]:
    return await _fetchone("SELECT * FROM firms WHERE telegram_id = ? AND is_active = 1", (telegram_id,))


async def get_firm_by_id(firm_id) -> Optional[dict]:
    return await _fetchone("SELECT * FROM firms WHERE id = ?", (firm_id,))


async def get_approved_firms() -> List[dict]:
    return await _fetchall("SELECT * FROM firms WHERE is_approved = 1 AND is_active = 1 ORDER BY id DESC")


async def get_firm_public_products(firm_id: int) -> List[dict]:
    return await _fetchall(
        """
        SELECT id, name, description, image_url, unit, min_qty, price
        FROM products
        WHERE firm_id = ? AND is_active = 1
        ORDER BY id DESC
        """,
        (firm_id,),
    )


async def get_pending_firms() -> List[dict]:
    return await _fetchall("SELECT * FROM firms WHERE is_approved = 0 AND is_active = 1 ORDER BY id DESC")


async def approve_firm(firm_id):
    firm = await get_firm_by_id(firm_id)
    if not firm:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("UPDATE firms SET is_approved = 1 WHERE id = ?", (firm_id,))
        await db.execute("UPDATE users SET role = 'firm' WHERE id = ?", (firm["user_id"],))
        await db.commit()


async def reject_firm(firm_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("UPDATE firms SET is_active = 0 WHERE id = ?", (firm_id,))
        await db.commit()


async def add_product(firm_id, name, description, unit, min_qty, price, image_url=None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "INSERT INTO products (firm_id, name, description, image_url, unit, min_qty, price) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (firm_id, name, description, image_url, unit, min_qty, price),
        )
        await db.commit()
        return cur.lastrowid


async def ensure_product(firm_id, name, description, unit, min_qty, price, image_url=None) -> int:
    product = await _fetchone(
        "SELECT * FROM products WHERE firm_id = ? AND name = ?",
        (firm_id, name),
    )
    if product:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                UPDATE products
                SET description = ?, image_url = ?, unit = ?, min_qty = ?, price = ?, is_active = 1
                WHERE id = ?
                """,
                (description, image_url, unit, min_qty, price, product["id"]),
            )
            await db.commit()
        return product["id"]
    return await add_product(firm_id, name, description, unit, min_qty, price, image_url=image_url)


async def get_products_count() -> int:
    row = await _fetchone("SELECT COUNT(*) as c FROM products")
    return row["c"]


async def get_products_by_firm(firm_id, active_only=True) -> List[dict]:
    if active_only:
        return await _fetchall("SELECT * FROM products WHERE firm_id = ? AND is_active = 1 ORDER BY id DESC", (firm_id,))
    return await _fetchall("SELECT * FROM products WHERE firm_id = ? ORDER BY id DESC", (firm_id,))


async def get_product_by_id(product_id) -> Optional[dict]:
    return await _fetchone("SELECT * FROM products WHERE id = ?", (product_id,))


async def toggle_product(product_id):
    product = await get_product_by_id(product_id)
    if not product:
        return
    new_value = 0 if product["is_active"] else 1
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("UPDATE products SET is_active = ? WHERE id = ?", (new_value, product_id))
        await db.commit()


async def delete_product(product_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await db.commit()


async def create_order(store_id, firm_id, store_note, items: List[dict]) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "INSERT INTO orders (store_id, firm_id, store_note) VALUES (?, ?, ?)",
            (store_id, firm_id, store_note),
        )
        order_id = cur.lastrowid
        for item in items:
            await db.execute(
                """
                INSERT INTO order_items (order_id, product_id, quantity, product_name, unit)
                VALUES (?, ?, ?, ?, ?)
                """,
                (order_id, item["product_id"], item["qty"], item["name"], item["unit"]),
            )
        await db.commit()
        return order_id


async def get_order_by_id(order_id) -> Optional[dict]:
    return await _fetchone("SELECT * FROM orders WHERE id = ?", (order_id,))


async def get_order_items(order_id) -> List[dict]:
    return await _fetchall("SELECT * FROM order_items WHERE order_id = ?", (order_id,))


async def confirm_order(order_id, delivery_date, agent_note=""):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            """
            UPDATE orders
            SET status = 'confirmed', delivery_date = ?, agent_note = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (delivery_date, agent_note, order_id),
        )
        await db.commit()


async def reject_order(order_id, agent_note):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            """
            UPDATE orders
            SET status = 'rejected', agent_note = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (agent_note, order_id),
        )
        await db.commit()


async def mark_delivered(order_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            "UPDATE orders SET status = 'delivered', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (order_id,),
        )
        await db.commit()


async def get_orders_for_store(store_id, limit=20) -> List[dict]:
    return await _fetchall(
        "SELECT * FROM orders WHERE store_id = ? ORDER BY id DESC LIMIT ?",
        (store_id, limit),
    )


async def get_orders_for_firm(firm_id, status=None, limit=30) -> List[dict]:
    if status:
        return await _fetchall(
            "SELECT * FROM orders WHERE firm_id = ? AND status = ? ORDER BY id DESC LIMIT ?",
            (firm_id, status, limit),
        )
    return await _fetchall("SELECT * FROM orders WHERE firm_id = ? ORDER BY id DESC LIMIT ?", (firm_id, limit))


async def get_firm_stats(firm_id) -> dict:
    total = await _fetchone("SELECT COUNT(*) as c FROM orders WHERE firm_id = ?", (firm_id,))
    new = await _fetchone("SELECT COUNT(*) as c FROM orders WHERE firm_id = ? AND status = 'new'", (firm_id,))
    confirmed = await _fetchone(
        "SELECT COUNT(*) as c FROM orders WHERE firm_id = ? AND status = 'confirmed'",
        (firm_id,),
    )
    delivered = await _fetchone(
        "SELECT COUNT(*) as c FROM orders WHERE firm_id = ? AND status = 'delivered'",
        (firm_id,),
    )
    return {"new": new["c"], "confirmed": confirmed["c"], "delivered": delivered["c"], "total": total["c"]}
