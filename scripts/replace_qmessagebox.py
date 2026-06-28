import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Script v2 - Replace ALL remaining QMessageBox.information across all tab files."""
import re
import os

TAB_FILES = [
    r"c:\ProgramData\Sandbox\Projects\EnglishApp\frontend\ui\tabs\vocab_tab.py",
    r"c:\ProgramData\Sandbox\Projects\EnglishApp\frontend\ui\tabs\grammar_tab.py", 
    r"c:\ProgramData\Sandbox\Projects\EnglishApp\frontend\ui\tabs\kanji_tab.py",
    r"c:\ProgramData\Sandbox\Projects\EnglishApp\frontend\ui\tabs\youtube_tab.py",
    r"c:\ProgramData\Sandbox\Projects\EnglishApp\frontend\ui\tabs\writing_tab.py",
    r"c:\ProgramData\Sandbox\Projects\EnglishApp\frontend\ui\tabs\speaking_tab.py",
    r"c:\ProgramData\Sandbox\Projects\EnglishApp\frontend\ui\tabs\reading_tab.py",
    r"c:\ProgramData\Sandbox\Projects\EnglishApp\frontend\ui\tabs\reading_practice_tab.py",
    r"c:\ProgramData\Sandbox\Projects\EnglishApp\frontend\ui\tabs\listening_practice_tab.py",
    r"c:\ProgramData\Sandbox\Projects\EnglishApp\frontend\ui\tabs\settings_tab.py",
    r"c:\ProgramData\Sandbox\Projects\EnglishApp\frontend\ui\tabs\vocab_practice_tab.py",
    r"c:\ProgramData\Sandbox\Projects\EnglishApp\frontend\ui\tabs\grammar_practice_tab.py",
    r"c:\ProgramData\Sandbox\Projects\EnglishApp\frontend\ui\tabs\kanji_practice_tab.py",
]

TOAST_IMPORT = "from frontend.utils.toast_helper import toast_success, toast_error, toast_info, toast_warning"

def add_toast_import(content: str) -> str:
    """Add toast import if not present."""
    if "from frontend.utils.toast_helper" in content:
        return content
    
    # Find the last import line
    lines = content.split('\n')
    last_import_idx = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            last_import_idx = i
    
    # Insert after last import
    lines.insert(last_import_idx + 1, TOAST_IMPORT)
    return '\n'.join(lines)

def replace_qmessagebox_info(content: str) -> tuple[str, int]:
    """Replace ALL QMessageBox.information with toast."""
    count = 0
    
    # Pattern for simple single-line: QMessageBox.information(self, "Title", "Message")
    pattern_simple = r'QMessageBox\.information\s*\(\s*self\s*,\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)'
    
    def replace_simple(m):
        nonlocal count
        count += 1
        title = m.group(1)
        msg = m.group(2)
        if any(x in title.lower() for x in ['thành công', 'success', 'hoàn thành', 'hoàn tất', 'chúc mừng']):
            return f'toast_success("{msg}")'
        elif any(x in title.lower() for x in ['lỗi', 'error', 'thất bại']):
            return f'toast_error("{msg}")'
        elif any(x in title.lower() for x in ['cảnh báo', 'warning']):
            return f'toast_warning("{msg}")'
        else:
            return f'toast_info("{msg}")'
    
    content = re.sub(pattern_simple, replace_simple, content)
    
    # Pattern for f-string: QMessageBox.information(self, "Title", f"...")
    pattern_fstring = r'QMessageBox\.information\s*\(\s*self\s*,\s*["\']([^"\']+)["\']\s*,\s*(f["\'][^"\']+["\'])\s*\)'
    
    def replace_fstring(m):
        nonlocal count
        count += 1
        title = m.group(1)
        msg = m.group(2)
        if any(x in title.lower() for x in ['thành công', 'success', 'hoàn thành', 'hoàn tất', 'chúc mừng']):
            return f'toast_success({msg})'
        elif any(x in title.lower() for x in ['lỗi', 'error', 'thất bại']):
            return f'toast_error({msg})'
        else:
            return f'toast_info({msg})'
    
    content = re.sub(pattern_fstring, replace_fstring, content)
    
    # Pattern for variable message: QMessageBox.information(self, "Title", msg)
    pattern_var = r'QMessageBox\.information\s*\(\s*self\s*,\s*["\']([^"\']+)["\']\s*,\s*(\w+)\s*\)'
    
    def replace_var(m):
        nonlocal count
        count += 1
        title = m.group(1)
        var_name = m.group(2)
        if any(x in title.lower() for x in ['thành công', 'success', 'hoàn thành', 'hoàn tất', 'chúc mừng']):
            return f'toast_success({var_name})'
        else:
            return f'toast_info({var_name})'
    
    content = re.sub(pattern_var, replace_var, content)
    
    return content, count

def process_file(filepath: str) -> int:
    """Process a single file."""
    if not os.path.exists(filepath):
        print(f"[SKIP] File not found: {filepath}")
        return 0
        
    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()
    
    # Add import
    content = add_toast_import(original)
    
    # Replace QMessageBox calls
    content, count = replace_qmessagebox_info(content)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] {os.path.basename(filepath)}: {count} replacements")
    else:
        print(f"[SKIP] {os.path.basename(filepath)}: no changes needed")
    
    return count

def main():
    total = 0
    for filepath in TAB_FILES:
        total += process_file(filepath)
    print(f"\nTotal: {total} more QMessageBox.information calls replaced with toast")

if __name__ == "__main__":
    main()

