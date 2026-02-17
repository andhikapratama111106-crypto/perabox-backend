import sys
import os

# Add the parent directory to sys.path to allow importing from 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import uuid
from decimal import Decimal
from sqlalchemy import text
from app.db.session import engine, Base, SessionLocal
from app.models.models import User, Service, ServiceCategory, Technician
from app.core.security import get_password_hash

def seed_db():
    print("Dropping all existing tables with CASCADE...")
    with engine.connect() as conn:
        # Get all table names in the public schema
        result = conn.execute(text("""
            SELECT tablename FROM pg_catalog.pg_tables 
            WHERE schemaname = 'public'
        """))
        tables = [row[0] for row in result]
        if tables:
            # Drop all tables with CASCADE
            conn.execute(text(f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE"))
            conn.commit()
    
    print("Creating all tables from models...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Create Categories
        print("Seeding Categories...")
        categories = [
            ServiceCategory(
                id=uuid.uuid4(),
                name="Air Conditioning",
                slug="air-conditioning",
                description="AC maintenance and repair",
                display_order=1
            ),
            ServiceCategory(
                id=uuid.uuid4(),
                name="Electrical",
                slug="electrical",
                description="Electrical installations and repairs",
                display_order=2
            ),
            ServiceCategory(
                id=uuid.uuid4(),
                name="Plumbing",
                slug="plumbing",
                description="Plumbing solutions",
                display_order=3
            ),
            ServiceCategory(
                id=uuid.uuid4(),
                name="Cleaning",
                slug="cleaning",
                description="Professional cleaning services",
                display_order=4
            )
        ]
        db.add_all(categories)
        db.commit()
        
        # Create Services
        print("Seeding Services...")
        ac_category = [c for c in categories if c.slug == "air-conditioning"][0]
        electrical_category = [c for c in categories if c.slug == "electrical"][0]
        
        services = [
            Service(
                id=uuid.uuid4(),
                category_id=ac_category.id,
                name="AC Maintenance",
                slug="ac-maintenance",
                description="Standard AC cleaning and checkup",
                base_price=Decimal("150000.00"),
                duration_minutes=60
            ),
            Service(
                id=uuid.uuid4(),
                category_id=ac_category.id,
                name="AC Repair",
                slug="ac-repair",
                description="Expert repair for all AC models",
                base_price=Decimal("250000.00"),
                duration_minutes=120
            ),
            Service(
                id=uuid.uuid4(),
                category_id=electrical_category.id,
                name="Light Installation",
                slug="light-installation",
                description="Fixing and installing light fixtures",
                base_price=Decimal("75000.00"),
                duration_minutes=30
            ),
            Service(
                id=uuid.uuid4(),
                category_id=electrical_category.id,
                name="Electrical Checkup",
                slug="electrical-checkup",
                description="Full house electrical circuit inspection",
                base_price=Decimal("200000.00"),
                duration_minutes=90
            )
        ]
        db.add_all(services)
        db.commit()
        
        # Create Test Customer
        print("Seeding Test Customer...")
        test_customer = User(
            id=uuid.uuid4(),
            email="customer1@example.com",
            password_hash=get_password_hash("Test123!"),
            full_name="Test Customer",
            phone="08123456789",
            role="customer",
            is_active=True,
            is_verified=True
        )
        db.add(test_customer)
        db.commit()
        
        
        print("Database seeded successfully!")
        
        print("Database seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
