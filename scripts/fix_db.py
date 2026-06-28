import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from sqlmodel import Session, create_engine, text
from frontend.core.config import settings

def fix_source_name():
    database_url = f"sqlite:///{settings.db_path}"
    engine = create_engine(database_url)
    
    with Session(engine) as session:
        # Update existing records to have a space in the name
        session.execute(text("UPDATE jp_vocab_items SET source_material = 'Mimikara Oboeru' WHERE source_material = 'MimikaraOboeru'"))
        session.commit()
        print("Updated source names in database.")

if __name__ == "__main__":
    fix_source_name()

