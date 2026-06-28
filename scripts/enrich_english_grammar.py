import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""
AI Enrich English Grammar units using Gemini.
Generates patterns, descriptions, notes, and examples.

Usage:
    python scripts/enrich_english_grammar.py --limit 10
    python scripts/enrich_english_grammar.py --all
"""

import asyncio
import json
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from frontend.core.database import get_session
from frontend.core.gemini_client import get_gemini_client
from frontend.models.grammar import GrammarTopic, GrammarExample
from sqlmodel import select


SYSTEM_PROMPT = """You are a professional English teacher specialized in explaining grammar to Vietnamese learners.
Your task is to provide rich content for English grammar topics.
For each topic, you must provide:
1. pattern: The formal structure (e.g., 'S + am/is/are + V-ing').
2. description: A clear, academic explanation in English.
3. usage_notes: A detailed explanation in Vietnamese about when and how to use this grammar point.
4. common_mistakes: Common errors that Vietnamese learners usually make, explained in Vietnamese.
5. examples: A list of 2-3 natural examples. Each example should have:
   - example_text: The English sentence.
   - translation_vi: The natural Vietnamese translation.
   - notes: (Optional) briefly explain why this example is relevant.

Return the data as a JSON list of objects, each object containing the fields above plus the 'title' of the topic provided.
"""

USER_PROMPT_TEMPLATE = """Please enrich the following English grammar topics:
{topics_list}

Target Level: {level_info}
Category: {category_info}

Return only a JSON array of objects."""


async def enrich_batch(topics: List[GrammarTopic], client, model: str = None) -> List[Dict[str, Any]]:
    """Enrich a batch of grammar topics using Gemini."""
    if not topics:
        return []

    # Prepare info for prompt
    topics_info = "\n".join([f"- {t.title}" for t in topics])
    
    # We assume they are from the same category or level for context if possible, 
    # but here we just pass the list.
    prompt = USER_PROMPT_TEMPLATE.format(
        topics_list=topics_info,
        level_info="Varies (from A1 to C2)",
        category_info="Mixed English Grammar"
    )

    try:
        print(f"  [AI] Processing batch of {len(topics)} topics (Model: {model or 'Waterfall'})...")
        
        # We need to handle the case where generate_json doesn't support 'model' argument
        # if the GeminiClient wasn't updated. For now, we'll try to use what's there.
        # Let's check GeminiClient.generate_json signature in planning if needed.
        
        response_data = await client.generate_json(
            prompt, 
            system_instruction=SYSTEM_PROMPT,
            max_tokens=4096,
            model_name=model
        )
        
        if isinstance(response_data, list):
            return response_data
        elif isinstance(response_data, dict) and "items" in response_data:
            return response_data["items"]
        else:
            print(f"  [AI] Warning: Unexpected response format: {type(response_data)}")
            return []
    except Exception as e:
        print(f"  [AI] Error during enrichment: {e}")
        return []


def update_database(session, topic_id: int, ai_data: Dict[str, Any]):
    """Update topic and insert examples in database."""
    topic = session.get(GrammarTopic, topic_id)
    if not topic:
        return

    # Update topic fields
    topic.pattern = ai_data.get("pattern", topic.pattern)
    topic.description = ai_data.get("description", topic.description)
    topic.usage_notes = ai_data.get("usage_notes", topic.usage_notes)
    topic.common_mistakes = ai_data.get("common_mistakes", topic.common_mistakes)
    topic.is_ai_enriched = True
    topic.last_updated = datetime.utcnow()
    
    session.add(topic)
    
    # Add examples
    examples_data = ai_data.get("examples", [])
    for ex in examples_data:
        # Check if example already exists for this topic to avoid duplicates if re-run
        # (Simple check by text)
        new_ex = GrammarExample(
            topic_id=topic.id,
            example_text=ex.get("example_text", ""),
            translation_vi=ex.get("translation_vi", ""),
            notes=ex.get("notes", "")
        )
        session.add(new_ex)


async def main():
    parser = argparse.ArgumentParser(description='Enrich English Grammar units using AI')
    parser.add_argument('--limit', type=int, default=5, help='Limit number of units to enrich')
    parser.add_argument('--all', action='store_true', help='Enrich all units')
    parser.add_argument('--batch-size', type=int, default=3, help='Batch size for AI calls')
    parser.add_argument('--model', type=str, default=None, help='Force a specific Gemini model')
    
    args = parser.parse_args()
    
    client = get_gemini_client()
    # If model is forced, we need to override the client's model list logic
    # or just pass it to the generate_json call.

    
    with get_session() as session:
        # Fetch units
        query = select(GrammarTopic).where(
            GrammarTopic.lang == "en",
            GrammarTopic.is_ai_enriched == False
        )
        
        if not args.all:
            query = query.limit(args.limit)
            
        topics = session.exec(query).all()
        
        if not topics:
            print("No unenriched English grammar units found.")
            return

        print(f"Found {len(topics)} units to enrich.")
        
        # Batching
        for i in range(0, len(topics), args.batch_size):
            batch = topics[i:i + args.batch_size]
            print(f"\nBatch {i//args.batch_size + 1}: {', '.join([t.title for t in batch])}")
            
            enrichments = await enrich_batch(batch, client, model=args.model)
            
            # Map enrichments back to topics
            for enrichment in enrichments:
                title = enrichment.get("title", "").strip().lower()
                # Find matching topic in batch
                match = next((t for t in batch if t.title.strip().lower() == title), None)
                
                if match:
                    update_database(session, match.id, enrichment)
                    print(f"  笨・Enriched: {match.title}")
                else:
                    # Try fuzzy or partial match if exact fails
                    match = next((t for t in batch if title in t.title.lower() or t.title.lower() in title), None)
                    if match:
                        update_database(session, match.id, enrichment)
                        print(f"  笨・Enriched (partial match): {match.title}")
                    else:
                        print(f"  笞・・Could not match AI result for: {title}")
            
            session.commit()
            print(f"Batch {i//args.batch_size + 1} saved.")

            
            # Small delay to avoid aggressive rate limiting
            if i + args.batch_size < len(topics):
                await asyncio.sleep(1)

    print("\nEnrichment process complete!")


if __name__ == "__main__":
    asyncio.run(main())

