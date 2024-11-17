import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import time

class SimpleCameraTest(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Simple Camera Test")
        self.geometry("400x200")
        
        # Create UI
        self.status_label = ttk.Label(self, text="Camera Inactive")
        self.status_label.pack(pady=20)
        
        self.start_button = ttk.Button(self, text="Start Preview", command=self.toggle_preview)
        self.start_button.pack(pady=20)
        
        # Initialize camera state
        self.preview_process = None
        self.preview_active = False

    def toggle_preview(self):
        if self.preview_active:
            self.stop_preview()
        else:
            self.start_preview()

    def start_preview(self):
        if not self.preview_active:
            try:
                # Basic command that worked in your testing
                cmd = ["libcamera-hello", "--qt"]
                print(f"Executing command: {' '.join(cmd)}")  # Debug print
                
                self.preview_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Start monitoring for errors
                def monitor_output():
                    while self.preview_process:
                        error = self.preview_process.stderr.readline()
                        if error:
                            print(f"Preview Error: {error.decode().strip()}")
                
                threading.Thread(target=monitor_output, daemon=True).start()
                
                self.preview_active = True
                self.status_label.config(text="Camera Active")
                self.start_button.config(text="Stop Preview")
                print("Preview process started")  # Debug print
                
            except Exception as e:
                print(f"Error starting preview: {e}")
                self.status_label.config(text=f"Error: {str(e)}")

    def stop_preview(self):
        if self.preview_process:
            try:
                print("Stopping preview process")  # Debug print
                self.preview_process.terminate()
                self.preview_process.wait(timeout=5)
                self.preview_process = None
                self.preview_active = False
                self.status_label.config(text="Camera Inactive")
                self.start_button.config(text="Start Preview")
                print("Preview process stopped")  # Debug print
            except Exception as e:
                print(f"Error stopping preview: {e}")
                self.status_label.config(text=f"Error stopping: {str(e)}")

    def on_closing(self):
        self.stop_preview()
        self.quit()

def main():
    app = SimpleCameraTest()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

if __name__ == "__main__":
    main()