import tkinter as tk
from tkinter import ttk
import sys
import subprocess
import datetime
import os
import cv2
from PIL import Image, ImageTk
import threading
import queue

class Component:
    """Base component class"""
    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.kwargs = kwargs
    
    def pack(self, **pack_options):
        self.frame.pack(**pack_options)
    
    def grid(self, **grid_options):
        self.frame.grid(**grid_options)
    
    def place(self, **place_options):
        self.frame.place(**place_options)
    
    def destroy(self):
        self.frame.destroy()

class RoundedButton(Component):
    """A button with rounded corners and customizable colors"""
    def __init__(self, parent, text: str, command, bg_color: str = "#4287f5",
                 hover_color: str = "#2c5ca6", text_color: str = "white",
                 width: int = None, height: int = None, corner_radius: int = 10,
                 **kwargs):
        super().__init__(parent, **kwargs)
        self.text = text
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.disabled_color = "#cccccc"
        self.enabled = True
        
        # Default sizes based on screen size
        self.width = width or int(parent.winfo_screenwidth() * 0.15)
        self.height = height or int(parent.winfo_screenheight() * 0.08)
        self.corner_radius = corner_radius
        
        self._create_button()

    def _create_button(self):
        # Create canvas with transparent background
        self.canvas = tk.Canvas(
            self.frame,
            width=self.width,
            height=self.height,
            highlightthickness=0,
            bg=self.frame.winfo_toplevel().cget('bg')
        )
        self.canvas.pack()

        # Create rounded rectangle
        self.shape = self._create_rounded_rectangle(
            2, 2, self.width-2, self.height-2,
            self.corner_radius
        )
        self.canvas.itemconfig(self.shape, fill=self.bg_color, outline=self.bg_color)
        
        # Create text
        font_size = int(self.height * 0.3)
        self.canvas_text = self.canvas.create_text(
            self.width/2,
            self.height/2,
            text=self.text,
            fill=self.text_color,
            font=('Arial', font_size, 'bold')
        )

        # Bind events
        self.canvas.bind('<Enter>', self._on_enter)
        self.canvas.bind('<Leave>', self._on_leave)
        self.canvas.bind('<Button-1>', self._on_click)

    def _create_rounded_rectangle(self, x1, y1, x2, y2, radius):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return self.canvas.create_polygon(points, smooth=True)

    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        self.canvas.itemconfig(
            self.shape,
            fill=self.bg_color if enabled else self.disabled_color
        )

    def _on_enter(self, event):
        if self.enabled:
            self.canvas.itemconfig(self.shape, fill=self.hover_color)

    def _on_leave(self, event):
        if self.enabled:
            self.canvas.itemconfig(self.shape, fill=self.bg_color)
        else:
            self.canvas.itemconfig(self.shape, fill=self.disabled_color)

    def _on_click(self, event):
        if self.enabled:
            self.command()

