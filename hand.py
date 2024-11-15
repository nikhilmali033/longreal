import tkinter as tk
from PIL import Image, ImageDraw
import numpy as np
import cv2
import pytesseract
import os
from datetime import datetime
import logging

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class CharacterDrawingOCR:
    def __init__(self, root, num_regions=5, region_size=100):
        self.root = root
        self.root.title("Character Drawing OCR")
        self.root.attributes('-fullscreen', True)
        
        # Initialize debug settings
        self.debug_mode = True
        self.debug_folder = "debug_captures"
        os.makedirs(self.debug_folder, exist_ok=True)
        
        logging.basicConfig(
            filename='drawing_ocr_debug.log',
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Drawing settings
        self.line_width = 3
        self.region_size = region_size
        self.num_regions = num_regions
        
        # Create main canvas
        self.canvas = tk.Canvas(
            root,
            highlightthickness=1,
            highlightbackground="gray",
            bg="white"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create regions and their corresponding image buffers
        self.regions = []
        self.region_images = []
        self.setup_regions()
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drawing)
        
        # Track drawing state
        self.drawing = False
        self.current_region = None
        self.last_x = None
        self.last_y = None
        
        # Create control buttons
        self.create_controls()
        
    def setup_regions(self):
        """Create predefined regions for character drawing"""
        # Calculate total width needed
        total_width = self.num_regions * (self.region_size + 20)  # 20px padding
        
        # Center the regions horizontally
        start_x = (self.root.winfo_screenwidth() - total_width) // 2
        start_y = (self.root.winfo_screenheight() - self.region_size) // 2
        
        for i in range(self.num_regions):
            x1 = start_x + i * (self.region_size + 20)
            y1 = start_y
            x2 = x1 + self.region_size
            y2 = y1 + self.region_size
            
            # Create region rectangle
            region = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline="blue",
                width=2
            )
            self.regions.append({
                'id': region,
                'coords': (x1, y1, x2, y2)
            })
            
            # Create corresponding image buffer
            img = Image.new('L', (self.region_size, self.region_size), 'white')
            self.region_images.append(img)
            
            logging.debug(f"Created region {i} at coordinates ({x1}, {y1}, {x2}, {y2})")
    
    def create_controls(self):
        """Create control buttons"""
        control_frame = tk.Frame(self.root)
        control_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        tk.Button(
            control_frame,
            text="Recognize",
            command=self.recognize_characters
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            control_frame,
            text="Clear All",
            command=self.clear_all
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            control_frame,
            text="Exit",
            command=self.root.quit
        ).pack(side=tk.RIGHT, padx=5)
    
    def start_drawing(self, event):
        """Start drawing when mouse is clicked in a region"""
        self.drawing = False
        self.current_region = None
        
        # Check if click is within any region
        for i, region in enumerate(self.regions):
            x1, y1, x2, y2 = region['coords']
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.drawing = True
                self.current_region = i
                self.last_x = event.x - x1  # Convert to region-relative coordinates
                self.last_y = event.y - y1
                logging.debug(f"Started drawing in region {i}")
                break
    
    def draw(self, event):
        """Handle drawing within a region"""
        if not self.drawing or self.current_region is None:
            return
            
        region = self.regions[self.current_region]
        x1, y1, x2, y2 = region['coords']
        
        # Check if we're still in the region
        if not (x1 <= event.x <= x2 and y1 <= event.y <= y2):
            return
            
        # Convert to region-relative coordinates
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
    
    def stop_drawing(self, event):
        """Stop drawing"""
        if self.drawing and self.current_region is not None:
            logging.debug(f"Stopped drawing in region {self.current_region}")
        self.drawing = False
    
    def clear_all(self):
        """Clear all regions"""
        # Clear canvas except for region rectangles
        for region in self.regions:
            coords = region['coords']
            self.canvas.create_rectangle(
                coords[0], coords[1], coords[2], coords[3],
                fill="white",
                outline="blue",
                width=2
            )
        
        # Reset image buffers
        self.region_images = [
            Image.new('L', (self.region_size, self.region_size), 'white')
            for _ in range(self.num_regions)
        ]
        
        logging.debug("Cleared all regions")
    
    def recognize_characters(self):
        """Perform OCR on each region"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = []
        
        for i, img in enumerate(self.region_images):
            # Preprocess the image
            img_array = np.array(img)
            _, thresh = cv2.threshold(
                img_array, 0, 255,
                cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
            )
            
            if self.debug_mode:
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
            logging.debug(f"Region {i} recognized as: '{text}'")
        
        # Display results
        result_window = tk.Toplevel(self.root)
        result_window.title("Recognition Results")
        
        for i, text in enumerate(results):
            tk.Label(
                result_window,
                text=f"Region {i + 1}: {text}",
                font=("Arial", 14)
            ).pack(pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = CharacterDrawingOCR(root)
    root.mainloop()