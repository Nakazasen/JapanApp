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
    answers = {}
    for page_num in [91, 92]:
        page_text = pdf.pages[page_num].extract_text()
        if not page_text: continue
        lines = page_text.split('\n')
        
        current_issues = []
        current_qs = []
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # Match "蝠城｡・1. 2. 10." or "蝠城｡・1 2 3"
            if line.startswith("蝠城｡・) and any(char.isdigit() for char in line):
                nums = re.findall(r'\d+', line)
                if nums:
                    current_issues = [int(n) for n in nums]
                    current_qs = []
                continue
            
            # Match "蝠・1. 2. 1. 2." 
            if line.startswith("蝠・) and any(char.isdigit() for char in line):
                nums = re.findall(r'\d+', line)
                if nums:
                    current_qs = [int(n) for n in nums]
                continue
                
            if line.startswith("豁｣隗｣"):
                values = re.findall(r'\d+', line)
                if not values: continue
                
                if current_qs and len(current_issues) > 0:
                    val_idx = 0
                    # Identify how many Qs per issue
                    # If we have issues [75, 76] and Qs [1, 2, 1, 2]
                    # We split values [ans1, ans2, ans3, ans4]
                    
                    q_idx = 0
                    for issue_id in current_issues:
                        issue_ans = {}
                        # Logic: usually each issue has a set of questions starting at 1
                        # If current_qs is [1, 2, 1, 2], first 2 go to first issue, next 2 to second
                        if q_idx < len(current_qs):
                            start_q = current_qs[q_idx]
                            issue_ans[start_q] = values[val_idx] if val_idx < len(values) else ""
                            val_idx += 1
                            q_idx += 1
                            while q_idx < len(current_qs) and current_qs[q_idx] != 1:
                                issue_ans[current_qs[q_idx]] = values[val_idx] if val_idx < len(values) else ""
                                val_idx += 1
                                q_idx += 1
                        answers[issue_id] = issue_ans
                        
                elif current_issues:
                    # Single question style
                    for idx, issue_id in enumerate(current_issues):
                        if idx < len(values):
                            answers[issue_id] = {1: values[idx]}
                
                # Don't clear current_issues if '蝠・ line follows on next iteration for the SAME issues
                # But usually '豁｣隗｣' is the end of a block.
    return answers

def clean_text(text):
    if not text: return ""
    text = re.sub(r'Thaolejp_N1_100 bﾃi ﾄ黛ｻ皇 hi盻ブ N1', '', text)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        if line.strip().isdigit(): continue
        cleaned_lines.append(line)
    return '\n'.join(cleaned_lines).strip()

def parse_pdf():
    with pdfplumber.open(pdf_path) as pdf:
        answer_key = parse_answers(pdf)
        print(f"Parsed answers for {len(answer_key)} issues.")

        data_rows = []
        full_text = ""
        for i in range(5, 91):
            full_text += pdf.pages[i].extract_text() + "\n"

        # Improved splitting regex
        # Problems can be "蝠城｡・1", "蝠城｡・", "蝠城｡・100"
        # We look for "蝠城｡・ followed by optional space and digits at the start of original lines
        # But since we merged text, let's use a capture group
        
        # Actually, let's use re.finditer to find starting positions
        matches = list(re.finditer(r'蝠城｡圭s*(\d+)', full_text))
        
        for i in range(len(matches)):
            start_pos = matches[i].start()
            end_pos = matches[i+1].start() if i + 1 < len(matches) else len(full_text)
            
            issue_header = matches[i].group(0)
            issue_id = int(matches[i].group(1))
            issue_body = full_text[matches[i].end():end_pos]
            
            title = f"Bﾃi ﾄ黛ｻ皇 N1 - S盻・{issue_id}"
            
            # Search for QUESTIONS
            q_matches = list(re.finditer(r'蝠・[・托ｼ抵ｼ・23])', issue_body))
            
            if not q_matches:
                # Try a more broad search if specific '蝠・ marker fails
                # Some might use "・托ｼ・ directly for the only question
                if issue_id <= 74:
                    # For issues 1-74, often there's just one implicit question
                    # or it starts with "蝠擾ｼ・ but maybe it's "蝠・" (half-width)
                    pass

            if q_matches:
                passage_text = issue_body[:q_matches[0].start()]
                # Clean passage
                passage_text = clean_text(passage_text)
                passage_text = re.sub(r'谺｡縺ｮ譁・ｫ繧定ｪｭ繧薙〒.*遲斐∴縺ｪ縺輔＞縲・, '', passage_text).strip()
                
                for j in range(len(q_matches)):
                    q_start = q_matches[j].start()
                    q_end = q_matches[j+1].start() if j + 1 < len(q_matches) else len(issue_body)
                    
                    q_full_header = q_matches[j].group(0)
                    q_num_char = q_matches[j].group(1)
                    q_num_map = {'・・: 1, '・・: 2, '・・: 3, '1': 1, '2': 2, '3': 3}
                    q_num = q_num_map.get(q_num_char)
                    
                    q_body = issue_body[q_start:q_end]
                    
                    # Split question text and options
                    opt_split = re.split(r'([・托ｼ抵ｼ難ｼ・234][・・\s])', q_body)
                    question_text = clean_text(opt_split[0])
                    # Remove the "蝠醜" from question text
                    question_text = re.sub(r'蝠充・托ｼ抵ｼ・23][・・]?', '', question_text).strip()
                    
                    options = {}
                    for o in range(1, len(opt_split), 2):
                        o_header = opt_split[o]
                        o_val = opt_split[o+1]
                        o_num_match = re.search(r'[・托ｼ抵ｼ難ｼ・234]', o_header)
                        if o_num_match:
                            o_num_map = {'・・: 1, '・・: 2, '・・: 3, '・・: 4, '1': 1, '2': 2, '3': 3, '4': 4}
                            o_num = o_num_map.get(o_num_match.group())
                            options[f"Option_{o_num}"] = clean_text(o_val)
                    
                    correct_ans = answer_key.get(issue_id, {}).get(q_num, "")
                    
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
                        "Explanation": "",
                        "Level": "N1",
                        "Source": "Tiengnhathay.com"
                    })
            else:
                # Case for single question without a clear "蝠醜" header?
                # Let's try to extract passage and options if possible
                pass

        print(f"Extracted {len(data_rows)} rows.")
        df = pd.DataFrame(data_rows)
        df.to_excel(output_excel, index=False)

if __name__ == "__main__":
    parse_pdf()

