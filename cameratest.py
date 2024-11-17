import tkinter as tk
from tkinter import ttk
import subprocess
import os
from datetime import datetime

class SimplifiedCamera:
    def __init__(self, parent, callback=None):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.callback = callback
        self.output_dir = "captured_images"
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        self._create_ui()
        
    def _create_ui(self):
        # Status/message area
        self.message_label = ttk.Label(
            self.frame,
            text="Click 'Capture Image' to take a photo",
            wraplength=400,
            justify=tk.CENTER,
            font=('Arial', 12)
        )
        self.message_label.pack(pady=20)
        
        # Capture button
        self.capture_button = ttk.Button(
            self.frame,
            text="Capture Image",
            command=self.capture_image,
            width=20
        )
        self.capture_button.pack(pady=10)

    def capture_image(self):
        try:
            # Update UI
            self.message_label.config(text="Capturing image...")
            self.capture_button.config(state=tk.DISABLED)
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
            
            self.message_label.config(
                text=f"Image captured successfully!\nSaved as: {os.path.basename(filename)}"
            )
            
            # Call callback if provided
            if self.callback:
                self.callback(filename)
                
        except Exception as e:
            self.message_label.config(text=f"Error capturing image: {str(e)}")
            print(f"Capture error: {e}")
        finally:
            self.capture_button.config(state=tk.NORMAL)

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
        
    def grid(self, **kwargs):
        self.frame.grid(**kwargs)
        
    def destroy(self):
        self.frame.destroy()