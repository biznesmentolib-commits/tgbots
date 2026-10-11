import aiosqlite
import logging
import os

# Railway volume mount path (persistent storage)
# Lokal ishlatganda oddiy "database.sqlite" ishlatiladi
VOLUME_PATH = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "")
DB_NAME = os.path.join(VOLUME_PATH, "database.sqlite") if VOLUME_PATH else "database.sqlite"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
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
        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_name TEXT NOT NULL,
                user_phone TEXT NOT NULL,
                service_id INTEGER NOT NULL,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (service_id) REFERENCES services (id)
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                image_file_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                value TEXT NOT NULL
            )
        ''')
        await db.commit()
        logging.info("Ma'lumotlar bazasi initsializatsiya qilindi.")

async def add_service(name, description, price, image_url=None):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO services (name, description, price, image_url) VALUES (?, ?, ?, ?)",
            (name, description, price, image_url)
        )
        await db.commit()

async def get_services(active_only=True):
    async with aiosqlite.connect(DB_NAME) as db:
        query = "SELECT * FROM services"
        if active_only:
            query += " WHERE is_active = 1"
        async with db.execute(query) as cursor:
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in await cursor.fetchall()]

async def get_service(service_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM services WHERE id = ?", (service_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                return dict(zip(columns, row))
            return None

async def delete_service(service_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM services WHERE id = ?", (service_id,))
        await db.commit()

async def update_service(service_id, **kwargs):
    if not kwargs:
        return
    async with aiosqlite.connect(DB_NAME) as db:
        columns = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values())
        values.append(service_id)
        await db.execute(f"UPDATE services SET {columns} WHERE id = ?", values)
        await db.commit()

async def add_order(user_id, user_name, user_phone, service_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO orders (user_id, user_name, user_phone, service_id) VALUES (?, ?, ?, ?)",
            (user_id, user_name, user_phone, service_id)
        )
        await db.commit()
        return cursor.lastrowid

async def get_orders(status=None):
    async with aiosqlite.connect(DB_NAME) as db:
        query = "SELECT orders.*, services.name as service_name FROM orders JOIN services ON orders.service_id = services.id"
        params = ()
        if status:
            query += " WHERE orders.status = ?"
            params = (status,)
        query += " ORDER BY orders.created_at DESC"
        async with db.execute(query, params) as cursor:
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in await cursor.fetchall()]

async def update_order_status(order_id, status):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        await db.commit()

async def add_portfolio(title, description, image_file_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO portfolio (title, description, image_file_id) VALUES (?, ?, ?)",
            (title, description, image_file_id)
        )
        await db.commit()

async def get_portfolio():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM portfolio ORDER BY created_at DESC") as cursor:
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in await cursor.fetchall()]

async def get_portfolio_item(item_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM portfolio WHERE id = ?", (item_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                return dict(zip(columns, row))
            return None

async def delete_portfolio(item_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM portfolio WHERE id = ?", (item_id,))
        await db.commit()

async def add_contact(contact_type, value):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO contacts (type, value) VALUES (?, ?)",
            (contact_type, value)
        )
        await db.commit()

async def get_contacts():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM contacts") as cursor:
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in await cursor.fetchall()]

async def delete_contact(contact_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        await db.commit()
