import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.db.session import SessionLocal
from app.models.models import User

def update_tech_name():
    db = SessionLocal()
    try:
        # Update Budi Santoso to Irma Santoso
        user = db.query(User).filter(User.full_name == "Budi Santoso").first()
        if user:
            user.full_name = "Irma Santoso"
            db.commit()
            print("Successfully updated Budi Santoso to Irma Santoso in the database.")
        else:
            print("Technician Budi Santoso not found in the database.")
        
        # Also check for "Budi Santoso User" (the customer)
        user_guest = db.query(User).filter(User.full_name == "Budi Santoso User").first()
        if user_guest:
            user_guest.full_name = "Irma Santoso User"
            db.commit()
            print("Successfully updated Budi Santoso User to Irma Santoso User in the database.")

    except Exception as e:
        print(f"Error updating technician name: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_tech_name()
