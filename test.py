import tkinter as tk
from tkinter import ttk
import json
import os
from PIL import Image, ImageDraw
from datetime import datetime

class FlashcardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Set up fullscreen
        self.attributes('-fullscreen', True)
        self.geometry("480x320")  # Common resolution for 3.5" TFT
        
        # Initialize storage
        self.cards_dir = "flashcards"
        if not os.path.exists(self.cards_dir):
            os.makedirs(self.cards_dir)
            
        self.current_page = None
        self.setup_styles()
        self.show_home()

    def setup_styles(self):
        # Configure large fonts for small screen
        self.title_font = ('Helvetica', 24, 'bold')
        self.button_font = ('Helvetica', 20)
        self.list_font = ('Helvetica', 16)
        
        # Style for buttons
        style = ttk.Style()
        style.configure('Large.TButton', font=self.button_font, padding=10)

    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_home(self):
        self.clear_screen()
        
        # Title
        title = tk.Label(self, text="Digital Flashcards", font=self.title_font)
        title.pack(pady=30)
        
        # Main buttons
        view_btn = ttk.Button(self, text="View Flashcards", 
                             command=self.show_view_cards,
                             style='Large.TButton')
        view_btn.pack(pady=20, padx=40, fill='x')
        
        new_btn = ttk.Button(self, text="Make New Flashcard", 
                            command=self.show_drawing_canvas,
                            style='Large.TButton')
        new_btn.pack(pady=20, padx=40, fill='x')

    def show_view_cards(self):
        self.clear_screen()
        
        # Title
        title = tk.Label(self, text="Your Flashcards", font=self.title_font)
        title.pack(pady=20)
        
        # Scrollable frame for cards
        container = ttk.Frame(self)
        container.pack(fill='both', expand=True, padx=20, pady=10)
        
        # List cards
        cards = sorted([f for f in os.listdir(self.cards_dir) if f.endswith('.png')])
        for i, card in enumerate(cards, 1):
            btn = ttk.Button(container, 
                           text=f"Flashcard {i}",
                           command=lambda c=card: self.view_card(c),
                           style='Large.TButton')
            btn.pack(pady=5, fill='x')
        
        # Back button
        back_btn = ttk.Button(self, text="Back", 
                             command=self.show_home,
                             style='Large.TButton')
        back_btn.pack(pady=20, side='bottom')

    def view_card(self, card_name):
        self.clear_screen()
        
        # Load and display card
        img = tk.PhotoImage(file=os.path.join(self.cards_dir, card_name))
        label = tk.Label(self, image=img)
        label.image = img  # Keep a reference
        label.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Back button
        back_btn = ttk.Button(self, text="Back", 
                             command=self.show_view_cards,
                             style='Large.TButton')
        back_btn.pack(pady=10, side='bottom')

    def show_drawing_canvas(self):
        self.clear_screen()
        
        # Canvas for drawing
        self.canvas = tk.Canvas(self, bg='white')
        self.canvas.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Drawing variables
        self.last_x = None
        self.last_y = None
        
        # Bind mouse events
        self.canvas.bind('<Button-1>', self.start_drawing)
        self.canvas.bind('<B1-Motion>', self.draw)
        self.canvas.bind('<ButtonRelease-1>', self.stop_drawing)
        
        # Button frame
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill='x', pady=10)
        
        # Save and back buttons
        save_btn = ttk.Button(btn_frame, text="Save", 
                             command=self.save_card,
                             style='Large.TButton')
        save_btn.pack(side='left', padx=10, expand=True)
        
        back_btn = ttk.Button(btn_frame, text="Back", 
                             command=self.show_home,
                             style='Large.TButton')
        back_btn.pack(side='right', padx=10, expand=True)

    def start_drawing(self, event):
        self.last_x = event.x
        self.last_y = event.y

    def draw(self, event):
        if self.last_x and self.last_y:
            self.canvas.create_line(self.last_x, self.last_y,
                                  event.x, event.y,
                                  width=3, smooth=True)
        self.last_x = event.x
        self.last_y = event.y

    def stop_drawing(self, event):
        self.last_x = None
        self.last_y = None

    def save_card(self):
        # Generate filename with timestamp
        filename = f"card_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        # Get canvas content
        self.canvas.update()
        x = self.canvas.winfo_rootx()
        y = self.canvas.winfo_rooty()
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        # Create image from canvas
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Copy canvas contents to image
        for item in self.canvas.find_all():
            coords = self.canvas.coords(item)
            if len(coords) >= 4:  # Line segments
                draw.line(coords, fill='black', width=3)
        
        # Save image
        image.save(os.path.join(self.cards_dir, filename))
        
        # Return to home screen
        self.show_home()

if __name__ == "__main__":
    app = FlashcardApp()
    app.mainloop()