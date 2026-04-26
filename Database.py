import sqlite3
import os
from pathlib import Path

_BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = str(_BASE_DIR / "gameswap.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        reputation REAL DEFAULT 5.0,
        total_sales INTEGER DEFAULT 0,
        total_trades INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0,
        balance REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS listings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT NOT NULL,
        platform TEXT NOT NULL,
        condition TEXT NOT NULL,
        price REAL,
        listing_type TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        image_data TEXT,
        views INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        listing_id INTEGER NOT NULL,
        seller_id INTEGER NOT NULL,
        buyer_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        platform_fee REAL NOT NULL,
        seller_amount REAL NOT NULL,
        transaction_type TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (listing_id) REFERENCES listings(id),
        FOREIGN KEY (seller_id) REFERENCES users(id),
        FOREIGN KEY (buyer_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,
        listing_id INTEGER,
        content TEXT NOT NULL,
        read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES users(id),
        FOREIGN KEY (receiver_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reviewer_id INTEGER NOT NULL,
        reviewed_id INTEGER NOT NULL,
        transaction_id INTEGER NOT NULL,
        rating INTEGER NOT NULL,
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (reviewer_id) REFERENCES users(id),
        FOREIGN KEY (reviewed_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS trade_offers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        listing_id INTEGER NOT NULL,
        offerer_id INTEGER NOT NULL,
        offered_listing_id INTEGER,
        message TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (listing_id) REFERENCES listings(id),
        FOREIGN KEY (offerer_id) REFERENCES users(id)
    );
    """)

    # Create default admin
    import hashlib
    admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
    try:
        c.execute("""
            INSERT OR IGNORE INTO users (username, email, password_hash, is_admin, reputation)
            VALUES ('admin', 'admin@gameswap.com.br', ?, 1, 5.0)
        """, (admin_hash,))
    except:
        pass

    conn.commit()
    conn.close()

def get_user_by_id(user_id):
    conn = get_conn()
    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None

def get_listings(filters=None):
    conn = get_conn()
    query = """
        SELECT l.*, u.username, u.reputation
        FROM listings l
        JOIN users u ON l.user_id = u.id
        WHERE l.status = 'active'
    """
    params = []
    if filters:
        if filters.get("platform") and filters["platform"] != "Todos":
            query += " AND l.platform = ?"
            params.append(filters["platform"])
        if filters.get("listing_type") and filters["listing_type"] != "Todos":
            query += " AND l.listing_type = ?"
            params.append(filters["listing_type"])
        if filters.get("search"):
            query += " AND (l.title LIKE ? OR l.description LIKE ?)"
            params.extend([f"%{filters['search']}%", f"%{filters['search']}%"])
        if filters.get("max_price"):
            query += " AND l.price <= ?"
            params.append(filters["max_price"])
    query += " ORDER BY l.created_at DESC"
    listings = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(l) for l in listings]

def get_user_listings(user_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT l.*, u.username FROM listings l
        JOIN users u ON l.user_id = u.id
        WHERE l.user_id = ? ORDER BY l.created_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_listing(data):
    conn = get_conn()
    conn.execute("""
        INSERT INTO listings (user_id, title, description, category, platform, condition, price, listing_type, image_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data["user_id"], data["title"], data["description"], data["category"],
          data["platform"], data["condition"], data.get("price"), data["listing_type"], data.get("image_data")))
    conn.commit()
    conn.close()

def delete_listing(listing_id, user_id):
    conn = get_conn()
    conn.execute("UPDATE listings SET status='removed' WHERE id=? AND user_id=?", (listing_id, user_id))
    conn.commit()
    conn.close()

def increment_views(listing_id):
    conn = get_conn()
    conn.execute("UPDATE listings SET views = views + 1 WHERE id=?", (listing_id,))
    conn.commit()
    conn.close()

def create_transaction(data):
    PLATFORM_FEE = 0.05
    fee = data["amount"] * PLATFORM_FEE
    seller_amount = data["amount"] - fee
    conn = get_conn()
    conn.execute("""
        INSERT INTO transactions (listing_id, seller_id, buyer_id, amount, platform_fee, seller_amount, transaction_type, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'completed')
    """, (data["listing_id"], data["seller_id"], data["buyer_id"],
          data["amount"], fee, seller_amount, data["transaction_type"]))
    conn.execute("UPDATE listings SET status='sold' WHERE id=?", (data["listing_id"],))
    conn.execute("UPDATE users SET total_sales = total_sales + 1 WHERE id=?", (data["seller_id"],))
    conn.commit()
    conn.close()
    return fee, seller_amount

def get_messages(user1_id, user2_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT m.*, u.username as sender_name FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE (m.sender_id=? AND m.receiver_id=?) OR (m.sender_id=? AND m.receiver_id=?)
        ORDER BY m.created_at ASC
    """, (user1_id, user2_id, user2_id, user1_id)).fetchall()
    conn.execute("UPDATE messages SET read=1 WHERE sender_id=? AND receiver_id=?", (user2_id, user1_id))
    conn.commit()
    conn.close()
    return [dict(r) for r in rows]

def send_message(sender_id, receiver_id, content, listing_id=None):
    conn = get_conn()
    conn.execute("""
        INSERT INTO messages (sender_id, receiver_id, content, listing_id)
        VALUES (?, ?, ?, ?)
    """, (sender_id, receiver_id, content, listing_id))
    conn.commit()
    conn.close()

def get_conversations(user_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT DISTINCT
            CASE WHEN m.sender_id=? THEN m.receiver_id ELSE m.sender_id END as other_id,
            u.username as other_username,
            MAX(m.created_at) as last_msg,
            SUM(CASE WHEN m.receiver_id=? AND m.read=0 THEN 1 ELSE 0 END) as unread
        FROM messages m
        JOIN users u ON u.id = CASE WHEN m.sender_id=? THEN m.receiver_id ELSE m.sender_id END
        WHERE m.sender_id=? OR m.receiver_id=?
        GROUP BY other_id
        ORDER BY last_msg DESC
    """, (user_id, user_id, user_id, user_id, user_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_unread_count(user_id):
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM messages WHERE receiver_id=? AND read=0", (user_id,)).fetchone()[0]
    conn.close()
    return count

def create_review(reviewer_id, reviewed_id, transaction_id, rating, comment):
    conn = get_conn()
    conn.execute("""
        INSERT OR IGNORE INTO reviews (reviewer_id, reviewed_id, transaction_id, rating, comment)
        VALUES (?, ?, ?, ?, ?)
    """, (reviewer_id, reviewed_id, transaction_id, rating, comment))
    avg = conn.execute("SELECT AVG(rating) FROM reviews WHERE reviewed_id=?", (reviewed_id,)).fetchone()[0]
    if avg:
        conn.execute("UPDATE users SET reputation=? WHERE id=?", (round(avg, 1), reviewed_id))
    conn.commit()
    conn.close()

def get_admin_stats():
    conn = get_conn()
    stats = {
        "total_users": conn.execute("SELECT COUNT(*) FROM users WHERE is_admin=0").fetchone()[0],
        "total_listings": conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0],
        "active_listings": conn.execute("SELECT COUNT(*) FROM listings WHERE status='active'").fetchone()[0],
        "total_transactions": conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0],
        "total_revenue": conn.execute("SELECT COALESCE(SUM(platform_fee),0) FROM transactions").fetchone()[0],
        "total_volume": conn.execute("SELECT COALESCE(SUM(amount),0) FROM transactions").fetchone()[0],
        "recent_transactions": [dict(r) for r in conn.execute("""
            SELECT t.*, u1.username as seller, u2.username as buyer, l.title
            FROM transactions t
            JOIN users u1 ON t.seller_id=u1.id
            JOIN users u2 ON t.buyer_id=u2.id
            JOIN listings l ON t.listing_id=l.id
            ORDER BY t.created_at DESC LIMIT 10
        """).fetchall()],
        "top_users": [dict(r) for r in conn.execute("""
            SELECT username, total_sales, reputation FROM users
            WHERE is_admin=0 ORDER BY total_sales DESC LIMIT 5
        """).fetchall()],
    }
    conn.close()
    return stats

def get_user_transactions(user_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT t.*, u1.username as seller, u2.username as buyer, l.title
        FROM transactions t
        JOIN users u1 ON t.seller_id=u1.id
        JOIN users u2 ON t.buyer_id=u2.id
        JOIN listings l ON t.listing_id=l.id
        WHERE t.seller_id=? OR t.buyer_id=?
        ORDER BY t.created_at DESC
    """, (user_id, user_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_user_reviews(user_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT r.*, u.username as reviewer_name FROM reviews r
        JOIN users u ON r.reviewer_id=u.id
        WHERE r.reviewed_id=? ORDER BY r.created_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
