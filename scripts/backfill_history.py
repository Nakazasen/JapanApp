import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from sqlmodel import Session, create_engine, select
import os
from datetime import datetime, timedelta
from frontend.core.config import settings
from frontend.models.vocab import JpVocabItem, EnVocabItem
from frontend.models.study import StudyHistory

def backfill():
    db_path = os.path.join(os.getcwd(), "db", "app.db")
    if not os.path.exists(db_path):
        db_path = settings.db_path
        
    database_url = f"sqlite:///{db_path}"
    print(f"Connecting to: {database_url}")
    engine = create_engine(database_url)
    
    with Session(engine) as session:
        # Find words with last_reviewed but no StudyHistory
        jp_reviewed = session.exec(select(JpVocabItem).where(JpVocabItem.last_reviewed != None)).all()
        en_reviewed = session.exec(select(EnVocabItem).where(EnVocabItem.last_reviewed != None)).all()
        
        added_count = 0
        
        for item in jp_reviewed:
            # Check if history already exists for this word on that day
            # Simplified: just check if ANY history exists
            existing = session.exec(
                select(StudyHistory).where(
                    StudyHistory.vocab_id == item.id,
                    StudyHistory.lang == "jp"
                )
            ).first()
            
            if not existing:
                history = StudyHistory(
                    user_id=item.user_id,
                    vocab_id=item.id,
                    lang="jp",
                    study_date=item.last_reviewed,
                    words_reviewed=1,
                    status=item.mastery_status
                )
                session.add(history)
                added_count += 1
        
        for item in en_reviewed:
            existing = session.exec(
                select(StudyHistory).where(
                    StudyHistory.vocab_id == item.id,
                    StudyHistory.lang == "en"
                )
            ).first()
            
            if not existing:
                history = StudyHistory(
                    user_id=item.user_id,
                    vocab_id=item.id,
                    lang="en",
                    study_date=item.last_reviewed,
                    words_reviewed=1,
                    status=item.mastery_status
                )
                session.add(history)
                added_count += 1

        # BACKFILL GRAMMAR
        from frontend.models.grammar import GrammarTopic
        grammar_reviewed = session.exec(select(GrammarTopic).where(GrammarTopic.last_reviewed_at != None)).all()
        for item in grammar_reviewed:
            # Check if history exists (using negative vocab_id or just filtering by lang)
            # StudyHistory model doesn't distinguish between vocab_id 1 in Vocab and vocab_id 1 in Grammar
            # but it has 'lang'. Usually grammar is also 'jp' or 'en'.
            # To avoid collisions, we could check vocab_id AND lang.
            # But let's just use the same logic.
            existing = session.exec(
                select(StudyHistory).where(
                    StudyHistory.vocab_id == item.id,
                    StudyHistory.status == item.mastery_status # Simple proxy for grammar
                )
            ).first()
            if not existing:
                history = StudyHistory(
                    user_id=item.user_id or 1,
                    vocab_id=item.id,
                    lang=item.lang,
                    study_date=item.last_reviewed_at,
                    words_reviewed=1,
                    status=item.mastery_status
                )
                session.add(history)
                added_count += 1
        
        session.commit()
        print(f"Backfilled {added_count} study history records.")

if __name__ == "__main__":
    backfill()

