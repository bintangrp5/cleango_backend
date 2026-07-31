import psycopg2, os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute("SELECT email, password_hash FROM users WHERE role='admin'")
print(cur.fetchall())
