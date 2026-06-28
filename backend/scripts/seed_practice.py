import os
import sys
from sqlmodel import Session, create_engine, select

# Ensure project root is in path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(project_root)

from frontend.core.config import settings
from frontend.models.vocab_practice import VocabPracticeItem, VocabPracticeQuestion
from frontend.models.grammar_practice import GrammarPracticeItem, GrammarPracticeQuestion
from frontend.models.kanji_practice import KanjiPracticeItem, KanjiPracticeQuestion

def get_session():
    engine = create_engine(f"sqlite:///{settings.db_path}")
    return Session(engine)

def seed_data():
    print(f"🌱 Seeding sample practice data to {settings.db_path}...")
    with get_session() as session:
        print("Adding sample items...")

        # 1. Vocab Practice
        v1 = VocabPracticeItem(title="Luyện từ vựng JLPT N3 - Bài 1", source="Mẫu")
        session.add(v1)
        session.commit()
        session.refresh(v1)
        
        q1 = VocabPracticeQuestion(
            item_id=v1.id,
            question_text="Từ nào sau đây nghĩa là 'Ăn'?",
            options={"A": "たべる", "B": "のむ", "C": "ねる", "D": "いく"},
            correct_option="A",
            explanation="'たべる' nghĩa là ăn."
        )
        session.add(q1)

        # 2. Grammar Practice
        g1 = GrammarPracticeItem(title="Luyện ngữ pháp N3 - Cấu trúc ~たことがある", source="Mẫu")
        session.add(g1)
        session.commit()
        session.refresh(g1)
        
        q2 = GrammarPracticeQuestion(
            item_id=g1.id,
            question_text="Tôi đã từng đi Nhật. (Dùng ~たことがある)",
            options={"A": "日本へ行きます。", "B": "日本へ行ったことがあります。", "C": "日本へ行きたいです。", "D": "日本へ行きませんでした。"},
            correct_option="B",
            explanation="~たことがある diễn tả trải nghiệm trong quá khứ."
        )
        session.add(q2)

        # 3. Kanji Practice
        k1 = KanjiPracticeItem(title="Luyện Hán tự N3 - Bộ Thủ", source="Mẫu")
        session.add(k1)
        session.commit()
        session.refresh(k1)
        
        q3 = KanjiPracticeQuestion(
            item_id=k1.id,
            question_text="Chữ 'Hưu' (休) gồm những bộ nào?",
            options={"A": "Nhân + Mộc", "B": "Nhân + Thủy", "C": "Mộc + Thủy", "D": "Nhật + Nguyệt"},
            correct_option="A",
            explanation="Chữ 休 (nghỉ ngơi) gồm bộ Nhân (người) và bộ Mộc (cây) - người tựa vào cây nghỉ ngơi."
        )
        session.add(q3)

        session.commit()
        print("✨ Seeding completed successfully!")

if __name__ == "__main__":
    seed_data()
