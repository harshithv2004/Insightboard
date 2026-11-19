"""
InsightBoard — Synthetic Data Seeder
Generates and inserts realistic data:
  400 customers, 40 products, 1500 orders, ~3000 order items

Run from the project root (with .venv activated):
    python sql/seed_data.py

The .env file must have valid DB credentials.
"""

import sys
import os
import random
from datetime import date, timedelta

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import mysql.connector
from mysql.connector import Error

# ---------------------------------------------------------------------------
# Data pools
# ---------------------------------------------------------------------------
FIRST_NAMES = [
    "James", "Emma", "Liam", "Olivia", "Noah", "Ava", "William", "Isabella",
    "Benjamin", "Sophia", "Lucas", "Mia", "Henry", "Charlotte", "Alexander",
    "Amelia", "Michael", "Harper", "Daniel", "Evelyn", "Matthew", "Abigail",
    "Jackson", "Emily", "Sebastian", "Elizabeth", "Jack", "Mila", "Owen",
    "Ella", "Aiden", "Luna", "Samuel", "Camila", "David", "Penelope",
    "Joseph", "Riley", "Carter", "Zoey",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
]

REGIONS = ["North", "South", "East", "West", "Central"]

# 40 products across 5 categories
PRODUCTS = [
    # Electronics (10)
    ("ProBook Laptop 15\"",        "Electronics",     1299.99),
    ("UltraWide Monitor 34\"",     "Electronics",      699.99),
    ("Mechanical Keyboard Pro",    "Electronics",      149.99),
    ("Wireless Mouse Precision",   "Electronics",       79.99),
    ("Noise Cancelling Headset",   "Electronics",      249.99),
    ("4K Webcam HD",               "Electronics",      119.99),
    ("USB-C Hub 10-Port",          "Electronics",       89.99),
    ("SSD Drive 1TB",              "Electronics",      129.99),
    ("DDR5 RAM 32GB",              "Electronics",      189.99),
    ("RTX Graphics Card",          "Electronics",      599.99),
    # Office Supplies (8)
    ("Premium Printer Paper A4",   "Office Supplies",   12.99),
    ("Heavy Duty Stapler",         "Office Supplies",   24.99),
    ("Ballpoint Pens Box (50)",    "Office Supplies",   15.99),
    ("Spiral Notebooks Pack (5)",  "Office Supplies",   22.99),
    ("Hanging File Folders (25)",  "Office Supplies",   18.99),
    ("Whiteboard Markers (12)",    "Office Supplies",   14.99),
    ("Sticky Notes Multicolor",    "Office Supplies",    8.99),
    ("Document Binders Pack (10)", "Office Supplies",   28.99),
    # Furniture (8)
    ("Ergonomic Office Chair",     "Furniture",        399.99),
    ("Height-Adjustable Desk",     "Furniture",        649.99),
    ("4-Drawer Filing Cabinet",    "Furniture",        189.99),
    ("5-Shelf Bookcase",           "Furniture",        149.99),
    ("LED Desk Lamp",              "Furniture",         59.99),
    ("Magnetic Whiteboard 4x3ft",  "Furniture",        129.99),
    ("Dual Monitor Stand",         "Furniture",         79.99),
    ("Anti-Fatigue Desk Mat",      "Furniture",         39.99),
    # Software (6)
    ("Windows 11 Pro License",     "Software",         199.99),
    ("Microsoft 365 Business",     "Software",         299.99),
    ("Antivirus Pro 5-Device",     "Software",          49.99),
    ("Adobe Creative Suite",       "Software",         599.99),
    ("QuickBooks Accounting",      "Software",         349.99),
    ("Salesforce CRM License",     "Software",         499.99),
    # Accessories (8)
    ("Adjustable Phone Stand",     "Accessories",       19.99),
    ("Cable Management Kit",       "Accessories",       24.99),
    ("Laptop Backpack Pro",        "Accessories",       69.99),
    ("20000mAh Power Bank",        "Accessories",       59.99),
    ("Tempered Glass Protector",   "Accessories",       14.99),
    ("Electronics Cleaning Kit",   "Accessories",       19.99),
    ("Premium Cable Bundle",       "Accessories",       34.99),
    ("Memory Foam Wrist Rest",     "Accessories",       29.99),
]

STATUS_CHOICES  = ["Completed", "Pending", "Cancelled"]
STATUS_WEIGHTS  = [70, 20, 10]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        database=os.getenv("DB_NAME", "insightboard"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        autocommit=False,
    )

