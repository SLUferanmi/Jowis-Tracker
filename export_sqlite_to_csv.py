# Save as export_sqlite_to_csv.py in your project folder
import sqlite3
import pandas as pd

tables = ["user", "project", "milestone", "task", "project_invite", "notification", "project_users"]

conn = sqlite3.connect("app.db")
for table in tables:
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    df.to_csv(f"{table}.csv", index=False)
conn.close()
print("Export complete.")