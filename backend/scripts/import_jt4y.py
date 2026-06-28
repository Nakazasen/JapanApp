import os
import sys
import requests
import json
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlmodel import Session, SQLModel, create_engine, select

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from frontend.core.config import settings
from frontend.services.jt4y_scraper import JT4YScraper

# Models
from frontend.models.vocab import JpVocabItem, VocabTopic
from frontend.models.grammar import GrammarTopic, GrammarCategory
from frontend.models.reading_practice import ReadingCategory, ReadingItem, ReadingQuestion
from frontend.models.listening_practice import ListeningCategory, ListeningItem, ListeningQuestion
from frontend.models.grammar_practice import GrammarPracticeItem, GrammarPracticeQuestion
from frontend.models.vocab_practice import VocabPracticeItem, VocabPracticeQuestion
from frontend.models.kanji_practice import KanjiPracticeItem, KanjiPracticeQuestion

# --- Configurations ---
DB_PATH = settings.db_path
LIMIT_PER_CAT = 100 

def get_session():
    engine = create_engine(f"sqlite:///{DB_PATH}")
    return Session(engine)

def clear_all_jt4y():
    """Clear ALL JT4Y-sourced data from specific tables."""
    print("🧹 Cleaning up ALL old JT4Y data surgically...")
    with get_session() as session:
        # Listening
        items = session.exec(select(ListeningItem).where(ListeningItem.source == "JT4Y")).all()
        for i in items:
            for q in i.questions: session.delete(q)
            session.delete(i)
        
        # Reading
        items = session.exec(select(ReadingItem).where(ReadingItem.source == "JT4Y")).all()
        for i in items:
            for q in i.questions: session.delete(q)
            session.delete(i)

        # Grammar Practice
        g_items = session.exec(select(GrammarPracticeItem).where(GrammarPracticeItem.source == "JT4Y")).all()
        for i in g_items:
            for q in i.questions: session.delete(q)
            session.delete(i)

        # Vocab Practice
        v_items = session.exec(select(VocabPracticeItem).where(VocabPracticeItem.source == "JT4Y")).all()
        for i in v_items:
            for q in i.questions: session.delete(q)
            session.delete(i)

        # Kanji Practice
        k_items = session.exec(select(KanjiPracticeItem).where(KanjiPracticeItem.source == "JT4Y")).all()
        for i in k_items:
            for q in i.questions: session.delete(q)
            session.delete(i)

        session.commit()

def ensure_category(level: str) -> None:
    """Ensure categories exist for the specific level."""
    print(f"📁 Ensuring categories for {level}...")
    with get_session() as session:
        # Listening
        if not session.exec(select(ListeningCategory).where(ListeningCategory.name == f"JT4Y {level} Listening")).first():
            session.add(ListeningCategory(name=f"JT4Y {level} Listening", level=level))
        # Reading
        if not session.exec(select(ReadingCategory).where(ReadingCategory.name == f"JT4Y {level} Reading")).first():
            session.add(ReadingCategory(name=f"JT4Y {level} Reading", level=level))
        session.commit()

def import_grammar(level: str, url: str):
    print(f"🚀 Importing {level} Grammar...")
    links = JT4YScraper.get_exercise_links(url)[:LIMIT_PER_CAT]
    with get_session() as session:
        for link in links:
            print(f"  Scraping {link['title']}...")
            questions = JT4YScraper.scrape_grammar_vocab_kanji(link['url'])
            if not questions: continue
            
            p_item = GrammarPracticeItem(title=link['title'], source="JT4Y")
            session.add(p_item)
            session.commit()
            session.refresh(p_item)
            
            for q in questions:
                question = GrammarPracticeQuestion(
                    item_id=p_item.id,
                    question_text=q['text'],
                    options=q['options'],
                    correct_option=str(q.get('answer', ""))
                )
                session.add(question)
            session.commit()

def import_vocab_kanji(level: str, mode: str, url: str):
    print(f"🚀 Importing {level} {mode.capitalize()}...")
    links = JT4YScraper.get_exercise_links(url)[:LIMIT_PER_CAT]
    with get_session() as session:
        for link in links:
            print(f"  Scraping {link['title']}...")
            questions = JT4YScraper.scrape_grammar_vocab_kanji(link['url'])
            if not questions: continue
            
            if mode == "vocab":
                p_item = VocabPracticeItem(title=link['title'], source="JT4Y")
            else:
                p_item = KanjiPracticeItem(title=link['title'], source="JT4Y")
                
            session.add(p_item)
            session.commit()
            session.refresh(p_item)
            
            Model = VocabPracticeQuestion if mode == "vocab" else KanjiPracticeQuestion
            for q in questions:
                question = Model(
                    item_id=p_item.id,
                    question_text=q['text'],
                    options=q['options'],
                    correct_option=str(q.get('answer', ""))
                )
                session.add(question)
            session.commit()

