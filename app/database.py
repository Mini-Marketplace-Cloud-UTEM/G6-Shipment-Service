import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# PostgreSQL via Supabase
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:G6.DESPACHO@db.cirrgzafgddejnqtrkdy.supabase.co:5432/postgres"
).strip()

# Render sometimes sets postgres:// instead of postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
