# DokonAgent

DokonAgent — Telegram bot va Mini App asosidagi B2B zakaz tizimi. Unda 3 rol bor:

- `store` — dokonlar zakaz yaratadi
- `firm` — ta'minotchilar mahsulot yuritadi va zakazlarni qabul/rad qiladi
- `admin` — firmalarni tasdiqlaydi va statistikani ko'radi

## Asosiy imkoniyatlar

- Telegram bot orqali dokon va firma ro'yxatdan o'tishi
- Admin tomonidan firma tasdiqlash oqimi
- Dokonlar uchun bot ichida zakaz yaratish
- Telegram Mini App orqali qulay katalog va savat
- Firma uchun mahsulot boshqaruvi
- Mahsulotga tavsif, rasm URL yoki Telegram orqali foto biriktirish
- Demo seed ma'lumotlari bilan tez ishga tushirish

## Lokal ishga tushirish

1. `cp .env.example .env`
2. `.env` ichida `BOT_TOKEN`, `ADMIN_IDS`, `WEBAPP_URL` ni to'ldiring
3. Python virtual environment yarating va dependency o'rnating:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. Botni ishga tushiring:

```bash
python bot.py
```

Bot birinchi startda:

- SQLite bazani yaratadi
- migratsiyalarni bajaradi
- demo firmalar va demo mahsulotlarni seed qiladi

## Muhit o'zgaruvchilari

- `BOT_TOKEN` — Telegram bot token
- `ADMIN_IDS` — admin Telegram ID lar ro'yxati, masalan `[123456789]`
- `WEBAPP_URL` — Railway yoki boshqa domeningiz
- `WEB_HOST` — default `0.0.0.0`
- `WEB_PORT` — default `8080`
- `DB_PATH` — default `zakaz_bot.db`

## Mahsulot rasmi qo'shish

Firma mahsulot qo'shganda ikki yo'l bor:

1. Step-by-step rejimda:
   tavsifdan keyin rasm URL yuboradi, yoki botga foto jo'natadi, yoki o'tkazib yuboradi.
2. Tez qo'shish rejimida:

```text
nom; narx; birlik; min_miqdor; izoh; rasm_url
```

Masalan:

```text
Cola 1L; 12000; dona; 5; sovutilgan; https://site.uz/cola.jpg
```

## Railway deploy

Repo ichida Railway uchun kerakli fayllar bor:

- `Procfile`
- `nixpacks.toml`
- `runtime.txt`

Deploy tartibi:

1. GitHub ga push qiling
2. Railway da `New Project` -> `Deploy from GitHub Repo`
3. Service root sifatida shu papkani tanlang
4. `BOT_TOKEN`, `ADMIN_IDS`, `WEBAPP_URL` env larini qo'shing
5. Deploy bo'lgach Railway domenini `WEBAPP_URL` ga yozing

## Muhim eslatma

Telegram orqali yuborilgan mahsulot rasmlari `static/uploads/products/` ga saqlanadi.
Agar Railway da bu rasmlar redeploydan keyin ham saqlansin desangiz, `static/uploads` uchun persistent volume ulash tavsiya qilinadi. Aks holda tashqi image URL ishlatish eng barqaror yo'l bo'ladi.</content>
<parameter name="filePath">/home/kali/Desktop/dokon agent/dokonagent/README.md