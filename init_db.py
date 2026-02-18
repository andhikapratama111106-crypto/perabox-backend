import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.db.session import engine, Base
from app.models.models import *  # Import all models to register them with Base

def init_db():
    print("Initializing database schema...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == "__main__":
    init_db()
