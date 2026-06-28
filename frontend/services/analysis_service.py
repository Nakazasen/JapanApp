
import logging
from typing import Dict, Any, List, Optional
import json
import re
import asyncio
from frontend.services.ai_service import get_ai_service

logger = logging.getLogger(__name__)

class LearningAnalysisService:
    """
    Service to analyze reading passages using AI.
    Extracts vocabulary, translation, and sentence-by-sentence analysis.
    """
    
    def __init__(self):
        self.ai_service = get_ai_service()

    async def analyze_reading_passage(self, text: str) -> Dict[str, Any]:
        """
        Analyze a Japanese reading passage.
        Returns detailed structured data: vocab, translation, sentence breakdown.
        """
        prompt = f"""Bạn là một giáo viên tiếng Nhật chuyên nghiệp. Hãy phân tích bài đọc tiếng Nhật sau đây để giúp học viên N1 học tập hiệu quả.

BÀI ĐỌC:
{text}

YÊU CẦU:
Trả về một JSON Object THUẦN TÚY (không markdown json, không giải thích thêm), chứa các trường sau:

1. "translation": Bản dịch tiếng Việt hoàn chỉnh, văn phong tự nhiên, hay.
2. "vocabulary": Danh sách khoảng 10-15 từ vựng quan trọng nhất trong bài (ưu tiên từ N1, N2).
   Mỗi từ gồm:
   - "word": Từ gốc (Kanji)
   - "reading": Cách đọc (Hiragana)
   - "meaning": Nghĩa tiếng Việt
   - "type": Loại từ (Danh từ, Động từ...)

3. "sentences": Tách bài đọc thành từng câu và phân tích chi tiết.
   Mỗi câu gồm:
   - "original": Câu tiếng Nhật gốc.
   - "translation": Dịch nghĩa câu đó sang tiếng Việt.
   - "grammar_notes": Giải thích ngắn gọn các ngữ pháp/cấu trúc quan trọng xuất hiện trong câu (nếu có).

MẪU JSON TRẢ VỀ:
{{
  "translation": "...",
  "vocabulary": [
    {{ "word": "自立", "reading": "じりつ", "meaning": "Tự lập", "type": "Danh từ" }}
  ],
  "sentences": [
    {{
      "original": "...",
      "translation": "...",
      "grammar_notes": "..."
    }}
  ]
}}
"""
        try:
            # Run AI generation in thread
            result = await asyncio.to_thread(self.ai_service.generate_response, prompt)
            
            if result.get("status") != "success":
                return {"success": False, "error": result.get("text", "AI Error")}
            
            text_resp = result.get("text", "")
            
            # Clean up markdown
            json_match = re.search(r'```json\s*(.*?)\s*```', text_resp, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try finding first { and last }
                json_match = re.search(r'\{.*\}', text_resp, re.DOTALL)
                json_str = json_match.group(0) if json_match else text_resp

            data = json.loads(json_str)
            return {"success": True, "data": data}
            
        except Exception as e:
            logger.error(f"[AnalysisService] Error: {e}")
            return {"success": False, "error": str(e)}

_analysis_service = None

def get_analysis_service():
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = LearningAnalysisService()
    return _analysis_service
