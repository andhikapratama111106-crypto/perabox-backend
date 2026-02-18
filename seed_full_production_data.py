import sys
import os
import uuid
from decimal import Decimal

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.db.session import SessionLocal
from app.models.models import User, Technician, ServiceCategory, Service
from app.core.security import get_password_hash

def seed_data():
    db = SessionLocal()
    try:
        # 1. Create Category
        print("Checking for categories...")
        category = db.query(ServiceCategory).filter(ServiceCategory.slug == "air-conditioning").first()
        if not category:
            category = ServiceCategory(
                id=uuid.uuid4(),
                name="Air Conditioning",
                slug="air-conditioning",
                description="Layanan perawatan dan perbaikan AC",
                icon_url="❄️",
                display_order=1,
                is_active=True
            )
            db.add(category)
            db.commit()
            db.refresh(category)
            print("Created category: Air Conditioning")
        else:
            print("Category 'Air Conditioning' exists.")

        # 2. Create Services
        services_data = [
            {"id": "srv-1", "name": "AC Cleaning", "price": 80000, "slug": "ac-cleaning"},
            {"id": "srv-2", "name": "AC Installation", "price": 300000, "slug": "ac-installation"},
            {"id": "srv-3", "name": "Freon Refill", "price": 200000, "slug": "freon-refill"},
            {"id": "srv-4", "name": "AC Repair", "price": 150000, "slug": "ac-repair"},
        ]
        
        for sd in services_data:
            existing_service = db.query(Service).filter(Service.slug == sd["slug"]).first()
            if not existing_service:
                service = Service(
                    category_id=category.id,
                    name=sd["name"],
                    slug=sd["slug"],
                    description=f"Layanan {sd['name']}",
                    base_price=Decimal(sd["price"]),
                    duration_minutes=60,
                    is_active=True
                )
                db.add(service)
                print(f"Created service: {sd['name']}")
        db.commit()

        # 3. Create Technicians
        techs_mock = [
            {'name': 'Irma Santoso', 'photo': '/technician_3.jpg', 'rating': 4.9, 'jobs': 128, 'specs': ['Service AC', 'Cuci AC'], 'exp': 5, 'phone': '6281234567890', 'bio': 'Berpengalaman lebih dari 5 tahun dalam menangani berbagai jenis kerusakan AC. Cepat, rapi, dan jujur.'},
            {'name': 'Ahmad Rizki', 'photo': '/technician_7.jpg', 'rating': 4.8, 'jobs': 95, 'specs': ['Bongkar Pasang', 'Service Besar'], 'exp': 4, 'phone': '6281234567891', 'bio': 'Spesialis bongkar pasang AC dengan pengerjaan yang presisi untuk semua merk AC.'},
            {'name': 'Dedi Kurniawan', 'photo': '/technician_6.jpg', 'rating': 4.7, 'jobs': 64, 'specs': ['Cuci AC', 'Freon Refill'], 'exp': 3, 'phone': '6281234567892', 'bio': 'Ahli dalam perawatan rutin AC dan pengisian freon. Mengutamakan kepuasan pelanggan.'},
            {'name': 'Sari Wulandari', 'photo': '/technician_1.jpg', 'rating': 5.0, 'jobs': 42, 'specs': ['Cuci AC', 'Perbaikan Ringan'], 'exp': 2, 'phone': '6281234567893', 'bio': 'Teknisi ramah dan teliti dalam pengerjaan pembersihan unit AC agar tetap dingin maksimal.'},
            {'name': 'Lestari Putri', 'photo': '/technician_2.jpg', 'rating': 4.8, 'jobs': 110, 'specs': ['Bongkar Pasang', 'Instalasi'], 'exp': 6, 'phone': '6281234567894', 'bio': 'Multi-skill teknisi dengan jam terbang tinggi. Solusi lengkap untuk urusan rumah Anda.'},
            {'name': 'Dewi Anggraini', 'photo': '/technician_4.jpg', 'rating': 4.9, 'jobs': 88, 'specs': ['Cleaning & Maintenance'], 'exp': 5, 'phone': '6281234567895', 'bio': 'Ahli instalasi dan perbaikan sistem kelistrikan bangunan. Aman dan bersertifikat.'},
            {'name': 'Siti Aminah', 'photo': '/technician_5.jpg', 'rating': 4.6, 'jobs': 56, 'specs': ['Service AC', 'Isi Freon'], 'exp': 4, 'phone': '6281234567896', 'bio': 'Cekatan dalam memberikan layanan pembersihan rumah secara menyeluruh.'}
        ]

        password_hash = get_password_hash("tech123!")

        for t in techs_mock:
            email = t['name'].lower().replace(" ", ".") + "@perabox.com"
            existing_user = db.query(User).filter(User.email == email).first()
            if not existing_user:
                user = User(
                    email=email,
                    password_hash=password_hash,
                    full_name=t['name'],
                    phone=t['phone'],
                    role="technician",
                    avatar_url=t['photo'],
                    is_active=True,
                    is_verified=True
                )
                db.add(user)
                db.flush() # Get user.id

                tech = Technician(
                    user_id=user.id,
                    specializations=t['specs'],
                    experience_years=t['exp'],
                    rating_average=Decimal(str(t['rating'])),
                    total_jobs=t['jobs'],
                    is_available=True,
                    bio=t['bio']
                )
                db.add(tech)
                print(f"Created technician: {t['name']}")
        
        db.commit()
        print("Seeding completed successfully!")

    except Exception as e:
        print(f"Error seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
