import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import pandas as pd
import re

file_path = r"C:\Users\Admin\Downloads\[Tailieutiengnhat.net]_tu-vung-tieng-nhat-n1-day-du.xlsx"
sheet_name = "斁E���E語彁E耳からN1"

df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
kanjis = set()
for val in df.iloc[:, 1].dropna():
    if isinstance(val, str):
        # Extract kanji characters
        for char in val:
            if '\u4e00' <= char <= '\u9faf':
                kanjis.add(char)

print(f"Total unique kanjis: {len(kanjis)}")
print(list(kanjis))

