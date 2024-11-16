# Python program to Build an App for the Screen Rotation   
# Using Tkinter in Python  
  
# Importing the reqd. packages  
from tkinter import *  
import rotatescreen as rotatescr
   
# Defining of a new function in order to be used to   
# rotate the screen  
def Scr_rotation(flag):  
    # Getting the default display of the screen  
    scr = rotatescr.get_primary_display()  
    # Rotating the screen upwards to attain landscape view  
    if flag == "up" :  
        scr.set_landscape()  
    # Rotating the screen rightwards to attain flipped portrait view  
    elif flag == "right" :  
        scr.set_portrait_flipped()  
    # Rotating the screen downwards to attain flipped landscape view  
    elif flag == "down" :  
        scr.set_landscape_flipped()  
    # Rotating the screen leftwards to attain portrait view  
    elif flag == "left" :  
        scr.set_portrait()  
   
   
# Creating a new instance of the tkinter object  
base = Tk()  
# Setting the dimensions of the screen  
base.geometry("100x100")  
# Giving the title for the screen  
base.title("Screen Rotation")  
   
# Var classes of the tkinter  
final = StringVar()  
   
# Creating buttons in order to change the view  
Button(base, text = "Up" , command = lambda: Scr_rotation(  
    "up"), bg = "white").grid(row = 0 , column = 3)  
  
Button(base , text = "Right" , command = lambda: Scr_rotation(  
    "right"), bg = "white").grid(row = 1 , column = 6)  
  
Button(base , text = "Left" , command = lambda: Scr_rotation(  
    "left") , bg = "white").grid(row = 1 , column = 2)  
  
Button(base , text = "Down" , command = lambda: Scr_rotation(  
    "down") , bg = "white").grid(row = 3 , column = 3)  
   
# Calling the main loop to execute the program   
mainloop() 