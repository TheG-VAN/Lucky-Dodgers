from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.graphics import Rectangle, Color
from random import uniform
from main_menu import MainMenu

# Create an instance of the ScreenManager class. This is used to switch between screens.
manager = ScreenManager()
# The FloatLayout class is a layout that allows you to place widgets inside it with relative or definite coordinates and
# sizes (size_hint and pos_hint are relative, size and pos are definite).
float_layout = FloatLayout()


class GUI(App):
    def build(self):
        with Window.canvas:
            Color(uniform(.8, 1), uniform(.8, 1), uniform(.8, 1))  # Randomly slightly tint the background
            Rectangle(source="Images/menu_bg.png", size=(Window.width, Window.height))  # Create a background
            Color(1, 1, 1)  # Set the canvas colour back to white
        float_layout.add_widget(manager)
        manager.add_widget(MainMenu(name="Main Menu"))
        return float_layout


if __name__ == "__main__":
    GUI().run()
