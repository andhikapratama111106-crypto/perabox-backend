import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.db.session import SessionLocal
from app.models.models import User
from app.core.security import get_password_hash

def seed_admin():
    db = SessionLocal()
    try:
        email = "admin@perabox.com"
        password = "admin123"
        
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"Admin user {email} already exists.")
            return

        admin_user = User(
            email=email,
            password_hash=get_password_hash(password),
            full_name="Super Admin",
            phone="081234567890",
            role="admin",
            is_active=True,
            is_verified=True
        )
        
        db.add(admin_user)
        db.commit()
        print(f"Admin user created successfully.\nEmail: {email}\nPassword: {password}")
        
    except Exception as e:
        print(f"Error seeding admin: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()
