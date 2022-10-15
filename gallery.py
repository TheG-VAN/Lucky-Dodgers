from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.core.window import Window
from os.path import isfile
from shutil import rmtree
from misc import switch, get_characters, ImageButton


class Gallery(Screen):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.changes_made = True  # Used so the gallery only updates if changes have been made (save has occurred)
        character_scroll = ScrollView(pos_hint={"x": .05, "y": .05}, size_hint=(.9, 0.65), bar_color=(1, 1, 1, 1),
                                      bar_inactive_color=(1, 1, 1, .6), bar_width=Window.height/100)
        self.character_picker = GridLayout(size_hint=(None, 1), rows=1)
        self.popup_layout = GridLayout(rows=2, spacing=[0, Window.height/50], padding=[0, Window.height/50])
        Popup(pos_hint={"x": .35, "y": .35}, size_hint=(.3, .3),  # This will pop up when a character is selected
              content=self.popup_layout, title="")
        character_scroll.add_widget(self.character_picker)
        draw = ImageButton(pos_hint={"x": .75, "y": .75}, size_hint=(.2, .1), source="Images/draw.png")
        draw.bind(on_press=lambda button: switch("Creation Station", self.manager, "down"))
        float_layout = FloatLayout()
        self.add_widget(float_layout)
        float_layout.add_widget(draw)
        float_layout.add_widget(character_scroll)

    def on_pre_enter(self):  # Gets called when the screenmanager starts switching to this screen.
        if self.changes_made:
            characters = get_characters()
            self.character_picker.clear_widgets()
            for character in characters:  # Create an ImageButton for each character
                # Only create a button if the character has a saved head.
                if not isfile("Images/" + character + "/rects_colors.pickle"):
                    continue
                char_button = ImageButton(source=characters[character])
                char_button.bind(on_press=self.character_pressed)
                char_button.reload()
                self.character_picker.add_widget(char_button)
            if len(self.character_picker.children) == 0:
                self.character_picker.add_widget(Image(source="Images/no_saved_chars.png"))
                self.character_picker.width = Window.width * .9
            else:
                self.character_picker.width = len(self.character_picker.children) * Window.height * 0.5
            self.changes_made = False

    def character_pressed(self, button):
        character_name = button.source.split("/")[1]
        self.popup_layout.clear_widgets()
        self.popup_layout.add_widget(ImageButton(source="Images/load.png",
                                                 on_press=lambda btn: self.popup_layout.parent.parent.parent.dismiss(),
                                                 on_release=lambda btn: self.manager.get_screen(
                                                     "Creation Station").load_character(character_name)))
        self.popup_layout.add_widget(ImageButton(source="Images/delete.png",
                                                 on_press=lambda btn: self.delete_char(character_name)))
        self.popup_layout.parent.parent.parent.open()  # This opens the popup

    def delete_char(self, character_name):
        self.popup_layout.parent.parent.parent.dismiss()  # This dismisses the popup
        while True:
            try:
                rmtree("Images/" + character_name)
                break
            except OSError:
                pass
        self.changes_made = True
        self.on_pre_enter()  # Reload the gallery
