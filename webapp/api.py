import os
import sys
import logging
from aiohttp import web
from dotenv import load_dotenv

# Parent directoryni import yo'liga qo'shish
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from database import db

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("webapp_api")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_HTML_PATH = os.path.join(CURRENT_DIR, "index.html")

# CORS middleware
@web.middleware
async def cors_middleware(request, handler):
    if request.method == "OPTIONS":
        response = web.Response(status=204)
    else:
        try:
            response = await handler(request)
        except web.HTTPException as ex:
            response = ex

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    return response

async def index_handler(request):
    """Serve index.html"""
    if os.path.exists(INDEX_HTML_PATH):
        return web.FileResponse(INDEX_HTML_PATH)
    return web.Response(text="index.html fayli topilmadi", status=404)

async def get_services_handler(request):
    """GET /api/services"""
    try:
        services = await db.get_services(active_only=True)
        return web.json_response({"status": "success", "data": services})
    except Exception as e:
        logger.error(f"Xizmatlarni olishda xatolik: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def get_portfolio_handler(request):
    """GET /api/portfolio"""
    try:
        portfolio = await db.get_portfolio()
        return web.json_response({"status": "success", "data": portfolio})
    except Exception as e:
        logger.error(f"Portfolioni olishda xatolik: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def get_contacts_handler(request):
    """GET /api/contacts"""
    try:
        contacts = await db.get_contacts()
        return web.json_response({"status": "success", "data": contacts})
    except Exception as e:
        logger.error(f"Aloqalarni olishda xatolik: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def notify_admin_via_bot(order_id, user_name, user_phone, service_name, user_id=0):
    """Adminga bot orqali bildirishnoma yuborish"""
    bot_token = os.getenv("BOT_TOKEN")
    admin_id = os.getenv("ADMIN_ID")
    if not bot_token or not admin_id:
        logger.warning("BOT_TOKEN yoki ADMIN_ID topilmadi, bildirishnoma yuborilmadi.")
        return

    text = (
        f"🆕 <b>Yangi Mini App buyurtmasi!</b> #{order_id}\n\n"
        f"🛠 <b>Xizmat:</b> {service_name}\n"
        f"👤 <b>Mijoz:</b> {user_name}\n"
        f"📞 <b>Telefon:</b> {user_phone}\n"
    )
    if user_id:
        text += f"🆔 <b>Telegram ID:</b> <code>{user_id}</code>\n"
        text += f"🔗 <a href='tg://user?id={user_id}'>Profilga o'tish</a>"

    telegram_api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": admin_id,
        "text": text,
        "parse_mode": "HTML"
    }

    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(telegram_api_url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    logger.info(f"Adminga #{order_id} buyurtma haqida xabar yuborildi.")
                else:
                    err_body = await resp.text()
                    logger.error(f"Telegram API xatosi ({resp.status}): {err_body}")
    except Exception as e:
        logger.error(f"Telegram xabar yuborishda xatolik: {e}")

async def create_order_handler(request):
    """POST /api/orders"""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"status": "error", "message": "Noto'g'ri JSON format"}, status=400)

    user_id = data.get("user_id") or 0
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        user_id = 0

    user_name = str(data.get("user_name", "")).strip()
    user_phone = str(data.get("user_phone", "")).strip()
    service_id = data.get("service_id")

    if not user_name:
        return web.json_response({"status": "error", "message": "Ism kiritilishi shart"}, status=400)
    if not user_phone:
        return web.json_response({"status": "error", "message": "Telefon raqami kiritilishi shart"}, status=400)
    if not service_id:
        return web.json_response({"status": "error", "message": "Xizmat tanlanishi shart"}, status=400)

    try:
        service_id = int(service_id)
    except (ValueError, TypeError):
        return web.json_response({"status": "error", "message": "Noto'g'ri xizmat ID"}, status=400)

    try:
        # Xizmat nomini aniqlash
        service = await db.get_service(service_id)
        service_name = service['name'] if service else f"Xizmat #{service_id}"

        order_id = await db.add_order(
            user_id=user_id,
            user_name=user_name,
            user_phone=user_phone,
            service_id=service_id
        )

        # Adminga xabar yuborish (fondda)
        await notify_admin_via_bot(order_id, user_name, user_phone, service_name, user_id)

        return web.json_response({
            "status": "success",
            "message": "Buyurtmangiz muvaffaqiyatli qabul qilindi!",
            "order_id": order_id
        })
    except Exception as e:
        logger.error(f"Buyurtma yaratishda xatolik: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def init_app():
    await db.init_db()
    app = web.Application(middlewares=[cors_middleware])
    app.router.add_get("/", index_handler)
    app.router.add_get("/api/services", get_services_handler)
    app.router.add_get("/api/portfolio", get_portfolio_handler)
    app.router.add_get("/api/contacts", get_contacts_handler)
    app.router.add_post("/api/orders", create_order_handler)
    return app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Mini App serveri http://0.0.0.0:{port} manzilida ishga tushmoqda...")
    web.run_app(init_app(), host="0.0.0.0", port=port)
