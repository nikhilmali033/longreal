import tkinter as tk
from tkinter import ttk
import sys

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
                 width: int = 200, height: int = 60, corner_radius: int = 10,
                 **kwargs):
        super().__init__(parent, **kwargs)
        self.text = text
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.width = width
        self.height = height
        self.corner_radius = corner_radius
        self.render()
    
    def render(self):
        # Create canvas with transparent background
        self.canvas = tk.Canvas(
            self.frame,
            width=self.width,
            height=self.height,
            highlightthickness=0,
            bg=self.frame.winfo_toplevel().cget('bg')  # Get root window background
        )
        self.canvas.pack()

        # Create rounded rectangle
        self.shape = self.create_rounded_rectangle(
            2, 2, self.width-2, self.height-2,
            self.corner_radius
        )
        self.canvas.itemconfig(self.shape, fill=self.bg_color, outline=self.bg_color)
        
        # Create text
        self.canvas_text = self.canvas.create_text(
            self.width/2,
            self.height/2,
            text=self.text,
            fill=self.text_color,
            font=('Arial', 12, 'bold')
        )

        # Bind events
        self.canvas.bind('<Enter>', self._on_enter)
        self.canvas.bind('<Leave>', self._on_leave)
        self.canvas.bind('<Button-1>', self._on_click)

    def create_rounded_rectangle(self, x1, y1, x2, y2, radius):
        """Create a rounded rectangle"""
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
    """A simple text editor component"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.render()
    
    def render(self):
        # Create text widget with scrollbar
        self.text_widget = tk.Text(
            self.frame,
            wrap='word',
            font=('Arial', 12),
            padx=10,
            pady=10
        )
        scrollbar = ttk.Scrollbar(
            self.frame,
            orient='vertical',
            command=self.text_widget.yview
        )
        self.text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
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
        self.root.attributes('-fullscreen', True)
        
        # Set default background color for the root window
        self.root.configure(bg='#f0f0f0')
        
        # Create main container
        self.container = ttk.Frame(root)
        self.container.pack(fill='both', expand=True)
        
        self.show_main_menu()
    
    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()
    
    def create_back_button(self):
        back_btn = RoundedButton(
            self.container,
            text="← Back",
            command=self.show_main_menu,
            width=100,
            height=40,
            bg_color="#666666"
        )
        back_btn.pack(anchor='nw', padx=10, pady=10)

    def show_main_menu(self):
        self.clear_container()
        
        # Create a 2x2 grid for the buttons
        grid_frame = ttk.Frame(self.container)
        grid_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Define button properties
        buttons = [
            {
                'text': "Write Notes",
                'command': self.show_text_editor,
                'color': "#4CAF50"  # Green
            },
            {
                'text': "View List",
                'command': self.show_scrollable_list,
                'color': "#2196F3"  # Blue
            },
            {
                'text': "Settings",
                'command': lambda: print("Settings clicked"),
                'color': "#9C27B0"  # Purple
            },
            {
                'text': "Quit",
                'command': lambda: sys.exit(),
                'color': "#f44336"  # Red
            }
        ]
        
        # Create buttons in grid
        for i, btn_props in enumerate(buttons):
            row = i // 2
            col = i % 2
            btn = RoundedButton(
                grid_frame,
                text=btn_props['text'],
                command=btn_props['command'],
                bg_color=btn_props['color'],
                width=200,
                height=150
            )
            btn.frame.grid(row=row, column=col, padx=20, pady=20)

    def show_text_editor(self):
        self.clear_container()
        self.create_back_button()
        
        # Create title
        title = ttk.Label(
            self.container,
            text="Write Notes",
            font=('Arial', 24)
        )
        title.pack(pady=20)
        
        # Create editor
        editor = TextEditor(self.container)
        editor.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Create save button
        save_btn = RoundedButton(
            self.container,
            text="Save Notes",
            command=lambda: print("Saving:", editor.get_text()[:50] + "..."),
            bg_color="#4CAF50",
            width=150,
            height=50
        )
        save_btn.pack(pady=(0, 20))

    def show_scrollable_list(self):
        self.clear_container()
        self.create_back_button()
        
        # Create title
        title = ttk.Label(
            self.container,
            text="Scrollable List",
            font=('Arial', 24)
        )
        title.pack(pady=20)
        
        # Create canvas with scrollbar for scrolling
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
        
        # Create multiple buttons
        for i in range(20):
            btn = RoundedButton(
                scrollable_frame,
                text=f"Item {i+1}",
                command=lambda x=i: print(f"Clicked item {x+1}"),
                width=300,
                height=60,
                bg_color=f"#{hash(str(i))% 0x1000000:06x}"  # Random color
            )
            btn.pack(pady=10, padx=20)
        
        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

if __name__ == "__main__":
    root = tk.Tk()
    app = MenuApp(root)
    root.mainloop()