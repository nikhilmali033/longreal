import tkinter as tk
from tkinter import ttk
import sys
import subprocess
from datetime import datetime
import os
import cv2
from PIL import Image, ImageTk
import threading
import queue
import numpy as np
import cv2
import pytesseract
import logging
from PIL import Image, ImageDraw

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

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
    def __init__(self, parent, text: str, command, bg_color: str = "#c6eb34",
                 hover_color: str = "#a8cc21", text_color: str = "black",
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
        
        # Smaller default sizes for small screens
        self.width = width or int(parent.winfo_screenwidth() * 0.12)  # Reduced from 0.15
        self.height = height or int(parent.winfo_screenheight() * 0.06)  # Reduced from 0.08
        self.corner_radius = min(corner_radius, self.height // 4)  # Scale radius with height
        
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
        
        # Create text with smaller font size (reduced from 0.3 to 0.2)
        font_size = int(self.height * 0.15)  # Reduced from 0.2
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
    """Camera preview component that strictly follows capture.py implementation"""
    def __init__(self, parent, callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.preview_active = False
        self.output_dir = "captured_images"
        self.callback = callback
        self.preview_process = None
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        self._create_ui()
        
    def _create_ui(self):
        # Create control frame for button
        self.control_frame = ttk.Frame(self.frame)
        self.control_frame.pack(pady=20)
        
        # Create capture button
        self.capture_btn = RoundedButton(
            self.control_frame,
            text="Capture",
            command=self.capture_image,
            bg_color="#4CAF50"
        )
        self.capture_btn.pack(pady=20)
        
        # Start preview when UI is ready
        self.frame.after(100, self.start_preview)
    
    def start_preview(self):
        """Start the preview window using libcamera-hello"""
        if self.preview_process is None:
            try:
                self.preview_active = True
                self.preview_process = subprocess.Popen([
                    "libcamera-hello",
                    "--qt",  # Essential qt flag
                    "--width", "2304",
                    "--height", "1296"
                ])
            except subprocess.CalledProcessError as e:
                print(f"Error starting preview: {e}")
    
    def stop_preview(self):
        """Stop the preview window"""
        if self.preview_process:
            self.preview_active = False
            self.preview_process.terminate()
            try:
                self.preview_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.preview_process.kill()
            self.preview_process = None
    
    def capture_image(self):
        """Capture an image following the exact capture.py implementation"""
        # Temporarily stop the preview
        self.stop_preview()
        
        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/image_{timestamp}.jpg"
        
        try:
            # Using exact command from capture.py
            cmd = [
                "libcamera-jpeg",
                "-o", filename,
                "--width", "2304",
                "--height", "1296",
                "--qt",  # Essential qt flag
                "--nopreview"  # Since we don't need preview for capture
            ]
            
            subprocess.run(cmd, check=True)
            print(f"Image captured successfully: {filename}")
            
            # Call the callback with the captured image path
            if self.callback:
                self.callback(filename)
            
            # Restart the preview
            self.start_preview()
            return filename
            
        except subprocess.CalledProcessError as e:
            print(f"Error capturing image: {e}")
            # Restart the preview even if capture failed
            self.start_preview()
            return None
    
    def destroy(self):
        """Clean up resources when component is destroyed"""
        self.stop_preview()
        super().destroy()
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
        nav_frame.pack(side='right', fill='y', padx=5)  # Reduced padding

        # Smaller navigation buttons
        nav_button_width = int(self.parent.winfo_screenwidth() * 0.06)  # Reduced from 0.08
        nav_button_height = int(self.parent.winfo_screenheight() * 0.10)  # Reduced from 0.15


        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        # Navigation buttons
        self.up_button = RoundedButton(
            nav_frame,
            text="▲",
            command=self._previous_page,
            width=nav_button_width,
            height=nav_button_height,
            bg_color="#4CAF50"
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
            bg_color="#4CAF50"
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
        button_width = int(self.parent.winfo_screenwidth() * 0.30)  # Reduced from 0.4
        button_height = int(self.parent.winfo_screenheight() * 0.12)  # Reduced from 0.18

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
                bg_color="#4CAF50"
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

class CaptureReviewComponent(Component):
    def __init__(self, parent, final_callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.final_callback = final_callback
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
            font=('Arial', int(self.parent.winfo_screenheight() * 0.02)),
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
        
        # Calculate button dimensions
        button_width = int(self.parent.winfo_screenwidth() * 0.15)
        button_height = int(self.parent.winfo_screenheight() * 0.08)
        
        # Capture button
        self.capture_button = RoundedButton(
            self.button_frame,
            text="Capture Image",
            command=self.capture_image,
            width=button_width,
            height=button_height,
            bg_color="#c6eb34"
        )
        self.capture_button.pack(side=tk.LEFT, padx=10)
        
        # Proceed button (initially disabled)
        self.proceed_button = RoundedButton(
            self.button_frame,
            text="Proceed",
            command=self.proceed,
            width=button_width,
            height=button_height,
            bg_color="#c6eb34"
        )
        self.proceed_button.pack(side=tk.LEFT, padx=10)
        self.proceed_button.set_enabled(False)
        
        # Bypass button
        self.bypass_button = RoundedButton(
            self.button_frame,
            text="Skip Photo",
            command=self.bypass_photo,
            width=button_width,
            height=button_height,
            bg_color="#c6eb34"
        )
        self.bypass_button.pack(side=tk.RIGHT, padx=10)

    def bypass_photo(self):
        """Skip the photo-taking process and go straight to name input"""
        # Clear current UI
        for widget in self.frame.winfo_children():
            widget.destroy()
        
        # Show name input OCR without an image
        self.name_input = NameInputOCR(
            self.frame,
            image_path=None,  # No image path when bypassing
            on_confirm=self._handle_name_confirmation,
            on_cancel=self._handle_name_cancel
        )
        self.name_input.pack(fill='both', expand=True)

    def capture_image(self):
        """Capture an image and display it for review"""
        try:
            # Update UI
            self.status_label.config(text="Capturing image...")
            self.capture_button.set_enabled(False)
            self.proceed_button.set_enabled(False)
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
            self.proceed_button.set_enabled(True)
            
        except Exception as e:
            self.status_label.config(text=f"Error capturing image: {str(e)}")
            print(f"Capture error: {e}")
        finally:
            self.capture_button.set_enabled(True)

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
        if self.current_image_path:
            # Clear current UI
            for widget in self.frame.winfo_children():
                widget.destroy()
            
            # Show name input OCR
            self.name_input = NameInputOCR(
                self.frame,
                self.current_image_path,
                on_confirm=self._handle_name_confirmation,
                on_cancel=self._handle_name_cancel
            )
            self.name_input.pack(fill='both', expand=True)

    def _handle_name_confirmation(self, new_name):
        """Handle the confirmed name from OCR"""
        try:
            # Generate new filename
            file_ext = os.path.splitext(self.current_image_path)[1]
            new_filename = f"{new_name}{file_ext}"
            new_path = os.path.join(self.output_dir, new_filename)
            
            # Rename file
            os.rename(self.current_image_path, new_path)
            
            # Call final callback with new path
            if self.final_callback:
                self.final_callback(new_path)
                
        except Exception as e:
            print(f"Error saving file: {e}")  # Just print to console instead of showing messagebox
            if self.final_callback:
                self.final_callback(self.current_image_path)  # Still proceed even if rename fails


    def _handle_name_cancel(self):
        """Handle cancellation of name input"""
        # Restore original capture review UI
        self.name_input.destroy()
        self._create_ui()
        if self.current_image_path:
            self.display_image(self.current_image_path)

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
        
        self.show_main_menu()

    def clear_container(self):
        if self.current_component:
            self.current_component.destroy()
            self.current_component = None
        for widget in self.container.winfo_children():
            widget.destroy()

    def create_back_button(self):
        # Smaller back button
        width = int(self.root.winfo_screenwidth() * 0.08)  # Reduced from 0.12
        height = int(self.root.winfo_screenheight() * 0.04)  # Reduced from 0.06
        
        back_btn = RoundedButton(
            self.container,
            text="← Back",
            command=self.show_main_menu,
            width=width,
            height=height,
            bg_color="#c6eb34"
        )
        back_btn.pack(anchor='nw', padx=5, pady=5)  # Reduced padding

    def show_main_menu(self):
        self.clear_container()
        
        grid_frame = ttk.Frame(self.container)
        grid_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        button_width = int(self.root.winfo_screenwidth() * 0.25)  # Reduced from 0.35
        button_height = int(self.root.winfo_screenheight() * 0.15)  # Reduced from 0.25
        
        buttons = [
            {
                'text': "Take balls",
                'command': self.show_ocr,
                'color': "#4CAF50"
            },
            {
                'text': "Take Picture",
                'command': self.show_camera_preview,
                'color': "#4CAF50"
            },
            {
                'text': "View Images",
                'command': self.show_image_list,
                'color': "#4CAF50"
            },
            {
                'text': "Settings",
                'command': lambda: print("Settings clicked"),
                'color': "#4CAF50"
            },
            {
                'text': "Quit",
                'command': self.root.quit,
                'color': "#4CAF50"
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
            btn.frame.grid(row=row, column=col, padx=10, pady=10)  # Reduced from 30

    def show_camera_preview(self):
        self.clear_container()
        self.create_back_button()
        
        title = ttk.Label(
            self.container,
            text="Take Picture",
            font=('Arial', int(self.root.winfo_screenheight() * 0.05), 'bold')
        )
        title.pack(pady=30)
        
        # Create capture review with final callback
        self.current_component = CaptureReviewComponent(
            self.container,
            final_callback=self._on_final_image_saved
        )
        self.current_component.pack(fill='both', expand=True, padx=30, pady=(0, 30))

    def _on_final_image_saved(self, final_image_path):
        """Callback for when an image is saved with its new name"""
        print(f"Image saved with new name: {final_image_path}")
        # Show the image list after successful save
        self.show_image_list()

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
        # Show the image list after capture
        self.show_image_list()

    def show_ocr(self):
        self.clear_container()
        self.create_back_button()
        
        self.current_component = CharacterOCRComponent(
            self.container,
            num_regions=5,
            debug=True
        )
        self.current_component.pack(fill='both', expand=True)

class CharacterOCRComponent(Component):
    def __init__(self, parent, num_rows=2, boxes_per_row=4, debug=True, **kwargs):
        """Initialize the OCR component with the parent widget"""
        super().__init__(parent, **kwargs)
        
        # Initialize debug settings
        self.debug = debug
        if debug:
            self.debug_folder = "ocr_debug"
            os.makedirs(self.debug_folder, exist_ok=True)
            logging.basicConfig(
                filename='ocr_debug.log',
                level=logging.DEBUG,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
        
        # Store grid dimensions
        self.num_rows = num_rows
        self.boxes_per_row = boxes_per_row
        self.num_regions = num_rows * boxes_per_row
        
        # Calculate dimensions based on screen size
        
        self.screen_width = parent.winfo_screenwidth()
        self.screen_height = parent.winfo_screenheight()
        
        # Calculate region size based on screen width and boxes per row
        # Account for some padding on the sides
        usable_width = self.screen_width * 0.9  # Use 90% of screen width
        self.region_size = int(usable_width / self.boxes_per_row)
        
        # Scale line width based on region size
        self.line_width = max(2, int(self.region_size * 0.03))
        
        self._create_ui()
        self._setup_regions()
        self._create_controls()
        
        # Initialize drawing state
        self.drawing = False
        self.current_region = None
        self.last_x = None
        self.last_y = None

    def _create_ui(self):
        """Create the main UI components"""
        # Title
        self.title_label = ttk.Label(
            self.frame,
            text="Character Recognition",
            font=('Arial', int(self.screen_height * 0.03), 'bold')
        )
        self.title_label.pack(pady=10)

        # Canvas container
        canvas_container = ttk.Frame(self.frame)
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Calculate canvas size based on region size and grid dimensions
        canvas_width = self.region_size * self.boxes_per_row
        canvas_height = self.region_size * self.num_rows
        
        # Main canvas with white background
        self.canvas = tk.Canvas(
            canvas_container,
            width=canvas_width,
            height=canvas_height,
            highlightthickness=2,
            highlightbackground="gray",
            bg="white"
        )
        self.canvas.pack(expand=True)
        
        # Center the canvas
        canvas_container.pack_propagate(False)
        canvas_container.configure(width=canvas_width + 40, height=canvas_height + 20)
        
        # Bind events
        self.canvas.bind("<Button-1>", self._start_drawing)
        self.canvas.bind("<B1-Motion>", self._draw)
        self.canvas.bind("<ButtonRelease-1>", self._stop_drawing)

    def _setup_regions(self):
        """Create the character regions in a grid layout"""
        self.regions = []
        self.region_images = []
        
        for row in range(self.num_rows):
            for col in range(self.boxes_per_row):
                # Calculate coordinates for this region
                x1 = col * self.region_size
                y1 = row * self.region_size
                x2 = x1 + self.region_size
                y2 = y1 + self.region_size
                
                # Create region rectangle
                region = self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline="#2196F3",  # Material Blue
                    width=2
                )
                
                # Store region info
                self.regions.append({
                    'id': region,
                    'coords': (x1, y1, x2, y2)
                })
                
                # Create image buffer
                img = Image.new('L', (self.region_size, self.region_size), 'white')
                self.region_images.append(img)
                
                if self.debug:
                    logging.debug(f"Created region {row * self.boxes_per_row + col} at ({x1}, {y1}, {x2}, {y2})")

    def _create_controls(self):
        """Create control buttons"""
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        # Calculate button dimensions
        button_width = int(self.screen_width * 0.15)
        button_height = int(self.screen_height * 0.06)
        
        # Recognize button
        self.recognize_btn = RoundedButton(
            control_frame,
            text="Recognize",
            command=self.recognize_characters,
            width=button_width,
            height=button_height,
            bg_color="#4CAF50"  # Green
        )
        self.recognize_btn.pack(side=tk.LEFT, padx=10)
        
        # Clear button
        self.clear_btn = RoundedButton(
            control_frame,
            text="Clear All",
            command=self.clear_all,
            width=button_width,
            height=button_height,
            bg_color="#f44336"  # Red
        )
        self.clear_btn.pack(side=tk.RIGHT, padx=10)

    def _start_drawing(self, event):
        """Handle drawing start"""
        self.drawing = False
        self.current_region = None
        
        # Check which region was clicked
        for i, region in enumerate(self.regions):
            x1, y1, x2, y2 = region['coords']
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.drawing = True
                self.current_region = i
                self.last_x = event.x - x1
                self.last_y = event.y - y1
                
                if self.debug:
                    logging.debug(f"Started drawing in region {i}")
                break

    def _draw(self, event):
        """Handle drawing motion"""
        if not self.drawing or self.current_region is None:
            return
            
        region = self.regions[self.current_region]
        x1, y1, x2, y2 = region['coords']
        
        if not (x1 <= event.x <= x2 and y1 <= event.y <= y2):
            return
            
        curr_x = event.x - x1
        curr_y = event.y - y1
        
        # Draw on canvas
        self.canvas.create_line(
            event.x, event.y,
            self.last_x + x1, self.last_y + y1,
            width=self.line_width,
            fill="black",
            capstyle=tk.ROUND,
            smooth=True
        )
        
        # Draw on image buffer
        draw = ImageDraw.Draw(self.region_images[self.current_region])
        draw.line(
            [self.last_x, self.last_y, curr_x, curr_y],
            fill="black",
            width=self.line_width
        )
        
        self.last_x = curr_x
        self.last_y = curr_y

    def _stop_drawing(self, event):
        """Handle drawing end"""
        if self.drawing and self.current_region is not None and self.debug:
            logging.debug(f"Stopped drawing in region {self.current_region}")
        self.drawing = False

    def clear_all(self):
        """Clear all regions"""
        # Clear canvas
        for region in self.regions:
            coords = region['coords']
            self.canvas.create_rectangle(
                coords[0], coords[1], coords[2], coords[3],
                fill="white",
                outline="#2196F3",
                width=2
            )
        
        # Reset image buffers
        self.region_images = [
            Image.new('L', (self.region_size, self.region_size), 'white')
            for _ in range(self.num_regions)
        ]
        
        if self.debug:
            logging.debug("Cleared all regions")

    def recognize_characters(self):
        """Perform OCR on each region"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = []
        
        for i, img in enumerate(self.region_images):
            # Preprocess image
            img_array = np.array(img)
            _, thresh = cv2.threshold(
                img_array, 0, 255,
                cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
            )
            
            if self.debug:
                debug_path = os.path.join(
                    self.debug_folder,
                    f"region_{i}_{timestamp}.png"
                )
                cv2.imwrite(debug_path, thresh)
                logging.debug(f"Saved debug image for region {i} to {debug_path}")
            
            # Perform OCR
            text = pytesseract.image_to_string(
                thresh,
                config='--psm 10 --oem 3'  # PSM 10 for single character
            ).strip()
            
            results.append(text)
            if self.debug:
                logging.debug(f"Region {i} recognized as: '{text}'")
        
        # Display results in a styled dialog
        self._show_results(results)

    def _show_results(self, results):
        """Show recognition results in a styled dialog"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Recognition Results")
        
        # Calculate size and position
        width = int(self.screen_width * 0.3)
        height = int(self.screen_height * 0.4)
        x = (self.screen_width - width) // 2
        y = (self.screen_height - height) // 2
        
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Title
        ttk.Label(
            dialog,
            text="Recognition Results",
            font=('Arial', int(self.screen_height * 0.03), 'bold')
        ).pack(pady=20)
        
        # Results
        for i, text in enumerate(results):
            ttk.Label(
                dialog,
                text=f"Character {i + 1}: {text}",
                font=('Arial', int(self.screen_height * 0.02))
            ).pack(pady=5)
        
        # Close button
        close_btn = RoundedButton(
            dialog,
            text="Close",
            command=dialog.destroy,
            width=int(width * 0.4),
            height=int(height * 0.15),
            bg_color="#666666"
        )
        close_btn.pack(pady=20)

class NameInputOCR(Component):
    """OCR component specifically for inputting image names"""
    def __init__(self, parent, image_path, on_confirm=None, on_cancel=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.image_path = image_path
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        
        # Calculate dimensions based on screen size
        self.screen_width = parent.winfo_screenwidth()
        self.screen_height = parent.winfo_screenheight()
        self.region_size = int(self.screen_width * 0.08)
        self.num_regions = 8
        self.line_width = max(1, int(self.region_size * 0.03))
        
        # Initialize the result label at class level
        self.result_label = None
        self.current_text = ""  # Add this to track the current text
        
        # Initialize drawing state
        self.drawing = False
        self.current_region = None
        self.last_x = None
        self.last_y = None
        
        # Create the UI
        self._create_ui()
        self._setup_regions()
        self._create_controls()

    def _create_ui(self):
        """Create the main UI components"""
        # Title
        self.title_label = ttk.Label(
            self.frame,
            text="Write Image Name",
            font=('Arial', int(self.screen_height * 0.03), 'bold')
        )
        self.title_label.pack(pady=10)

        # Instructions
        self.instructions = ttk.Label(
            self.frame,
            text="Write one character per box to name your image",
            font=('Arial', int(self.screen_height * 0.02))
        )
        self.instructions.pack(pady=5)

        # Preview of captured image
        self.preview_frame = ttk.Frame(self.frame)
        self.preview_frame.pack(pady=10)
        self._show_image_preview()

        # Canvas for character input
        canvas_container = ttk.Frame(self.frame)
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        total_width = self.num_regions * self.region_size
        self.canvas = tk.Canvas(
            canvas_container,
            width=total_width,
            height=self.region_size,
            highlightthickness=2,
            highlightbackground="gray",
            bg="white"
        )
        self.canvas.pack(expand=True)
        
        # Result label - Added after canvas
        self.result_label = ttk.Label(
            self.frame,
            text="",  # Empty initially
            font=('Arial', int(self.screen_height * 0.02))
        )
        self.result_label.pack(pady=10)  # Make sure to pack it!
        
        # Bind events
        self.canvas.bind("<Button-1>", self._start_drawing)
        self.canvas.bind("<B1-Motion>", self._draw)
        self.canvas.bind("<ButtonRelease-1>", self._stop_drawing)


    def _show_image_preview(self):
        """Show a small preview of the captured image if available"""
        if not self.image_path:
            # If no image, show a message instead
            ttk.Label(
                self.preview_frame,
                text="No image - Name input only",
                font=('Arial', int(self.screen_height * 0.02))
            ).pack()
            return
            
        try:
            image = Image.open(self.image_path)
            
            # Calculate preview size
            preview_height = int(self.screen_height * 0.2)
            aspect_ratio = image.width / image.height
            preview_width = int(preview_height * aspect_ratio)
            
            # Resize image
            image = image.resize((preview_width, preview_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            # Display image
            self.preview_label = ttk.Label(self.preview_frame, image=photo)
            self.preview_label.image = photo
            self.preview_label.pack()
            
        except Exception as e:
            print(f"Error displaying preview: {e}")
            ttk.Label(
                self.preview_frame,
                text="Error displaying image preview",
                font=('Arial', int(self.screen_height * 0.02))
            ).pack()

    def _setup_regions(self):
        """Create the character input regions"""
        self.regions = []
        self.region_images = []
        
        start_x = 0
        start_y = 0
        
        for i in range(self.num_regions):
            x1 = start_x + i * self.region_size
            y1 = start_y
            x2 = x1 + self.region_size
            y2 = y1 + self.region_size
            
            region = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline="#2196F3",
                width=2
            )
            
            self.regions.append({
                'id': region,
                'coords': (x1, y1, x2, y2)
            })
            
            img = Image.new('L', (self.region_size, self.region_size), 'white')
            self.region_images.append(img)

    def _create_controls(self):
        """Create control buttons"""
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        button_width = int(self.screen_width * 0.12)
        button_height = int(self.screen_height * 0.04)
        
        # OCR button to read characters
        self.ocr_btn = RoundedButton(
            control_frame,
            text="Read Text",
            command=self._perform_ocr,
            width=button_width,
            height=button_height,
            bg_color="#c6eb34"
        )
        self.ocr_btn.pack(side=tk.LEFT, padx=20)
        
        # Save button (initially disabled)
        self.save_btn = RoundedButton(
            control_frame,
            text="Save",
            command=self._save_and_proceed,
            width=button_width,
            height=button_height,
            bg_color="#c6eb34"
        )
        self.save_btn.pack(side=tk.LEFT, padx=20)
        self.save_btn.set_enabled(False)  # Disabled until OCR is performed
        
        # Clear button
        self.clear_btn = RoundedButton(
            control_frame,
            text="Clear",
            command=self.clear_all,
            width=button_width,
            height=button_height,
            bg_color="#c6eb34"
        )
        self.clear_btn.pack(side=tk.LEFT, padx=20)
        
        # Cancel button
        self.cancel_btn = RoundedButton(
            control_frame,
            text="Cancel",
            command=self._cancel,
            width=button_width,
            height=button_height,
            bg_color="#c6eb34"
        )
        self.cancel_btn.pack(side=tk.RIGHT, padx=20)



    def _perform_ocr(self):
        """Process the written characters and show result"""
        results = []
        for img in self.region_images:
            img_array = np.array(img)
            _, thresh = cv2.threshold(
                img_array, 0, 255,
                cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
            )
            
            text = pytesseract.image_to_string(
                thresh,
                config='--psm 10 --oem 3'
            ).strip()
            
            if text:  # Only append non-empty results
                results.append(text)
        
        if results:
            # Join characters and clean the filename
            self.current_text = ''.join(results)
            self.current_text = ''.join(c for c in self.current_text if c.isalnum() or c in '._- ')
            
            # Update result label and enable save button
            self.result_label.configure(text=f"Recognized text: {self.current_text}")
            self.save_btn.set_enabled(True)
        else:
            self.current_text = ""  # Set empty text if no results
            self.result_label.configure(text="No text detected. Please try again.")
            self.save_btn.set_enabled(False)


    def _save_and_proceed(self):
        """Save the recognized text and proceed"""
        if hasattr(self, 'current_text') and self.current_text:
            if self.on_confirm:
                self.on_confirm(self.current_text)

    def clear_all(self):
        """Clear all regions and reset UI"""
        super().clear_all()  # Call existing clear method
        self.result_label.config(text="")  # Clear result text
        self.save_btn.set_enabled(False)  # Disable save button


    def _confirm_name(self):
        """Process the written characters and confirm the name"""
        results = []
        for img in self.region_images:
            img_array = np.array(img)
            _, thresh = cv2.threshold(
                img_array, 0, 255,
                cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
            )
            
            text = pytesseract.image_to_string(
                thresh,
                config='--psm 10 --oem 3'
            ).strip()
            
            if text:  # Only append non-empty results
                results.append(text)
        
        if results:
            # Join characters and clean the filename
            filename = ''.join(results)
            filename = ''.join(c for c in filename if c.isalnum() or c in '._- ')
            
            # Show confirmation dialog
            OCRConfirmationDialog(
                self.parent,
                filename,
                on_confirm=lambda name: self._handle_confirmation(name),
                on_retry=self.clear_all
            )
        else:
            # Show error if no characters were recognized
            self._show_error("No characters detected. Please write a name.")

    def _handle_confirmation(self, filename):
        """Handle confirmed filename"""
        if self.on_confirm:
            self.on_confirm(filename)

    def _show_error(self, message):
        """Show error message to user"""
        tk.messagebox.showerror("Error", message)

    def _cancel(self):
        """Handle cancel button click"""
        if self.on_cancel:
            self.on_cancel()

    # Drawing methods (similar to original OCR component)
    def _start_drawing(self, event):
        self.drawing = False
        self.current_region = None
        
        for i, region in enumerate(self.regions):
            x1, y1, x2, y2 = region['coords']
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.drawing = True
                self.current_region = i
                self.last_x = event.x - x1
                self.last_y = event.y - y1
                break

    def _draw(self, event):
        if not self.drawing or self.current_region is None:
            return
            
        region = self.regions[self.current_region]
        x1, y1, x2, y2 = region['coords']
        
        if not (x1 <= event.x <= x2 and y1 <= event.y <= y2):
            return
            
        curr_x = event.x - x1
        curr_y = event.y - y1
        
        self.canvas.create_line(
            event.x, event.y,
            self.last_x + x1, self.last_y + y1,
            width=self.line_width,
            fill="black",
            capstyle=tk.ROUND,
            smooth=True
        )
        
        draw = ImageDraw.Draw(self.region_images[self.current_region])
        draw.line(
            [self.last_x, self.last_y, curr_x, curr_y],
            fill="black",
            width=self.line_width
        )
        
        self.last_x = curr_x
        self.last_y = curr_y

    def _stop_drawing(self, event):
        self.drawing = False

    def clear_all(self):
        """Clear all regions"""
        for region in self.regions:
            coords = region['coords']
            self.canvas.create_rectangle(
                coords[0], coords[1], coords[2], coords[3],
                fill="white",
                outline="#2196F3",
                width=2
            )
        
        self.region_images = [
            Image.new('L', (self.region_size, self.region_size), 'white')
            for _ in range(self.num_regions)
        ]
        
        # Update the result label text
        if self.result_label:
            self.result_label.configure(text="")  # Clear result text
            
        if hasattr(self, 'save_btn'):
            self.save_btn.set_enabled(False)  # Disable save button

class OCRConfirmationDialog(Component):
    """Custom dialog for confirming OCR results"""
    def __init__(self, parent, recognized_text, on_confirm, on_retry, **kwargs):
        super().__init__(parent, **kwargs)
        self.recognized_text = recognized_text
        self.on_confirm = on_confirm
        self.on_retry = on_retry
        
        # Calculate dimensions based on screen size
        self.screen_width = parent.winfo_screenwidth()
        self.screen_height = parent.winfo_screenheight()
        
        # Create semi-transparent overlay
        self.overlay = tk.Frame(
            parent,
            bg='black'
        )
        self.overlay.place(
            x=0, y=0,
            relwidth=1, relheight=1
        )
        self.overlay.configure(bg='black')
        self.overlay.winfo_toplevel().wm_attributes('-alpha', 0.6)
        
        # Create dialog frame
        dialog_width = int(self.screen_width * 0.8)
        dialog_height = int(self.screen_height * 0.4)
        
        self.frame.configure(
            relief='solid',
            borderwidth=1,
            padding=10
        )
        self.frame.place(
            relx=0.5, rely=0.5,
            anchor='center',
            width=dialog_width,
            height=dialog_height
        )
        self.frame.configure(style='Custom.TFrame')
        
        self._create_ui(dialog_width, dialog_height)
        
    def _create_ui(self, width, height):
        # Title
        ttk.Label(
            self.frame,
            text="Confirm Name",
            font=('Arial', int(self.screen_height * 0.03), 'bold'),
            justify='center'
        ).pack(pady=(height * 0.05, height * 0.02))
        
        # Recognition result
        ttk.Label(
            self.frame,
            text=f"Recognized text: {self.recognized_text}",
            font=('Arial', int(self.screen_height * 0.025)),
            justify='center',
            wraplength=width * 0.8
        ).pack(pady=(0, height * 0.05))
        
        # Buttons container
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(side='bottom', pady=height * 0.05)
        
        # Button dimensions
        button_width = int(width * 0.25)
        button_height = int(height * 0.15)
        
        # Confirm button
        self.confirm_btn = RoundedButton(
            button_frame,
            text="Save",
            command=self._confirm,
            width=button_width,
            height=button_height,
            bg_color="#c6eb34"
        )
        self.confirm_btn.pack(side='left', padx=width * 0.05)
        
        # Retry button
        self.retry_btn = RoundedButton(
            button_frame,
            text="Retry",
            command=self._retry,
            width=button_width,
            height=button_height,
            bg_color="#c6eb34"
        )
        self.retry_btn.pack(side='left', padx=width * 0.05)
    
    def _confirm(self):
        self.destroy()
        if self.on_confirm:
            self.on_confirm(self.recognized_text)
    
    def _retry(self):
        self.destroy()
        if self.on_retry:
            self.on_retry()
    
    def destroy(self):
        self.overlay.destroy()
        super().destroy()

def main():
    root = tk.Tk()
    app = FlashcardApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()