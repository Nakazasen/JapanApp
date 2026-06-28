"""Simulate Progress Update from Background Thread.

This script verifies that QProgressDialog updates correctly when
signaled from a background thread using the same mechanism implemented in vocab_tab.py.
"""
import sys
import os
import asyncio
from PySide6.QtWidgets import QApplication, QProgressDialog, QWidget, QVBoxLayout, QPushButton, QMessageBox
from PySide6.QtCore import Qt, QObject, Signal, QTimer

# Add project root to python path
sys.path.append(os.getcwd())

from frontend.utils.async_helpers import run_async

class WorkerSignals(QObject):
    progress = Signal(int, str)

class SimulationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Progress Simulation")
        self.resize(300, 200)
        layout = QVBoxLayout(self)
        
        self.btn = QPushButton("Start Simulation")
        self.btn.clicked.connect(self.start_simulation)
        layout.addWidget(self.btn)
        
    def start_simulation(self):
        self.btn.setEnabled(False)
        total = 100
        
        progress = QProgressDialog("Simulating...", "Cancel", 0, total, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        self.worker_signals = WorkerSignals()
        
        def update_ui(val, text):
            print(f"UI Update: {val}% - {text}")
            progress.setValue(val)
            progress.setLabelText(text)
            
        self.worker_signals.progress.connect(update_ui)
        
        async def work():
            print("Worker started")
            for i in range(1, total + 1):
                if progress.wasCanceled():
                    print("Canceled by user")
                    break
                
                self.worker_signals.progress.emit(i, f"Processing {i}/{total}...")
                await asyncio.sleep(0.05) # Simulate work
            return "Done"

        def on_complete(result):
            print(f"Complete: {result}")
            self.btn.setEnabled(True)
            progress.setValue(total)
            if hasattr(self, 'worker_signals'):
                del self.worker_signals
            QMessageBox.information(self, "Success", "Simulation Complete!")
            self.close()

        run_async(work, on_complete)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimulationWindow()
    window.show()
    
    # Auto-click start for automation context
    QTimer.singleShot(1000, window.start_simulation)
    
    sys.exit(app.exec())
