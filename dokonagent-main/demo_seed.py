from database import ensure_firm, ensure_product, ensure_store, ensure_user, get_products_count


DEMO_FIRMS = [
    {
        "telegram_id": 710001001,
        "user_name": "Parfyum Farg'ona Optom",
        "firm_name": "Parfyum Farg'ona Optom",
        "inn": "309900101",
        "address": "Farg'ona, Gul Bozor",
        "phone": "+998901110011",
        "products": [
            {
                "name": "Amber Oud 50ml",
                "description": "Premium sharqona hid. Do'kon vitrinasi uchun ko'p so'raladigan aromat.",
                "unit": "dona",
                "min_qty": 3,
                "price": 89000,
                "image_url": "/static/demo/amber-oud.svg",
            },
            {
                "name": "Velvet Bloom Body Mist",
                "description": "Ayollar uchun yengil body mist, kundalik savdo uchun mos demo mahsulot.",
                "unit": "dona",
                "min_qty": 5,
                "price": 47000,
                "image_url": "/static/demo/velvet-bloom.svg",
            },
        ],
    },
    {
        "telegram_id": 710001002,
        "user_name": "Fergana 1000 Melochey",
        "firm_name": "Fergana 1000 Melochey",
        "inn": "309900202",
        "address": "Farg'ona, Markaziy bozor",
        "phone": "+998901110022",
        "products": [
            {
                "name": "Bag Master 120L",
                "description": "Qalin chiqindi paketlari, 10 dona. Xo'jalik do'konlari uchun tez aylanadigan tovar.",
                "unit": "korobka",
                "min_qty": 1,
                "price": 32000,
                "image_url": "/static/demo/bag-master.svg",
            },
            {
                "name": "Microfiber Pro 3-set",
                "description": "Uy va vitrinalar uchun yumshoq mikrofiber salfetka to'plami.",
                "unit": "dona",
                "min_qty": 4,
                "price": 18000,
                "image_url": "/static/demo/microfiber-pro.svg",
            },
        ],
    },
    {
        "telegram_id": 710001003,
        "user_name": "Avto Aksessuary Farg'ona",
        "firm_name": "Avto Aksessuary Farg'ona",
        "inn": "309900303",
        "address": "Farg'ona, Avto bozor",
        "phone": "+998901110033",
        "products": [
            {
                "name": "Magnetic Phone Holder",
                "description": "Panelga mahkam o'rnatiladigan magnit ushlagich. Avto aksessuar demo katalogi uchun.",
                "unit": "dona",
                "min_qty": 2,
                "price": 39000,
                "image_url": "/static/demo/phone-holder.svg",
            },
            {
                "name": "Seat Organizer Plus",
                "description": "Orqa o'rindiq uchun ko'p cho'ntakli organayzer, oilaviy mashinalarda ommabop.",
                "unit": "dona",
                "min_qty": 2,
                "price": 65000,
                "image_url": "/static/demo/seat-organizer.svg",
            },
        ],
    },
]


async def ensure_demo_data(admin_ids: list[int]):
    if await get_products_count():
        return

    for admin_id in admin_ids:
        user_id = await ensure_user(admin_id, "Demo Store Owner", role="admin", phone="+998900000000")
        await ensure_store(
            user_id=user_id,
            telegram_id=admin_id,
            name="Demo Market",
            address="Farg'ona, test filial",
            phone="+998900000000",
        )

    for firm in DEMO_FIRMS:
        user_id = await ensure_user(firm["telegram_id"], firm["user_name"], role="firm", phone=firm["phone"])
        firm_id = await ensure_firm(
            user_id=user_id,
            telegram_id=firm["telegram_id"],
            name=firm["firm_name"],
            inn=firm["inn"],
            address=firm["address"],
            phone=firm["phone"],
            approved=True,
        )
        for product in firm["products"]:
            await ensure_product(
                firm_id=firm_id,
                name=product["name"],
                description=product["description"],
                unit=product["unit"],
                min_qty=product["min_qty"],
                price=product["price"],
                image_url=product["image_url"],
            )
