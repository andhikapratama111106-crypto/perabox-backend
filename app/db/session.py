from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

settings = get_settings()

import ssl
# Fix for Heroku/Supabase requiring postgresql:// instead of postgres://
db_url = settings.DATABASE_URL
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+pg8000://", 1)
elif db_url and db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+pg8000://", 1)

# Note: Supabase hostname resolves to IPv6 only. Port 6543 is IPv4 only.
# We must use port 5432 which supports IPv6.
# Vercel environment supports IPv6. pg8000 supports IPv6.

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
