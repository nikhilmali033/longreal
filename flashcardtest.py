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
    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.kwargs = kwargs
        self.widgets = {}
    
    def render(self):
        pass
    
    def pack(self, **pack_options):
        self.frame.pack(**pack_options)
    
    def grid(self, **grid_options):
        self.frame.grid(**grid_options)
    
    def place(self, **place_options):
        self.frame.place(**place_options)



class CameraPreview(Component):
    """Component for camera preview and capture functionality"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.preview_active = False
        self.frame_queue = queue.Queue(maxsize=1)
        self.output_dir = "captured_images"
        
        # Ensure output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        self.render()
        
    def render(self):
        # Calculate preview dimensions based on screen size
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
            bg_color="#4CAF50",
            width=int(screen_width * 0.2),
            height=int(screen_height * 0.08)
        )
        self.capture_btn.pack(pady=20)
        
        # Start preview
        self.start_preview()
    
    def start_preview(self):
        """Start the camera preview"""
        self.preview_active = True
        
        # Start preview process
        self.preview_process = subprocess.Popen([
            "libcamera-vid",
            "--width", "2304",
            "--height", "1296",
            "--codec", "mjpeg",
            "--inline",  # Output MJPEG stream
            "--output", "-"  # Output to stdout
        ], stdout=subprocess.PIPE)
        
        # Start thread to read frames
        self.preview_thread = threading.Thread(target=self._read_preview_frames)
        self.preview_thread.daemon = True
        self.preview_thread.start()
        
        # Start updating preview
        self._update_preview()
    
    def _read_preview_frames(self):
        """Thread function to read frames from libcamera-vid"""
        cap = cv2.VideoCapture()
        cap.open(f"pipe:{self.preview_process.stdout.fileno()}")
        
        while self.preview_active:
            ret, frame = cap.read()
            if ret:
                # Resize frame to fit preview
                frame = cv2.resize(frame, (self.preview_width, self.preview_height))
                # Convert from BGR to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Convert to PhotoImage
                image = Image.fromarray(frame)
                photo = ImageTk.PhotoImage(image)
                
                # Update queue with newest frame
                try:
                    self.frame_queue.get_nowait()  # Remove old frame if exists
                except queue.Empty:
                    pass
                self.frame_queue.put(photo)
    
    def _update_preview(self):
        """Update the preview canvas with the latest frame"""
        try:
            # Get the latest frame
            photo = self.frame_queue.get_nowait()
            # Update canvas
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(
                self.preview_width/2,
                self.preview_height/2,
                image=photo,
                anchor='center'
            )
            # Keep a reference to avoid garbage collection
            self.preview_canvas.photo = photo
        except queue.Empty:
            pass
        
        # Schedule next update
        if self.preview_active:
            self.frame.after(30, self._update_preview)  # Update every ~30ms (approx. 30 fps)
    
    def capture_image(self):
        """Capture and save an image"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/image_{timestamp}.jpg"
        
        try:
            # Temporarily disable preview
            self.preview_active = False
            if hasattr(self, 'preview_process'):
                self.preview_process.terminate()
                self.preview_process.wait()
            
            # Capture image
            cmd = [
                "libcamera-jpeg",
                "-o", filename,
                "--width", "2304",
                "--height", "1296"
            ]
            subprocess.run(cmd, check=True)
            print(f"Image captured successfully: {filename}")
            
            # Restart preview
            self.start_preview()
            
            return filename
        except subprocess.CalledProcessError as e:
            print(f"Error capturing image: {e}")
            # Restart preview on error
            self.start_preview()
            return None
    
    def destroy(self):
        """Clean up resources when component is destroyed"""
        self.preview_active = False
        if hasattr(self, 'preview_process'):
            self.preview_process.terminate()
            self.preview_process.wait()
        super().destroy()
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
        self.disabled_color = "#cccccc"  # Color for disabled state
        self.enabled = True  # Track enabled state
        
        # Default sizes as proportions of screen size
        self.width = width or int(parent.winfo_screenwidth() * 0.15)
        self.height = height or int(parent.winfo_screenheight() * 0.08)
        self.corner_radius = corner_radius
        self.render()

    def render(self):
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
        self.shape = self.create_rounded_rectangle(
            2, 2, self.width-2, self.height-2,
            self.corner_radius
        )
        self.canvas.itemconfig(self.shape, fill=self.bg_color, outline=self.bg_color)
        
        # Create text with responsive font size
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

    def set_enabled(self, enabled: bool):
        """Enable or disable the button"""
        self.enabled = enabled
        if enabled:
            self.canvas.itemconfig(self.shape, fill=self.bg_color)
        else:
            self.canvas.itemconfig(self.shape, fill=self.disabled_color)

    def create_rounded_rectangle(self, x1, y1, x2, y2, radius):
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
class TextEditor(Component):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.render()
    
    def render(self):
        initial_font_size = int(self.parent.winfo_screenheight() * 0.03)
        
        self.text_widget = tk.Text(
            self.frame,
            wrap='word',
            font=('Arial', initial_font_size),
            padx=20,
            pady=20
        )
        scrollbar = ttk.Scrollbar(
            self.frame,
            orient='vertical',
            command=self.text_widget.yview
        )
        self.text_widget.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side='right', fill='y')
        self.text_widget.pack(side='left', fill='both', expand=True)
    
    def get_text(self):
        return self.text_widget.get('1.0', 'end-1c')
    
    def set_text(self, text):
        self.text_widget.delete('1.0', 'end')
        self.text_widget.insert('1.0', text)
