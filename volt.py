import RPi.GPIO as GPIO
import time

# Set up GPIO mode
GPIO.setmode(GPIO.BCM)  # Use BCM numbering

# Define the GPIO pin for the button
BUTTON_PIN = 16  # GPIO16 (physical pin 36)

# Set up the button pin with internal pull-up resistor
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
    print("Press the button (Press Ctrl+C to exit)")
    while True:
        # Read button state
        button_state = GPIO.input(BUTTON_PIN)
        
        # Button is pressed when state is LOW (0) because of pull-up resistor
        if button_state == GPIO.LOW:
            print("Button pressed!")
            time.sleep(0.2)  # Simple debouncing
            
except KeyboardInterrupt:
    print("\nProgram stopped by user")
finally:
    GPIO.cleanup()  # Clean up GPIO on program exit