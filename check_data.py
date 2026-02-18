import os
from sqlalchemy import create_engine, text
from app.db.session import SessionLocal

def check_data():
    db = SessionLocal()
    try:
        # Check Categories
        categories = db.execute(text("SELECT id, name FROM service_categories")).fetchall()
        print(f"Categories ({len(categories)}):")
        for c in categories:
            print(f"- {c.name} ({c.id})")
            
        # Check Services
        services = db.execute(text("SELECT id, name, category_id FROM services")).fetchall()
        print(f"\nServices ({len(services)}):")
        for s in services:
            print(f"- {s.name} ({s.id}) [Category: {s.category_id}]")
            
        # Check Technicians
        technicians = db.execute(text("SELECT t.id, u.full_name, t.is_available, u.is_active FROM technicians t JOIN users u ON t.user_id = u.id")).fetchall()
        print(f"\nTechnicians ({len(technicians)}):")
        for t in technicians:
            print(f"- {t.full_name} ({t.id}) [Available: {t.is_available}, Active: {t.is_active}]")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_data()
