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
            if line.startswith("蝠城｡・):
                current_issues = [int(n) for n in re.findall(r'\d+', line)]
                current_qs = []
            elif line.startswith("蝠・):
                current_qs = [int(n) for n in re.findall(r'\d+', line)]
            elif line.startswith("豁｣隗｣"):
                values = re.findall(r'\d+', line)
                if not values: continue
                if current_qs and current_issues:
                    val_idx = 0
                    q_idx = 0
                    for issue_id in current_issues:
                        issue_ans = {}
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
                    for idx, issue_id in enumerate(current_issues):
                        if idx < len(values): answers[issue_id] = {1: values[idx]}
    return answers

def clean_text(text):
    if not text: return ""
    text = re.sub(r'Thaolejp_N1_100 bﾃi ﾄ黛ｻ皇 hi盻ブ N1', '', text)
    lines = text.split('\n')
    cleaned = [l for l in lines if not l.strip().isdigit()]
    return '\n'.join(cleaned).strip()

def parse_pdf():
    with pdfplumber.open(pdf_path) as pdf:
        answer_key = parse_answers(pdf)
        print(f"Answers parsed for {len(answer_key)} issues.")

        full_text = ""
        for i in range(5, 91): # Pages 6 to 91
            full_text += pdf.pages[i].extract_text() + "\n"

        matches = list(re.finditer(r'蝠城｡圭s*(\d+)', full_text))
        data_rows = []

        for i in range(len(matches)):
            issue_id = int(matches[i].group(1))
            start_pos = matches[i].end()
            end_pos = matches[i+1].start() if i+1 < len(matches) else len(full_text)
            body = full_text[start_pos:end_pos]
            
            # Check for multiple questions "蝠擾ｼ・, "蝠擾ｼ托ｼ・, "蝠・1"
            q_matches = list(re.finditer(r'蝠・[・托ｼ抵ｼ・23])', body))
            
            if q_matches:
                # Multi-question logic
                passage_text = clean_text(body[:q_matches[0].start()])
                passage_text = re.sub(r'谺｡縺ｮ譁・ｫ繧定ｪｭ繧薙〒.*遲斐∴縺ｪ縺輔＞縲・, '', passage_text).strip()
                
                for j in range(len(q_matches)):
                    q_start = q_matches[j].start()
                    q_end = q_matches[j+1].start() if j+1 < len(q_matches) else len(body)
                    q_num = {'・・:1,'・・:2,'・・:3,'1':1,'2':2,'3':3}.get(q_matches[j].group(1))
                    
                    q_body = body[q_start:q_end]
                    opt_split = re.split(r'([・托ｼ抵ｼ難ｼ・234][・・\s])', q_body)
                    question_text = clean_text(opt_split[0])
                    question_text = re.sub(r'蝠充・托ｼ抵ｼ・23][・・]?', '', question_text).strip()
                    
                    options = {}
                    for k in range(1, len(opt_split), 2):
                        o_num = {'・・:1,'・・:2,'・・:3,'・・:4,'1':1,'2':2,'3':3,'4':4}.get(re.search(r'[・托ｼ抵ｼ難ｼ・234]', opt_split[k]).group())
                        options[f"Option_{o_num}"] = clean_text(opt_split[k+1])
                    
                    data_rows.append({
                        "Passage_ID": issue_id,
                        "Title": f"Bﾃi ﾄ黛ｻ皇 N1 - S盻・{issue_id}",
                        "Content": passage_text,
                        "Question": question_text,
                        "Option_1": options.get("Option_1", ""),
                        "Option_2": options.get("Option_2", ""),
                        "Option_3": options.get("Option_3", ""),
                        "Option_4": options.get("Option_4", ""),
                        "Answer": answer_key.get(issue_id, {}).get(q_num, ""),
                        "Explanation": "", "Level": "N1", "Source": "Tiengnhathay.com"
                    })
            else:
                # Single question logic (no "蝠擾ｼ・ header)
                # Split by first option "・托ｼ・
                opt_split = re.split(r'([・托ｼ抵ｼ難ｼ・234][・・\s])', body)
                if len(opt_split) > 1:
                    pre_opt_text = clean_text(opt_split[0])
                    # Last paragraph is usually the question
                    lines = pre_opt_text.split('\n')
                    # Find where instruction/content ends
                    # Often starts with "谺｡縺ｮ譁・ｫ縺ｧ..." or similar or just the last sentence
                    question_text = lines[-1] if lines else ""
                    content_text = '\n'.join(lines[:-1]) if len(lines) > 1 else pre_opt_text
                    
                    content_text = re.sub(r'谺｡縺ｮ譁・ｫ繧定ｪｭ繧薙〒.*遲斐∴縺ｪ縺輔＞縲・, '', content_text).strip()
                    
                    options = {}
                    for k in range(1, len(opt_split), 2):
                        o_num = {'・・:1,'・・:2,'・・:3,'・・:4,'1':1,'2':2,'3':3,'4':4}.get(re.search(r'[・托ｼ抵ｼ難ｼ・234]', opt_split[k]).group())
                        options[f"Option_{o_num}"] = clean_text(opt_split[k+1])
                        
                    data_rows.append({
                        "Passage_ID": issue_id,
                        "Title": f"Bﾃi ﾄ黛ｻ皇 N1 - S盻・{issue_id}",
                        "Content": content_text,
                        "Question": question_text,
                        "Option_1": options.get("Option_1", ""),
                        "Option_2": options.get("Option_2", ""),
                        "Option_3": options.get("Option_3", ""),
                        "Option_4": options.get("Option_4", ""),
                        "Answer": answer_key.get(issue_id, {}).get(1, ""),
                        "Explanation": "", "Level": "N1", "Source": "Tiengnhathay.com"
                    })

        print(f"Final Count: {len(data_rows)} rows.")
        pd.DataFrame(data_rows).to_excel(output_excel, index=False)
        print("Success.")

if __name__ == "__main__":
    parse_pdf()