def import_listening(level: str, url: str):
    print(f"🚀 Importing {level} Listening...")
    links = JT4YScraper.get_exercise_links(url)[:LIMIT_PER_CAT]
    with get_session() as session:
        cat_name = f"JT4Y {level} Listening"
        cat = session.exec(select(ListeningCategory).where(ListeningCategory.name == cat_name)).first()
        if not cat: return 
        
        for link in links:
            print(f"  Scraping {link['title']}...")
            sections = JT4YScraper.scrape_listening(link['url'])
            if not sections: continue
            
            for data in sections:
                if not data or not data.get('questions'): continue
                
                # Master title for the exercise
                item = ListeningItem(
                    category_id=cat.id,
                    title=data['title'],
                    audio_path="per_question", # Indicator that audio is in questions
                    transcript=data.get('raw_content', ""),
                    source="JT4Y"
                )
                session.add(item)
                session.commit()
                session.refresh(item)
                
                for q in data['questions']:
                    q_audio_url = q.get('audio_url')
                    local_q_audio = None
                    if q_audio_url:
                        local_q_audio = JT4YScraper.download_asset(q_audio_url, "listening")
                    
                    question = ListeningQuestion(
                        item_id=item.id,
                        question_text=q.get('text', f"Question {q['number']}"),
                        options=q.get('options', {}),
                        correct_option=str(q.get('answer', "")),
                        audio_path=local_q_audio
                    )
                    session.add(question)
                session.commit()

def import_reading(level: str, url: str):
    print(f"🚀 Importing {level} Reading...")
    links = JT4YScraper.get_exercise_links(url)[:LIMIT_PER_CAT]
    with get_session() as session:
        cat_name = f"JT4Y {level} Reading"
        cat = session.exec(select(ReadingCategory).where(ReadingCategory.name == cat_name)).first()
        if not cat: return 

        for link in links:
            print(f"  Scraping {link['title']}...")
            sections = JT4YScraper.scrape_reading(link['url'])
            if not sections: continue
            
            for section in sections:
                if not section.get('questions'): continue
                item = ReadingItem(
                    category_id=cat.id,
                    title=section['title'],
                    content=section.get('passage', ""),
                    source="JT4Y"
                )
                session.add(item)
                session.commit()
                session.refresh(item)
                for q in section['questions']:
                    question = ReadingQuestion(
                        item_id=item.id,
                        question_text=q['text'],
                        options=q['options'],
                        correct_option=str(q.get('answer'))
                    )
                    session.add(question)
                session.commit()

def main():
    print("🌟 Starting Refactored Japanesetest4you N5-N1 Import...")
    engine = create_engine(f"sqlite:///{DB_PATH}")
    SQLModel.metadata.create_all(engine)
    
    # Clean ONCE at start
    clear_all_jt4y()
    
    levels = ["N5", "N4", "N3", "N2", "N1"]
    
    for level in levels:
        print(f"\n--- PROCESSING LEVEL {level} ---")
        ensure_category(level)
        
        # Construct URLs
        level_lower = level.lower()
        # Some URLs might vary slightly, but this is the standard pattern
        grammar_url = f"https://japanesetest4you.com/category/jlpt-{level_lower}/jlpt-{level_lower}-grammar-test/"
        vocab_url = f"https://japanesetest4you.com/category/jlpt-{level_lower}/jlpt-{level_lower}-vocabulary-test/"
        kanji_url = f"https://japanesetest4you.com/category/jlpt-{level_lower}/jlpt-{level_lower}-kanji-test/"
        listening_url = f"https://japanesetest4you.com/category/jlpt-{level_lower}/jlpt-{level_lower}-listening-test/"
        reading_url = f"https://japanesetest4you.com/category/jlpt-{level_lower}/jlpt-{level_lower}-reading-test/"

        try:
            import_grammar(level, grammar_url)
            import_vocab_kanji(level, "vocab", vocab_url)
            import_vocab_kanji(level, "kanji", kanji_url)
            import_listening(level, listening_url)
            import_reading(level, reading_url)
        except Exception as e:
            print(f"❌ Error processing {level}: {e}")
            import traceback
            traceback.print_exc()

    print("\n✨ All finished! N5-N1 data imported.")

if __name__ == "__main__":
    main()
