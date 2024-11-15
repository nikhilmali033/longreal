import tkinter as tk
from PIL import Image, ImageDraw, ImageTk
import numpy as np
import cv2
import pytesseract
import os
import subprocess
import datetime
import signal
import logging
from pathlib import Path

class FlashcardApp:
    def __init__(self, root, width, height, callback, back_callback):
        self.frame = tk.Frame(root)
        self.frame.pack(expand=True, fill=tk.BOTH)
        
        # Drawing canvas for OCR - make it slightly smaller to ensure room for buttons
        canvas_size = min(width, height) - 80  # Reduced size to ensure space for buttons
        self.canvas = tk.Canvas(
            self.frame,
            width=canvas_size,
            height=canvas_size,
            bg="white"
        )
        self.canvas.pack(pady=5)  # Reduced padding
        
        # Drawing state
        self.drawing = False
        self.last_x = None
        self.last_y = None
        
        # Create image buffer
        self.image = Image.new('L', (canvas_size, canvas_size), 'white')
        self.draw = ImageDraw.Draw(self.image)
        
        # Bind events
        self.canvas.bind("<Button-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.draw_character)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drawing)
        
        # Button frame
        button_frame = tk.Frame(self.frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create buttons with consistent size
        button_width = 8  # Reduced width to fit all buttons
        button_height = 1
        button_font = ('Arial', 12)
        
        tk.Button(
            button_frame,
            text="Recognize",
            command=lambda: self.recognize_and_callback(callback),
            width=button_width,
            height=button_height,
            font=button_font
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            button_frame,
            text="Clear",
            command=self.clear_canvas,
            width=button_width,
            height=button_height,
            font=button_font
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            button_frame,
            text="Back",
            command=back_callback,
            width=button_width,
            height=button_height,
            font=button_font
        ).pack(side=tk.LEFT, padx=2)
        self.root = root
        self.root.title("Flashcard App")
        
        # Configure for 3.5" TFT LCD (480x320 is common for these displays)
        self.screen_width = 480
        self.screen_height = 320
        self.root.geometry(f"{self.screen_width}x{self.screen_height}")
        
        # Setup directories
        self.base_dir = Path("flashcards")
        self.images_dir = self.base_dir / "images"
        self.debug_dir = self.base_dir / "debug"
        for directory in [self.base_dir, self.images_dir, self.debug_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize logging
        logging.basicConfig(
            filename='flashcard_app.log',
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Setup SIGINT handler
        signal.signal(signal.SIGINT, self.handle_sigint)
        
        # Initialize main screen
        self.current_screen = None
        self.show_main_screen()
    
    def handle_sigint(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        logging.info("Received SIGINT, shutting down...")
        self.root.quit()
    
    def clear_screen(self):
        """Clear current screen contents"""
        if self.current_screen:
            self.current_screen.destroy()
    
    def create_button(self, parent, text, command, height=2):
        """Create a standardized button"""
        return tk.Button(
            parent,
            text=text,
            command=command,
            height=height,
            font=('Arial', 16),
            width=20
        )
    
    def show_main_screen(self):
        """Display main menu"""
        self.clear_screen()
        self.current_screen = tk.Frame(self.root)
        self.current_screen.pack(expand=True)
        
        self.create_button(
            self.current_screen,
            "New Flashcard",
            self.start_new_flashcard
        ).pack(pady=20)
        
        self.create_button(
            self.current_screen,
            "View Flashcards",
            self.show_flashcard_list
        ).pack(pady=20)
    
    def capture_image(self):
        """Capture image using libcamera-jpeg"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.images_dir / f"temp_{timestamp}.jpg"
        
        try:
            cmd = [
                "libcamera-jpeg",
                "-o", str(filename),
                "--width", "2304",
                "--height", "1296",
                "--nopreview"
            ]
            
            subprocess.run(cmd, check=True)
            logging.info(f"Image captured: {filename}")
            return filename
        except subprocess.CalledProcessError as e:
            logging.error(f"Camera capture error: {e}")
            return None
    
    def start_new_flashcard(self):
        """Start new flashcard creation process"""
        self.clear_screen()
        self.current_screen = tk.Frame(self.root)
        self.current_screen.pack(expand=True)
        
        self.create_button(
            self.current_screen,
            "Take Picture",
            self.take_picture_and_label
        ).pack(pady=20)
        
        self.create_button(
            self.current_screen,
            "Back",
            self.show_main_screen
        ).pack(pady=20)
    
    def take_picture_and_label(self):
        """Capture image and proceed to labeling"""
        image_path = self.capture_image()
        if image_path:
            self.current_image_path = image_path
            self.show_ocr_screen()
        else:
            # Show error message
            tk.messagebox.showerror(
                "Error",
                "Failed to capture image. Please try again."
            )
    
    def show_ocr_screen(self):
        """Show OCR input screen"""
        self.clear_screen()
        self.current_screen = OCRScreen(
            self.root,
            self.screen_width,
            self.screen_height,
            self.finish_flashcard,
            self.show_main_screen
        )
    
    def finish_flashcard(self, label):
        """Save flashcard with OCR label"""
        if hasattr(self, 'current_image_path'):
            # Rename image file with label
            new_path = self.images_dir / f"{label}.jpg"
            Path(self.current_image_path).rename(new_path)
            logging.info(f"Created flashcard: {label}")
            
            # Return to main screen
            self.show_main_screen()
    
    def show_flashcard_list(self):
        """Display list of existing flashcards"""
        self.clear_screen()
        self.current_screen = tk.Frame(self.root)
        self.current_screen.pack(expand=True)
        
        # Create scrollable frame for flashcard list
        canvas = tk.Canvas(self.current_screen)
        scrollbar = tk.Scrollbar(
            self.current_screen,
            orient="vertical",
            command=canvas.yview
        )
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # List all flashcards
        for image_file in sorted(self.images_dir.glob("*.jpg")):
            name = image_file.stem
            self.create_button(
                scrollable_frame,
                name,
                lambda p=image_file: self.show_flashcard(p),
                height=1
            ).pack(pady=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.create_button(
            self.current_screen,
            "Back",
            self.show_main_screen,
            height=1
        ).pack(pady=10)
    
    def show_flashcard(self, image_path):
        """Display individual flashcard"""
        self.clear_screen()
        self.current_screen = tk.Frame(self.root)
        self.current_screen.pack(expand=True)
        
        # Load and resize image to fit screen
        image = Image.open(image_path)
        image.thumbnail((
            self.screen_width - 20,
            self.screen_height - 60
        ))
        photo = ImageTk.PhotoImage(image)
        
        # Display image
        label = tk.Label(self.current_screen, image=photo)
        label.image = photo  # Keep reference
        label.pack(pady=10)
        
        self.create_button(
            self.current_screen,
            "Back",
            self.show_flashcard_list,
            height=1
        ).pack(pady=5)

class OCRScreen:
    def __init__(self, root, width, height, callback, back_callback):
        self.frame = tk.Frame(root)
        self.frame.pack(expand=True)
        
        # Drawing canvas for OCR
        canvas_size = min(width, height) - 60
        self.canvas = tk.Canvas(
            self.frame,
            width=canvas_size,
            height=canvas_size,
            bg="white"
        )
        self.canvas.pack(pady=10)
        
        # Drawing state
        self.drawing = False
        self.last_x = None
        self.last_y = None
        
        # Create image buffer
        self.image = Image.new('L', (canvas_size, canvas_size), 'white')
        self.draw = ImageDraw.Draw(self.image)
        
        # Bind events
        self.canvas.bind("<Button-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.draw_character)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drawing)
        
        # Buttons
        tk.Button(
            self.frame,
            text="Recognize",
            command=lambda: self.recognize_and_callback(callback)
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            self.frame,
            text="Clear",
            command=self.clear_canvas
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            self.frame,
            text="Back",
            command=back_callback
        ).pack(side=tk.RIGHT, padx=10)
    
    def start_drawing(self, event):
        self.drawing = True
        self.last_x = event.x
        self.last_y = event.y
    
    def draw_character(self, event):
        if self.drawing:
            self.canvas.create_line(
                self.last_x, self.last_y,
                event.x, event.y,
                width=3
            )
            self.draw.line(
                [self.last_x, self.last_y, event.x, event.y],
                fill="black",
                width=3
            )
            self.last_x = event.x
            self.last_y = event.y
    
    def stop_drawing(self, event):
        self.drawing = False
    
    def clear_canvas(self):
        self.canvas.delete("all")
        self.image = Image.new('L', self.image.size, 'white')
        self.draw = ImageDraw.Draw(self.image)
    
    def recognize_and_callback(self, callback):
        # Convert to numpy array for OpenCV
        img_array = np.array(self.image)
        
        # Preprocess
        _, thresh = cv2.threshold(
            img_array, 0, 255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )
        
        # Perform OCR
        text = pytesseract.image_to_string(
            thresh,
            config='--psm 10 --oem 3'
        ).strip()
        
        if text:
            callback(text)
    
    def destroy(self):
        self.frame.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FlashcardApp(root)
    root.mainloop()