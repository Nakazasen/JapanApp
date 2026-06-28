import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from sqlmodel import Session, create_engine, select
from frontend.core.config import settings
from frontend.models.grammar import GrammarTopic, GrammarCategory
from datetime import datetime

def seed_grammar():
    # Create SQLite engine directly
    database_url = f"sqlite:///{settings.db_path}"
    engine = create_engine(database_url)
    
    with Session(engine) as session:
        # 1. Create a Category
        cat = session.exec(select(GrammarCategory).where(GrammarCategory.name == "Cơ bản")).first()
        if not cat:
            cat = GrammarCategory(
                name="Cơ bản", 
                description="Các cấu trúc ngữ pháp cơ bản",
                lang="jp",
                user_id=1
            )
            session.add(cat)
            session.commit()
            session.refresh(cat)
        cat_id = cat.id

        # 2. Sample Japanese Grammar
        jp_grammar = [
            {
                "title": "V-te kudasai", 
                "pattern": "Vて + ください", 
                "description": "Hãy làm gì đó (yêu cầu lịch sự)", 
                "level": "N5", 
                "source_material": "Minna no Nihongo"
            },
            {
                "title": "V-te iru", 
                "pattern": "Vて + ぁE��", 
                "description": "Đang làm gì đó (thì hiện tại tiếp diềE)", 
                "level": "N5", 
                "source_material": "Minna no Nihongo"
            },
            {
                "title": "Hazu da", 
                "pattern": "V-plain + はずだ", 
                "description": "Chắc chắn là...", 
                "level": "N3", 
                "source_material": "Soumatome N3"
            }
        ]
        
        print("Seeding Japanese grammar...")
        for g in jp_grammar:
            # Check if exists for USER 1
            existing = session.exec(select(GrammarTopic).where(
                GrammarTopic.title == g['title'],
                GrammarTopic.user_id == 1
            )).first()
            if not existing:
                item = GrammarTopic(
                    **g, 
                    category_id=cat_id, 
                    lang="jp",
                    user_id=1,
                    mastery_status="new",
                    created_at=datetime.utcnow()
                )
                session.add(item)
                print(f"  Added JP Grammar: {g['title']}")
            else:
                print(f"  Skipped JP Grammar: {g['title']} (exists)")

        # 3. Sample English Grammar
        en_grammar = [
            {
                "title": "Present Perfect", 
                "pattern": "Have/Has + V3/ed", 
                "description": "Thì hiện tại hoàn thành", 
                "level": "B1", 
                "source_material": "Basic English Grammar"
            },
            {
                "title": "Conditional Type 1", 
                "pattern": "If + S + V(s/es), S + will + V", 
                "description": "Câu điều kiện loại 1", 
                "level": "B2", 
                "source_material": "Oxford Grammar"
            }
        ]
        
        print("\nSeeding English grammar...")
        for g in en_grammar:
            existing = session.exec(select(GrammarTopic).where(
                GrammarTopic.title == g['title'],
                GrammarTopic.user_id == 1
            )).first()
            if not existing:
                item = GrammarTopic(
                    **g, 
                    category_id=cat_id, 
                    lang="en",
                    user_id=1,
                    mastery_status="new",
                    created_at=datetime.utcnow()
                )
                session.add(item)
                print(f"  Added EN Grammar: {g['title']}")
            else:
                print(f"  Skipped EN Grammar: {g['title']} (exists)")

        session.commit()
    print("\nDone seeding grammar!")

if __name__ == "__main__":
    seed_grammar()

