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
import tkinter.messagebox

class OCRScreen:
    def __init__(self, root, width, height, callback, back_callback):
        self.frame = tk.Frame(root)
        self.frame.pack(expand=True, fill=tk.BOTH)
        
        # Create button frame FIRST and pack at BOTTOM
        button_frame = tk.Frame(self.frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # Create buttons with larger size for touch
        button_width = 10
        button_height = 2
        button_font = ('Arial', 14)
        
        # Pack buttons from right to left to ensure visibility
        self.back_btn = tk.Button(
            button_frame,
            text="Back",
            command=back_callback,
            width=button_width,
            height=button_height,
            font=button_font
        )
        self.back_btn.pack(side=tk.RIGHT, padx=5)
        
        self.clear_btn = tk.Button(
            button_frame,
            text="Clear",
            command=self.clear_canvas,
            width=button_width,
            height=button_height,
            font=button_font
        )
        self.clear_btn.pack(side=tk.RIGHT, padx=5)
        
        self.recognize_btn = tk.Button(
            button_frame,
            text="Recognize",
            command=lambda: self.recognize_and_callback(callback),
            width=button_width,
            height=button_height,
            font=button_font
        )
        self.recognize_btn.pack(side=tk.RIGHT, padx=5)
        
        # Calculate canvas size to fit above buttons
        canvas_height = height - 100  # Reduced height to ensure buttons are visible
        canvas_width = width - 20     # Small margin on sides
        canvas_size = min(canvas_width, canvas_height)
        
        # Drawing canvas for OCR - pack AFTER buttons
        self.canvas = tk.Canvas(
            self.frame,
            width=canvas_size,
            height=canvas_size,
            bg="white",
            highlightthickness=2,
            highlightbackground="blue"
        )
        self.canvas.pack(expand=True, padx=10, pady=5)
        
        # Drawing state
        self.drawing = False
        self.last_x = None
        self.last_y = None
        
        # Create image buffer with specific size
        self.canvas_size = canvas_size
        self.image = Image.new('L', (self.canvas_size, self.canvas_size), 'white')
        self.draw = ImageDraw.Draw(self.image)
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.draw_character)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drawing)
    
    def start_drawing(self, event):
        self.drawing = True
        self.last_x = event.x
        self.last_y = event.y
    
    def draw_character(self, event):
        if self.drawing and self.last_x is not None and self.last_y is not None:
            # Draw on canvas
            self.canvas.create_line(
                self.last_x, self.last_y,
                event.x, event.y,
                fill="black",
                width=3,
                smooth=True,
                splinesteps=12
            )
            
            # Draw on image buffer
            self.draw.line(
                [self.last_x, self.last_y, event.x, event.y],
                fill="black",
                width=3,
                joint="curve"
            )
            
            self.last_x = event.x
            self.last_y = event.y
    
    def stop_drawing(self, event):
        self.drawing = False
        self.last_x = None
        self.last_y = None
    
    def clear_canvas(self):
        self.canvas.delete("all")
        self.image = Image.new('L', (self.canvas_size, self.canvas_size), 'white')
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
        else:
            tkinter.messagebox.showwarning(
                "Recognition Failed",
                "Could not recognize character. Please try again."
            )
    
    def destroy(self):
        self.frame.destroy()

class FlashcardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Flashcard App")
        
        # Configure for 3.5" TFT LCD (480x320)
        self.screen_width = 480
        self.screen_height = 320
        self.root.geometry(f"{self.screen_width}x{self.screen_height}")
        
        # Force fullscreen and remove window decorations
        self.root.attributes('-fullscreen', True)
        
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
        
        # Create main screen container
        self.current_screen = tk.Frame(self.root)
        self.current_screen.pack(fill=tk.BOTH, expand=True)
        
        # Create top frame for exit button
        top_frame = tk.Frame(self.current_screen)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add X button in its own frame
        exit_btn = tk.Button(
            top_frame,
            text="X",
            command=self.root.quit,
            font=('Arial', 16, 'bold'),
            width=3,
            height=1,
            bg='red',
            fg='white'
        )
        exit_btn.pack(side=tk.RIGHT)
        
        # Create center frame for main buttons
        center_frame = tk.Frame(self.current_screen)
        center_frame.pack(expand=True)
        
        self.create_button(
            center_frame,
            "New Flashcard",
            self.start_new_flashcard
        ).pack(pady=20)
        
        self.create_button(
            center_frame,
            "View Flashcards",
            self.show_flashcard_list
        ).pack(pady=20)
        """Display main menu"""
        self.clear_screen()
        self.current_screen = tk.Frame(self.root)
        self.current_screen.pack(expand=True)
        
        self.create_button(
            self.current_screen,
            "Exit",
            self.root.quit
        ).pack(pady=20)
        

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
            tkinter.messagebox.showerror(
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

if __name__ == "__main__":
    root = tk.Tk()
    app = FlashcardApp(root)
    root.mainloop()