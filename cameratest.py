import tkinter as tk
from tkinter import ttk
import subprocess
import os
from datetime import datetime
from PIL import Image, ImageTk

class CaptureReviewComponent:
    def __init__(self, parent, proceed_callback=None):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.proceed_callback = proceed_callback
        self.output_dir = "captured_images"
        self.current_image_path = None
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        self._create_ui()
        
    def _create_ui(self):
        # Top status message
        self.status_label = ttk.Label(
            self.frame,
            text="Take a picture to begin",
            font=('Arial', 12),
            justify=tk.CENTER,
            wraplength=400
        )
        self.status_label.pack(pady=20)
        
        # Image display area
        self.image_frame = ttk.Frame(
            self.frame,
            relief="solid",
            borderwidth=1
        )
        self.image_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # Image label within frame
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.pack(padx=10, pady=10)
        
        # Button frame
        self.button_frame = ttk.Frame(self.frame)
        self.button_frame.pack(pady=20)
        
        # Capture button
        self.capture_button = ttk.Button(
            self.button_frame,
            text="Capture Image",
            command=self.capture_image,
            width=20
        )
        self.capture_button.pack(side=tk.LEFT, padx=10)
        
        # Proceed button (initially disabled)
        self.proceed_button = ttk.Button(
            self.button_frame,
            text="Proceed",
            command=self.proceed,
            width=20,
            state=tk.DISABLED
        )
        self.proceed_button.pack(side=tk.LEFT, padx=10)

    def capture_image(self):
        """Capture an image and display it for review"""
        try:
            # Update UI
            self.status_label.config(text="Capturing image...")
            self.capture_button.config(state=tk.DISABLED)
            self.proceed_button.config(state=tk.DISABLED)
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
            
            # Display the captured image
            self.display_image(filename)
            self.current_image_path = filename
            
            # Update UI
            self.status_label.config(
                text="Image captured! Review the image and proceed, or capture again."
            )
            self.proceed_button.config(state=tk.NORMAL)
            
        except Exception as e:
            self.status_label.config(text=f"Error capturing image: {str(e)}")
            print(f"Capture error: {e}")
        finally:
            self.capture_button.config(state=tk.NORMAL)

    def display_image(self, image_path):
        """Display an image in the UI"""
        try:
            # Open and resize image to fit display
            image = Image.open(image_path)
            
            # Calculate size to maintain aspect ratio
            display_width = min(800, self.parent.winfo_width() - 100)
            display_height = min(600, self.parent.winfo_height() - 200)
            
            # Calculate scaling factor
            width_ratio = display_width / image.width
            height_ratio = display_height / image.height
            scale_factor = min(width_ratio, height_ratio)
            
            new_width = int(image.width * scale_factor)
            new_height = int(image.height * scale_factor)
            
            # Resize image
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image)
            
            # Update label
            self.image_label.configure(image=photo)
            self.image_label.image = photo  # Keep a reference!
            
        except Exception as e:
            self.status_label.config(text=f"Error displaying image: {str(e)}")
            print(f"Display error: {e}")

    def proceed(self):
        """Handle proceed button click"""
        if self.current_image_path and self.proceed_callback:
            self.proceed_callback(self.current_image_path)

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
        
    def grid(self, **kwargs):
        self.frame.grid(**kwargs)
        
    def destroy(self):
        self.frame.destroy()

# Test code
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Capture and Review")
    root.geometry("1024x768")
    
    def on_proceed(image_path):
        print(f"Proceeding with image: {image_path}")
        # Here you would transition to your OCR component
    
    app = CaptureReviewComponent(root, proceed_callback=on_proceed)
    app.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
    
    root.mainloop()

