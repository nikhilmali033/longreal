import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import time
import os
from datetime import datetime
import signal

class CameraPreviewTest(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Camera Preview Test")
        self.geometry("800x600")
        
        # Initialize variables
        self.preview_process = None
        self.preview_active = False
        self.output_dir = "camera_test_captures"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        self._create_ui()
        
        # Bind cleanup on window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def _create_ui(self):
        """Create the user interface"""
        # Main container
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Status label
        self.status_label = ttk.Label(
            self.main_frame,
            text="Camera Preview Test",
            font=('Arial', 14, 'bold')
        )
        self.status_label.pack(pady=(0, 20))
        
        # Preview frame placeholder
        self.preview_frame = ttk.Frame(
            self.main_frame,
            relief='solid',
            borderwidth=1
        )
        self.preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Control buttons
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=20)
        
        # Method selection
        self.preview_method = tk.StringVar(value="method1")
        self.method_frame = ttk.LabelFrame(
            self.button_frame,
            text="Preview Method"
        )
        self.method_frame.pack(fill=tk.X, pady=(0, 10))
        
        methods = [
            ("Method 1 (Basic Qt)", "method1"),
            ("Method 2 (Embedded)", "method2"),
            ("Method 3 (Windowed)", "method3")
        ]
        
        for text, value in methods:
            ttk.Radiobutton(
                self.method_frame,
                text=text,
                value=value,
                variable=self.preview_method
            ).pack(side=tk.LEFT, padx=10, pady=5)
        
        # Control buttons
        ttk.Button(
            self.button_frame,
            text="Start Preview",
            command=self.start_preview
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            self.button_frame,
            text="Stop Preview",
            command=self.stop_preview
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            self.button_frame,
            text="Capture Image",
            command=self.capture_image
        ).pack(side=tk.LEFT, padx=5)
        
        # Log frame
        self.log_frame = ttk.LabelFrame(self.main_frame, text="Log")
        self.log_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        self.log_text = tk.Text(
            self.log_frame,
            height=6,
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def log(self, message):
        """Add message to log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert('1.0', f"[{timestamp}] {message}\n")
        self.update_idletasks()
        
    def start_preview_method1(self):
        """Basic Qt preview in separate window"""
        try:
            cmd = [
                "libcamera-hello",
                "--qt",
                "--width", "800",
                "--height", "600"
            ]
            self.preview_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.log("Started preview (Method 1)")
            return True
        except Exception as e:
            self.log(f"Error starting preview: {e}")
            return False
            
    def start_preview_method2(self):
        """Attempt to embed preview in tkinter window"""
        try:
            # Get window ID of preview frame
            self.preview_frame.update()
            window_id = self.preview_frame.winfo_id()
            
            cmd = [
                "libcamera-hello",
                "--qt",
                "--width", "800",
                "--height", "600",
                "--parent-window", str(window_id)
            ]
            self.preview_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.log("Started preview (Method 2)")
            return True
        except Exception as e:
            self.log(f"Error starting preview: {e}")
            return False
            
    def start_preview_method3(self):
        """Windowed preview with position matching"""
        try:
            # Get preview frame position
            self.preview_frame.update()
            x = self.preview_frame.winfo_rootx()
            y = self.preview_frame.winfo_rooty()
            
            cmd = [
                "libcamera-hello",
                "--qt",
                "--width", "800",
                "--height", "600",
                "--position", f"{x},{y}"
            ]
            self.preview_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.log("Started preview (Method 3)")
            return True
        except Exception as e:
            self.log(f"Error starting preview: {e}")
            return False
            
    def start_preview(self):
        """Start camera preview using selected method"""
        if self.preview_active:
            self.log("Preview already running")
            return
            
        method = self.preview_method.get()
        success = False
        
        if method == "method1":
            success = self.start_preview_method1()
        elif method == "method2":
            success = self.start_preview_method2()
        elif method == "method3":
            success = self.start_preview_method3()
            
        if success:
            self.preview_active = True
            self.status_label.config(text="Preview Active")
            
            # Start monitoring thread
            threading.Thread(
                target=self._monitor_preview,
                daemon=True
            ).start()
            
    def stop_preview(self):
        """Stop camera preview"""
        if self.preview_process:
            try:
                # Try graceful shutdown first
                self.preview_process.terminate()
                try:
                    self.preview_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    # Force kill if necessary
                    self.preview_process.kill()
                    self.preview_process.wait()
            except Exception as e:
                self.log(f"Error stopping preview: {e}")
            
            self.preview_process = None
            self.preview_active = False
            self.status_label.config(text="Preview Stopped")
            self.log("Stopped preview")
            
    def capture_image(self):
        """Capture an image"""
        # Stop preview temporarily
        self.stop_preview()
        
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.output_dir, f"test_{timestamp}.jpg")
            
            # Capture image
            cmd = [
                "libcamera-jpeg",
                "--qt",
                "-o", filename,
                "--width", "2304",
                "--height", "1296"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.log(f"Image captured: {filename}")
            else:
                self.log(f"Capture failed: {result.stderr}")
                
        except Exception as e:
            self.log(f"Error capturing image: {e}")
            
        # Restart preview
        self.start_preview()
            
    def _monitor_preview(self):
        """Monitor preview process"""
        while self.preview_active and self.preview_process:
            if self.preview_process.poll() is not None:
                self.log("Preview process ended unexpectedly")
                self.preview_active = False
                self.preview_process = None
                self.status_label.config(text="Preview Stopped")
                break
            time.sleep(0.5)
            
    def on_closing(self):
        """Clean up on window close"""
        self.stop_preview()
        self.quit()

def main():
    app = CameraPreviewTest()
    app.mainloop()

if __name__ == "__main__":
    main()