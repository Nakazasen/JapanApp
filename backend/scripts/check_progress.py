import os
import sys
from sqlmodel import Session, create_engine, select, func
from typing import Optional, List, Dict, Any, Type
import re

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), ".")))

from frontend.core.config import settings
from frontend.models.practice import PracticeItem, PracticeCategory
from frontend.models.listening_practice import ListeningItem, ListeningCategory, ListeningQuestion

DB_PATH = settings.db_path

def is_junk(content: Optional[str]) -> bool:
    if not content: return True
    content_str = str(content).strip()
    if len(content_str) < 150: return True
    
    # Strong garbage markers
    junk_markers = [
        "Home", "Ebooks", "Flashcards", "F.A.Q", "Donate", "Copyright",
        "Answer Key", "Question 1", "Question 2", "Download", 
        "New words", "View transcript", "Japanesetest4you"
    ]
    if re.search(r'^\d+\.\s+Question\s+\d+$', content_str, re.MULTILINE):
        return True
    found_markers = [m for m in junk_markers if m.lower() in content_str.lower()]
    return len(found_markers) > 0

def check_remaining():
    engine = create_engine(f"sqlite:///{DB_PATH}")
    
    with Session(engine) as session:
        # 1. Listening Questions
        q_total = session.exec(select(func.count(ListeningQuestion.id)).where(ListeningQuestion.audio_path != None)).one()
        q_done = session.exec(select(func.count(ListeningQuestion.id)).where(
            ListeningQuestion.audio_path != None,
            ListeningQuestion.transcript != None,
            ListeningQuestion.transcript != ""
        )).one()
        
        # 2. Practice Items (Listening categories)
        p_cats = session.exec(select(PracticeCategory.id).where(PracticeCategory.name.like("%Listening%"))).all()
        p_items = session.exec(select(PracticeItem).where(
            PracticeItem.category_id.in_(p_cats),
            PracticeItem.audio_path != None,
            PracticeItem.audio_path != "per_question"
        )).all()
        p_total = len(p_items)
        p_done = len([i for i in p_items if not is_junk(i.content)])
        
        # 3. Listening Items (direct audio)
        l_items = session.exec(select(ListeningItem).where(
            ListeningItem.audio_path != None,
            ListeningItem.audio_path != "per_question"
        )).all()
        l_total = len(l_items)
        l_done = len([i for i in l_items if not is_junk(i.transcript)])
        
        print(f"--- TRANSCRIBE PROGRESS REPORT ---")
        print(f"1. Listening Questions:")
        print(f"   Done: {q_done} / {q_total} ({q_done/q_total*100:.1f}%)")
        print(f"   Remaining: {q_total - q_done}")
        
        print(f"\n2. Practice Items (Direct audio):")
        print(f"   Done: {p_done} / {p_total} ({p_done/p_total*100:.2f}%)" if p_total else "   N/A")
        print(f"   Remaining: {p_total - p_done}")
        
        print(f"\n3. Listening Items (Direct audio):")
        print(f"   Done: {l_done} / {l_total} ({l_done/l_total*100:.1f}%)" if l_total else "   N/A")
        print(f"   Remaining: {l_total - l_done}")
        
        total_rem = (q_total - q_done) + (p_total - p_done) + (l_total - l_done)
        print(f"\nTOTAL REMAINING: {total_rem} items")

if __name__ == "__main__":
    check_remaining()
