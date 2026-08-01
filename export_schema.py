import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.schema import CreateTable
from dotenv import load_dotenv

load_dotenv()
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("DATABASE_URL not found")
    exit(1)

# Fix URL for sqlalchemy (postgres -> postgresql)
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(database_url)
metadata = MetaData()
metadata.reflect(bind=engine)

with open("database_schema.sql", "w") as f:
    for table in metadata.sorted_tables:
        f.write(str(CreateTable(table).compile(engine)).strip() + ";\n\n")

print("Schema exported successfully to database_schema.sql")