class CardList(Component):
    """Component to display 4 cards at a time with navigation buttons"""
    def __init__(self, parent, items, **kwargs):
        super().__init__(parent, **kwargs)
        self.items = items
        self.current_page = 0
        self.cards_per_page = 4
        self.total_pages = (len(items) + self.cards_per_page - 1) // self.cards_per_page
        self.render()

    def render(self):
        # Create container for navigation buttons
        nav_frame = ttk.Frame(self.frame)
        nav_frame.pack(side='right', fill='y', padx=20)

        # Calculate button sizes based on screen dimensions
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        nav_button_width = int(screen_width * 0.08)
        nav_button_height = int(screen_height * 0.15)

        # Create up button
        self.up_button = RoundedButton(
            nav_frame,
            text="▲",
            command=self.previous_page,
            width=nav_button_width,
            height=nav_button_height,
            bg_color="#666666"
        )
        self.up_button.pack(pady=(0, 10))

        # Create page indicator
        self.page_indicator = ttk.Label(
            nav_frame,
            text=f"1/{self.total_pages}",
            font=('Arial', int(screen_height * 0.03), 'bold')
        )
        self.page_indicator.pack(pady=10)

        # Create down button
        self.down_button = RoundedButton(
            nav_frame,
            text="▼",
            command=self.next_page,
            width=nav_button_width,
            height=nav_button_height,
            bg_color="#666666"
        )
        self.down_button.pack(pady=(10, 0))

        # Create frame for cards
        self.cards_frame = ttk.Frame(self.frame)
        self.cards_frame.pack(side='left', fill='both', expand=True)

        # Show initial page
        self.show_current_page()

    def show_current_page(self):
        # Clear current cards
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        # Calculate button dimensions
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        button_width = int(screen_width * 0.4)
        button_height = int(screen_height * 0.18)

        # Get current page items
        start_idx = self.current_page * self.cards_per_page
        end_idx = start_idx + self.cards_per_page
        current_items = self.items[start_idx:end_idx]

        # Create buttons for current page
        for i, item in enumerate(current_items):
            btn = RoundedButton(
                self.cards_frame,
                text=f"Item {start_idx + i + 1}",
                command=lambda x=start_idx+i: print(f"Clicked item {x+1}"),
                width=button_width,
                height=button_height,
                bg_color=f"#{hash(str(start_idx+i))% 0x1000000:06x}"
            )
            btn.pack(pady=10, padx=30)

        # Update page indicator
        self.page_indicator.configure(text=f"{self.current_page + 1}/{self.total_pages}")

        # Update navigation button states
        self.up_button.set_enabled(self.current_page > 0)
        self.down_button.set_enabled(self.current_page < self.total_pages - 1)

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.show_current_page()

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.show_current_page()
class MenuApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Photo Flashcard App")
        
        # Make fullscreen
        self.root.attributes('-fullscreen', True)
        
        # Set default background color
        self.root.configure(bg='#f0f0f0')
        
        # Create main container
        self.container = ttk.Frame(root)
        self.container.pack(fill='both', expand=True)
        
        # Bind escape key to exit fullscreen
        self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))
        # Bind F11 to toggle fullscreen
        self.root.bind('<F11>', lambda e: self.root.attributes('-fullscreen', not self.root.attributes('-fullscreen')))
        
        self.show_main_menu()

    def clear_container(self):
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
        
        # Create a frame for the grid
        grid_frame = ttk.Frame(self.container)
        grid_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Calculate button dimensions
        button_width = int(self.root.winfo_screenwidth() * 0.35)
        button_height = int(self.root.winfo_screenheight() * 0.25)
        
        buttons = [
            {
                'text': "Take Picture",  # Changed from "Write Notes"
                'command': self.show_camera_preview,  # Changed command
                'color': "#4CAF50"
            },
            {
                'text': "View List",
                'command': self.show_scrollable_list,
                'color': "#2196F3"
            },
            {
                'text': "Settings",
                'command': lambda: print("Settings clicked"),
                'color': "#9C27B0"
            },
            {
                'text': "Quit",
                'command': lambda: sys.exit(),
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
        
        # Create title
        title = ttk.Label(
            self.container,
            text="Take Picture",
            font=('Arial', int(self.root.winfo_screenheight() * 0.05), 'bold')
        )
        title.pack(pady=30)
        
        # Create camera preview
        camera = CameraPreview(self.container)
        camera.pack(fill='both', expand=True, padx=30, pady=(0, 30))
        self.clear_container()
        self.create_back_button()
        
        # Create title
        title = ttk.Label(
            self.container,
            text="Write Notes",
            font=('Arial', int(self.root.winfo_screenheight() * 0.05), 'bold')
        )
        title.pack(pady=30)
        
        # Create editor
        editor = TextEditor(self.container)
        editor.pack(fill='both', expand=True, padx=30, pady=(0, 30))
        
        # Create save button
        save_btn = RoundedButton(
            self.container,
            text="Save Notes",
            command=lambda: print("Saving:", editor.get_text()[:50] + "..."),
            bg_color="#4CAF50",
            width=int(self.root.winfo_screenwidth() * 0.2),
            height=int(self.root.winfo_screenheight() * 0.08)
        )
        save_btn.pack(pady=(0, 30))

    def show_scrollable_list(self):
        self.clear_container()
        self.create_back_button()
        
        # Create title
        title = ttk.Label(
            self.container,
            text="Flashcards",
            font=('Arial', int(self.root.winfo_screenheight() * 0.05), 'bold')
        )
        title.pack(pady=30)
        
        # Create list of items (replace with your actual data)
        items = [f"Card {i+1}" for i in range(20)]
        
        # Create card list with navigation
        card_list = CardList(self.container, items)
        card_list.pack(fill='both', expand=True, padx=30, pady=(0, 30))

if __name__ == "__main__":
    root = tk.Tk()
    app = MenuApp(root)
    root.mainloop()