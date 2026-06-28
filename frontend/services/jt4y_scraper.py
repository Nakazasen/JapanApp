"""Scraper service specifically for japanesetest4you.com."""
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import os
import uuid
from typing import List, Dict, Any, Optional

class JT4YScraper:
    """Service for scraping JLPT N1-N5 materials from japanesetest4you.com."""
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    BASE_URL = "https://japanesetest4you.com/"

    @staticmethod
    def _get_main_content(soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Find the most specific container for the post content."""
        content = (soup.find('div', class_='entry-content') or 
                   soup.find('div', class_='entry') or 
                   soup.find('div', id='content') or
                   soup.find('div', class_='pf-content') or
                   soup.find('div', class_='post-content') or
                   soup.find('article'))
        return content

    @staticmethod
    def _get_title(soup: BeautifulSoup) -> str:
        """Clean title of website suffixes."""
        title_el = (soup.find('h1', class_='entry-title') or 
                    soup.find('h1', class_='post-title') or
                    soup.find('h1') or 
                    soup.find('title'))
        if title_el:
            res = title_el.get_text(strip=True)
            res = res.split('– Japanesetest4you.com')[0].strip()
            res = res.split('- Japanesetest4you.com')[0].strip()
            return res
        return "Untitled Exercise"

    @staticmethod
    def get_exercise_links(category_url: str) -> List[Dict[str, str]]:
        """Scrape exercise links across all paginated pages."""
        all_unique_links = []
        seen_urls = set()
        for page in range(1, 15): # Max 15 pages (enough for ~300 exercises)
            url = category_url if page == 1 else f"{category_url.rstrip('/')}/page/{page}/"
            try:
                response = requests.get(url, headers=JT4YScraper.HEADERS, timeout=15)
                if response.status_code == 404: break
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                found_on_this_page = 0
                for a in soup.find_all('a', href=True):
                    text = a.get_text(strip=True)
                    href = a['href']
                    # Use a broader set of keywords and check if it's an exercise link
                    if any(k in text for k in ["Exercise", "Practice", "Test", "Quiz", "Reading"]):
                        if "jlpt-" in href and href not in seen_urls:
                            seen_urls.add(href)
                            all_unique_links.append({"title": text, "url": href})
                            found_on_this_page += 1
                
                # If no new links found or no next page indicator, we might be done
                if found_on_this_page == 0: break
                
                # Look for 'Next' button with various common classes
                next_btn = (soup.find('a', class_='next') or 
                            soup.find('a', class_='nextpostslink') or 
                            soup.find('a', rel='next'))
                if not next_btn and page > 1:
                    # Some sites don't have a next btn on the last page 
                    # but if we found links, we're good. If we didn't, we stop.
                    pass 
                if not next_btn and found_on_this_page < 5: # Small number of items usually means last page
                    break
                    
            except Exception: break
        return all_unique_links

    @staticmethod
    def _find_answer_map(content: BeautifulSoup) -> Dict[int, str]:
        """Global scan for answer key."""
        text = content.get_text()
        answers = {}
        matches = re.finditer(r'(?:Question\s*)?(\d+)\s*[:．.]\s*([1-4a-dA-D])', text, re.I)
        for m in matches:
            answers[int(m.group(1))] = m.group(2)
        return answers

    @staticmethod
    def scrape_reading(url: str) -> List[Dict[str, Any]]:
        """Scrape reading exercises with correct passage/question separation."""
        try:
            response = requests.get(url, headers=JT4YScraper.HEADERS, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            content = JT4YScraper._get_main_content(soup)
            if not content: return []

            main_title = JT4YScraper._get_title(soup)
            answer_map = JT4YScraper._find_answer_map(content)
            
            passage_parts = []
            questions = []
            
            # Markers for footer junk
            stop_keywords = ["answer key:", "new words:", "grammar points:", "copyright"]

            # Process top-level elements
            for child in content.children:
                if not child or not hasattr(child, 'name') or not child.name:
                    continue
                
                # Rule: Is it a junk tag?
                if child.name in ['script', 'style', 'noscript', 'ins', 'meta', 'link']: continue
                
                # Rule: Is it empty or just whitespace?
                txt_full = child.get_text(separator=" ", strip=True)
                if not txt_full: continue
                
                # Rule: Is it a stop marker?
                txt_lower = txt_full.lower()
                if any(k in txt_lower for k in stop_keywords):
                    break

                # Rule: Is it a question block? 
                is_q = False
                if child.find('input', type='radio'):
                    is_q = True
                elif re.match(r'^\d+[．.:\)]', txt_full) and len(txt_full) < 800:
                    is_q = True

                if is_q:
                    # Robust parsing for question + options in one block
                    all_text = child.get_text(separator="[[SEP]]", strip=True)
                    # We use a unique separator to avoid splitting on actual text newlines
                    lines = [l.strip() for l in all_text.split("[[SEP]]") if l.strip()]
                    
                    if lines:
                        # Find the first line that looks like a question number
                        q_num = None
                        q_text_parts = []
                        start_idx = -1
                        
                        for i, line in enumerate(lines):
                            m = re.match(r'^(\d+)[．.:\)]\s*(.*)', line)
                            if m:
                                q_num = int(m.group(1))
                                q_text_parts.append(m.group(2).strip())
                                start_idx = i
                                break
                        
                        if q_num is not None:
                            # Collect question text until we hit an option marker
                            # Markers: radio inputs (which we can't see in text list easily)
                            # Or lines that look like (1) (2) or just short lines after a question
                            
                            # Re-parse specifically for options if we have radio inputs in HTML
                            opts = {}
                            current_q_text = " ".join(q_text_parts)
                            
                            # If the HTML has radio inputs, let's use them as true separators
                            radio_inputs = child.find_all('input', type='radio')
                            if radio_inputs:
                                # Logic: Text before first radio is Question. 
                                # Text between radios are options.
                                full_html_bits = []
                                for node in child.contents:
                                    if node.name == 'input' and node.get('type') == 'radio':
                                        full_html_bits.append("[[OPT]]")
                                    else:
                                        full_html_bits.append(node.get_text(strip=True))
                                
                                segments = " ".join(full_html_bits).split("[[OPT]]")
                                # Segment 0 is question (potentially with number)
                                q_raw = segments[0].strip()
                                q_clean = re.sub(r'^\d+[．.:\)]\s*', '', q_raw).strip()
                                
                                # Segments 1+ are options
                                for seg in segments[1:]:
                                    opt_val = re.sub(r'^(?:\d+[．.:\)]|\s*[◯○●①②③④]|[1-4a-d][．.:\)])\s*', '', seg, flags=re.I).strip()
                                    if opt_val:
                                        opts[str(len(opts) + 1)] = opt_val
                                
                                questions.append({
                                    "number": q_num,
                                    "text": q_clean or q_raw,
                                    "options": opts,
                                    "answer": str(answer_map.get(q_num, ""))
                                })
                            else:
                                # Fallback if no radio buttons but matched regex
                                # Just use the lines strategy
                                for l in lines[start_idx+1:]:
                                    # Very simple bullet cleaning
                                    clean = re.sub(r'^(?:\d+[．.:\)]|\s*[◯○● ①②③④]|[1-4a-d][．.:\)])\s*', '', l, flags=re.I).strip()
                                    if clean: opts[str(len(opts) + 1)] = clean
                                
                                questions.append({
                                    "number": q_num,
                                    "text": current_q_text,
                                    "options": opts,
                                    "answer": str(answer_map.get(q_num, ""))
                                })
                else:
                    # It's a passage block
                    if any(k in txt_lower for k in ["privacy policy", "japanesetest4you"]): continue
                    passage_parts.append(child.get_text(separator="\n", strip=True))

            # Final check: If passage is empty, the site might have a weird structure.
            # We join with double newlines
            passage_content = "\n\n".join(passage_parts)
            
            # If after all that, we still have no passage but questions exist, 
            # maybe the passage was inside a div we processed.
            # But based on Exercise 01/44, this should work.

            return [{
                "title": main_title,
                "passage": passage_content,
                "questions": questions
            }]
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return []

    # Other methods used for other tabs
    @staticmethod
    def scrape_listening(url: str) -> List[Dict[str, Any]]:
        """Scrape listening exercises, associating each audio with its question."""
        try:
            r = requests.get(url, headers=JT4YScraper.HEADERS, timeout=15)
            r.raise_for_status()
            s = BeautifulSoup(r.content, 'html.parser')
            c = JT4YScraper._get_main_content(s)
            if not c: return []

            main_title = JT4YScraper._get_title(s)
            answer_map = JT4YScraper._find_answer_map(c)
            
            # 1. Identify all audio tags/sources in order
            found_audios = []
            for audio_tag in c.find_all('audio'):
                src = audio_tag.get('src')
                if not src and audio_tag.find('source'):
                    src = audio_tag.find('source').get('src')
                if src:
                    found_audios.append(src)

            # 2. Collect all elements and identify blocks
            blocks = []
            current_block = {"audios": [], "q_num": None, "q_text": "", "options": {}}
            
            for child in c.children:
                if not child or not hasattr(child, 'name') or not child.name: continue
                
                # Check for audio
                audio_tags = child.find_all('audio') if child.name != 'audio' else [child]
                for a in audio_tags:
                    src = a.get('src') or (a.find('source').get('src') if a.find('source') else None)
                    if src:
                        # If we already have a question number in the current block, 
                        # this new audio might belong to the NEXT question.
                        if current_block["q_num"] is not None:
                            blocks.append(current_block)
                            current_block = {"audios": [], "q_num": None, "q_text": "", "options": {}}
                        current_block["audios"].append(src)

                # Check for question marker
                txt = child.get_text(separator=" ", strip=True)
                m = re.match(r'^(\d+)[．.:\)]\s*Question\s*(\d*)', txt, re.I)
                if not m:
                    # Alternative marker: just the number at start for some older posts
                    m = re.match(r'^(\d+)[．.:\)]\s*(.*)', txt)
                
                if m:
                    q_num = int(m.group(1))
                    # If we already have a question and this is a NEW number, close the previous block
                    if current_block["q_num"] is not None and current_block["q_num"] != q_num:
                        blocks.append(current_block)
                        current_block = {"audios": [], "q_num": q_num, "q_text": "", "options": {}}
                    
                    current_block["q_num"] = q_num
                    current_block["q_text"] = m.group(2) if len(m.groups()) > 1 else f"Question {q_num}"

                # Check for options
                radio_inputs = child.find_all('input', type='radio')
                if radio_inputs:
                    full_html_bits = []
                    for node in child.contents:
                        if node.name == 'input' and node.get('type') == 'radio':
                            full_html_bits.append("[[OPT]]")
                        else:
                            if hasattr(node, 'get_text'):
                                full_html_bits.append(node.get_text(strip=True))
                    
                    segments = " ".join(full_html_bits).split("[[OPT]]")
                    for seg in segments[1:]:
                        opt_val = re.sub(r'^(?:\d+[．.:\)]|\s*[◯○●①②③④]|[1-4a-d][．.:\)])\s*', '', seg, flags=re.I).strip()
                        if opt_val:
                            current_block["options"][str(len(current_block["options"]) + 1)] = opt_val

            # Final block
            if current_block["q_num"] is not None or current_block["audios"]:
                blocks.append(current_block)

            # 3. Associate and Build Results
            all_questions_with_audio = []
            for b in blocks:
                if not b["q_num"] and not b["audios"]: continue
                
                q_num = b["q_num"] or (len(all_questions_with_audio) + 1)
                all_questions_with_audio.append({
                    "number": q_num,
                    "text": b["q_text"] or f"Question {q_num}",
                    "options": b["options"],
                    "answer": str(answer_map.get(q_num, "")),
                    "audio_url": b["audios"][0] if b["audios"] else None
                })
            
            # Return a single record for the whole page
            return [{
                "title": main_title,
                "questions": all_questions_with_audio,
                "raw_content": c.get_text(separator="\n")
            }]
        except Exception as e:
            print(f"Error scraping listening {url}: {e}")
            return []

    @staticmethod
    def scrape_grammar_vocab_kanji(url: str) -> List[Dict[str, Any]]:
        # This is a simplified version for MCQ tabs
        try:
            r = requests.get(url, headers=JT4YScraper.HEADERS, timeout=15)
            s = BeautifulSoup(r.content, 'html.parser')
            c = JT4YScraper._get_main_content(s)
            if not c: return []
            ans = JT4YScraper._find_answer_map(c)
            qs = []
            for p in c.find_all('p'):
                txt = p.get_text(separator="\n", strip=True)
                lines = [l.strip() for l in txt.split("\n") if l.strip()]
                if not lines: continue
                m = re.match(r'^(\d+)[．.:\)]\s*(.*)', lines[0])
                if m:
                    q_num = int(m.group(1))
                    opts = {}
                    for l in lines[1:]:
                        clean = re.sub(r'^(?:\d+[．.:\)]|\s*[◯○●①②③④]|[1-4a-d][．.:\)])\s*', '', l, flags=re.I).strip()
                        if clean: opts[str(len(opts) + 1)] = clean
                    if opts:
                        qs.append({"number": q_num, "text": m.group(2).strip(), "options": opts, "answer": str(ans.get(q_num, ""))})
            return qs
        except Exception: return []

    @staticmethod
    def download_asset(url: str, subfolder: str) -> Optional[str]:
        try:
            base = r"c:\ProgramData\Sandbox\Projects\EnglishApp\data\assets\jt4y"
            os.makedirs(os.path.join(base, subfolder), exist_ok=True)
            name = f"{uuid.uuid4()}.mp3"
            path = os.path.join(base, subfolder, name)
            r = requests.get(url, stream=True, timeout=30)
            with open(path, 'wb') as f:
                for ch in r.iter_content(8192): f.write(ch)
            return f"data/assets/jt4y/{subfolder}/{name}"
        except Exception: return None
