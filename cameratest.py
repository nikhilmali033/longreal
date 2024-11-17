import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import time
import os
from datetime import datetime

class RefinedCameraPreview:
    """A refined camera preview component that works with Qt-based libcamera"""
    def __init__(self, parent, callback=None):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.preview_process = None
        self.preview_active = False
        self.callback = callback
        self.output_dir = "captured_images"
        
        # Get screen dimensions
        self.screen_width = parent.winfo_screenwidth()
        self.screen_height = parent.winfo_screenheight()
        
        # Calculate preview window size (16:9 aspect ratio)
        self.preview_width = min(1280, int(self.screen_width * 0.6))
        self.preview_height = int(self.preview_width * 9 / 16)
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        self._create_ui()
        
    def _create_ui(self):
        """Create the user interface"""
        # Status frame
        self.status_frame = ttk.Frame(self.frame)
        self.status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Status indicator (circle)
        self.canvas = tk.Canvas(
            self.status_frame,
            width=20,
            height=20,
            bg=self.frame.cget('background'),
            highlightthickness=0
        )
        self.canvas.pack(side=tk.LEFT, padx=5)
        
        self.status_indicator = self.canvas.create_oval(
            5, 5, 15, 15,
            fill='red'  # Initially red for inactive
        )
        
        # Status label
        self.status_label = ttk.Label(
            self.status_frame,
            text="Preview Inactive",
            font=('Arial', 10)
        )
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Preview placeholder
        self.placeholder = ttk.Frame(
            self.frame,
            relief='solid',
            borderwidth=1,
            style='Preview.TFrame'
        )
        self.placeholder.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create a custom style for the placeholder
        style = ttk.Style()
        style.configure('Preview.TFrame', background='#2a2a2a')
        
        # Placeholder text
        self.placeholder_label = ttk.Label(
            self.placeholder,
            text="Camera preview is displayed in a separate window\nClick 'Start Preview' to begin",
            font=('Arial', 12),
            justify=tk.CENTER
        )
        self.placeholder_label.pack(expand=True)
        
        # Control frame
        self.control_frame = ttk.Frame(self.frame)
        self.control_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Start/Stop Preview button
        self.preview_button = ttk.Button(
            self.control_frame,
            text="Start Preview",
            command=self.toggle_preview
        )
        self.preview_button.pack(side=tk.LEFT, padx=5)
        
        # Capture button
        self.capture_button = ttk.Button(
            self.control_frame,
            text="Capture Image",
            command=self.capture_image,
            state=tk.DISABLED  # Initially disabled
        )
        self.capture_button.pack(side=tk.LEFT, padx=5)
        
    def toggle_preview(self):
        """Toggle preview state"""
        if self.preview_active:
            self.stop_preview()
        else:
            self.start_preview()
            
    def start_preview(self):
        """Start the camera preview"""
        if not self.preview_active:
            try:
                # Calculate center position for preview window
                x = (self.screen_width - self.preview_width) // 2
                y = (self.screen_height - self.preview_height) // 2
                
                cmd = [
                    "libcamera-hello",
                    "--qt",
                    "--width", str(self.preview_width),
                    "--height", str(self.preview_height),
                    "--position", f"{x},{y}",  # Position the window
                    "--info", "0"  # Disable info overlay for cleaner preview
                ]
                
                self.preview_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Update UI
                self.preview_active = True
                self.canvas.itemconfig(self.status_indicator, fill='green')
                self.status_label.config(text="Preview Active")
                self.preview_button.config(text="Stop Preview")
                self.capture_button.config(state=tk.NORMAL)
                self.placeholder_label.config(
                    text="Preview window is now active\nUse the preview window to frame your shot"
                )
                
                # Start monitoring thread
                threading.Thread(
                    target=self._monitor_preview,
                    daemon=True
                ).start()
                
            except Exception as e:
                self._show_error(f"Failed to start preview: {e}")
                
    def stop_preview(self):
        """Stop the camera preview"""
        if self.preview_process:
            try:
                self.preview_process.terminate()
                try:
                    self.preview_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.preview_process.kill()
                    self.preview_process.wait()
            except Exception as e:
                self._show_error(f"Error stopping preview: {e}")
            
            self.preview_process = None
            self.preview_active = False
            
            # Update UI
            self.canvas.itemconfig(self.status_indicator, fill='red')
            self.status_label.config(text="Preview Inactive")
            self.preview_button.config(text="Start Preview")
            self.capture_button.config(state=tk.DISABLED)
            self.placeholder_label.config(
                text="Camera preview is displayed in a separate window\nClick 'Start Preview' to begin"
            )
            
    def capture_image(self):
        """Capture an image"""
        # Temporarily stop preview
        self.stop_preview()
        
        try:
            # Update UI
            self.status_label.config(text="Capturing...")
            self.parent.update()
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.output_dir, f"image_{timestamp}.jpg")
            
            # Capture image
            cmd = [
                "libcamera-jpeg",
                "--qt",
                "-o", filename,
                "--width", "2304",  # Max resolution for capture
                "--height", "1296",
                "--nopreview"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Call callback with captured image path
            if self.callback:
                self.callback(filename)
                
            # Show success in UI
            self.placeholder_label.config(
                text=f"Image captured successfully!\nSaved as: {os.path.basename(filename)}"
            )
            
        except subprocess.CalledProcessError as e:
            self._show_error(f"Failed to capture image: {e.stderr}")
        except Exception as e:
            self._show_error(f"Error during capture: {e}")
            
        # Restart preview
        self.start_preview()
            
    def _monitor_preview(self):
        """Monitor the preview process"""
        while self.preview_active and self.preview_process:
            if self.preview_process.poll() is not None:
                # Preview process ended unexpectedly
                self.preview_active = False
                self.parent.after(0, self.stop_preview)  # Schedule UI update on main thread
                break
            time.sleep(0.5)
            
    def _show_error(self, message):
        """Show error message in UI"""
        self.status_label.config(text="Error")
        self.placeholder_label.config(text=f"Error: {message}")
        print(f"Camera Error: {message}")  # Also print to console for debugging
        
    def pack(self, **kwargs):
        """Pack the frame with given options"""
        self.frame.pack(**kwargs)
        
    def grid(self, **kwargs):
        """Grid the frame with given options"""
        self.frame.grid(**kwargs)
        
    def destroy(self):
        """Clean up resources"""
        self.stop_preview()
        self.frame.destroy()