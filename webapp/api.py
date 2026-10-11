import os
import sys
import logging
import json
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

# ==============================================================================
# DO'KON API (PUBLIC STORE ENDPOINTS)
# ==============================================================================

async def get_products_handler(request):
    """GET /api/products — Barcha faol aksessuarlar ro'yxati"""
    try:
        category = request.query.get("category", "all")
        products = await db.get_products(category=category, active_only=True)
        # Parse options_json
        for p in products:
            if p.get("options_json"):
                try:
                    p["options"] = json.loads(p["options_json"])
                except Exception:
                    p["options"] = []
            else:
                p["options"] = []
        return web.json_response({"status": "success", "data": products})
    except Exception as e:
        logger.error(f"Aksessuarlarni olishda xatolik: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def notify_admin_via_bot(order_id, user_name, user_phone, address, items, total_amount, user_id=0):
    """Adminga bot orqali interaktiv tugmalar bilan xabarnoma yuborish"""
    bot_token = os.getenv("BOT_TOKEN")
    admin_id = os.getenv("ADMIN_ID")
    if not bot_token or not admin_id:
        return

    text = (
        f"🛍 <b>Yangi Aksessuar Buyurtmasi!</b> #{order_id}\n\n"
        f"👤 <b>Mijoz:</b> {user_name}\n"
        f"📞 <b>Telefon:</b> <a href='tel:{user_phone}'>{user_phone}</a>\n"
    )
    if address:
        text += f"📍 <b>Manzil / PVZ:</b> {address}\n"

    text += "\n📦 <b>Tarkibi:</b>\n"
    for idx, item in enumerate(items, 1):
        name = item.get("name", "Aksessuar")
        qty = item.get("qty", 1)
        price = item.get("price", "")
        opt = item.get("option", "")
        opt_str = f" ({opt})" if opt else ""
        text += f"{idx}. {name}{opt_str} — {qty} dona ({price})\n"

    text += f"\n💰 <b>Jami to'lov:</b> <b>{total_amount:,} so'm</b>\n"
    if user_id:
        text += f"🆔 <b>Telegram:</b> <a href='tg://user?id={user_id}'>Profilga o'tish</a>"

    # Statusni o'zgartirish uchun inline tugmalar
    inline_keyboard = {
        "inline_keyboard": [
            [
                {"text": "🚗 Kuryerga berish", "callback_data": f"status_shipping_{order_id}"},
                {"text": "✅ Yetkazildi", "callback_data": f"status_completed_{order_id}"}
            ],
            [
                {"text": "❌ Bekor qilish", "callback_data": f"status_cancelled_{order_id}"}
            ]
        ]
    }

    telegram_api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": admin_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": inline_keyboard
    }

    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(telegram_api_url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    logger.info(f"Adminga #{order_id} buyurtma haqida xabar yuborildi.")
    except Exception as e:
        logger.error(f"Telegram xabar yuborishda xatolik: {e}")

async def create_order_handler(request):
    """POST /api/orders — Do'kondan yangi buyurtma yaratish"""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"status": "error", "message": "Noto'g'ri JSON format"}, status=400)

    user_name = str(data.get("user_name", "")).strip()
    user_phone = str(data.get("user_phone", "")).strip()
    address = str(data.get("address", "")).strip()
    items = data.get("items", [])
    user_id = data.get("user_id") or 0

    if not user_name or not user_phone:
        return web.json_response({"status": "error", "message": "Ism va telefon raqami kiritilishi shart"}, status=400)

    if not items:
        return web.json_response({"status": "error", "message": "Savatchada mahsulot topilmadi"}, status=400)

    try:
        user_id = int(user_id)
    except Exception:
        user_id = 0

    # Jami summani hisoblash
    total_amount = 0
    for it in items:
        p_val = it.get("price_raw") or it.get("price") or 0
        if isinstance(p_val, str):
            p_val = int("".join(filter(str.isdigit, p_val)) or 0)
        total_amount += p_val * it.get("qty", 1)

    try:
        order_id = await db.create_crm_order(
            user_id=user_id,
            user_name=user_name,
            user_phone=user_phone,
            address=address,
            items=items,
            total_amount=total_amount,
            notes=data.get("notes", "")
        )

        # Adminga xabar yuborish
        await notify_admin_via_bot(order_id, user_name, user_phone, address, items, total_amount, user_id)

        return web.json_response({
            "status": "success",
            "message": "Buyurtmangiz muvaffaqiyatli qabul qilindi!",
            "order_id": order_id
        })
    except Exception as e:
        logger.error(f"Buyurtma qabul qilishda xatolik: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

# ==============================================================================
# CRM ADMIN PANEL ENDPOINTS
# ==============================================================================

async def crm_stats_handler(request):
    """GET /api/crm/stats — CRM Analitika va Moliya statistikasi"""
    try:
        stats = await db.get_crm_stats()
        admin_id_env = os.getenv("ADMIN_ID", "")
        return web.json_response({
            "status": "success",
            "data": stats,
            "admin_id": admin_id_env
        })
    except Exception as e:
        logger.error(f"CRM stats xatosi: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def crm_orders_handler(request):
    """GET /api/crm/orders — Barcha buyurtmalar ro'yxati"""
    try:
        status = request.query.get("status", "all")
        orders = await db.get_crm_orders(status=status)
        return web.json_response({"status": "success", "data": orders})
    except Exception as e:
        logger.error(f"CRM orders xatosi: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def crm_update_order_status_handler(request):
    """POST /api/crm/orders/status — Buyurtma statusini o'zgartirish"""
    try:
        data = await request.json()
        order_id = int(data.get("order_id"))
        new_status = str(data.get("status"))
        notes = data.get("notes")
        await db.update_order_status(order_id, new_status, notes)
        return web.json_response({"status": "success", "message": "Status yangilandi"})
    except Exception as e:
        logger.error(f"Status yangilashda xato: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def crm_add_product_handler(request):
    """POST /api/crm/products/add — Yangi aksessuar qo'shish"""
    try:
        data = await request.json()
        name = str(data.get("name")).strip()
        category = str(data.get("category", "cases"))
        price = int(data.get("price", 0))
        cost_price = int(data.get("cost_price", 0))
        old_price = int(data.get("old_price", 0))
        stock = int(data.get("stock", 10))
        icon = str(data.get("icon", "📱"))
        desc = str(data.get("description", ""))
        options = data.get("options", [])

        p_id = await db.add_product(
            name=name,
            category=category,
            price=price,
            cost_price=cost_price,
            old_price=old_price,
            stock=stock,
            icon=icon,
            description=desc,
            options=options
        )
        return web.json_response({"status": "success", "product_id": p_id})
    except Exception as e:
        logger.error(f"Mahsulot qo'shishda xato: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def crm_update_product_handler(request):
    """POST /api/crm/products/update — Mahsulot ma'lumotlarini yangilash"""
    try:
        data = await request.json()
        product_id = int(data.get("id"))
        updates = {}
        for k in ["price", "cost_price", "old_price", "stock", "is_active", "name", "description"]:
            if k in data:
                updates[k] = data[k]

        await db.update_product(product_id, **updates)
        return web.json_response({"status": "success", "message": "Mahsulot yangilandi"})
    except Exception as e:
        logger.error(f"Mahsulot yangilashda xato: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def crm_delete_product_handler(request):
    """POST /api/crm/products/delete — Mahsulotni o'chirish"""
    try:
        data = await request.json()
        product_id = int(data.get("id"))
        await db.delete_product(product_id)
        return web.json_response({"status": "success", "message": "Mahsulot o'chirildi"})
    except Exception as e:
        logger.error(f"Mahsulot o'chirishda xato: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def crm_customers_handler(request):
    """GET /api/crm/customers — Barcha mijozlar (CRM Table)"""
    try:
        customers = await db.get_customers()
        return web.json_response({"status": "success", "data": customers})
    except Exception as e:
        logger.error(f"Mijozlarni olishda xato: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

# ==============================================================================
# APP INIT
# ==============================================================================

async def init_app():
    await db.init_db()
    app = web.Application(middlewares=[cors_middleware])
    
    # Static & Public Store
    app.router.add_get("/", index_handler)
    app.router.add_get("/api/products", get_products_handler)
    app.router.add_get("/api/services", get_products_handler) # backward compatibility
    app.router.add_post("/api/orders", create_order_handler)
    
    # CRM Endpoints
    app.router.add_get("/api/crm/stats", crm_stats_handler)
    app.router.add_get("/api/crm/orders", crm_orders_handler)
    app.router.add_post("/api/crm/orders/status", crm_update_order_status_handler)
    app.router.add_post("/api/crm/products/add", crm_add_product_handler)
    app.router.add_post("/api/crm/products/update", crm_update_product_handler)
    app.router.add_post("/api/crm/products/delete", crm_delete_product_handler)
    app.router.add_get("/api/crm/customers", crm_customers_handler)

    return app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Server http://0.0.0.0:{port} manzilida ishga tushmoqda...")
    web.run_app(init_app(), host="0.0.0.0", port=port)
