import sqlite3
import os

# Get the database file path
db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
print(f"Checking database: {db_path}")
print(f"Database exists: {os.path.exists(db_path)}")

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all core tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%core%' ORDER BY name;")
core_tables = cursor.fetchall()

print(f"\nCore tables found: {len(core_tables)}")
for table in core_tables:
    print(f"  - {table[0]}")

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
all_tables = cursor.fetchall()

print(f"\nAll tables in database: {len(all_tables)}")
for table in all_tables:
    print(f"  - {table[0]}")

conn.close()
