import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from database import db
from handlers import start, services, orders, portfolio, contacts, admin

load_dotenv()

async def main():
    logging.basicConfig(level=logging.INFO)
    
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logging.error("BOT_TOKEN topilmadi. .env faylini tekshiring.")
        return
        
    await db.init_db()

    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(services.router)
    dp.include_router(orders.router)
    dp.include_router(portfolio.router)
    dp.include_router(contacts.router)
    dp.include_router(admin.router)

    logging.info("Bot ishga tushmoqda...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
