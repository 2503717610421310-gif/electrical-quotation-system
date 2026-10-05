import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "electrical_data.db")


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# DEFAULT SETTINGS
# ============================================================

DEFAULT_SETTINGS = {
    "company_name": "HARI ALTRIGAL",
    "company_subtitle": "Electrical & Plumbing Specialist",
    "company_address": "Tamil Nadu, India",
    "company_phone": "8056977906",
    "company_email": "hari.electricalpumbing@gamil.com",
    "gst_number": "33ABCDE1234F1Z5",
    "currency_symbol": "₹",
    "tax_rate": "18",
    "quotation_prefix": "EST",
    "invoice_prefix": "INV"
}


# ============================================================
# DEFAULT CATALOG
# ============================================================

DEFAULT_CATALOG = [
    {
        "name": "LED Bulb 9W",
        "category": "Lighting",
        "description": "Energy efficient LED bulb",
        "unit": "Nos",
        "rate": 120,
        "gst": 18,
        "image_url": "https://images.unsplash.com/photo-1550985616-10810253b84d?auto=format&fit=crop&w=200&q=80"
    },
    {
        "name": "LED Tube Light 20W",
        "category": "Lighting",
        "description": "20W LED tube light",
        "unit": "Nos",
        "rate": 350,
        "gst": 18,
        "image_url": "https://images.unsplash.com/photo-1513506003901-1e6a229e2d15?auto=format&fit=crop&w=200&q=80"
    },
    {
        "name": "Ceiling Fan 1200mm",
        "category": "Fans",
        "description": "1200mm energy efficient ceiling fan",
        "unit": "Nos",
        "rate": 2200,
        "gst": 18,
        "image_url": "https://images.unsplash.com/photo-1618961734760-466979ce35b0?auto=format&fit=crop&w=200&q=80"
    },
    {
        "name": "PVC Wire 1.5 sq.mm",
        "category": "Wires",
        "description": "FR PVC copper wire",
        "unit": "Meter",
        "rate": 12,
        "gst": 18,
        "image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=200&q=80"
    },
    {
        "name": "CPVC Pipe 1 Inch",
        "category": "Plumbing",
        "description": "High pressure plumbing CPVC pipe",
        "unit": "Meter",
        "rate": 110,
        "gst": 18,
        "image_url": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=200&q=80"
    },
    {
        "name": "Plumbing Labour",
        "category": "Labour",
        "description": "General plumbing installation and repair",
        "unit": "Hour",
        "rate": 450,
        "gst": 18,
        "image_url": "https://images.unsplash.com/photo-1607472586893-edb57bdc0e39?auto=format&fit=crop&w=200&q=80"
    }
]


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS catalog_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            unit TEXT NOT NULL,
            rate REAL NOT NULL,
            gst REAL DEFAULT 18,
            image_url TEXT,
            active INTEGER DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_number TEXT UNIQUE,
            doc_type TEXT NOT NULL,
            is_gst INTEGER DEFAULT 1,
            doc_date TEXT NOT NULL,

            client_name TEXT,
            client_company TEXT,
            client_address TEXT,
            client_phone TEXT,
            client_email TEXT,
            client_gst TEXT,

            subtotal REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            taxable REAL DEFAULT 0,
            tax REAL DEFAULT 0,
            grand_total REAL DEFAULT 0,

            status TEXT DEFAULT 'Draft',
            terms TEXT,

            items_json TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Ensure image_url column exists in catalog_items
    try:
        cur.execute("ALTER TABLE catalog_items ADD COLUMN image_url TEXT")
    except sqlite3.OperationalError:
        pass

    # Ensure is_gst column exists in documents
    try:
        cur.execute("ALTER TABLE documents ADD COLUMN is_gst INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass

    # Seed default settings
    for key, value in DEFAULT_SETTINGS.items():
        cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))

    # Seed catalog if empty
    cur.execute("SELECT COUNT(*) AS count FROM catalog_items")
    if cur.fetchone()["count"] == 0:
        for item in DEFAULT_CATALOG:
            cur.execute("""
                INSERT INTO catalog_items (name, category, description, unit, rate, gst, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (item["name"], item["category"], item["description"], item["unit"], item["rate"], item["gst"], item["image_url"]))

    conn.commit()
    conn.close()


def get_settings():
    conn = get_connection()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}


def get_catalog():
    conn = get_connection()
    rows = conn.execute("SELECT id, name, category, description, unit, rate, gst, image_url FROM catalog_items WHERE active = 1 ORDER BY category, name").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_next_doc_number(doc_type="quotation"):
    conn = get_connection()
    prefix = "EST" if doc_type.lower() == "quotation" else "INV"
    row = conn.execute("SELECT COUNT(*) AS count FROM documents WHERE doc_type = ?", (doc_type,)).fetchone()
    next_number = row["count"] + 1
    conn.close()
    year = datetime.now().year
    return f"{prefix}-{year}-{next_number:04d}"


def save_document(data):
    import json
    conn = get_connection()
    doc_type = data.get("doc_type", "quotation")
    doc_number = data.get("doc_number") or get_next_doc_number(doc_type)
    doc_date = data.get("doc_date", datetime.now().strftime("%Y-%m-%d"))
    items = data.get("items", [])

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO documents (
            doc_number, doc_type, is_gst, doc_date,
            client_name, client_company, client_address, client_phone, client_email, client_gst,
            subtotal, discount, taxable, tax, grand_total,
            status, terms, items_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        doc_number, doc_type, 1 if data.get("is_gst", True) else 0, doc_date,
        data.get("client_name", ""), data.get("client_company", ""), data.get("client_address", ""),
        data.get("client_phone", ""), data.get("client_email", ""), data.get("client_gst", ""),
        float(data.get("subtotal", 0)), float(data.get("discount", 0)), float(data.get("taxable", 0)),
        float(data.get("tax", 0)), float(data.get("grand_total", 0)),
        data.get("status", "Draft"), data.get("terms", ""), json.dumps(items)
    ))

    doc_id = cur.lastrowid
    conn.commit()
    conn.close()
    return doc_id


def get_document(doc_id):
    import json
    conn = get_connection()
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    conn.close()

    if row is None:
        return None

    result = dict(row)
    try:
        result["items"] = json.loads(result["items_json"] or "[]")
    except Exception:
        result["items"] = []
    result.pop("items_json", None)
    return result


def get_documents():
    conn = get_connection()
    rows = conn.execute("SELECT id, doc_number, doc_type, is_gst, doc_date, client_name, client_company, grand_total, status, created_at FROM documents ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def convert_quotation_to_invoice(quotation_id):
    import json
    quotation = get_document(quotation_id)
    if quotation is None:
        raise ValueError("Quotation not found")

    conn = get_connection()
    invoice_number = get_next_doc_number("invoice")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO documents (
            doc_number, doc_type, is_gst, doc_date,
            client_name, client_company, client_address, client_phone, client_email, client_gst,
            subtotal, discount, taxable, tax, grand_total,
            status, terms, items_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        invoice_number, "invoice", quotation.get("is_gst", 1), datetime.now().strftime("%Y-%m-%d"),
        quotation["client_name"], quotation["client_company"], quotation["client_address"],
        quotation["client_phone"], quotation["client_email"], quotation["client_gst"],
        quotation["subtotal"], quotation["discount"], quotation["taxable"], quotation["tax"],
        quotation["grand_total"], "Unpaid", quotation["terms"], json.dumps(quotation["items"])
    ))

    invoice_id = cur.lastrowid
    cur.execute("UPDATE documents SET status = 'Billed' WHERE id = ?", (quotation_id,))
    conn.commit()
    conn.close()
    return invoice_id


def update_setting(key, value):
    conn = get_connection()
    conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, str(value)))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")