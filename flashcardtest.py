import tkinter as tk
from tkinter import ttk
import sys
import os

class ScreenManager:
    """Handles screen rotation and dimensions"""
    @staticmethod
    def setup_screen_rotation():
        # Try to rotate screen using xrandr if available
        try:
            # Check if we're on Linux/Pi
            if os.name == 'posix':
                # Get the primary display
                import subprocess
                output = subprocess.check_output(['xrandr', '--current']).decode()
                primary_display = None
                for line in output.split('\n'):
                    if ' connected' in line and 'primary' in line:
                        primary_display = line.split()[0]
                        break
                    elif ' connected' in line:  # fallback if no primary is specified
                        primary_display = line.split()[0]
                        break
                
                if primary_display:
                    # Rotate the display
                    subprocess.run(['xrandr', '--output', primary_display, '--rotate', 'right'])
                    return True
        except Exception as e:
            print(f"Screen rotation failed: {e}")
            return False
        return False

    @staticmethod
    def get_rotated_dimensions(root):
        """Get screen dimensions accounting for rotation"""
        # Get actual screen dimensions
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # For 90-degree rotation, swap width and height
        return screen_height, screen_width

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
        
        # Get rotated screen dimensions
        screen_height, screen_width = ScreenManager.get_rotated_dimensions(parent)
        
        # Default sizes as proportions of rotated screen size
        self.width = width or int(screen_width * 0.15)
        self.height = height or int(screen_height * 0.08)
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
        font_size = int(self.height * 0.3)  # Increased font size proportion
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
        self.canvas.itemconfig(self.shape, fill=self.hover_color)

    def _on_leave(self, event):
        self.canvas.itemconfig(self.shape, fill=self.bg_color)

    def _on_click(self, event):
        self.command()

class TextEditor(Component):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.render()
    
    def render(self):
        screen_height, screen_width = ScreenManager.get_rotated_dimensions(self.parent)
        initial_font_size = int(screen_height * 0.03)  # Increased font size
        
        self.text_widget = tk.Text(
            self.frame,
            wrap='word',
            font=('Arial', initial_font_size),
            padx=20,  # Increased padding
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

class MenuApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Photo Flashcard App")
        
        # Setup screen rotation
        ScreenManager.setup_screen_rotation()
        
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
        screen_height, screen_width = ScreenManager.get_rotated_dimensions(self.root)
        width = int(screen_width * 0.12)
        height = int(screen_height * 0.06)
        
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
        
        screen_height, screen_width = ScreenManager.get_rotated_dimensions(self.root)
        
        # Create a frame for the grid
        grid_frame = ttk.Frame(self.container)
        grid_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Calculate button dimensions based on rotated screen size
        button_width = int(screen_width * 0.35)  # Increased proportion
        button_height = int(screen_height * 0.25)  # Increased proportion
        
        buttons = [
            {
                'text': "Write Notes",
                'command': self.show_text_editor,
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
            btn.frame.grid(row=row, column=col, padx=30, pady=30)  # Increased padding

    def show_text_editor(self):
        self.clear_container()
        self.create_back_button()
        
        screen_height, screen_width = ScreenManager.get_rotated_dimensions(self.root)
        
        # Create title with larger font size
        title = ttk.Label(
            self.container,
            text="Write Notes",
            font=('Arial', int(screen_height * 0.05), 'bold')
        )
        title.pack(pady=30)
        
        # Create editor
        editor = TextEditor(self.container)
        editor.pack(fill='both', expand=True, padx=30, pady=(0, 30))
        
        # Create save button with larger size
        save_btn = RoundedButton(
            self.container,
            text="Save Notes",
            command=lambda: print("Saving:", editor.get_text()[:50] + "..."),
            bg_color="#4CAF50",
            width=int(screen_width * 0.2),
            height=int(screen_height * 0.08)
        )
        save_btn.pack(pady=(0, 30))

    def show_scrollable_list(self):
        self.clear_container()
        self.create_back_button()
        
        screen_height, screen_width = ScreenManager.get_rotated_dimensions(self.root)
        
        # Create title with larger font
        title = ttk.Label(
            self.container,
            text="Scrollable List",
            font=('Arial', int(screen_height * 0.05), 'bold')
        )
        title.pack(pady=30)
        
        # Create canvas with scrollbar
        canvas = tk.Canvas(self.container)
        scrollbar = ttk.Scrollbar(
            self.container,
            orient="vertical",
            command=canvas.yview
        )
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Calculate button dimensions
        button_width = int(screen_width * 0.4)
        button_height = int(screen_height * 0.1)
        
        # Create multiple buttons
        for i in range(20):
            btn = RoundedButton(
                scrollable_frame,
                text=f"Item {i+1}",
                command=lambda x=i: print(f"Clicked item {x+1}"),
                width=button_width,
                height=button_height,
                bg_color=f"#{hash(str(i))% 0x1000000:06x}"
            )
            btn.pack(pady=15, padx=30)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(30, 0))
        scrollbar.pack(side="right", fill="y", padx=(0, 30))

if __name__ == "__main__":
    root = tk.Tk()
    app = MenuApp(root)
    root.mainloop()