class CameraPreview(Component):
    """Camera preview component with capture functionality"""
    def __init__(self, parent, callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.preview_active = False
        self.frame_queue = queue.Queue(maxsize=1)
        self.output_dir = "captured_images"
        self.callback = callback
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        self._create_ui()
        
    def _create_ui(self):
        # Calculate preview dimensions
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        self.preview_width = int(screen_width * 0.7)
        self.preview_height = int(screen_height * 0.6)
        
        # Create preview canvas
        self.preview_canvas = tk.Canvas(
            self.frame,
            width=self.preview_width,
            height=self.preview_height,
            bg='black',
            highlightthickness=0
        )
        self.preview_canvas.pack(pady=20)
        
        # Create capture button
        self.capture_btn = RoundedButton(
            self.frame,
            text="Capture",
            command=self.capture_image,
            bg_color="#4CAF50"
        )
        self.capture_btn.pack(pady=20)
        
        self.start_preview()
    
    def start_preview(self):
        self.preview_active = True
        self.preview_process = subprocess.Popen([
            "libcamera-vid",
            "--qt-preview",  # Use QT preview instead of default
            "--width", "2304",
            "--height", "1296",
            "--codec", "mjpeg",
            "--inline",
            "--output", "-"
        ], stdout=subprocess.PIPE)
        
        self.preview_thread = threading.Thread(target=self._read_preview_frames)
        self.preview_thread.daemon = True
        self.preview_thread.start()
        
        self._update_preview()
    
    def capture_image(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/image_{timestamp}.jpg"
        
        try:
            self.preview_active = False
            if hasattr(self, 'preview_process'):
                self.preview_process.terminate()
                self.preview_process.wait()
            
            # Use qt-preview for capture as well
            subprocess.run([
                "libcamera-jpeg",
                "--qt-preview",
                "-o", filename,
                "--width", "2304",
                "--height", "1296"
            ], check=True)
            
            if self.callback:
                self.callback(filename)
            
            self.start_preview()
            return filename
            
        except subprocess.CalledProcessError as e:
            print(f"Error capturing image: {e}")
            self.start_preview()
            return None
class ImageList(Component):
    """Component to display captured images as a scrollable list"""
    def __init__(self, parent, image_dir="captured_images", **kwargs):
        super().__init__(parent, **kwargs)
        self.image_dir = image_dir
        self.current_page = 0
        self.images_per_page = 4
        self._create_ui()
        self.refresh_images()

    def _create_ui(self):
        # Navigation buttons container
        nav_frame = ttk.Frame(self.frame)
        nav_frame.pack(side='right', fill='y', padx=20)

        # Calculate button sizes
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        nav_button_width = int(screen_width * 0.08)
        nav_button_height = int(screen_height * 0.15)

        # Navigation buttons
        self.up_button = RoundedButton(
            nav_frame,
            text="▲",
            command=self._previous_page,
            width=nav_button_width,
            height=nav_button_height,
            bg_color="#666666"
        )
        self.up_button.pack(pady=(0, 10))

        self.page_indicator = ttk.Label(
            nav_frame,
            text="1/1",
            font=('Arial', int(screen_height * 0.03), 'bold')
        )
        self.page_indicator.pack(pady=10)

        self.down_button = RoundedButton(
            nav_frame,
            text="▼",
            command=self._next_page,
            width=nav_button_width,
            height=nav_button_height,
            bg_color="#666666"
        )
        self.down_button.pack(pady=(10, 0))

        # Images container
        self.images_frame = ttk.Frame(self.frame)
        self.images_frame.pack(side='left', fill='both', expand=True)

    def refresh_images(self):
        if os.path.exists(self.image_dir):
            self.image_files = sorted(
                [f for f in os.listdir(self.image_dir) if f.endswith('.jpg')],
                reverse=True
            )
            self.total_pages = (len(self.image_files) + self.images_per_page - 1) // self.images_per_page
            self._show_current_page()
        else:
            self.image_files = []
            self.total_pages = 1
            self._show_current_page()

    def _show_current_page(self):
        # Clear current images
        for widget in self.images_frame.winfo_children():
            widget.destroy()

        # Calculate dimensions
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        button_width = int(screen_width * 0.4)
        button_height = int(screen_height * 0.18)

        # Get current page images
        start_idx = self.current_page * self.images_per_page
        end_idx = start_idx + self.images_per_page
        current_images = self.image_files[start_idx:end_idx]

        # Create image buttons
        for image_file in current_images:
            image_path = os.path.join(self.image_dir, image_file)
            btn = RoundedButton(
                self.images_frame,
                text=image_file,
                command=lambda p=image_path: self._view_image(p),
                width=button_width,
                height=button_height,
                bg_color="#4287f5"
            )
            btn.pack(pady=10, padx=30)

        # Update navigation
        self.page_indicator.configure(text=f"{self.current_page + 1}/{max(1, self.total_pages)}")
        self.up_button.set_enabled(self.current_page > 0)
        self.down_button.set_enabled(self.current_page < self.total_pages - 1)

    def _next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._show_current_page()

    def _previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._show_current_page()

    def _view_image(self, image_path):
        # For now, just print the path - we'll implement viewing later
        print(f"Viewing image: {image_path}")

class FlashcardApp:
    """Main application class"""
    def __init__(self, root):
        self.root = root
        self.root.title("Photo Flashcard App")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='#f0f0f0')
        
        self.container = ttk.Frame(root)
        self.container.pack(fill='both', expand=True)
        
        # Key bindings
        self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))
        self.root.bind('<F11>', lambda e: self.root.attributes('-fullscreen', 
                                        not self.root.attributes('-fullscreen')))
        
        # Initialize components
        self.current_component = None
        self.camera = None
        
        self.show_main_menu()

    def clear_container(self):
        if self.current_component:
            self.current_component.destroy()
            self.current_component = None
        for widget in self.container.winfo_children():
            widget.destroy()

    def create_back_button(self):
        width = int(self.root.winfo_screenwidth() * 0.12)
        height = int(self.root.winfo_screenheight() * 0.06)
        
        back_btn = RoundedButton(
            self.container,
            text="← Back",
            command=self.show_main_menu,
            width=width,
            height=height,
            bg_color="#666666"
        )
        back_btn.pack(anchor='nw', padx=20, pady=20)

    def show_main_menu(self):
        self.clear_container()
        
        grid_frame = ttk.Frame(self.container)
        grid_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        button_width = int(self.root.winfo_screenwidth() * 0.35)
        button_height = int(self.root.winfo_screenheight() * 0.25)
        
        buttons = [
            {
                'text': "Take Picture",
                'command': self.show_camera_preview,
                'color': "#4CAF50"
            },
            {
                'text': "View Images",
                'command': self.show_image_list,
                'color': "#2196F3"
            },
            {
                'text': "Settings",
                'command': lambda: print("Settings clicked"),
                'color': "#9C27B0"
            },
            {
                'text': "Quit",
                'command': self.root.quit,
                'color': "#f44336"
            }
        ]
        
        for i, btn_props in enumerate(buttons):
            row = i // 2
            col = i % 2
            btn = RoundedButton(
                grid_frame,
                text=btn_props['text'],
                command=btn_props['command'],
                bg_color=btn_props['color'],
                width=button_width,
                height=button_height
            )
            btn.frame.grid(row=row, column=col, padx=30, pady=30)

    def show_camera_preview(self):
        self.clear_container()
        self.create_back_button()
        
        title = ttk.Label(
            self.container,
            text="Take Picture",
            font=('Arial', int(self.root.winfo_screenheight() * 0.05), 'bold')
        )
        title.pack(pady=30)
        
        # Create camera preview with callback for image capture
        self.current_component = CameraPreview(
            self.container,
            callback=self._on_image_captured
        )
        self.current_component.pack(fill='both', expand=True, padx=30, pady=(0, 30))

    def show_image_list(self):
        self.clear_container()
        self.create_back_button()
        
        title = ttk.Label(
            self.container,
            text="Captured Images",
            font=('Arial', int(self.root.winfo_screenheight() * 0.05), 'bold')
        )
        title.pack(pady=30)
        
        self.current_component = ImageList(self.container)
        self.current_component.pack(fill='both', expand=True, padx=30, pady=(0, 30))

    def _on_image_captured(self, image_path):
        """Callback for when an image is captured"""
        print(f"Image captured: {image_path}")
        # Here you could add additional processing, like displaying the image
        # or automatically switching to the image list view

def main():
    root = tk.Tk()
    app = FlashcardApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()