import sqlite3
import os

# Get the database file path
db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all applied migrations for the core app
cursor.execute("SELECT app, name, applied FROM django_migrations WHERE app='core' ORDER BY applied;")
core_migrations = cursor.fetchall()

print("Core migrations applied:")
for migration in core_migrations:
    print(f"  - {migration[0]}.{migration[1]} (applied: {migration[2]})")

conn.close()
