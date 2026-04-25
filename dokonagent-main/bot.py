import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database import init_db
from demo_seed import ensure_demo_data
from handlers import admin, agent, products, registration, start, store
from webapp import start_web_server

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")


async def main():
    await init_db()
    await ensure_demo_data(settings.ADMIN_IDS)
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    web_runner = await start_web_server(bot)

    dp.include_router(admin.router)
    dp.include_router(registration.router)
    dp.include_router(products.router)
    dp.include_router(agent.router)
    dp.include_router(store.router)
    dp.include_router(start.router)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await web_runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
