import json
import logging
from pathlib import Path
from datetime import datetime

from aiohttp import web

from config import settings
from database import (
    create_order,
    get_approved_firms,
    get_firm_by_id,
    get_firm_public_products,
    get_product_by_id,
    get_store_by_telegram,
    get_order_items,
)
from keyboards import ikb_order_actions
from utils import validate_date, format_order_summary

logger = logging.getLogger(__name__)


def _mini_app_html() -> str:
    return """<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Zakaz Mini App</title>
  <style>
    :root{--bg:#0f1221;--card:#161a2f;--muted:#9aa4c7;--text:#eef2ff;--accent:#7c5cff;--ok:#22c55e}
    *{box-sizing:border-box} body{margin:0;background:linear-gradient(180deg,#0f1221,#0b1020);font-family:Inter,system-ui,sans-serif;color:var(--text)}
    .wrap{max-width:900px;margin:0 auto;padding:16px}.hero{padding:14px;border-radius:14px;background:#151934;border:1px solid #232953}
    .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;margin-top:12px}
    .card{background:var(--card);border:1px solid #293058;border-radius:12px;padding:12px}
    .thumb{width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:10px;border:1px solid #293058;background:#0c1022;margin-bottom:10px}
    .price{color:#93c5fd}.btn{background:var(--accent);color:white;border:0;padding:8px 10px;border-radius:10px;cursor:pointer}
    .btn2{background:#232953;color:#c7d2fe;border:1px solid #3b4474;padding:8px 10px;border-radius:10px;cursor:pointer}
    .row{display:flex;gap:8px;align-items:center}.muted{color:var(--muted);font-size:13px}
    input,select,textarea{width:100%;background:#0f1430;color:#e5e7eb;border:1px solid #2f3868;border-radius:10px;padding:10px}
    .qty{width:78px}.cart{margin-top:12px}.pill{background:#20315d;color:#bfdbfe;border-radius:999px;padding:3px 8px;font-size:12px}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <div class="row" style="justify-content:space-between"><h3 style="margin:0">🛒 Zakaz Mini App</h3><span id="store" class="pill">store...</span></div>
      <p class="muted">Figma-inspired clean layout: firma tanlang, mahsulot qo'shing, savatdan zakaz yuboring.</p>
    </div>
    <div style="margin-top:12px"><select id="firm"></select></div>
    <div id="products" class="grid"></div>
    <div class="card cart">
      <h4 style="margin:0 0 10px 0">Savat</h4>
      <div id="cart"></div>
      <div class="row" style="margin-top:10px"><input id="date" placeholder="Yetkazish sanasi DD.MM.YYYY" /><input id="note" placeholder="Izoh (ixtiyoriy)" /></div>
      <div class="row" style="margin-top:10px;justify-content:space-between"><span id="total" class="muted">0 ta mahsulot</span><button class="btn" onclick="submitOrder()">Zakaz yuborish</button></div>
    </div>
  </div>
  <script>
    const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
    if (tg) { try { tg.ready(); } catch (_) {} }
    const qs = new URLSearchParams(location.search);
    const tgId = Number(qs.get("tg_id") || (tg && tg.initDataUnsafe && tg.initDataUnsafe.user && tg.initDataUnsafe.user.id) || 0);
    let firms = [], products = [], cart = {};

    function fmt(v){ return (v ?? "-") + "" }
    async function j(url, opts={}){ const r = await fetch(url, opts); if(!r.ok) throw new Error(await r.text()); return r.json(); }
    function renderProducts(){
      const el = document.getElementById("products");
      el.innerHTML = products.map(p => `
        <div class="card">
          ${p.image_url ? `<img class="thumb" src="${p.image_url}" alt="${p.name}" />` : ""}
          <div class="row" style="justify-content:space-between"><b>${p.name}</b><span class="price">${p.price ?? "-"} so'm</span></div>
          <div class="muted">${fmt(p.description)}</div>
          <div class="row" style="margin-top:8px"><span class="pill">min: ${p.min_qty} ${p.unit}</span></div>
          <div class="row" style="margin-top:10px">
            <input class="qty" id="q_${p.id}" type="number" min="${p.min_qty}" step="0.1" value="${p.min_qty}" />
            <button class="btn2" onclick="addToCart(${p.id})">Qo'shish</button>
          </div>
        </div>`).join("");
    }
    function renderCart(){
      const keys = Object.keys(cart);
      document.getElementById("total").innerText = `${keys.length} ta mahsulot`;
      document.getElementById("cart").innerHTML = keys.length ? keys.map(k => {
        const i = cart[k];
        return `<div class="row" style="justify-content:space-between"><span>${i.name} — ${i.qty} ${i.unit}</span><button class="btn2" onclick="delFromCart(${i.product_id})">O'chirish</button></div>`;
      }).join("") : '<span class="muted">Savat bo\\'sh</span>';
    }
    function addToCart(id){
      const p = products.find(x => x.id===id); if(!p) return;
      const qty = Number(document.getElementById(`q_${id}`).value || 0);
      if(qty < Number(p.min_qty)){ alert("Minimal miqdordan kam"); return; }
      cart[id] = { product_id:id, name:p.name, unit:p.unit, qty };
      renderCart();
    }
    function delFromCart(id){ delete cart[id]; renderCart(); }
    async function loadProducts(){
      const firmId = Number(document.getElementById("firm").value || 0);
      products = await j(`/api/products?firm_id=${firmId}`);
      renderProducts();
      cart = {}; renderCart();
    }
    async function submitOrder(){
      const firmId = Number(document.getElementById("firm").value || 0);
      const date = document.getElementById("date").value.trim();
      const note = document.getElementById("note").value.trim();
      if(!Object.keys(cart).length){ alert("Savat bo'sh"); return; }
      const payload = { tg_id: tgId, firm_id: firmId, delivery_date: date, note, items: Object.values(cart) };
      const res = await j("/api/orders", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(payload)});
      alert(`Zakaz #${res.order_id} yuborildi`);
      cart = {}; renderCart();
    }
    async function init(){
      if(!tgId){
        throw new Error("Store aniqlanmadi. Mini App'ni Telegram ichidan bot orqali oching.");
      }
      const s = await j(`/api/store?tg_id=${tgId}`);
      document.getElementById("store").innerText = s.name;
      firms = await j("/api/firms");
      const select = document.getElementById("firm");
      select.innerHTML = firms.map(f => `<option value="${f.id}">${f.name}</option>`).join("");
      if(!firms.length){
        throw new Error("Hozircha production bazada tasdiqlangan firmalar yo'q.");
      }
      select.onchange = loadProducts;
      await loadProducts();
    }
    init().catch(e => {
      const msg = String(e && e.message || e);
      if (msg.includes("Store not found")) {
        alert("Bu Telegram akkaunt production bazada dokon sifatida topilmadi. Bot ichida qayta ro'yxatdan o'ting yoki persistent baza ulang.");
        return;
      }
      alert(msg);
    });
  </script>
</body>
</html>"""


