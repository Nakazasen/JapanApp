import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Test script for SRSService logic."""
from frontend.services.srs_service import SRSService
from datetime import datetime

def test_sm2_scenarios():
    print("=== Testing SM-2 Algorithm Scenarios ===\n")
    
    scenarios = [
        {
            "name": "New Item - Good Rating",
            "streak": 0, "ef": 2.5, "interval": 0, "quality": 3,
            "expected_streak": 1, "expected_interval": 1
        },
        {
            "name": "Learning Item (1 correct) - Good Rating",
            "streak": 1, "ef": 2.5, "interval": 1, "quality": 3,
            "expected_streak": 2, "expected_interval": 6
        },
        {
            "name": "Established Item (2 correct) - Good Rating",
            "streak": 2, "ef": 2.5, "interval": 6, "quality": 3,
            "expected_streak": 3, "expected_interval": 15
        },
        {
            "name": "Established Item - Easy Rating",
            "streak": 2, "ef": 2.5, "interval": 6, "quality": 4,
            "expected_streak": 3, "expected_interval": 15 # EF increases for next time
        },
        {
            "name": "Known Item - Failed (Again)",
            "streak": 5, "ef": 2.3, "interval": 50, "quality": 1,
            "expected_streak": 0, "expected_interval": 1
        }
    ]

    for s in scenarios:
        streak, ef, interval = SRSService.calculate_next_state(
            s["streak"], s["ef"], s["interval"], s["quality"]
        )
        
        passed_streak = streak == s["expected_streak"]
        passed_interval = interval == s["expected_interval"]
        
        status = "[PASS]" if passed_streak and passed_interval else "[FAIL]"
        
        print(f"{status} {s['name']}")
        print(f"  Input:  Streak={s['streak']}, EF={s['ef']}, Interval={s['interval']}, Quality={s['quality']}")
        print(f"  Output: Streak={streak}, EF={ef:.2f}, Interval={interval}")
        if not passed_streak:
            print(f"  ! Streak mismatch: expected {s['expected_streak']}")
        if not passed_interval:
            print(f"  ! Interval mismatch: expected {s['expected_interval']}")
        print("-" * 30)

if __name__ == "__main__":
    test_sm2_scenarios()

