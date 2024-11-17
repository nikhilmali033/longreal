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

#pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class CharacterOCRComponent:
    def __init__(self, parent, num_regions=5, debug=True):
        """Initialize the OCR component with the parent widget"""
        self.parent = parent
        self.frame = ttk.Frame(parent)
        
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
        
        # Calculate dimensions based on screen size
        self.screen_width = parent.winfo_screenwidth()
        self.screen_height = parent.winfo_screenheight()
        
        # Adjust region size based on screen dimensions
        self.region_size = min(int(self.screen_width * 0.15), int(self.screen_height * 0.2))
        self.num_regions = num_regions
        self.line_width = max(2, int(self.region_size * 0.03))  # Scaled line width
        
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

        # Canvas container (to ensure proper centering)
        canvas_container = ttk.Frame(self.frame)
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Main canvas with white background
        self.canvas = tk.Canvas(
            canvas_container,
            highlightthickness=2,
            highlightbackground="gray",
            bg="white"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind events
        self.canvas.bind("<Button-1>", self._start_drawing)
        self.canvas.bind("<B1-Motion>", self._draw)
        self.canvas.bind("<ButtonRelease-1>", self._stop_drawing)

    def _setup_regions(self):
        """Create the character regions"""
        self.regions = []
        self.region_images = []
        
        # Calculate layout
        total_width = self.num_regions * (self.region_size + 10)
        start_x = (self.screen_width - total_width) // 2
        start_y = (self.screen_height - self.region_size) // 2
        
        for i in range(self.num_regions):
            x1 = start_x + i * (self.region_size + 10)
            y1 = start_y
            x2 = x1 + self.region_size
            y2 = y1 + self.region_size
            
            # Create region rectangle with blue border
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
                logging.debug(f"Created region {i} at ({x1}, {y1}, {x2}, {y2})")

    def _create_controls(self):
        """Create control buttons"""
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        # Button style matching your Flashcard app
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

    def pack(self, **kwargs):
        """Pack the frame with the given options"""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        """Grid the frame with the given options"""
        self.frame.grid(**kwargs)

    def destroy(self):
        """Clean up resources"""
        self.frame.destroy()
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

class CharacterOCRComponent(Component):
    def __init__(self, parent, debug=True):
        """Initialize the OCR component with the parent widget"""
        super().__init__(parent)
        
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
        
        # Set up grid configuration
        self.rows = 2
        self.cols = 4
        self.num_regions = self.rows * self.cols
        
        # Calculate dimensions based on screen size
        self.screen_width = parent.winfo_screenwidth()
        self.screen_height = parent.winfo_screenheight()
        
        # Calculate region size based on screen width and number of columns
        # Subtract padding and borders to ensure exact fit
        total_horizontal_padding = 40  # 20px padding on each side
        self.region_size = (self.screen_width - total_horizontal_padding) // self.cols
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
        self.canvas_container = ttk.Frame(self.frame)
        self.canvas_container.pack(fill=tk.BOTH, expand=True, padx=20)
        
        # Main canvas with white background
        canvas_height = (self.region_size * self.rows) + 40  # Add some padding
        self.canvas = tk.Canvas(
            self.canvas_container,
            width=self.screen_width - 40,  # Full width minus padding
            height=canvas_height,
            highlightthickness=1,
            highlightbackground="gray",
            bg="white"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind events
        self.canvas.bind("<Button-1>", self._start_drawing)
        self.canvas.bind("<B1-Motion>", self._draw)
        self.canvas.bind("<ButtonRelease-1>", self._stop_drawing)

    def _setup_regions(self):
        """Create the character regions in a grid layout"""
        self.regions = []
        self.region_images = []
        
        for row in range(self.rows):
            for col in range(self.cols):
                # Calculate coordinates for this region
                x1 = col * self.region_size
                y1 = row * self.region_size
                x2 = x1 + self.region_size
                y2 = y1 + self.region_size
                
                # Create region rectangle with blue border
                region = self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline="#2196F3",  # Material Blue
                    width=1
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
                    logging.debug(f"Created region at row {row}, col {col} at ({x1}, {y1}, {x2}, {y2})")

    def _create_controls(self):
        """Create control buttons"""
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        # Button dimensions based on screen size
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
        
        # Results container
        results_frame = ttk.Frame(dialog)
        results_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Grid layout for results
        for i, text in enumerate(results):
            row = i // self.cols
            col = i % self.cols
            
            result_label = ttk.Label(
                results_frame,
                text=text,
                font=('Arial', int(self.screen_height * 0.03))
            )
            result_label.grid(row=row, column=col, padx=10, pady=10)
        
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

    # The rest of the methods remain largely unchanged
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
        for region in self.regions:
            coords = region['coords']
            self.canvas.create_rectangle(
                coords[0], coords[1], coords[2], coords[3],
                fill="white",
                outline="#2196F3",
                width=1
            )
        
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
            
        # Display results in a styled dialog
        self._show_results(results)
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
        self.current_component = CaptureReviewComponent(
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

def main():
    root = tk.Tk()
    app = FlashcardApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()