async def miniapp_page(_: web.Request) -> web.Response:
    return web.Response(text=_mini_app_html(), content_type="text/html")


async def api_store(request: web.Request) -> web.Response:
    tg_id = int(request.query.get("tg_id", "0"))
    store = await get_store_by_telegram(tg_id)
    if not store:
        return web.json_response({"error": "Store not found"}, status=404)
    return web.json_response({"id": store["id"], "name": store["name"]})


async def api_firms(_: web.Request) -> web.Response:
    firms = await get_approved_firms()
    return web.json_response([{"id": f["id"], "name": f["name"]} for f in firms])


async def api_products(request: web.Request) -> web.Response:
    firm_id = int(request.query.get("firm_id", "0"))
    products = await get_firm_public_products(firm_id)
    return web.json_response(products)


async def api_create_order(request: web.Request) -> web.Response:
    payload = await request.json()
    tg_id = int(payload.get("tg_id", 0))
    firm_id = int(payload.get("firm_id", 0))
    note = (payload.get("note") or "").strip()
    delivery_date = (payload.get("delivery_date") or "").strip()
    items_raw = payload.get("items") or []

    store = await get_store_by_telegram(tg_id)
    firm = await get_firm_by_id(firm_id)
    if not store or not firm:
        return web.json_response({"error": "Store/Firm not found"}, status=400)
    if delivery_date and not validate_date(delivery_date):
        return web.json_response({"error": "Delivery date format invalid"}, status=400)
    if not items_raw:
        return web.json_response({"error": "Cart is empty"}, status=400)

    items = []
    for row in items_raw:
        product_id = int(row.get("product_id", 0))
        qty = float(row.get("qty", 0))
        product = await get_product_by_id(product_id)
        if not product or product["firm_id"] != firm_id or not product["is_active"]:
            return web.json_response({"error": f"Product {product_id} invalid"}, status=400)
        if qty < float(product["min_qty"]):
            return web.json_response({"error": f"{product['name']} min qty {product['min_qty']}"}, status=400)
        items.append({"product_id": product_id, "name": product["name"], "qty": qty, "unit": product["unit"]})

    full_note = note
    if delivery_date:
        full_note = f"{note}\nYetkazish: {delivery_date}".strip()
    order_id = await create_order(store["id"], firm_id, full_note, items)

    bot = request.app["bot"]
    if bot:
        try:
            order_items = await get_order_items(order_id)
            text = "🔔 <b>Yangi zakaz (Mini App) keldi!</b>\n\n" + format_order_summary(
                store_name=store["name"],
                firm_name=firm["name"],
                items=order_items,
                note=note,
                delivery_date=delivery_date,
                order_id=order_id,
                created_at=datetime.now().strftime("%d.%m.%Y %H:%M"),
            )
            await bot.send_message(firm["telegram_id"], text, reply_markup=ikb_order_actions(order_id))
        except Exception as exc:
            logger.warning("Cannot send mini app order notification: %s", exc)

    return web.json_response({"ok": True, "order_id": order_id})


def build_web_app(bot) -> web.Application:
    app = web.Application()
    app["bot"] = bot
    static_dir = Path(__file__).resolve().parent / "static"
    app.router.add_get("/health", lambda _: web.json_response({"ok": True}))
    app.router.add_get("/miniapp", miniapp_page)
    app.router.add_get("/api/store", api_store)
    app.router.add_get("/api/firms", api_firms)
    app.router.add_get("/api/products", api_products)
    app.router.add_post("/api/orders", api_create_order)
    app.router.add_static("/static/", path=static_dir, name="static")
    return app


async def start_web_server(bot):
    app = build_web_app(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=settings.WEB_HOST, port=settings.WEB_PORT)
    await site.start()
    logger.info("Mini App server started on %s:%s", settings.WEB_HOST, settings.WEB_PORT)
    return runner
