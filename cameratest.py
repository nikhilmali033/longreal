import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import time
import os
from datetime import datetime

class WorkingCameraPreview:
    def __init__(self, parent, callback=None):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.preview_process = None
        self.preview_active = False
        self.callback = callback
        self.output_dir = "captured_images"
        
        # Preview window dimensions (16:9 aspect ratio)
        self.preview_width = 800
        self.preview_height = 450
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        self._create_ui()
        
    def _create_ui(self):
        # Status frame
        self.status_frame = ttk.Frame(self.frame)
        self.status_frame.pack(fill=tk.X, pady=10, padx=10)
        
        # Status indicator (circle)
        self.canvas = tk.Canvas(
            self.status_frame,
            width=20,
            height=20,
            highlightthickness=0
        )
        self.canvas.pack(side=tk.LEFT, padx=5)
        
        # Configure canvas background to match parent
        self.canvas.configure(bg=self.status_frame.winfo_toplevel().cget('bg'))
        
        self.status_indicator = self.canvas.create_oval(
            5, 5, 15, 15,
            fill='red'  # Initially red for inactive
        )
        
        # Status text
        self.status_label = ttk.Label(
            self.status_frame,
            text="Preview Inactive"
        )
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Instructions/feedback area
        self.message_label = ttk.Label(
            self.frame,
            text="Click 'Start Preview' to begin",
            wraplength=400,
            justify=tk.CENTER
        )
        self.message_label.pack(pady=20)
        
        # Preview placeholder to help with positioning
        self.placeholder = ttk.Frame(
            self.frame,
            height=200  # Arbitrary height for visual reference
        )
        self.placeholder.pack(fill=tk.X, padx=20, pady=10)
        
        # Button frame
        self.button_frame = ttk.Frame(self.frame)
        self.button_frame.pack(pady=20)
        
        # Preview toggle button
        self.preview_button = ttk.Button(
            self.button_frame,
            text="Start Preview",
            command=self.toggle_preview,
            width=20
        )
        self.preview_button.pack(side=tk.LEFT, padx=5)
        
        # Capture button
        self.capture_button = ttk.Button(
            self.button_frame,
            text="Capture Image",
            command=self.capture_image,
            width=20,
            state=tk.DISABLED
        )
        self.capture_button.pack(side=tk.LEFT, padx=5)

    def calculate_preview_position(self):
        """Calculate the position for the preview window relative to the placeholder"""
        # Ensure placeholder widget is updated
        self.placeholder.update_idletasks()
        
        # Get the placeholder's position on screen
        x = self.placeholder.winfo_rootx()
        y = self.placeholder.winfo_rooty()
        
        # Get placeholder dimensions
        width = self.placeholder.winfo_width()
        
        # Center the preview window horizontally relative to the placeholder
        x = x + (width - self.preview_width) // 2
        
        # Ensure preview window stays on screen
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        
        x = max(0, min(x, screen_width - self.preview_width))
        y = max(0, min(y, screen_height - self.preview_height))
        
        return x, y

    def start_preview(self):
        if not self.preview_active:
            try:
                # Calculate position
                x, y = self.calculate_preview_position()
                
                # Command with positioning
                cmd = [
                    "libcamera-hello",
                    "--qt",
                    "--width", str(self.preview_width),
                    "--height", str(self.preview_height),
                    "--position", f"{x},{y}"
                ]
                
                self.preview_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Start monitoring thread
                threading.Thread(target=self._monitor_preview, daemon=True).start()
                
                # Update UI
                self.preview_active = True
                self.canvas.itemconfig(self.status_indicator, fill='green')
                self.status_label.config(text="Preview Active")
                self.preview_button.config(text="Stop Preview")
                self.capture_button.config(state=tk.NORMAL)
                self.message_label.config(text="Preview window is active\nUse the separate window to frame your shot")
                
            except Exception as e:
                self.message_label.config(text=f"Error: {str(e)}")
                print(f"Preview error: {e}")

    def toggle_preview(self):
        if self.preview_active:
            self.stop_preview()
        else:
            self.start_preview()

    def stop_preview(self):
        if self.preview_process:
            try:
                self.preview_process.terminate()
                try:
                    self.preview_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.preview_process.kill()
                    self.preview_process.wait()
                    
                self.preview_process = None
                self.preview_active = False
                
                # Update UI
                self.canvas.itemconfig(self.status_indicator, fill='red')
                self.status_label.config(text="Preview Inactive")
                self.preview_button.config(text="Start Preview")
                self.capture_button.config(state=tk.DISABLED)
                self.message_label.config(text="Click 'Start Preview' to begin")
                
            except Exception as e:
                self.message_label.config(text=f"Error stopping preview: {str(e)}")
                print(f"Error stopping preview: {e}")

    def capture_image(self):
        # Temporarily stop preview
        self.stop_preview()
        
        try:
            # Update UI
            self.message_label.config(text="Capturing image...")
            self.parent.update()
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.output_dir, f"image_{timestamp}.jpg")
            
            # Capture image
            cmd = [
                "libcamera-jpeg",
                "--qt",
                "-o", filename,
                "--width", "2304",
                "--height", "1296",
                "--nopreview"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            self.message_label.config(text=f"Image captured successfully!\nSaved as: {os.path.basename(filename)}")
            
            # Call callback if provided
            if self.callback:
                self.callback(filename)
                
        except Exception as e:
            self.message_label.config(text=f"Error capturing image: {str(e)}")
            print(f"Capture error: {e}")
            
        # Restart preview
        self.start_preview()

    def _monitor_preview(self):
        """Monitor the preview process for unexpected termination"""
        while self.preview_active and self.preview_process:
            if self.preview_process.poll() is not None:
                # Process ended unexpectedly
                self.preview_active = False
                self.parent.after(0, self.stop_preview)  # Schedule UI update on main thread
                break
            time.sleep(0.5)

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
        
    def grid(self, **kwargs):
        self.frame.grid(**kwargs)
        
    def destroy(self):
        self.stop_preview()
        self.frame.destroy()

# Test code
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Camera Preview Test")
    root.geometry("1024x768")  # Larger window for testing
    
    def on_image_captured(filename):
        print(f"Image captured: {filename}")
    
    preview = WorkingCameraPreview(root, callback=on_image_captured)
    preview.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
    
    root.mainloop()