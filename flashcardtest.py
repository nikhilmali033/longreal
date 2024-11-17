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
                 width: int = None, height: int = None, corner_radius: int = 10,
                 **kwargs):
        super().__init__(parent, **kwargs)
        self.text = text
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        
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
        initial_font_size = int(self.parent.winfo_screenheight() * 0.03)
        self.text_widget = tk.Text(
            self.frame,
            wrap='word',
            font=('Arial', initial_font_size),
            padx=20,
            pady=20
        )
        self.text_widget.pack(fill='both', expand=True)
    
    def get_text(self):
        return self.text_widget.get('1.0', 'end-1c')
    
    def set_text(self, text):
        self.text_widget.delete('1.0', 'end')
        self.text_widget.insert('1.0', text)

class PaginatedList(Component):
    """A component that displays items in pages of 4"""
    def __init__(self, parent, items, **kwargs):
        super().__init__(parent, **kwargs)
        self.items = items
        self.current_page = 0
        self.items_per_page = 4
        self.total_pages = (len(items) + self.items_per_page - 1) // self.items_per_page
        self.card_buttons = []
        self.render()

    def render(self):
        # Create container for cards
        self.cards_frame = ttk.Frame(self.frame)
        self.cards_frame.pack(fill='both', expand=True, pady=20)
        
        # Create navigation frame
        self.nav_frame = ttk.Frame(self.frame)
        self.nav_frame.pack(fill='x', pady=20)
        
        # Calculate button sizes based on screen dimensions
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        
        nav_button_width = int(screen_width * 0.15)
        nav_button_height = int(screen_height * 0.08)
        
        # Create navigation buttons
        self.prev_button = RoundedButton(
            self.nav_frame,
            text="↑ Previous",
            command=self.prev_page,
            width=nav_button_width,
            height=nav_button_height,
            bg_color="#666666"
        )
        
        self.page_label = ttk.Label(
            self.nav_frame,
            text=f"Page {self.current_page + 1} of {self.total_pages}",
            font=('Arial', int(screen_height * 0.03), 'bold')
        )
        
        self.next_button = RoundedButton(
            self.nav_frame,
            text="↓ Next",
            command=self.next_page,
            width=nav_button_width,
            height=nav_button_height,
            bg_color="#666666"
        )
        
        # Pack navigation elements
        self.prev_button.pack(side='left', padx=20)
        self.page_label.pack(side='left', expand=True)
        self.next_button.pack(side='right', padx=20)
        
        self.update_page()

    def update_page(self):
        # Clear existing cards
        for button in self.card_buttons:
            button.frame.destroy()
        self.card_buttons.clear()
        
        # Calculate start and end indices for current page
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.items))
        
        # Calculate button dimensions
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        button_width = int(screen_width * 0.8)
        button_height = int((screen_height * 0.6) / self.items_per_page)
        
        # Create new cards for current page
        for i in range(start_idx, end_idx):
            item = self.items[i]
            btn = RoundedButton(
                self.cards_frame,
                text=f"Item {i+1}",
                command=lambda x=i: print(f"Clicked item {x+1}"),
                width=button_width,
                height=button_height,
                bg_color=f"#{hash(str(i))% 0x1000000:06x}"
            )
            btn.pack(pady=10)
            self.card_buttons.append(btn)
        
        # Update page label
        self.page_label.configure(text=f"Page {self.current_page + 1} of {self.total_pages}")
        
        # Update navigation button states
        if self.current_page == 0:
            self.prev_button.frame.pack_forget()
        else:
            self.prev_button.frame.pack(side='left', padx=20)
            
        if self.current_page >= self.total_pages - 1:
            self.next_button.frame.pack_forget()
        else:
            self.next_button.frame.pack(side='right', padx=20)

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page()

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
            btn.frame.grid(row=row, column=col, padx=30, pady=30)

    def show_text_editor(self):
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
        
        # Create sample items (replace with your actual items)
        items = [f"Card {i+1}" for i in range(20)]
        
        # Create paginated list
        paginated_list = PaginatedList(self.container, items)
        paginated_list.pack(fill='both', expand=True, padx=30)

if __name__ == "__main__":
    root = tk.Tk()
    app = MenuApp(root)
    root.mainloop()