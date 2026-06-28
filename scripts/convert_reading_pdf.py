import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import pdfplumber
import pandas as pd
import re
import os

pdf_path = r"C:\Users\Admin\Downloads\Tiengnhathay.com_100-de-doc-hieu-n1.pdf"
output_excel = r"C:\ProgramData\Sandbox\Projects\EnglishApp\reading_n1_data.xlsx"

def parse_answers(pdf):
    """Parses the answer key from the last pages (92-93)."""
    answers = {} # {issue_num: {q_num: ans}}
    
    # Process pages 92 and 93
    for page_num in [91, 92]: # 0-indexed
        page_text = pdf.pages[page_num].extract_text()
        lines = page_text.split('\n')
        
        current_issues = []
        current_qs = []
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # Match "蝠城｡・1. 2. 10." line
            if line.startswith("蝠城｡・) and any(char.isdigit() for char in line):
                # Extract all numbers after "蝠城｡・
                current_issues = [int(n) for n in re.findall(r'\d+', line)]
                current_qs = [] # Reset Qs for these issues
                continue
            
            # Match "蝠・1. 2. 1. 2." line
            if line.startswith("蝠・) and any(char.isdigit() for char in line):
                current_qs = [int(n) for n in re.findall(r'\d+', line)]
                continue
                
            # Match "豁｣隗｣ 4 2 3 1" line
            if line.startswith("豁｣隗｣"):
                values = re.findall(r'\d+', line)
                
                if current_qs: # Multi-question style (75-100)
                    val_idx = 0
                    # Distribute values across issues based on Q count
                    # This logic assumes the '蝠・ line repeats numbers for each issue
                    # e.g. 1 2 1 2 1 2 for 3 issues
                    q_count_per_issue = {} # issue_id -> count
                    
                    # We need to know how many questions each issue has. 
                    # For issues 75-100, we usually have 2 or 3.
                    # Let's count occurrences of '1' in current_qs to split groups
                    groups = []
                    temp_group = []
                    for qnum in current_qs:
                        if qnum == 1 and temp_group:
                            groups.append(temp_group)
                            temp_group = [qnum]
                        else:
                            temp_group.append(qnum)
                    if temp_group: groups.append(temp_group)
                    
                    for idx, issue_id in enumerate(current_issues):
                        if idx < len(groups):
                            group_qs = groups[idx]
                            issue_ans = {}
                            for qnum in group_qs:
                                if val_idx < len(values):
                                    issue_ans[qnum] = values[val_idx]
                                    val_idx += 1
                            answers[issue_id] = issue_ans
                        
                else: # Single question style (1-74)
                    for idx, issue_id in enumerate(current_issues):
                        if idx < len(values):
                            answers[issue_id] = {1: values[idx]}
                
                current_issues = []
                current_qs = []
                
    return answers

def clean_text(text):
    if not text: return ""
    # Remove footer text
    text = re.sub(r'Thaolejp_N1_100 bﾃi ﾄ黛ｻ皇 hi盻ブ N1', '', text)
    # Remove page numbers at bottom or top (standalone digits on a line)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        if line.strip().isdigit(): continue
        cleaned_lines.append(line)
    return '\n'.join(cleaned_lines).strip()

def parse_pdf():
    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found at {pdf_path}")
        return

    data_rows = []
    
    with pdfplumber.open(pdf_path) as pdf:
        print("Parsing answers...")
        answer_key = parse_answers(pdf)
        
        print("Parsing passages and questions...")
        current_content = ""
        current_issue_id = None
        current_title = ""
        collecting_passage = False
        
        all_text = ""
        # Combine pages 6 to 91 for easier stream parsing
        for i in range(5, 91):
            all_text += pdf.pages[i].extract_text() + "\n"
        
        # Split by "蝠城｡・X" pattern
        # Use regex to find all "蝠城｡・\d+" and split
        parts = re.split(r'(蝠城｡圭s*\d+)', all_text)
        
        # parts looks like: ["text before", "蝠城｡・1", "content 1", "蝠城｡・2", "content 2"...]
        for idx in range(1, len(parts), 2):
            issue_header = parts[idx]
            issue_body = parts[idx+1]
            
            issue_id_match = re.search(r'\d+', issue_header)
            if not issue_id_match: continue
            issue_id = int(issue_id_match.group())
            
            title = f"Bﾃi ﾄ黛ｻ皇 N1 - S盻・{issue_id}"
            
            # Split body into Passage and Questions
            # Questions start with "蝠擾ｼ・, "蝠擾ｼ托ｼ・, "蝠・1" etc.
            # Usually follows "谺｡縺ｮ譁・ｫ繧定ｪｭ繧薙〒蠕後・蝠上＞縺ｫ遲斐∴縺ｪ縺輔＞縲・
            
            # Find the starting point of questions
            q_start_match = re.search(r'蝠充・・]', issue_body)
            if q_start_match:
                passage_text = issue_body[:q_start_match.start()]
                questions_text = issue_body[q_start_match.start():]
                
                # Clean passage
                passage_text = clean_text(passage_text)
                # Remove "谺｡縺ｮ譁・ｫ繧定ｪｭ繧薙〒蠕後・蝠上＞縺ｫ遲斐∴縺ｪ縺輔＞縲・
                passage_text = re.sub(r'谺｡縺ｮ譁・ｫ繧定ｪｭ繧薙〒.*遲斐∴縺ｪ縺輔＞縲・, '', passage_text).strip()
                
                # Split questions by "蝠醜"
                q_parts = re.split(r'(蝠充・托ｼ抵ｼ・23][・・]?)', questions_text)
                
                # q_parts: ["", "蝠・", "q1 text...", "蝠・", "q2 text..."]
                for q_idx in range(1, len(q_parts), 2):
                    q_header = q_parts[q_idx]
                    q_body = q_parts[q_idx+1]
                    
                    q_num_match = re.search(r'[・托ｼ抵ｼ・23]', q_header)
                    if not q_num_match: continue
                    # Map full-width to normal
                    q_num_map = {'・・: 1, '・・: 2, '・・: 3, '1': 1, '2': 2, '3': 3}
                    q_num = q_num_map.get(q_num_match.group())
                    
                    # Extract options 1-4
                    options = {}
                    # Pattern for options: "・托ｼ・, "1.", "・・"
                    # Split by the option markers
                    opt_parts = re.split(r'([・托ｼ抵ｼ難ｼ・234][・・\s])', q_body)
                    
                    question_text = clean_text(opt_parts[0])
                    
                    for o_idx in range(1, len(opt_parts), 2):
                        o_header = opt_parts[o_idx]
                        o_content = opt_parts[o_idx+1]
                        o_num_match = re.search(r'[・托ｼ抵ｼ難ｼ・234]', o_header)
                        if o_num_match:
                            o_num_map = {'・・: 1, '・・: 2, '・・: 3, '・・: 4, '1': 1, '2': 2, '3': 3, '4': 4}
                            o_num = o_num_map.get(o_num_match.group())
                            options[f"Option_{o_num}"] = clean_text(o_content)
                    
                    # Get Answer
                    correct_ans = ""
                    if issue_id in answer_key and q_num in answer_key[issue_id]:
                        correct_ans = answer_key[issue_id][q_num]
                    
                    data_rows.append({
                        "Passage_ID": issue_id,
                        "Title": title,
                        "Content": passage_text,
                        "Question": question_text,
                        "Option_1": options.get("Option_1", ""),
                        "Option_2": options.get("Option_2", ""),
                        "Option_3": options.get("Option_3", ""),
                        "Option_4": options.get("Option_4", ""),
                        "Answer": correct_ans,
                        "Explanation": "", # Empty per request if not found
                        "Level": "N1",
                        "Source": "Tiengnhathay.com"
                    })
            else:
                # No question found in this part? Maybe it's a multi-page passage
                # I'll log or skip for now
                pass

    print(f"Total rows extracted: {len(data_rows)}")
    df = pd.DataFrame(data_rows)
    df.to_excel(output_excel, index=False)
    print(f"File saved successfully to {output_excel}")

if __name__ == "__main__":
    parse_pdf()

