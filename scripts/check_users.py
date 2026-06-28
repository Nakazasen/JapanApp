import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlmodel import Session, select
from frontend.core.database import engine
from frontend.models.user import User

with Session(engine) as session:
    users = session.exec(select(User)).all()
    for u in users:
        print(f"User: {u.username}, ID: {u.id}")

