import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.db.session import SessionLocal
from app.models.models import User
from app.core.security import get_password_hash

def seed_customer():
    db = SessionLocal()
    try:
        email = "customer1@example.com"
        password = "Test123!"
        
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"Customer user {email} already exists.")
            # Update password just in case
            existing_user.password_hash = get_password_hash(password)
            db.commit()
            print("Updated password.")
            return

        user = User(
            email=email,
            password_hash=get_password_hash(password),
            full_name="Customer Satu",
            phone="081234567891",
            role="customer",
            is_active=True,
            is_verified=True
        )
        
        db.add(user)
        db.commit()
        print(f"Customer user created successfully.\nEmail: {email}\nPassword: {password}")
        
    except Exception as e:
        print(f"Error seeding customer: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_customer()
