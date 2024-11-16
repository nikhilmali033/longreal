import tkinter as tk
from typing import Dict, Optional, Callable
from abc import ABC, abstractmethod

class MenuComponent(ABC):
    """Abstract base class for menu components"""
    @abstractmethod
    def create_widget(self, parent: tk.Frame) -> tk.Widget:
        pass

class NavigationButton(MenuComponent):
    """Component for navigation buttons"""
    def __init__(self, text: str, command: Callable):
        self.text = text
        self.command = command

    def create_widget(self, parent: tk.Frame) -> tk.Button:
        return tk.Button(parent, text=self.text, command=self.command)

class ScreenshotButton(MenuComponent):
    """Component for screenshot functionality (placeholder)"""
    def create_widget(self, parent: tk.Frame) -> tk.Button:
        return tk.Button(parent, text="Screenshot", command=lambda: print("Screenshot taken!"))

class MenuItem:
    """Represents a menu item with its submenu structure"""
    def __init__(self, name: str):
        self.name = name
        self.children: Dict[str, MenuItem] = {}

class MenuSystem(tk.Tk):
    """Main menu system class"""
    def __init__(self):
        super().__init__()
        
        # Initialize menu structure
        self.menu_structure = MenuItem("Root")
        self.current_menu = self.menu_structure
        self.navigation_history = []
        
        # Configure window
        self.title("Menu System")
        self.attributes('-fullscreen', True)
        
        # Create main container
        self.container = tk.Frame(self)
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Initialize components list
        self.components: list[MenuComponent] = []
        
        # Add quit button by default
        self.add_component(NavigationButton("Quit", self.quit))

    def add_menu_item(self, path: str) -> None:
        """Add a menu item at the specified path"""
        current = self.menu_structure
        parts = path.split('/')
        
        for part in parts:
            if part not in current.children:
                current.children[part] = MenuItem(part)
            current = current.children[part]

    def add_component(self, component: MenuComponent) -> None:
        """Add a new component to the menu system"""
        self.components.append(component)
        self.refresh_display()

    def navigate_to(self, menu_item: MenuItem) -> None:
        """Navigate to a specific menu item"""
        self.navigation_history.append(self.current_menu)
        self.current_menu = menu_item
        self.refresh_display()

    def go_back(self) -> None:
        """Navigate to the previous menu"""
        if self.navigation_history:
            self.current_menu = self.navigation_history.pop()
            self.refresh_display()

    def refresh_display(self) -> None:
        """Refresh the display with current menu items"""
        # Clear existing widgets
        for widget in self.container.winfo_children():
            widget.destroy()

        # Create buttons frame
        buttons_frame = tk.Frame(self.container)
        buttons_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        # Add navigation buttons for current menu items
        for name, item in self.current_menu.children.items():
            NavigationButton(
                name,
                lambda i=item: self.navigate_to(i)
            ).create_widget(self.container).pack(pady=5)

        # Add back button if we're not at root
        if self.navigation_history:
            NavigationButton("Back", self.go_back).create_widget(buttons_frame).pack(side=tk.LEFT, padx=5)

        # Add all registered components
        for component in self.components:
            component.create_widget(buttons_frame).pack(side=tk.LEFT, padx=5)

# Example usage
if __name__ == "__main__":
    # Create menu system
    menu = MenuSystem()

    # Add menu structure
    menu.add_menu_item("Settings")
    menu.add_menu_item("Settings/Display")
    menu.add_menu_item("Settings/Audio")
    menu.add_menu_item("Games")
    menu.add_menu_item("Games/Action")
    menu.add_menu_item("Games/Strategy")

    # Add screenshot button component
    menu.add_component(ScreenshotButton())

    # Start the application
    menu.mainloop()