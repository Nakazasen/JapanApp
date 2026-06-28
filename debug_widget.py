import sys
import os

# Add project root to path
project_root = r"C:\ProgramData\Sandbox\Projects\EnglishApp"
sys.path.append(project_root)

try:
    from frontend.ui.widgets.ai_settings_widget import AISettingsWidget
    print(f"✅ Successfully imported AISettingsWidget")
    
    # Check if method exists in the class
    if hasattr(AISettingsWidget, '_create_pomodoro_section'):
        print(f"✅ Method '_create_pomodoro_section' found in AISettingsWidget class")
    else:
        print(f"❌ Method '_create_pomodoro_section' NOT found in AISettingsWidget class")
        # List all methods
        methods = [m for m in dir(AISettingsWidget) if not m.startswith('__')]
        print(f"Available methods: {methods}")
        
except Exception as e:
    print(f"❌ Error during import: {e}")
    import traceback
    traceback.print_exc()

# Let's also check the file for Tabs
file_path = os.path.join(project_root, "frontend", "ui", "widgets", "ai_settings_widget.py")
with open(file_path, 'rb') as f:
    content = f.read()
    if b'\t' in content:
        print("⚠️ Found TABS in the file!")
    else:
        print("✅ No TABS found in the file.")
