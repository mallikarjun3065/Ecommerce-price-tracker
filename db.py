import sqlite3
from datetime import datetime
from contextlib import contextmanager

DB_NAME = "price_tracker.db"


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        cur = conn.cursor()

        # table for products
        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                store TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                target_price REAL,
                currency TEXT DEFAULT 'INR',
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                last_checked TEXT,
                group_id TEXT
            );
        """)

        # table for price history
        cur.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                price REAL NOT NULL,
                checked_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                UNIQUE(product_id, checked_at)
            );
        """)

        # Migrate existing database if needed
        migrate_db(cur)

        # Create indexes for better performance
        cur.execute("CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_price_history_product_id ON price_history(product_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_price_history_checked_at ON price_history(checked_at);")

        conn.commit()


def migrate_db(cur):
    """Add new columns to existing tables if they don't exist."""
    # Check and add columns to products table
    cur.execute("PRAGMA table_info(products)")
    columns = [row[1] for row in cur.fetchall()]

    if 'currency' not in columns:
        cur.execute("ALTER TABLE products ADD COLUMN currency TEXT")
        cur.execute("UPDATE products SET currency = 'INR' WHERE currency IS NULL")
    if 'status' not in columns:
        cur.execute("ALTER TABLE products ADD COLUMN status TEXT")
        cur.execute("UPDATE products SET status = 'active' WHERE status IS NULL")
    if 'created_at' not in columns:
        cur.execute("ALTER TABLE products ADD COLUMN created_at TEXT")
        cur.execute("UPDATE products SET created_at = datetime('now') WHERE created_at IS NULL")
    if 'updated_at' not in columns:
        cur.execute("ALTER TABLE products ADD COLUMN updated_at TEXT")
        cur.execute("UPDATE products SET updated_at = datetime('now') WHERE updated_at IS NULL")
    if 'last_checked' not in columns:
        cur.execute("ALTER TABLE products ADD COLUMN last_checked TEXT")

    if 'group_id' not in columns:
        cur.execute("ALTER TABLE products ADD COLUMN group_id TEXT")

    # Check and add columns to price_history table
    cur.execute("PRAGMA table_info(price_history)")
    columns = [row[1] for row in cur.fetchall()]

    if 'checked_at' not in columns:
        cur.execute("ALTER TABLE price_history ADD COLUMN checked_at TEXT NOT NULL DEFAULT (datetime('now'))")
        cur.execute("UPDATE price_history SET checked_at = datetime('now') WHERE checked_at IS NULL")


def add_product(name, store, url, target_price=None, currency='INR'):
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO products (name, store, url, target_price, currency)
                VALUES (?, ?, ?, ?, ?)
            """, (name, store, url, target_price, currency))
            conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Product with URL '{url}' already exists") from e


def get_all_products(status='active'):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM products WHERE status = ?", (status,))
        rows = cur.fetchall()
        return rows


def get_product(product_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cur.fetchone()
        return row


def add_price(product_id, price):
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO price_history (product_id, price, checked_at)
                VALUES (?, ?, datetime('now'))
            """, (product_id, price))
            # Update last_checked in products
            cur.execute("""
                UPDATE products SET last_checked = datetime('now'), updated_at = datetime('now')
                WHERE id = ?
            """, (product_id,))
            conn.commit()
        except sqlite3.IntegrityError:
            # Price already recorded at this time, skip
            pass


def get_price_history(product_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT price, checked_at
            FROM price_history
            WHERE product_id = ?
            ORDER BY checked_at
        """, (product_id,))
        rows = cur.fetchall()
        return rows
def update_product(product_id, name, store, url, target_price):
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                """
                UPDATE products SET name=?, store=?, url=?, target_price=?, updated_at=datetime('now')
                WHERE id=?
                """,
                (name, store, url, target_price, product_id),
            )
            if cur.rowcount == 0:
                raise ValueError(f"Product with id {product_id} not found")
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Product with URL '{url}' already exists") from e


def delete_product_db(product_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM price_history WHERE product_id=?", (product_id,))
        cur.execute("DELETE FROM products WHERE id=?", (product_id,))
        if cur.rowcount == 0:
            raise ValueError(f"Product with id {product_id} not found")
        conn.commit()


def get_product_comparison(group_id):
    """Get all products in a comparison group with their latest prices."""
    with get_connection() as conn:
        cur = conn.cursor()
        # Get products in the group
        cur.execute("""
            SELECT p.*, ph.price as current_price, ph.checked_at
            FROM products p
            LEFT JOIN (
                SELECT product_id, price, checked_at
                FROM price_history
                WHERE (product_id, checked_at) IN (
                    SELECT product_id, MAX(checked_at)
                    FROM price_history
                    GROUP BY product_id
                )
            ) ph ON p.id = ph.product_id
            WHERE p.group_id = ? AND p.status = 'active'
            ORDER BY ph.price ASC
        """, (group_id,))
        rows = cur.fetchall()

        # Convert rows to dictionaries and format dates
        products = []
        for row in rows:
            product = dict(row)  # Convert sqlite3.Row to dict
            if product['checked_at']:
                try:
                    # Parse the ISO format date and format it nicely
                    from datetime import datetime
                    dt = datetime.fromisoformat(product['checked_at'])
                    product['formatted_checked_at'] = dt.strftime('%b %d, %H:%M')
                except:
                    product['formatted_checked_at'] = 'Unknown'
            else:
                product['formatted_checked_at'] = 'Never'
            products.append(product)

        return products


def get_all_comparison_groups():
    """Get all unique product groups with their product counts."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT group_id, COUNT(*) as product_count,
                   MIN(name) as representative_name
            FROM products
            WHERE group_id IS NOT NULL AND status = 'active'
            GROUP BY group_id
            ORDER BY representative_name
        """)
        groups = cur.fetchall()
        return groups


def update_product_group(product_id, group_id):
    """Update the group_id for a product."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE products SET group_id = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (group_id, product_id))
        conn.commit()
