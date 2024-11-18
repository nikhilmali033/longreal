from gpiozero import Button
from time import sleep

# Create a button object connected to GPIO16
button = Button(16, pull_up=True)

try:
    print("Press the button (Press Ctrl+C to exit)")
    while True:
        if button.is_pressed:
            print("Button pressed!")
            sleep(0.2)  # Simple debouncing
            
except KeyboardInterrupt:
    print("\nProgram stopped by user")