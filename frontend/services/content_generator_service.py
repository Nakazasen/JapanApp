import json
import asyncio
from typing import Dict, Any, List, Optional
from frontend.core.gemini_client import get_gemini_client
from frontend.services.tts_service import get_tts_service
from frontend.models.toeic import ToeicQuestion, QuestionType
from frontend.core.database import get_session

class ContentGenerationService:
    """
    Service to generate TOEIC questions and scripts using Gemini AI.
    Handles JSON structured output and database persistence.
    """
    
    def __init__(self):
        self.ai_client = get_gemini_client()
        self.tts_service = get_tts_service()

    async def generate_reading_part5(self, topic: str = "Business") -> Dict[str, Any]:
        """
        Generates a TOEIC Part 5 (Incomplete Sentence) question using structured JSON mode.
        """
        # Improved Prompt for specific JSON structure
        prompt = (
            f"Generate a single dictionary for a TOEIC Part 5 (Incomplete Sentences) question about '{topic}'. "
            "Ensure the question tests grammar or vocabulary relevant to business contexts. "
            "Return JSON matching this schema: "
            "{ 'question_text': 'string', 'options': {'A': 'str', 'B': 'str', 'C': 'str', 'D': 'str'}, "
            "'correct_answer': 'A', 'explanation': 'string' }"
        )
        
        try:
            # Use generate_json for reliability
            data = await self.ai_client.generate_json(prompt, temperature=0.7)
            
            # Validate essential fields
            if not all(k in data for k in ["question_text", "options", "correct_answer"]):
                print("Invalid JSON structure received from AI")
                return {}

            return {
                "part": 5,
                "topic": topic,
                "question_text": data.get("question_text"),
                "options": data.get("options"),
                "correct_answer": data.get("correct_answer"),
                "explanation": data.get("explanation")
            }
        except Exception as e:
            print(f"Error generating Part 5: {e}")
            return {}

    async def generate_listening_part2(self, topic: str = "Office") -> Dict[str, Any]:
        """
        Generates a TOEIC Part 2 (Question-Response) script using structured JSON mode.
        Returns script for TTS and metadata.
        """
        prompt = (
            f"Generate a TOEIC Part 2 (Question-Response) item about '{topic}'. "
            "It consists of one Question and three Responses (A, B, C). "
            "One response is correct, two are distractors. "
            "Return JSON matching this schema: "
            "{ 'question': 'Where is the meeting room?', "
            "'responses': {'A': 'It is on the second floor.', 'B': 'At 2 PM.', 'C': 'Yes, I did.'}, "
            "'correct_response': 'A' }"
        )
        
        try:
            data = await self.ai_client.generate_json(prompt, temperature=0.7)
            
            if not all(k in data for k in ["question", "responses", "correct_response"]):
                 return {}
            
            # Format Script for Display & TTS
            # Part 2 format: Audio plays Question, then (A)... (B)... (C)...
            # Text display usually hides the question and options in real test, 
            # but for practice we might show them or just the script.
            
            question = data["question"]
            resps = data["responses"]
            
            script = f"Question: {question}\n\n"
            script += f"(A) {resps.get('A', '')}\n"
            script += f"(B) {resps.get('B', '')}\n"
            script += f"(C) {resps.get('C', '')}"
            
            return {
                "part": 2,
                "topic": topic,
                "question_text": question, # For DB storage
                "options": [resps.get("A"), resps.get("B"), resps.get("C")], # List format for DB
                "correct_answer": data.get("correct_response"),
                "script": script, # For TTS
                "explanation": "Correct response matches the question type/context." # Generic or ask AI
            }
            
        except Exception as e:
            print(f"Error generating Listening Part 2: {e}")
            return {}

    async def generate_listening_part1_script(self, topic: str = "Office") -> Dict[str, Any]:
        """
        Generates a script for Part 1 (Photographs).
        """
        prompt = (
            f"Generate a TOEIC Part 1 (Photographs) item about '{topic}'. "
            "Provide 4 statements (A, B, C, D) describing a hypothetical image. "
            "One is correct, three are distractors. "
            "Return JSON: { 'statements': {'A': 'str', 'B': 'str', 'C': 'str', 'D': 'str'}, 'correct_option': 'A' }"
        )
        
        try:
            data = await self.ai_client.generate_json(prompt, temperature=0.7)
            
            stmts = data.get("statements", {})
            script = ""
            options_list = []
            
            for key in ['A', 'B', 'C', 'D']:
                val = stmts.get(key, "")
                script += f"({key}) {val}\n"
                options_list.append(val)
                
            return {
                "part": 1,
                "topic": topic,
                "script": script,
                "options": options_list,
                "correct_answer": data.get("correct_option"),
                "explanation": "Correct statement accurately describes the image context."
            }
            
        except Exception as e:
             print(f"Error generating Listening Part 1: {e}")
             return {}

    async def save_question_to_db(self, question_data: Dict[str, Any]) -> bool:
        """
        Saves a generated question object to the database.
        """
        try:
            with get_session() as session:
                part = question_data.get("part")
                
                # Map fields to ToeicQuestion model
                new_q = ToeicQuestion(
                    part=part,
                    topic=question_data.get("topic"),
                    question_text=question_data.get("question_text"), # May be None for Part 1
                    correct_answer=question_data.get("correct_answer"),
                    explanation=question_data.get("explanation"),
                    source="AI Generated",
                    transcript=question_data.get("script") # For listening parts
                )
                
                # Handle Options (List[str] or Dict)
                raw_opts = question_data.get("options")
                if isinstance(raw_opts, dict):
                    # Convert dict {'A': 'val'} to list ['val', 'val'] or keep ordered?
                    # The Model expects List[str]. 
                    # For Part 5, UI expects dict map options.
                    # Standardizing to List for DB: [Index 0=A, 1=B...]
                    opts_list = []
                    for k in sorted(raw_opts.keys()):
                        opts_list.append(raw_opts[k])
                    new_q.options = opts_list
                elif isinstance(raw_opts, list):
                    new_q.options = raw_opts
                
                # Set Question Type based on Part
                if part == 1: new_q.question_type = QuestionType.PHOTO
                elif part == 2: new_q.question_type = QuestionType.QR
                elif part == 5: new_q.question_type = QuestionType.GRAMMAR
                
                # Handle Audio Path (if exists in input data)
                if "audio_path" in question_data:
                    new_q.audio_path = question_data["audio_path"]
                    
                session.add(new_q)
                session.commit()
                print(f"✅ Saved question ID {new_q.id} to DB.")
                return True
                
        except Exception as e:
            print(f"Error saving to DB: {e}")
            return False

# Singleton
_content_service = None

def get_content_service():
    global _content_service
    if _content_service is None:
        _content_service = ContentGenerationService()
    return _content_service
