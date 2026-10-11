import asyncio
import logging
import os
from dotenv import load_dotenv
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import MenuButtonWebApp, WebAppInfo

from database import db
from handlers import start, services, orders, portfolio, contacts, admin
from webapp.api import init_app

load_dotenv()

async def start_web_server():
    """Aiohttp veb-serverini ishga tushirish (Mini App va uning API'si)"""
    port = int(os.getenv("PORT", 8080))
    app = await init_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"🚀 Telegram Mini App serveri http://0.0.0.0:{port} manzilida ishga tushdi.")
    return runner

async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logging.error("BOT_TOKEN topilmadi. .env faylini tekshiring.")
        return
        
    await db.init_db()

    # Veb-serverni ishga tushirish (Mini Appni Railway portida taqdim etadi)
    runner = await start_web_server()

    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(services.router)
    dp.include_router(orders.router)
    dp.include_router(portfolio.router)
    dp.include_router(contacts.router)
    dp.include_router(admin.router)

    # Agar WEBAPP_URL bo'lsa, Telegram pastki chat menyusiga Mini App tugmasini biriktirish
    webapp_url = os.getenv("WEBAPP_URL")
    if webapp_url:
        webapp_url = webapp_url.strip()
        if not webapp_url.startswith("https://") and not webapp_url.startswith("http://"):
            webapp_url = f"https://{webapp_url}"
        try:
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="📱 Mini App",
                    web_app=WebAppInfo(url=webapp_url)
                )
            )
            logging.info(f"Bot menyu tugmasi Mini App ga sozlandi: {webapp_url}")
        except Exception as e:
            logging.warning(f"Menyu tugmasini sozlashda xatolik: {e}")

    logging.info("Bot ishga tushmoqda...")
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
