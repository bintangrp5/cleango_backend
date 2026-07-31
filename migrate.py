import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

def run_migration():
    if not DB_URL:
        print("DATABASE_URL is not set!")
        return

    print("Connecting to Neon DB...")
    try:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Reading schema.sql...")
        with open("sql/schema.sql", "r", encoding="utf-8") as f:
            sql_script = f.read()
            
        print("Executing schema.sql...")
        cursor.execute(sql_script)
        
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    run_migration()
