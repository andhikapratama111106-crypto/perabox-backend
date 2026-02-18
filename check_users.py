import os
from sqlalchemy import create_engine, text
from app.db.session import SessionLocal

def check_users():
    db = SessionLocal()
    try:
        emails = ['customer1@example.com', 'admin@perabox.com']
        for email in emails:
            result = db.execute(text("SELECT email, role, is_active FROM users WHERE email = :email"), {"email": email}).fetchone()
            if result:
                print(f"Found user: {result.email}, Role: {result.role}, Active: {result.is_active}")
            else:
                print(f"User NOT found: {email}")
        
        # Also list all users for context
        all_users = db.execute(text("SELECT email, role FROM users")).fetchall()
        print("\nAll users in DB:")
        for u in all_users:
            print(f"- {u.email} ({u.role})")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_users()
