import tkinter as tk
from PIL import Image, ImageDraw, ImageTk
import numpy as np
import cv2
import pytesseract
import os
import subprocess
import datetime
import logging
from pathlib import Path

class FlashcardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Flashcard OCR")
        
        # Get screen dimensions
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        
        # Make it fullscreen and remove window decorations
        self.root.attributes('-fullscreen', True)
        self.root.config(cursor="none")  # Hide cursor for touch interface
        
        # Set up directories
        self.base_dir = Path("flashcards")
        self.image_dir = self.base_dir / "images"
        self.debug_dir = self.base_dir / "debug"
        for dir_path in [self.base_dir, self.image_dir, self.debug_dir]:
            dir_path.mkdir(exist_ok=True)
            
        # Set up logging
        logging.basicConfig(
            filename='flashcard_ocr.log',
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Initialize state variables
        self.current_image = None
        self.current_frame = None
        
        # Create and show main menu
        self.show_main_menu()
        
    def show_main_menu(self):
        self.clear_screen()
        
        # Create main menu frame
        menu_frame = tk.Frame(self.root)
        menu_frame.pack(expand=True)
        
        # Calculate button sizes based on screen
        button_width = min(200, self.screen_width // 2)
        button_height = min(100, self.screen_height // 4)
        
        # Create menu buttons
        tk.Button(
            menu_frame,
            text="New Flashcard",
            command=self.start_new_flashcard,
            width=button_width,
            height=button_height
        ).pack(pady=20)
        
        tk.Button(
            menu_frame,
            text="View Flashcards",
            command=self.show_flashcard_list,
            width=button_width,
            height=button_height
        ).pack(pady=20)
        
    def clear_screen(self):
        """Remove all widgets from the screen"""
        for widget in self.root.winfo_children():
            widget.destroy()
            
    def capture_image(self):
        """Capture image using libcamera-jpeg"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.image_dir / f"temp_{timestamp}.jpg"
        
        try:
            # Adjust resolution for your screen
            cmd = [
                "libcamera-jpeg",
                "-o", str(filename),
                "--width", "640",  # Adjusted for smaller display
                "--height", "480",
                "--nopreview"
            ]
            
            subprocess.run(cmd, check=True)
            logging.debug(f"Image captured: {filename}")
            return filename
        except subprocess.CalledProcessError as e:
            logging.error(f"Camera capture error: {e}")
            return None
            
    def start_new_flashcard(self):
        self.clear_screen()
        
        # Create capture button frame
        capture_frame = tk.Frame(self.root)
        capture_frame.pack(expand=True)
        
        tk.Button(
            capture_frame,
            text="Take Picture",
            command=self.handle_capture,
            width=20,
            height=3
        ).pack(pady=20)
        
        tk.Button(
            capture_frame,
            text="Back",
            command=self.show_main_menu,
            width=10,
            height=2
        ).pack(pady=10)
        
    def handle_capture(self):
        """Handle image capture and transition to OCR"""
        image_path = self.capture_image()
        if image_path:
            self.current_image = image_path
            self.show_ocr_input()
            
    def show_ocr_input(self):
        """Show OCR drawing interface"""
        self.clear_screen()
        
        # Create drawing canvas sized for small screen
        canvas_size = min(self.screen_width - 20, 300)  # Maximum 300px wide
        char_size = canvas_size // 5  # Size for each character region
        
        self.canvas = tk.Canvas(
            self.root,
            width=canvas_size,
            height=char_size,
            bg="white"
        )
        self.canvas.pack(pady=10)
        
        # Create character regions
        self.regions = []
        for i in range(5):  # 5 character regions
            x1 = i * char_size
            x2 = x1 + char_size
            region = self.canvas.create_rectangle(
                x1, 0, x2, char_size,
                outline="blue"
            )
            self.regions.append({
                'id': region,
                'coords': (x1, 0, x2, char_size)
            })
            
        # Create image buffer for each region
        self.region_images = [
            Image.new('L', (char_size, char_size), 'white')
            for _ in range(5)
        ]
        
        # Bind drawing events
        self.canvas.bind("<Button-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drawing)
        
        # Control buttons
        tk.Button(
            self.root,
            text="Recognize",
            command=self.process_and_save_flashcard
        ).pack(pady=5)
        
        tk.Button(
            self.root,
            text="Clear",
            command=self.clear_drawing
        ).pack(pady=5)
        
        tk.Button(
            self.root,
            text="Back",
            command=self.show_main_menu
        ).pack(pady=5)
        
    def start_drawing(self, event):
        """Initialize drawing in a region"""
        self.drawing = False
        self.current_region = None
        
        for i, region in enumerate(self.regions):
            x1, y1, x2, y2 = region['coords']
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.drawing = True
                self.current_region = i
                self.last_x = event.x - x1
                self.last_y = event.y
                break
                
    def draw(self, event):
        """Handle drawing within a region"""
        if not self.drawing or self.current_region is None:
            return
            
        region = self.regions[self.current_region]
        x1, y1, x2, y2 = region['coords']
        
        if x1 <= event.x <= x2 and y1 <= event.y <= y2:
            curr_x = event.x - x1
            curr_y = event.y
            
            # Draw on canvas
            self.canvas.create_line(
                event.x, event.y,
                self.last_x + x1, self.last_y,
                width=2,
                fill="black"
            )
            
            # Draw on image buffer
            draw = ImageDraw.Draw(self.region_images[self.current_region])
            draw.line(
                [self.last_x, self.last_y - y1, curr_x, curr_y - y1],
                fill="black",
                width=2
            )
            
            self.last_x = curr_x
            self.last_y = curr_y
            
    def stop_drawing(self, event):
        self.drawing = False
        
    def clear_drawing(self):
        """Clear all drawing regions"""
        for region in self.regions:
            x1, y1, x2, y2 = region['coords']
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill="white",
                outline="blue"
            )
        
        self.region_images = [
            Image.new('L', (x2-x1, y2-y1), 'white')
            for x1, y1, x2, y2 in [r['coords'] for r in self.regions]
        ]
        
    def process_and_save_flashcard(self):
        """Process OCR and save flashcard"""
        text = ""
        for img in self.region_images:
            # Preprocess image
            img_array = np.array(img)
            _, thresh = cv2.threshold(
                img_array, 0, 255,
                cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
            )
            
            # Perform OCR
            char = pytesseract.image_to_string(
                thresh,
                config='--psm 10 --oem 3'
            ).strip()
            text += char
            
        if text and self.current_image:
            # Create new filename based on OCR text
            new_name = f"{text}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            new_path = self.image_dir / new_name
            
            # Rename and move the image
            os.rename(self.current_image, new_path)
            logging.debug(f"Saved flashcard: {new_path}")
            
            # Show success message
            self.show_message(f"Saved flashcard: {text}")
            
    def show_message(self, message, duration=2000):
        """Show temporary message"""
        msg_label = tk.Label(self.root, text=message)
        msg_label.pack(pady=10)
        self.root.after(duration, msg_label.destroy)
        self.root.after(duration, self.show_main_menu)
        
    def show_flashcard_list(self):
        """Show list of existing flashcards"""
        self.clear_screen()
        
        # Create scrollable frame
        container = tk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Get list of flashcards
        flashcards = sorted(self.image_dir.glob("*.jpg"))
        
        # Create button for each flashcard
        for card_path in flashcards:
            name = card_path.stem  # Remove extension
            tk.Button(
                container,
                text=name,
                command=lambda p=card_path: self.show_flashcard(p)
            ).pack(fill=tk.X, padx=5, pady=2)
            
        tk.Button(
            container,
            text="Back",
            command=self.show_main_menu
        ).pack(pady=10)
        
    def show_flashcard(self, image_path):
        """Display individual flashcard"""
        self.clear_screen()
        
        # Load and resize image for display
        image = Image.open(image_path)
        image.thumbnail((self.screen_width - 20, self.screen_height - 60))
        photo = ImageTk.PhotoImage(image)
        
        # Show image
        label = tk.Label(self.root, image=photo)
        label.image = photo  # Keep reference
        label.pack(pady=10)
        
        # Back button
        tk.Button(
            self.root,
            text="Back",
            command=self.show_flashcard_list
        ).pack(pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = FlashcardApp(root)
    root.mainloop()