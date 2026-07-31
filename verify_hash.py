import bcrypt

hash_from_db = b"$2b$12$iLQPjQiwyman7By0sXGGUuRrwoly2tQQqGCyrNjZpYIWKlfLOOhKa"
try:
    print("admin123:", bcrypt.checkpw(b"admin123", hash_from_db))
except:
    pass
try:
    print("password:", bcrypt.checkpw(b"password", hash_from_db))
except:
    pass
try:
    print("admin:", bcrypt.checkpw(b"admin", hash_from_db))
except:
    pass
try:
    print("123456:", bcrypt.checkpw(b"123456", hash_from_db))
except:
    pass
