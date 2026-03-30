from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

settings = get_settings()

import ssl

# Use standard psycopg2 which natively supports SNI and IPv4 Supabase Poolers.
db_url = settings.DATABASE_URL
# Fix for Heroku/Supabase requiring postgresql:// instead of postgres://
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Allow SQLAlchemy to use the default psycopg2 driver.

connect_args = {}
if "pg8000" in db_url:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE  # Try loose SSL first for debugging
    connect_args = {
        "ssl_context": ssl_context
    }

engine = create_engine(
    db_url,
    pool_pre_ping=True,
    connect_args=connect_args,
    poolclass=NullPool,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
