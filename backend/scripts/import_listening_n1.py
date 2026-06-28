
import os
import sys
from sqlmodel import Session, create_engine, select

# Ensure project root is in path so we can import frontend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from frontend.core.config import settings
from frontend.models.practice import PracticeCategory, PracticeItem, PracticeQuestion

# --- Configurations ---
DB_PATH = settings.db_path
USER_ID = 1 # Default admin

def import_listening_data():
    database_url = f"sqlite:///{DB_PATH}"
    engine = create_engine(database_url)
    
    with Session(engine) as session:
        # 1. Ensure Category exists
        cat_name = "JLPT N1 Listening"
        statement = select(PracticeCategory).where(PracticeCategory.name == cat_name)
        category = session.exec(statement).first()
        
        if not category:
            print(f"📂 Creating category: {cat_name}")
            category = PracticeCategory(
                name=cat_name,
                type="listening",
                level="N1",
                icon="🎧",
                user_id=USER_ID
            )
            session.add(category)
            session.commit()
            session.refresh(category)
        else:
            print(f"✅ Category already exists: {cat_name}")

        # 2. Define Data
        data = [
            {
                "title": "JLPT N1 Listening - Flower Shop Care",
                "audio_url": "https://japanesetest4you.com/choukai/0008/n1_1_1.mp3",
                "question_text": "女の人はこの後、どうしますか。",
                "options": {
                    "1": "水の量を増やす (Tăng lượng nước)",
                    "2": "水の量を減らす (Giảm lượng nước)",
                    "3": "ひりょうを増やす (Tăng lượng phân bón)",
                    "4": "ひりょう m減らす (Giảm lượng phân bón)"
                },
                "correct_answer": "2",
                "explanation": "Cửa hàng bán hoa giải thích rằng cây bị yếu do tưới quá nhiều nước làm thối rễ. Người phụ nữ được khuyên nên để đất khô rồi mới tưới (khoảng 2-3 ngày 1 lần) và nên ngừng bón phân khi cây đang yếu. Vì cô ấy đang tưới hàng ngày, hành động tiếp theo là giảm lượng nước.",
                "transcript": "女：あの、すみません。昨日、こちらでこの花を買ったんですが、なんだか元気がなくて。\n男：あ、そうですか。ええと、これは日当たりのいい場所に置いてますか。\n女：はい。窓際に置いています。水も毎日欠かさずやってるんですが。\n男：あ、それが原因かもしれませんね。この花は水をやりすぎると、根が腐ってしまうんですよ。\n女：あ、そうなんですか。\n男：ええ。土が乾いてからやるぐらいでちょうどいいんです。今の時期なら二、三日に一回で十分ですよ。\n女：分かりました。\n男：あと、肥料なんですが、弱っているときは控えたほうがいいですね。元気になってからやってください。\n女：はい。分かりました。ありがとうございました。"
            },
            {
                "title": "JLPT N1 Listening - Project Cancellation",
                "audio_url": "https://japanesetest4you.com/choukai/0009/n1_2_1.mp3",
                "question_text": "会議で新しい製品の開発について話しています。開発が中止になった一番の理由は何ですか。",
                "options": {
                    "1": "商品化に莫大な費用がかかるため (Vì tốn quá nhiều chi phí)",
                    "2": "商品化に長時間かかると予想されるから (Vì dự kiến mất nhiều thời gian)",
                    "3": "買う人が限定されると考えられるため (Vì đối tượng mua bị hạn chế)",
                    "4": "技術的な課題が解決できないため (Vì không giải quyết được vấn đề kỹ thuật)"
                },
                "correct_answer": "1",
                "explanation": "Mặc dù kỹ thuật ổn, nhưng việc thương mại hóa tốn phí quá lớn nên dự án bị dừng lại.",
                "transcript": "男：今回の新製品の開発プロジェクトですが、残念ながら中止することになりました。\n女：えっ、どうしてですか。技術的な問題はクリアしたと聞いていましたが。\n男：ええ、技術面は問題ないんです。ただ、試作の段階で分かったことですが、実際に量産して商品化するとなると、莫大な費用がかかることが判明しまして。"
            }
        ]

        # 3. Add items
        for item_data in data:
            # Check if item exists
            item_stmt = select(PracticeItem).where(PracticeItem.title == item_data["title"])
            existing_item = session.exec(item_stmt).first()
            if existing_item:
                print(f"⏩ Item already exists, skipping: {item_data['title']}")
                continue
            
            print(f"📖 Adding item: {item_data['title']}")
            item = PracticeItem(
                category_id=category.id,
                title=item_data["title"],
                content=item_data["transcript"], # For listening, content can be transcript
                audio_path=item_data["audio_url"],
                source="Japanesetest4you"
            )
            session.add(item)
            session.commit()
            session.refresh(item)
            
            # Add question
            question = PracticeQuestion(
                item_id=item.id,
                question_text=item_data["question_text"],
                options=item_data["options"],
                correct_option=item_data["correct_answer"],
                explanation=item_data["explanation"]
            )
            session.add(question)
        
        session.commit()
        print("✨ Import finished successfully!")

if __name__ == "__main__":
    import_listening_data()
