import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sys
import os
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication

def verify():
    # We omit QApplication and instantiation to avoid environment issues
    print("Testing VocabTab import...")
    from frontend.ui.tabs.vocab_tab import VocabTab
    print("VocabTab imported OK")
    
    print("Testing GrammarTab import...")
    from frontend.ui.tabs.grammar_tab import GrammarTab
    print("GrammarTab imported OK")
    
    return True

if __name__ == "__main__":
    try:
        verify()
        print("Verification SUCCESSFUL")
        sys.exit(0)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Verification FAILED: {e}")
        sys.exit(1)

