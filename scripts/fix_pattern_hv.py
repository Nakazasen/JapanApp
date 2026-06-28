import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from sqlmodel import Session, create_engine, select
from frontend.core.config import settings
from frontend.models.vocab import JpVocabItem

def fix_pattern_data():
    database_url = f"sqlite:///{settings.db_path}"
    engine = create_engine(database_url)
    
    with Session(engine) as session:
        statement = select(JpVocabItem).where(JpVocabItem.source_material == "Pattern Goi N1")
        items = session.exec(statement).all()
        
        count = 0
        for item in items:
            examples = item.example_jp or ""
            # In my import_pattern script, I did: f"Âm Hán Việt: {han_viet}"
            if "Âm Hán Việt:" in examples:
                lines = examples.split('\n')
                new_examples = []
                found_hv = ""
                for line in lines:
                    if line.startswith("Âm Hán Việt:"):
                        found_hv = line.replace("Âm Hán Việt:", "").strip()
                    else:
                        new_examples.append(line)
                
                if found_hv:
                    item.han_viet = found_hv
                    item.example_jp = "\n".join(new_examples).strip()
                    session.add(item)
                    count += 1
        
        session.commit()
        print(f"Moved Hán Việt for {count} records in 'Pattern Goi N1'.")

if __name__ == "__main__":
    fix_pattern_data()

