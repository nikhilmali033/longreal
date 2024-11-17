import tkinter as tk
from typing import Dict, List, Type, Optional
from abc import ABC, abstractmethod
from enum import Enum, auto
from dataclasses import dataclass

class LayoutType(Enum):
    """Available layout types"""
    SCROLL = auto()
    FOUR_BUTTON = auto()
    GRID = auto()

class MenuComponent(ABC):
    """Abstract base class for menu components"""
    @abstractmethod
    def create_widget(self, parent: tk.Frame) -> tk.Widget:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

class Button(MenuComponent):
    """Basic button component"""
    def __init__(self, name: str, command):
        self._name = name
        self.command = command

    def create_widget(self, parent: tk.Frame) -> tk.Button:
        return tk.Button(parent, text=self.get_name(), command=self.command)

    def get_name(self) -> str:
        return self._name

class SystemButton(MenuComponent):
    """System-level buttons (screenshot, quit, etc.)"""
    def __init__(self, name: str, command):
        self._name = name
        self.command = command

    def create_widget(self, parent: tk.Frame) -> tk.Button:
        return tk.Button(parent, text=self.get_name(), command=self.command)

    def get_name(self) -> str:
        return self._name

class Layout(ABC):
    """Abstract base class for layouts"""
    @abstractmethod
    def validate_components(self, components: List[MenuComponent]) -> bool:
        pass

    @abstractmethod
    def render(self, parent: tk.Frame, components: List[MenuComponent]):
        pass

class ScrollLayout(Layout):
    """Vertical scrolling layout for variable number of buttons"""
    def validate_components(self, components: List[MenuComponent]) -> bool:
        return len(components) > 0

    def render(self, parent: tk.Frame, components: List[MenuComponent]):
        canvas = tk.Canvas(parent)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        content_frame = tk.Frame(canvas)

        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Create window inside canvas
        canvas.create_window((0, 0), window=content_frame, anchor="nw")

        # Add components
        for component in components:
            component.create_widget(content_frame).pack(fill="x", padx=5, pady=5)

        # Update scroll region
        content_frame.bind("<Configure>", 
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

class FourButtonLayout(Layout):
    """Exactly four buttons in a grid"""
    def validate_components(self, components: List[MenuComponent]) -> bool:
        return len(components) == 4

    def render(self, parent: tk.Frame, components: List[MenuComponent]):
        grid_frame = tk.Frame(parent)
        grid_frame.pack(expand=True)

        for i, component in enumerate(components):
            row = i // 2
            col = i % 2
            btn = component.create_widget(grid_frame)
            btn.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

@dataclass
class MenuItem:
    """Represents a menu item with its layout and components"""
    name: str
    layout: Layout
    components: List[MenuComponent]
    
    def validate(self) -> bool:
        return self.layout.validate_components(self.components)

class MenuSystem(tk.Tk):
    """Main menu system class"""
    def __init__(self):
        super().__init__()
        
        # Initialize menu items dictionary
        self.menu_items: Dict[str, MenuItem] = {}
        self.current_path = "/"
        
        # Configure window
        self.title("Menu System")
        self.attributes('-fullscreen', True)
        
        # Create main container
        self.container = tk.Frame(self)
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Create system buttons frame
        self.system_frame = tk.Frame(self)
        self.system_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Add system buttons
        self.add_system_button("Back", self.go_back)
        self.add_system_button("Home", lambda: self.navigate_to("/"))
        self.add_system_button("Screenshot", lambda: print("Screenshot taken!"))
        self.add_system_button("Quit", self.quit)

    def add_system_button(self, name: str, command) -> None:
        """Add a system-level button"""
        SystemButton(name, command).create_widget(self.system_frame).pack(side=tk.LEFT, padx=5)

    def add_menu_item(self, path: str, layout: Layout, components: List[MenuComponent]) -> None:
        """Add a menu item with specified layout and components"""
        menu_item = MenuItem(path.split("/")[-1], layout, components)
        if not menu_item.validate():
            raise ValueError(f"Invalid components for layout at path: {path}")
        self.menu_items[path] = menu_item

    def navigate_to(self, path: str) -> None:
        """Navigate to a specific path"""
        if path in self.menu_items or path == "/":
            self.current_path = path
            self.refresh_display()

    def go_back(self) -> None:
        """Navigate to parent menu"""
        parent_path = "/".join(self.current_path.split("/")[:-1])
        if not parent_path:
            parent_path = "/"
        self.navigate_to(parent_path)

    def refresh_display(self) -> None:
        """Refresh the display with current menu items"""
        # Clear existing content
        for widget in self.container.winfo_children():
            widget.destroy()

        if self.current_path == "/":
            # Root menu - show all top-level items
            scroll = ScrollLayout()
            root_components = [
                Button(self.menu_items[path].name, 
                      lambda p=path: self.navigate_to(p))
                for path in self.menu_items.keys()
                if "/" not in path[1:] # Only top-level items
            ]
            scroll.render(self.container, root_components)
        else:
            # Show current menu item's layout
            current_item = self.menu_items[self.current_path]
            current_item.layout.render(self.container, current_item.components)

# Example usage
if __name__ == "__main__":
    menu = MenuSystem()

    # Create some example buttons
    settings_buttons = [
        Button("Display", lambda: print("Display settings")),
        Button("Audio", lambda: print("Audio settings")),
        Button("Network", lambda: print("Network settings")),
        Button("Storage", lambda: print("Storage settings")),
    ]

    games_buttons = [
        Button("Action", lambda: print("Action games")),
        Button("Strategy", lambda: print("Strategy games")),
        Button("RPG", lambda: print("RPG games")),
        Button("Simulation", lambda: print("Simulation games")),
    ]

    # Add menu items with different layouts
    menu.add_menu_item("/settings", FourButtonLayout(), settings_buttons)
    menu.add_menu_item("/games", FourButtonLayout(), games_buttons)

    # Add a scrolling menu
    scroll_buttons = [Button(f"Item {i}", lambda i=i: print(f"Item {i} clicked"))
                     for i in range(10)]
    menu.add_menu_item("/scroll-demo", ScrollLayout(), scroll_buttons)

    # Start the application
    menu.mainloop()