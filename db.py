import sqlite3
import json
import os

# Path to the SQLite database file
DB_PATH = "src/database/vehicle_system.db"

def initialize_database():
    """Initialize the SQLite database and create the transactions table."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            data TEXT NOT NULL,
            signature TEXT NOT NULL,
            timestamp REAL NOT NULL
        )
    """
    )
    conn.commit()
    conn.close()


def add_transaction_to_db(sender, data, signature):
    """Add a transaction record to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transactions (sender, data, signature, timestamp) VALUES (?, ?, ?, datetime('now'))",
        (sender, json.dumps(data), signature)
    )
    conn.commit()
    conn.close()


def get_all_transactions():
    """Retrieve all transactions stored in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions")
    rows = cursor.fetchall()
    conn.close()

    transactions = []
    for row in rows:
        transactions.append({
            "id": row[0],
            "sender": row[1],
            "data": json.loads(row[2]),
            "signature": row[3],
            "timestamp": row[4]
        })
    return transactions