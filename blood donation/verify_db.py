from app import app, db
from models import ChatMessage
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print("Tables found:", tables)
    if 'chat_messages' in tables:
        print("SUCCESS: chat_messages table exists.")
    else:
        print("FAILURE: chat_messages table missing.")
