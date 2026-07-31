import bcrypt, psycopg2, os
from dotenv import load_dotenv

load_dotenv()
pw = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute("UPDATE users SET password_hash=%s WHERE email='admin@cleango.com'", (pw,))
conn.commit()
print('Password reset to admin123!')