# ---------------------------------------------------------------------------
# Seeding functions
# ---------------------------------------------------------------------------

def seed_customers(cursor, n=400):
    print(f"  Inserting {n} customers ...")
    used_emails = set()
    rows = []
    for i in range(n):
        fname = random.choice(FIRST_NAMES)
        lname = random.choice(LAST_NAMES)
        name  = f"{fname} {lname}"
        base  = f"{fname.lower()}.{lname.lower()}"
        email = f"{base}{random.randint(1, 9999)}@example.com"
        # Ensure unique email
        while email in used_emails:
            email = f"{base}{random.randint(1, 99999)}@example.com"
        used_emails.add(email)
        region = random.choice(REGIONS)
        signup = random_date(date(2022, 1, 1), date(2024, 6, 30))
        rows.append((name, email, region, signup))

    cursor.executemany(
        "INSERT INTO Customers (customer_name, email, region, signup_date) "
        "VALUES (%s, %s, %s, %s)",
        rows,
    )
    # Fetch generated IDs
    cursor.execute("SELECT customer_id FROM Customers ORDER BY customer_id DESC LIMIT %s", (n,))
    ids = [r[0] for r in cursor.fetchall()]
    print(f"  OK {n} customers inserted.")
    return ids


def seed_products(cursor):
    print(f"  Inserting {len(PRODUCTS)} products ...")
    cursor.executemany(
        "INSERT INTO Products (product_name, category, unit_price) VALUES (%s, %s, %s)",
        PRODUCTS,
    )
    cursor.execute("SELECT product_id, unit_price FROM Products ORDER BY product_id")
    rows = cursor.fetchall()
    print(f"  OK {len(rows)} products inserted.")
    # Return list of (product_id, unit_price) tuples
    return rows


def seed_orders(cursor, customer_ids, n=1500):
    print(f"  Inserting {n} orders …")
    rows = []
    for _ in range(n):
        cid    = random.choice(customer_ids)
        odate  = random_date(date(2023, 1, 1), date(2024, 12, 31))
        region = random.choice(REGIONS)
        status = random.choices(STATUS_CHOICES, weights=STATUS_WEIGHTS, k=1)[0]
        rows.append((cid, odate, region, status))

    cursor.executemany(
        "INSERT INTO Orders (customer_id, order_date, region, status) "
        "VALUES (%s, %s, %s, %s)",
        rows,
    )
    cursor.execute("SELECT order_id FROM Orders ORDER BY order_id DESC LIMIT %s", (n,))
    ids = [r[0] for r in cursor.fetchall()]
    print(f"  OK {n} orders inserted.")
    return ids


def seed_order_items(cursor, order_ids, products):
    print("  Inserting order items (1-4 per order) ...")
    rows = []
    for oid in order_ids:
        n_items = random.randint(1, 4)
        chosen  = random.sample(products, min(n_items, len(products)))
        for pid, price in chosen:
            qty = random.randint(1, 10)
            # Slight price variation (±10%) to simulate promotions / price changes
            actual_price = round(float(price) * random.uniform(0.90, 1.10), 2)
            rows.append((oid, pid, qty, actual_price))

    cursor.executemany(
        "INSERT INTO OrderItems (order_id, product_id, quantity, unit_price) "
        "VALUES (%s, %s, %s, %s)",
        rows,
    )
    print(f"  OK {len(rows)} order items inserted.")
    return len(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=== InsightBoard - Seed Data Generator ===\n")
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        print("[1/4] Seeding customers …")
        customer_ids = seed_customers(cursor, n=400)

        print("[2/4] Seeding products …")
        products = seed_products(cursor)

        print("[3/4] Seeding orders …")
        order_ids = seed_orders(cursor, customer_ids, n=1500)

        print("[4/4] Seeding order items …")
        item_count = seed_order_items(cursor, order_ids, products)

        conn.commit()
        print("\n=== Done! ===")
        print(f"  Customers : 400")
        print(f"  Products  : {len(products)}")
        print(f"  Orders    : 1500")
        print(f"  Items     : {item_count}")
        print("\nYou can now start the Flask app with:  python run.py")

    except Error as e:
        print(f"\n[ERROR] MySQL error: {e}")
        print("Make sure the schema has been created first:")
        print("  mysql -u root -p < sql/schema.sql")
        sys.exit(1)
    finally:
        if "cursor" in dir() and cursor:
            cursor.close()
        if "conn" in dir() and conn and conn.is_connected():
            conn.close()


if __name__ == "__main__":
    main()
