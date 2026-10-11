import aiosqlite
import logging
import os
import json

# Railway volume mount path (persistent storage)
VOLUME_PATH = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "")
DB_NAME = os.path.join(VOLUME_PATH, "database.sqlite") if VOLUME_PATH else "database.sqlite"

logger = logging.getLogger("database")

async def init_db():
    """Ma'lumotlar bazasi va jadvallarni initsializatsiya qilish (CRM & Aksessuarlar)"""
    async with aiosqlite.connect(DB_NAME) as db:
        # 1. Aksessuarlar (Products) jadvali
        await db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price INTEGER NOT NULL,
                cost_price INTEGER DEFAULT 0,
                old_price INTEGER DEFAULT 0,
                stock INTEGER DEFAULT 10,
                icon TEXT DEFAULT '📱',
                description TEXT,
                options_json TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 2. Buyurtmalar (CRM Orders) jadvali
        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_name TEXT NOT NULL,
                user_phone TEXT NOT NULL,
                address TEXT,
                items_json TEXT,
                total_amount INTEGER DEFAULT 0,
                status TEXT DEFAULT 'new',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 3. Mijozlar bazasi (CRM Customers)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                orders_count INTEGER DEFAULT 1,
                total_spent INTEGER DEFAULT 0,
                last_order_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        ''')

        # 4. Standart xizmatlar jadvali (moslik uchun)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price TEXT,
                image_url TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        ''')

        # 5. Aloqa ma'lumotlari
        await db.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                value TEXT NOT NULL
            )
        ''')

        await db.commit()

        # Dastlabki Aksessuarlar to'plamini tekshirish va kiritish
        await seed_initial_accessories(db)

    logging.info("Ma'lumotlar bazasi va CRM jadvallari tayyorlandi.")

async def seed_initial_accessories(db):
    """Do'konga boshlang'ich premium aksessuarlarni joylashtirish"""
    async with db.execute("SELECT COUNT(*) FROM products") as cursor:
        count = (await cursor.fetchone())[0]

    if count == 0:
        accessories = [
            (
                "MagSafe Silk Silicone Case (iPhone 13 - 16 Pro Max)",
                "cases",
                95000, 35000, 140000, 30, "📱",
                "Yumshoq ipak sirtli, kuchli MagSafe magnitli original darajadagi g'ilof. Barmoq izi qolmaydi.",
                json.dumps(["iPhone 13", "iPhone 14 Pro", "iPhone 15 Pro", "iPhone 15 Pro Max", "iPhone 16 Pro", "iPhone 16 Pro Max"])
            ),
            (
                "Luxury Leather Case MagSafe (Titan tugmali)",
                "cases",
                145000, 55000, 210000, 20, "🧥",
                "Tabiiy baxmal charm, metall tugmalar va mikrofibra ichki qatlam. Premium darajadagi himoya.",
                json.dumps(["Qora Charm", "Jigarrang Charm", "To'q Ko'k Charm"])
            ),
            (
                "Remax 9D Crystal Himoya Oynasi (O'rnatish ramkasi bilan)",
                "glasses",
                45000, 12000, 70000, 50, "🛡",
                "9H qattiqlik, tirnalishga chidamli va o'rnatish uchun maxsus avtomatik qolip bilan.",
                json.dumps(["Shaffof 9D", "Anti-Spy (Maxfiy)", "Matte (O'yin uchun)"])
            ),
            (
                "20W Type-C Original Fast Charger Adapter",
                "chargers",
                85000, 28000, 125000, 45, "⚡",
                "30 daqiqada 50% gacha tezkor quvvatlash. Qizib ketishdan himoyalovchi smart chip.",
                json.dumps(["Yevro vilka (Standart)", "AQSH vilka"])
            ),
            (
                "35W Dual Type-C Tezkor Quvvatlagich (2 ta qurilma)",
                "chargers",
                135000, 50000, 190000, 25, "🔌",
                "Bir vaqtning o'zida telefon va soat yoki noutbukni tezkor quvvatlash imkoniyati.",
                json.dumps(["Oq", "Qora"])
            ),
            (
                "10 000 mAh Magnetic MagSafe Power Bank",
                "powerbanks",
                195000, 85000, 260000, 18, "🔋",
                "Simsiz 15W MagSafe magnit quvvatlash + 20W Type-C simli port. Yengil va ixcham korpus.",
                json.dumps(["Oq Titan", "Qora Mat", "Binafsharang"])
            ),
            (
                "AirPods Pro 2 (Active Noise Cancelling, Type-C)",
                "audio",
                260000, 130000, 380000, 15, "🎧",
                "Kuchli shovqinni so'ndirish (ANC), shaffof rejim va kristaldek toza bas ovoz.",
                json.dumps(["Oq Original komplekt"])
            ),
            (
                "Apple Watch Alpine & Ocean Tasmalar (Ultra / 45-49mm)",
                "straps",
                55000, 18000, 85000, 40, "⌚",
                "Titan qisqichli, nafas oluvchi va suvga chidamli mustahkam sport tasmalar.",
                json.dumps(["To'q Sariq Alpine", "Qora Ocean", "Yashil Trail", "Kumush Milanese"])
            ),
            (
                "MagSafe Avtomobil Derjateli Simsiz Zaryadka 15W",
                "car",
                125000, 48000, 180000, 22, "🚗",
                "Deflektorga mustahkam o'rnatiladi, 360 daraja aylanadi va telefonni kuchli magnitda ushlab turadi.",
                json.dumps(["Qora Mat"])
            )
        ]

        await db.executemany('''
            INSERT INTO products (name, category, price, cost_price, old_price, stock, icon, description, options_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', accessories)
        await db.commit()
        logging.info("9 ta boshlang'ich aksessuarlar bazaga kiritildi.")

# ==============================================================================
# AKSESSUARLAR (PRODUCTS) CRUD
# ==============================================================================

async def get_products(category=None, active_only=True):
    async with aiosqlite.connect(DB_NAME) as db:
        query = "SELECT * FROM products WHERE 1=1"
        params = []
        if active_only:
            query += " AND is_active = 1"
        if category and category != 'all':
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY id DESC"

        async with db.execute(query, params) as cursor:
            columns = [c[0] for c in cursor.description]
            return [dict(zip(columns, row)) for row in await cursor.fetchall()]

async def get_product(product_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM products WHERE id = ?", (product_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                columns = [c[0] for c in cursor.description]
                return dict(zip(columns, row))
            return None

async def add_product(name, category, price, cost_price=0, old_price=0, stock=10, icon="📱", description="", options=None):
    async with aiosqlite.connect(DB_NAME) as db:
        options_json = json.dumps(options or [])
        cursor = await db.execute('''
            INSERT INTO products (name, category, price, cost_price, old_price, stock, icon, description, options_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, category, price, cost_price, old_price, stock, icon, description, options_json))
        await db.commit()
        return cursor.lastrowid

async def update_product(product_id, **kwargs):
    if not kwargs:
        return
    async with aiosqlite.connect(DB_NAME) as db:
        cols = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values())
        values.append(product_id)
        await db.execute(f"UPDATE products SET {cols} WHERE id = ?", values)
        await db.commit()

async def delete_product(product_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await db.commit()

# ==============================================================================
# CRM BUYURTMALAR VA MIJOZLAR (ORDERS & CRM)
# ==============================================================================

async def create_crm_order(user_id, user_name, user_phone, address, items, total_amount, notes=""):
    """Yangi buyurtma yaratish va CRM mijozini yangilash"""
    async with aiosqlite.connect(DB_NAME) as db:
        items_json = json.dumps(items)
        cursor = await db.execute('''
            INSERT INTO orders (user_id, user_name, user_phone, address, items_json, total_amount, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, 'new', ?)
        ''', (user_id, user_name, user_phone, address, items_json, total_amount, notes))
        order_id = cursor.lastrowid

        # Ombor qoldig'ini kamaytirish (stock update)
        for item in items:
            p_id = item.get("id")
            qty = item.get("qty", 1)
            if p_id:
                await db.execute("UPDATE products SET stock = MAX(0, stock - ?) WHERE id = ?", (qty, p_id))

        # Mijozlar bazasini (CRM) yangilash yoki qo'shish
        if user_id:
            await db.execute('''
                INSERT INTO customers (user_id, name, phone, orders_count, total_spent, last_order_at)
                VALUES (?, ?, ?, 1, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    name = excluded.name,
                    phone = excluded.phone,
                    orders_count = orders_count + 1,
                    total_spent = total_spent + excluded.total_spent,
                    last_order_at = CURRENT_TIMESTAMP
            ''', (user_id, user_name, user_phone, total_amount))

        await db.commit()
        return order_id

async def get_crm_orders(status=None):
    async with aiosqlite.connect(DB_NAME) as db:
        query = "SELECT * FROM orders"
        params = []
        if status and status != 'all':
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY id DESC"

        async with db.execute(query, params) as cursor:
            columns = [c[0] for c in cursor.description]
            orders = [dict(zip(columns, row)) for row in await cursor.fetchall()]
            for o in orders:
                if o.get("items_json"):
                    try:
                        o["items"] = json.loads(o["items_json"])
                    except Exception:
                        o["items"] = []
                else:
                    o["items"] = []
            return orders

async def update_order_status(order_id, status, notes=None):
    async with aiosqlite.connect(DB_NAME) as db:
        if notes:
            await db.execute("UPDATE orders SET status = ?, notes = ? WHERE id = ?", (status, notes, order_id))
        else:
            await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        await db.commit()

async def get_crm_stats():
    """CRM Analitika va Statistika ko'rsatkichlari"""
    async with aiosqlite.connect(DB_NAME) as db:
        # Jami tushum va buyurtmalar
        async with db.execute('''
            SELECT 
                COUNT(*) as total_orders,
                COALESCE(SUM(total_amount), 0) as total_revenue,
                SUM(CASE WHEN status = 'new' THEN 1 ELSE 0 END) as new_orders,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_orders
            FROM orders
        ''') as cursor:
            row = await cursor.fetchone()
            total_orders, total_revenue, new_orders, completed_orders = row

        # Jami mijozlar soni
        async with db.execute("SELECT COUNT(*) FROM customers") as cursor:
            total_customers = (await cursor.fetchone())[0]

        # Ombordagi tovarlar soni va kam qolganlari (stock < 5)
        async with db.execute("SELECT COUNT(*), SUM(CASE WHEN stock <= 5 THEN 1 ELSE 0 END) FROM products WHERE is_active = 1") as cursor:
            p_row = await cursor.fetchone()
            total_products, low_stock = p_row

        return {
            "total_orders": total_orders or 0,
            "total_revenue": total_revenue or 0,
            "new_orders": new_orders or 0,
            "completed_orders": completed_orders or 0,
            "total_customers": total_customers or 0,
            "total_products": total_products or 0,
            "low_stock_count": low_stock or 0
        }

async def get_customers():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM customers ORDER BY total_spent DESC") as cursor:
            columns = [c[0] for c in cursor.description]
            return [dict(zip(columns, row)) for row in await cursor.fetchall()]

# ==============================================================================
# MOSLIK UCHUN QO'SHIMCHA FUNKSIYALAR (SERVICES & CONTACTS)
# ==============================================================================

async def get_services(active_only=True):
    return await get_products(active_only=active_only)

async def get_service(service_id):
    return await get_product(service_id)

async def add_order(user_id, user_name, user_phone, service_id):
    product = await get_product(service_id)
    price = product['price'] if product else 0
    items = [{"id": service_id, "name": product['name'] if product else "Aksessuar", "qty": 1, "price": f"{price:,} so'm"}]
    return await create_crm_order(user_id, user_name, user_phone, "", items, price)

async def get_orders(status=None):
    return await get_crm_orders(status=status)
