from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE chat_messages ADD COLUMN is_read BOOLEAN DEFAULT 0"))
            conn.commit()
        print("SUCCESS: Added is_read column.")
    except Exception as e:
        print(f"INFO: {e}")
