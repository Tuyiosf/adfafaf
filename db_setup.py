import sqlite3, os

os.makedirs("database", exist_ok=True)
db = sqlite3.connect("database/users.db")
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    point REAL DEFAULT 0,
    all_point REAL DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    transaction_id TEXT UNIQUE,
    amount REAL,
    method TEXT,
    timestamp TEXT
)
""")

db.commit()
db.close()
print("✅ Database created successfully: database/users.db")
