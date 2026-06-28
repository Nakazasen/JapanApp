
import sys
import os
sys.path.append(os.getcwd())

from sqlmodel import SQLModel
from frontend.core.database import engine
# Import models to register them
from frontend.models import *

def init_db():
    print("Creating tables if not exist...")
    SQLModel.metadata.create_all(engine)
    print("Done.")

if __name__ == "__main__":
    init_db()
