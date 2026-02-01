from app import app
from models import db, User, Admin, SystemSettings, AIConfig
from werkzeug.security import generate_password_hash
import os

def reset_db():
    # Force absolute path to avoid confusion
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if not os.path.isabs(db_path):
            db_path = os.path.join(app.root_path, db_path) # or app.instance_path if using instance
            
        # Check standard locations too just in case
        possible_paths = [
            db_path,
            os.path.join(os.getcwd(), 'lifelink.db'),
            os.path.join(os.getcwd(), 'instance', 'lifelink.db')
        ]
        
        for p in possible_paths:
            if os.path.exists(p):
                print(f"Deleting existing database: {p}")
                try:
                    os.remove(p)
                except PermissionError:
                    print(f"Error: Could not delete {p}. Is it open?")

        print("Creating new database schema...")
        db.create_all()
        
        # Seed System Settings
        if not SystemSettings.query.first():
            print("Seeding System Settings...")
            settings = SystemSettings(
                donation_gap_days=90,
                emergency_radius_km=50.0,
                admin_contact_email='admin@lifelink.com'
            )
            db.session.add(settings)
            
        # Seed AI Config
        if not AIConfig.query.first():
            print("Seeding AI Config...")
            ai_config = AIConfig(
                weight_blood_group=40.0,
                weight_distance=30.0,
                weight_recency=20.0,
                weight_health=10.0
            )
            db.session.add(ai_config)
            
        # Seed Admin
        if not Admin.query.filter_by(username='admin').first():
            print("Seeding Admin User...")
            admin = Admin(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                role='SuperAdmin'
            )
            db.session.add(admin)
            
        db.session.commit()
        print("Database reset and seeded successfully!")

if __name__ == '__main__':
    reset_db()
