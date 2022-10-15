from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
import os


# Class that combines the image widget with a button
class ImageButton(ButtonBehavior, Image):
    pass


class Menu(ImageButton):  # This is a button that returns to the main menu
    def __init__(self, direction):
        super().__init__()
        self.pos_hint = {"x": .01, "top": .99}
        self.size_hint = (0.05, 0.1)
        self.source = "Images/home.png"
        self.on_press = lambda: switch("Main Menu", self.parent.parent.manager, direction)


# Function for switching between screens. If the screen hasn't been created yet, create it.
def switch(screen, manager, direction, screen_type=None):
    if not manager.has_screen(screen):
        manager.add_widget(screen_type(name=screen))
    manager.transition.direction = direction
    manager.current = screen


def get_characters():  # Function that finds all the saved characters and creates a dictionary with preview images.
    characters = {}
    character_folders = next(os.walk("Images"))[1]  # Finds all the subdirectories in Images
    for character in character_folders:
        characters[character] = "Images/" + character + "/preview.png"
    return characters


def set_color(widget, color):
    widget.color = color
