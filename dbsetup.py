import sqlite3
from datetime import datetime, timedelta

today = datetime.today()

# Connect to database (creates file if it doesn't exist)
conn = sqlite3.connect("indian_bank_system.db")
cur = conn.cursor()

# Create tables
cur.executescript("""
CREATE TABLE IF NOT EXISTS login (
    user_id TEXT PRIMARY KEY,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    firstname TEXT,
    lname TEXT,
    email TEXT,
    phone TEXT,
    dob TEXT,
    addr TEXT,
    accno TEXT UNIQUE,
    ifsc TEXT,
    balance REAL,
    status TEXT
);

CREATE TABLE IF NOT EXISTS cards (
    cardno TEXT PRIMARY KEY,
    user_id TEXT,
    expiry TEXT,
    status TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS loans (
    loan_id TEXT PRIMARY KEY,
    user_id TEXT,
    loantype TEXT,
    amount REAL,
    duration INTEGER,
    interestrate REAL,
    intrestpendingtopay REAL,
    appliedon TEXT,
    status TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS transactions (
    t_id TEXT PRIMARY KEY,
    from_acc TEXT,
    to_acc TEXT,
    amount REAL,
    date TEXT,
    type TEXT CHECK(type IN ('neft', 'upi', 'rgts'))
);
""")
# Insert sample data
cur.executemany("INSERT INTO login (user_id, password) VALUES (?, ?)", [
    ("raviravi987", "pass123"),
    ("anjali2022", "secure456")
])

cur.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
    ("raviravi987", "Ravi", "Kumar", "ravi.k@example.com", "9876543210", "1990-05-12", "Hyderabad, TS", "ACC1234567", "SBIN0001234", 45000.0, "active"),
    ("anjali2022", "Anjali", "Verma", "anjali.v@example.com", "9123456780", "1995-08-22", "Pune, MH", "ACC9876543", "ICIC0005678", 82000.0, "active")
])

cur.executemany("INSERT INTO cards VALUES (?, ?, ?, ?)", [
    ("CARD001", "raviravi987", "12/27", "active"),
    ("CARD002", "anjali2022", "06/26", "active")
])

cur.executemany("INSERT INTO loans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", [
    ("LN001", "raviravi987", "home", 1500000, 1095, 8.5, 127500.0, today.strftime("%Y-%m-%d"), "approved"),
    ("LN002", "anjali2022", "personal", 300000, 365, 11.5, 34500.0, today.strftime("%Y-%m-%d"), "pending")
])

# Save and close
conn.commit()
conn.close()

print("✅ Database 'indian_bank_system.db' created with sample data.")
