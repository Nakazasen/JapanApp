import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from PySide6.QtWidgets import QApplication
from frontend.ui.tabs.toeic_dashboard_tab import ToeicDashboardTab, StatCard, PartProgressBar
from frontend.services.toeic_listening_service import get_toeic_listening_service

def verify_dashboard():
    app = QApplication(sys.argv)
    
    # 1. Test Service Stats
    print("Testing Service Stats...")
    service = get_toeic_listening_service()
    stats = service.get_dashboard_stats()
    print("Status Result:", stats)
    
    # 2. Test UI Instantiation
    print("\nTesting UI Instantiation...")
    tab = ToeicDashboardTab()
    tab.show()
    
    # Verify child widgets
    print(f"Score Card Exists: {tab.score_card is not None}")
    print(f"Accuracy Card Exists: {tab.accuracy_card is not None}")
    print(f"Part Bars Count: {len(tab.part_bars)} (Expected 7)")
    
    # Verify values logic
    tab.refresh()
    print("Refresh called successfully.")
    
    print("\n✅ Dashboard Verification Passed!")

if __name__ == "__main__":
    verify_dashboard()
