from app import app, db
from sqlalchemy import text
from models import Hospital

with app.app_context():
    try:
        with db.engine.connect() as conn:
            # Add new columns to users table if they don't exist
            # SQLite doesn't support IF NOT EXISTS in ALTER TABLE, so we wrap in try/except or check first
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_approved BOOLEAN DEFAULT 1"))
            except Exception as e:
                print(f"Skipping is_approved (likely exists): {e}")

            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN qr_code_data VARCHAR(500)"))
            except Exception as e:
                print(f"Skipping qr_code_data (likely exists): {e}")

            # Create Hospital table
            try:
                db.create_all() # This creates any missing tables like 'hospitals'
                print("Tables created/verified.")
            except Exception as e:
                print(f"Error creating tables: {e}")

            conn.commit()
        print("SUCCESS: Database updated for Phase 1.")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
