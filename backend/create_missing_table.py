import sqlite3
import os

# Get the database file path
db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create the core_useruniversitypreference table
create_table_sql = """
CREATE TABLE IF NOT EXISTS "core_useruniversitypreference" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "ip_address" char(39) NOT NULL,
    "visit_count" integer NOT NULL,
    "last_visited" datetime NOT NULL,
    "created_at" datetime NOT NULL,
    "university_id" bigint NOT NULL REFERENCES "properties_university" ("id") DEFERRABLE INITIALLY DEFERRED,
    "user_id" bigint NULL REFERENCES "accounts_user" ("id") DEFERRABLE INITIALLY DEFERRED
);
"""

print("Creating core_useruniversitypreference table...")
cursor.execute(create_table_sql)

# Create index for university_id
print("Creating index on university_id...")
cursor.execute("""
CREATE INDEX IF NOT EXISTS "core_useruniversitypreference_university_id_idx" 
ON "core_useruniversitypreference" ("university_id");
""")

# Create index for user_id
print("Creating index on user_id...")
cursor.execute("""
CREATE INDEX IF NOT EXISTS "core_useruniversitypreference_user_id_idx" 
ON "core_useruniversitypreference" ("user_id");
""")

# Create unique constraint
print("Creating unique constraint...")
cursor.execute("""
CREATE UNIQUE INDEX IF NOT EXISTS "core_useruniversitypreference_ip_address_university_id_uniq" 
ON "core_useruniversitypreference" ("ip_address", "university_id");
""")

conn.commit()

# Verify the table was created
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='core_useruniversitypreference';")
result = cursor.fetchone()

if result:
    print(f"✓ Table created successfully: {result[0]}")
    
    # Show table structure
    cursor.execute("PRAGMA table_info(core_useruniversitypreference);")
    columns = cursor.fetchall()
    print("\nTable columns:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
else:
    print("✗ Table creation failed")

conn.close()
