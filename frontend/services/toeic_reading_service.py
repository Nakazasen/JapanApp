
import json
import os
import random

class ToeicReadingService:
    """Service to handle TOEIC Reading data (Part 5, 6, 7)."""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'toeic', 'reading')
        self.part5_file = os.path.join(self.data_dir, 'part5_sample.json')
        
    def get_part5_questions(self, topic=None, limit=10):
        """
        Fetch Part 5 questions, optionally filtered by topic.
        """
        if not os.path.exists(self.part5_file):
            return []
            
        try:
            with open(self.part5_file, 'r', encoding='utf-8') as f:
                questions = json.load(f)
                
            if topic:
                questions = [q for q in questions if q.get('topic') == topic]
                
            random.shuffle(questions)
            return questions[:limit]
            
        except Exception as e:
            print(f"Error loading Part 5 data: {e}")
            return []

    def get_topics(self):
        """Return list of available grammar topics."""
        # In a real app, this might query the DB
        return ["Verb Tense", "Prepositions", "Word Form", "Conjunctions"]
