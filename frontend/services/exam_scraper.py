"""Exam scraping service for dethitiengnhat.com."""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re
from urllib.parse import urljoin, urlparse


class ExamScraperService:
    """Service for scraping JLPT exams from dethitiengnhat.com."""
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    BASE_URL = "https://dethitiengnhat.com"
    
    @staticmethod
    def get_exam_list(level: str = "N1") -> List[Dict]:
        """Get list of available exams for a JLPT level.
        
        Args:
            level: JLPT level (N1, N2, N3, N4, N5)
        
        Returns:
            List of exam info: {title, url, type, date}
        """
        try:
            url = f"{ExamScraperService.BASE_URL}/jlpt/{level}"
            response = requests.get(url, headers=ExamScraperService.HEADERS, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            exams = []
            
            # Find all exam links
            # The page has sections: Từ Vựng, Đọc Hiểu, Nghe
            sections = soup.find_all(['h2', 'h3', 'div'], class_=re.compile(r'section|category|group'))
            
            # Look for links with exam patterns
            links = soup.find_all('a', href=True)
            seen_urls = set()
            
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Check if it's an exam link
                if not text or len(text) < 10:
                    continue
                
                # Make absolute URL - convert to string first
                href_str = str(href) if href else ""
                if not href_str:
                    continue
                
                if href_str.startswith('/'):
                    href_str = urljoin(ExamScraperService.BASE_URL, href_str)
                elif not href_str.startswith('http'):
                    continue
                
                # Filter exam links
                if '/jlpt/' in href_str and level in href_str and href_str not in seen_urls:
                    seen_urls.add(href)
                    
                    # Determine exam type from text
                    exam_type = "Từ Vựng"
                    if "Đọc Hiểu" in text or "読解" in text:
                        exam_type = "Đọc Hiểu"
                    elif "Nghe" in text or "聴解" in text:
                        exam_type = "Nghe"
                    elif "Từ Vựng" in text or "文字語彙" in text:
                        exam_type = "Từ Vựng"
                    elif "Ngữ pháp" in text or "文法" in text:
                        exam_type = "Ngữ pháp"
                    
                    # Extract date from text or URL
                    date_match = re.search(r'(\d{2})/(\d{4})', text)
                    date_str = None
                    if date_match:
                        date_str = f"{date_match.group(1)}/{date_match.group(2)}"
                    
                    exams.append({
                        "title": text,
                        "url": href,
                        "type": exam_type,
                        "date": date_str,
                        "level": level
                    })
            
            return exams
        except Exception as e:
            raise RuntimeError(f"Failed to get exam list: {e}")
    
    @staticmethod
    def scrape_exam(exam_url: str) -> Dict:
        """Scrape exam questions from a specific exam URL.
        
        Args:
            exam_url: URL of the exam page
        
        Returns:
            Dictionary with exam info and questions
        """
        try:
            response = requests.get(exam_url, headers=ExamScraperService.HEADERS, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = None
            title_tag = soup.find('h1') or soup.find('h2') or soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)
            
            questions = []
            
            # Find instruction text (usually at the top of the form or in a specific div)
            instruction_text = ""
            # Look for instruction in various places
            instruction_pattern = re.compile(r'問題\d+.*?選びなさい', re.DOTALL)
            
            # Try to find instruction text
            # Method 1: Find by string content
            instruction_elem = soup.find(string=instruction_pattern)
            if instruction_elem:
                if isinstance(instruction_elem, str):
                    instruction_text = instruction_elem.strip()
                elif hasattr(instruction_elem, 'parent'):
                    parent = instruction_elem.parent
                    if parent:
                        instruction_text = parent.get_text(strip=True)
            
            # Method 2: Find in p or div tags
            if not instruction_text:
                for tag_name in ['p', 'div']:
                    tags = soup.find_all(tag_name)
                    for tag in tags:
                        tag_text = tag.get_text(strip=True)
                        if instruction_pattern.search(tag_text):
                            instruction_text = tag_text
                            break
                    if instruction_text:
                        break
            
            # Method 1: Find question containers (div.question_list or similar)
            # Look for common question container classes
            question_containers = (
                soup.find_all('div', class_=re.compile(r'question|problem|item', re.I)) +
                soup.find_all('div', id=re.compile(r'question|problem|item', re.I)) +
                soup.find_all('table', class_=re.compile(r'question|problem|item', re.I))
            )
            
            # If no specific containers, look for forms
            forms = soup.find_all('form')
            
            # Method 1a: Parse by question containers first
            if question_containers:
                for container in question_containers:
                    # Get all text in container
                    container_text = container.get_text(separator='\n', strip=True)
                    
                    # Find all radio buttons in this container
                    radios = container.find_all('input', type='radio')
                    if not radios:
                        continue
                    
                    # Group radios by name (each name = one question)
                    radio_groups = {}
                    for radio in radios:
                        name = radio.get('name', '')
                        if name:
                            if name not in radio_groups:
                                radio_groups[name] = []
                            radio_groups[name].append(radio)
                    
                    # Process each question group
                    for name, radio_list in radio_groups.items():
                        if not radio_list:
                            continue
                        
                        first_radio = radio_list[0]
                        q_num_match = re.search(r'(\d+)', name)
                        question_num = int(q_num_match.group(1)) if q_num_match else len(questions) + 1
                        
                        # Get the row/div containing this question's radios
                        question_row = first_radio.find_parent(['tr', 'div', 'p', 'li'])
                        if not question_row:
                            question_row = container
                        
                        # Extract options - get clean text only
                        options = {}
                        seen_options = set()
                        
                        for radio in radio_list[:4]:  # Limit to 4
                            value = radio.get('value', '')
                            
                            # Get text after radio button
                            option_text = ""
                            label = radio.find_next(['label'])
                            if label:
                                option_text = label.get_text(strip=True)
                            else:
                                next_elem = radio.next_sibling
                                if next_elem:
                                    if isinstance(next_elem, str):
                                        option_text = next_elem.strip()
                                    else:
                                        option_text = next_elem.get_text(strip=True) if hasattr(next_elem, 'get_text') else value
                                else:
                                    option_text = value
                            
                            # Clean option text
                            option_text = re.sub(r'^\d+[\)\.]\s*', '', option_text).strip()
                            # Remove duplicates
                            parts = re.split(r'\s*[\.・]\s*', option_text)
                            if len(parts) > 1:
                                unique_parts = [p.strip() for p in parts if p.strip() and p.strip() not in seen_options]
                                if unique_parts:
                                    option_text = unique_parts[0]
                            
                            option_text = option_text.rstrip('. ').strip()
                            
                            if option_text and option_text not in seen_options and len(options) < 4:
                                seen_options.add(option_text)
                                options[value] = option_text
                        
                        # Extract question text - get text before first radio in question_row
                        row_text = question_row.get_text(separator='\n', strip=True)
                        japanese_sentence = ""
                        
                        # Find where options start
                        if options:
                            first_option = list(options.values())[0]
                            # Find option marker in text
                            option_marker = re.compile(r'\d+\)\s*' + re.escape(first_option[:6]), re.IGNORECASE)
                            option_match = option_marker.search(row_text)
                            
                            if option_match:
                                text_before = row_text[:option_match.start()].strip()
                                
                                # Extract Japanese sentence - pattern: "数字. [Japanese text ending with 。]"
                                japanese_pattern = re.compile(r'(\d+)\.\s*([^。\n]*[。])', re.MULTILINE)
                                match = japanese_pattern.search(text_before)
                                if match:
                                    found_num = int(match.group(1))
                                    if found_num == question_num:
                                        japanese_sentence = match.group(2).strip()
                                
                                # If no match, try simpler pattern
                                if not japanese_sentence:
                                    simple_pattern = re.compile(r'(\d+)\.\s*([^\d\)]+)', re.MULTILINE)
                                    simple_match = simple_pattern.search(text_before)
                                    if simple_match:
                                        found_num = int(simple_match.group(1))
                                        if found_num == question_num:
                                            japanese_sentence = simple_match.group(2).strip()
                                            if japanese_sentence.endswith('.') and '。' not in japanese_sentence:
                                                japanese_sentence = japanese_sentence.rstrip('.')
                                
                                # If still no match, use text before options (cleaned)
                                if not japanese_sentence:
                                    japanese_sentence = text_before
                                    # Remove instruction
                                    if instruction_text and japanese_sentence.startswith(instruction_text):
                                        japanese_sentence = japanese_sentence[len(instruction_text):].strip()
                                    # Remove question number prefix
                                    japanese_sentence = re.sub(r'^\d+\.\s*', '', japanese_sentence).strip()
                                    # CRITICAL: Remove any option-like patterns (e.g., "1) せっきょう")
                                    # This is the key fix - remove patterns that look like options
                                    japanese_sentence = re.sub(r'\d+[\)\.]\s*[^\s。]+', '', japanese_sentence).strip()
                                    
                                    # Additional check: if the remaining text looks like an option (short, only hiragana/katakana), skip it
                                    if japanese_sentence:
                                        # Check if text is too short or looks like an option
                                        if len(japanese_sentence) < 10 or re.match(r'^[\u3040-\u309F\u30A0-\u30FF]+$', japanese_sentence):
                                            # This might be an option, try to find a longer sentence
                                            japanese_sentence = ""
                        
                        # Build question text
                        question_parts = []
                        if instruction_text:
                            question_parts.append(instruction_text)
                        
                        if japanese_sentence:
                            question_parts.append(f"{question_num}. {japanese_sentence}")
                        else:
                            question_parts.append(f"Câu hỏi {question_num}")
                        
                        question_text = '\n'.join(question_parts)
                        
                        # Add question
                        if options:
                            questions.append({
                                "question_number": question_num,
                                "question_text": question_text,
                                "options": options,
                                "correct_option": ""
                            })
            
            # Method 1b: Parse by forms if no question containers found
            if not questions:
                for form in forms:
                    # Find all table rows that contain questions
                    table_rows = form.find_all('tr')
                    
                    # Group radios by name to identify questions
                    radio_groups = {}
                    radios = form.find_all('input', type='radio')
                    
                    # First pass: collect all radio buttons and group by name
                    for radio in radios:
                        name = radio.get('name', '')
                        value = radio.get('value', '')
                        
                        if not name:
                            continue
                        
                        if name not in radio_groups:
                            radio_groups[name] = {
                                'radios': [],
                                'question_num': None
                            }
                        
                        radio_groups[name]['radios'].append(radio)
                        
                        # Extract question number from name
                        if radio_groups[name]['question_num'] is None:
                            name_str = str(name) if name else ""
                            q_num_match = re.search(r'(\d+)', name_str)
                            if q_num_match:
                                radio_groups[name]['question_num'] = int(q_num_match.group(1))
                    
                    # Second pass: for each question group, find the question text
                    for name, group_data in radio_groups.items():
                        if not group_data['radios']:
                            continue
                        
                        first_radio = group_data['radios'][0]
                        
                        # Find the table row containing this question
                        question_row = first_radio.find_parent('tr')
                        if not question_row:
                            # Try to find any container
                            question_row = first_radio.find_parent(['div', 'p', 'td'])
                        
                        if not question_row:
                            continue
                        
                        # Get all text in the row/container
                        row_text = question_row.get_text(separator='\n', strip=True)
                        
                        # Extract options from radio buttons - get clean text only
                        options = {}
                        seen_options = set()  # Track to avoid duplicates
                        
                        for radio in group_data['radios'][:4]:  # Limit to 4 options
                            value = radio.get('value', '')
                            
                            # Find label or text after radio - get only the immediate text
                            option_text = ""
                            
                            # Method 1: Check for label
                            label = radio.find_next(['label'])
                        if label:
                            option_text = label.get_text(strip=True)
                        else:
                            # Method 2: Get text immediately after radio button
                            # Look for text node or next element
                            current = radio.next_sibling
                            while current and not option_text:
                                if isinstance(current, str):
                                    text = current.strip()
                                    if text and len(text) > 2:  # Valid text
                                        option_text = text
                                        break
                                elif hasattr(current, 'name') and hasattr(current, 'get_text'):
                                    # Check if it's a Tag element with name attribute
                                    try:
                                        tag_name = getattr(current, 'name', None)
                                        if tag_name and tag_name in ['span', 'td', 'div']:
                                            text = current.get_text(strip=True)
                                            if text and len(text) > 2:
                                                option_text = text
                                                break
                                    except (AttributeError, TypeError):
                                        pass
                                # Move to next sibling
                                if isinstance(current, str):
                                    # String doesn't have next_sibling, need to get from parent
                                    if hasattr(radio, 'parent') and radio.parent:
                                        # Find next element after radio
                                        for sibling in radio.parent.children:
                                            if sibling == radio:
                                                # Next iteration will be the next sibling
                                                pass
                                            elif sibling == current:
                                                # Get next sibling after current
                                                try:
                                                    siblings = list(radio.parent.children)
                                                    idx = siblings.index(sibling)
                                                    if idx + 1 < len(siblings):
                                                        current = siblings[idx + 1]
                                                    else:
                                                        current = None
                                                except (ValueError, IndexError):
                                                    current = None
                                                break
                                    else:
                                        current = None
                                elif hasattr(current, 'next_sibling'):
                                    current = current.next_sibling
                                else:
                                    current = None
                            
                            # If still no text, use value
                            if not option_text:
                                option_text = value
                            
                            # Clean option text - remove leading numbers and formatting
                            option_text_str = str(option_text) if option_text else ""
                            option_text = re.sub(r'^\d+[\)\.]\s*', '', option_text_str).strip()
                            
                            # Remove duplicate patterns (e.g., "せっきょう . せっきょう" -> "せっきょう")
                            # Split by common separators
                            parts = re.split(r'\s*[\.・]\s*', option_text)
                            if len(parts) > 1:
                                # Check if parts are duplicates
                                unique_parts = []
                                for part in parts:
                                    part = part.strip()
                                    if part and part not in unique_parts:
                                        unique_parts.append(part)
                                # If all parts are the same, use only one
                                if len(unique_parts) == 1:
                                    option_text = unique_parts[0]
                                else:
                                    # Use first meaningful part (usually the hiragana reading)
                                    option_text = unique_parts[0] if unique_parts else option_text
                            
                            # Remove any trailing dots or spaces
                            option_text = option_text.rstrip('. ').strip()
                            
                            # Skip if empty or duplicate
                            if option_text and option_text not in seen_options and len(options) < 4:
                                seen_options.add(option_text)
                                options[value] = option_text
                            
                            # Stop if we have 4 unique options
                            if len(options) >= 4:
                                break
                        
                        # Extract question text - find Japanese sentence before options
                        # CRITICAL: Must NOT include any option text in the question
                        japanese_sentence = ""
                        question_num = group_data['question_num'] or len(questions) + 1
                        
                        # Get text from question_row
                        row_text = question_row.get_text(separator='\n', strip=True)
                        
                        # Find where options start - look for first option text
                        if options:
                            first_option = list(options.values())[0]
                            
                            # Find position of first option in row_text
                            # Look for pattern like "1) option_text" or "1. option_text"
                            option_patterns = [
                                re.compile(r'\d+\)\s*' + re.escape(first_option[:6]), re.IGNORECASE),
                                re.compile(r'\d+\.\s*' + re.escape(first_option[:6]), re.IGNORECASE),
                            ]
                            
                            option_pos = -1
                            for pattern in option_patterns:
                                match = pattern.search(row_text)
                                if match:
                                    option_pos = match.start()
                                    break
                            
                            if option_pos > 0:
                                # Get text before options
                                text_before_options = row_text[:option_pos].strip()
                                
                                # CRITICAL: Remove any option-like patterns from text_before_options
                                # Remove patterns like "1) text" or "1. text" that look like options
                                text_before_options = re.sub(r'\d+[\)\.]\s*[^\s。]+', '', text_before_options).strip()
                                
                                # Extract Japanese sentence - pattern: "数字. [Japanese text ending with 。]"
                                japanese_pattern = re.compile(r'(\d+)\.\s*([^。\n]*[。])', re.MULTILINE)
                                match = japanese_pattern.search(text_before_options)
                                if match:
                                    found_num = int(match.group(1))
                                    if found_num == question_num:
                                        japanese_sentence = match.group(2).strip()
                                
                                # If no match, try simpler pattern
                                if not japanese_sentence:
                                    simple_pattern = re.compile(r'(\d+)\.\s*([^\d\)]+)', re.MULTILINE)
                                    simple_match = simple_pattern.search(text_before_options)
                                    if simple_match:
                                        found_num = int(simple_match.group(1))
                                        if found_num == question_num:
                                            japanese_sentence = simple_match.group(2).strip()
                                            # Remove trailing dot if not Japanese period
                                            if japanese_sentence.endswith('.') and '。' not in japanese_sentence:
                                                japanese_sentence = japanese_sentence.rstrip('.')
                                
                                # If still no match, look for any Japanese sentence (with kanji/hiragana)
                                if not japanese_sentence:
                                    # Look for pattern with Japanese characters ending with 。
                                    japanese_char_pattern = re.compile(r'([\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+[。])', re.MULTILINE)
                                    match = japanese_char_pattern.search(text_before_options)
                                    if match:
                                        japanese_sentence = match.group(1).strip()
                                        # Remove leading number if present
                                        japanese_sentence = re.sub(r'^\d+\.\s*', '', japanese_sentence).strip()
                                    
                                    # If still no match, use cleaned text_before_options
                                    if not japanese_sentence:
                                        japanese_sentence = text_before_options
                                        # Remove instruction if present
                                        if instruction_text and japanese_sentence.startswith(instruction_text):
                                            japanese_sentence = japanese_sentence[len(instruction_text):].strip()
                                        # Remove question number prefix
                                        japanese_sentence = re.sub(r'^\d+\.\s*', '', japanese_sentence).strip()
                                        # Remove any remaining option-like patterns
                                        japanese_sentence = re.sub(r'\d+[\)\.]\s*[^\s。]+', '', japanese_sentence).strip()
                        
                        # Fallback: If still no sentence, try to find in parent container
                        if not japanese_sentence:
                            parent = question_row.find_parent(['div', 'tr', 'td'])
                            if parent:
                                parent_text = parent.get_text(separator='\n', strip=True)
                                # Find Japanese sentence pattern
                                japanese_pattern = re.compile(r'(\d+)\.\s*([^。\n]*[。])', re.MULTILINE)
                                match = japanese_pattern.search(parent_text)
                                if match:
                                    found_num = int(match.group(1))
                                    if found_num == question_num:
                                        japanese_sentence = match.group(2).strip()
                        
                        # Build question text
                        question_parts = []
                        if instruction_text:
                            question_parts.append(instruction_text)
                        
                        if japanese_sentence:
                            question_parts.append(f"{question_num}. {japanese_sentence}")
                        else:
                            question_parts.append(f"Câu hỏi {question_num}")
                        
                        question_text = '\n'.join(question_parts)
                        
                        # Add question
                        if options:
                            questions.append({
                                "question_number": question_num,
                                "question_text": question_text,
                                "options": options,
                                "correct_option": ""
                            })
            
            # Method 2: If no forms, try to parse from text patterns
            if not questions:
                # Look for numbered questions in text
                all_text = soup.get_text(separator='\n')
                # Pattern: "1.", "問題1", etc.
                question_pattern = re.compile(r'^(\d+)\.|^問題\s*(\d+)|^Câu\s*(\d+)', re.MULTILINE | re.IGNORECASE)
                matches = list(question_pattern.finditer(all_text))
                
                if matches:
                    for i, match in enumerate(matches):
                        q_num = int(match.group(1) or match.group(2) or match.group(3))
                        start_pos = match.start()
                        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(all_text)
                        question_text = all_text[start_pos:end_pos].strip()
                        
                        question_data = ExamScraperService._parse_question(question_text, soup)
                        if question_data:
                            question_data['question_number'] = q_num
                            questions.append(question_data)
            
            # Sort questions by question number
            questions.sort(key=lambda x: x.get('question_number', 0))
            
            # Remove duplicates based on question_number
            seen_numbers = set()
            unique_questions = []
            for q in questions:
                q_num = q.get('question_number', 0)
                if q_num not in seen_numbers:
                    seen_numbers.add(q_num)
                    unique_questions.append(q)
                else:
                    # If duplicate, keep the one with more options or better question text
                    existing = next((x for x in unique_questions if x.get('question_number') == q_num), None)
                    if existing:
                        if len(q.get('options', {})) > len(existing.get('options', {})):
                            unique_questions.remove(existing)
                            unique_questions.append(q)
            
            # Re-number questions sequentially
            for idx, q in enumerate(unique_questions, 1):
                q['question_number'] = idx
            
            return {
                "title": title or "Untitled Exam",
                "url": exam_url,
                "questions": unique_questions,
                "total_questions": len(unique_questions)
            }
        except Exception as e:
            raise RuntimeError(f"Failed to scrape exam: {e}")
    
    @staticmethod
    def _parse_question(text: str, soup: BeautifulSoup) -> Optional[Dict]:
        """Parse a question from text.
        
        Args:
            text: Question text
            soup: BeautifulSoup object for additional parsing
        
        Returns:
            Dictionary with question data or None
        """
        try:
            # Extract question number
            q_num_match = re.search(r'(?:問題|Question|Câu)\s*(\d+)', text, re.IGNORECASE)
            question_num = int(q_num_match.group(1)) if q_num_match else 0
            
            # Extract options (typically 1, 2, 3, 4 or A, B, C, D)
            options = {}
            option_pattern = re.compile(r'([1-4]|A|B|C|D)[\.\)]\s*([^\d]+?)(?=[1-4]|A|B|C|D|$)', re.DOTALL)
            matches = option_pattern.findall(text)
            
            for match in matches:
                option_key = match[0]
                option_text = match[1].strip()
                if option_text:
                    options[option_key] = option_text
            
            # If no options found, try different pattern
            if not options:
                # Look for numbered list
                lines = text.split('\n')
                for line in lines:
                    option_match = re.match(r'^([1-4]|A|B|C|D)[\.\)]\s*(.+)', line.strip())
                    if option_match:
                        options[option_match.group(1)] = option_match.group(2).strip()
            
            # Extract question text (everything before options)
            question_text = text
            if options:
                # Remove options from question text
                for key, value in options.items():
                    question_text = question_text.replace(f"{key}. {value}", "").replace(f"{key}) {value}", "")
                question_text = question_text.strip()
            
            if question_text and options:
                return {
                    "question_number": question_num,
                    "question_text": question_text,
                    "options": options,
                    "correct_option": None  # Would need to scrape from answer page
                }
            
            return None
        except Exception as e:
            print(f"Error parsing question: {e}")
            return None

