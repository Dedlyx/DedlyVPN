import aiosqlite
import time
from datetime import datetime

DB_NAME = "vpn_bot_v2.db" # <--- ИЗМЕНЕНО ИМЯ БАЗЫ, ЧТОБЫ СТАРАЯ НЕ МЕШАЛА

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance REAL DEFAULT 0,
                sub_end_ts INTEGER DEFAULT 0,
                vpn_link TEXT,
                devices INTEGER DEFAULT 2,
                traffic_left REAL DEFAULT 100.0,
                referrer_id INTEGER DEFAULT NULL,
                ref_count INTEGER DEFAULT 0,
                trial_used INTEGER DEFAULT 0,
                reg_date TEXT,
                notified_3d INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                days INTEGER,
                amount REAL,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                vpn_link TEXT,
                admin_acc TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                comment TEXT,
                file_id TEXT,
                status TEXT DEFAULT 'pending'
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        defaults = {
            'bank_card': '0000 0000 0000 0000',
            'bank_name': 'Т-Банк',
            'price_28': '299', 'price_14': '159', 'price_5': '69', 'price_trial': '22',
            'stars_28': '299', 'stars_14': '159', 'stars_5': '69', 'stars_trial': '22',
            'ref_percent': '15'
        }
        for k, v in defaults.items():
            await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
            
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def create_user(user_id, username, referrer_id=None):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)) as cursor:
            if await cursor.fetchone(): return
        reg_date = datetime.now().strftime("%d.%m.%Y")
        await db.execute(
            "INSERT INTO users (user_id, username, referrer_id, reg_date) VALUES (?, ?, ?, ?)",
            (user_id, username, referrer_id, reg_date)
        )
        if referrer_id:
            await db.execute("UPDATE users SET ref_count = ref_count + 1 WHERE user_id = ?", (referrer_id,))
        await db.commit()

async def update_balance(user_id, amount):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        if amount > 0:
            async with db.execute("SELECT referrer_id FROM users WHERE user_id = ?", (user_id,)) as c:
                row = await c.fetchone()
                if row and row[0]:
                    ref_id = row[0]
                    async with db.execute("SELECT value FROM settings WHERE key = 'ref_percent'") as c2:
                        p_row = await c2.fetchone()
                        percent = float(p_row[0]) if p_row else 15.0
                    bonus = round(amount * (percent / 100), 2)
                    if bonus > 0:
                        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (bonus, ref_id))
        await db.commit()

async def extend_sub(user_id, days):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT sub_end_ts FROM users WHERE user_id = ?", (user_id,)) as c:
            row = await c.fetchone()
            current_ts = row[0] if row[0] else 0
            
        now_ts = int(time.time())
        base_ts = current_ts if current_ts > now_ts else now_ts
        new_ts = base_ts + (days * 86400)
        
        await db.execute("UPDATE users SET sub_end_ts = ?, notified_3d = 0 WHERE user_id = ?", (new_ts, user_id))
        await db.commit()

async def use_trial(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET trial_used = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM users") as c:
            return [row[0] for row in await c.fetchall()]

async def get_expiring_users():
    async with aiosqlite.connect(DB_NAME) as db:
        now = int(time.time())
        three_days = 3 * 86400
        min_time = now + int(three_days * 0.8)
        max_time = now + int(three_days * 1.2)
        
        async with db.execute(
            "SELECT user_id, sub_end_ts FROM users WHERE sub_end_ts > ? AND sub_end_ts < ? AND notified_3d = 0", 
            (min_time, max_time)
        ) as c:
            return await c.fetchall()

async def mark_notified(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET notified_3d = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def set_setting(key, value):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        await db.commit()

async def get_setting(key):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def create_purchase(user_id, username, days, amount):
    async with aiosqlite.connect(DB_NAME) as db:
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        cursor = await db.execute("INSERT INTO purchases (user_id, username, days, amount, created_at) VALUES (?, ?, ?, ?, ?)", (user_id, username, days, amount, now))
        await db.commit()
        return cursor.lastrowid

async def get_purchase(purchase_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM purchases WHERE id = ?", (purchase_id,)) as c:
            return await c.fetchone()

async def get_pending_purchases():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM purchases WHERE status = 'pending' ORDER BY id ASC") as c:
            return await c.fetchall()

async def approve_purchase(purchase_id, user_id, days, vpn_link, admin_acc):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE purchases SET status = 'completed', vpn_link = ?, admin_acc = ? WHERE id = ?", (vpn_link, admin_acc, purchase_id))
        await db.execute("UPDATE users SET vpn_link = ? WHERE user_id = ?", (vpn_link, user_id))
        await db.commit()
    await extend_sub(user_id, days)

async def reject_purchase(purchase_id, user_id, amount):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE purchases SET status = 'rejected' WHERE id = ?", (purchase_id,))
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

async def get_all_purchases(limit=10):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM purchases ORDER BY id DESC LIMIT ?", (limit,)) as c:
            return await c.fetchall()

async def add_check(user_id, amount, comment, file_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("INSERT INTO checks (user_id, amount, comment, file_id) VALUES (?, ?, ?, ?)", (user_id, amount, comment, file_id))
        await db.commit()
        return cursor.lastrowid

async def get_check(check_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM checks WHERE id = ?", (check_id,)) as c:
            return await c.fetchone()

async def get_pending_checks():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM checks WHERE status = 'pending' ORDER BY id ASC") as c:
            return await c.fetchall()

async def set_check_status(check_id, status):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE checks SET status = ? WHERE id = ?", (status, check_id))
        await db.commit()

async def get_stats():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            total_users = (await c.fetchone())[0]
        
        now_ts = int(time.time())
        async with db.execute("SELECT COUNT(*) FROM users WHERE sub_end_ts > ?", (now_ts,)) as c:
            active_subs = (await c.fetchone())[0]
            
        three_days = now_ts + (3 * 86400)
        async with db.execute("SELECT COUNT(*) FROM users WHERE sub_end_ts > ? AND sub_end_ts < ?", (now_ts, three_days)) as c:
            expiring_subs = (await c.fetchone())[0]
        
        async with db.execute("SELECT SUM(amount) FROM checks WHERE status = 'approved'") as c:
            turnover = (await c.fetchone())[0] or 0.0
        
        async with db.execute("SELECT COUNT(*) FROM purchases WHERE status = 'completed'") as c:
            subs_sold = (await c.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM checks WHERE status = 'pending'") as c:
            pending_checks = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM purchases WHERE status = 'pending'") as c:
            pending_buys = (await c.fetchone())[0]
            
        return total_users, active_subs, expiring_subs, pending_checks, pending_buys, turnover, subs_sold