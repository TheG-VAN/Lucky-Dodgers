from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen
from character_selection import CharacterSelection
from misc import Menu, ImageButton, switch
from multiplayer import Multiplayer


class Play(Screen):
    def __init__(self, name):
        super().__init__()
        self.name = name
        float_layout = FloatLayout()
        menu = Menu("up")
        single_player = ImageButton(pos_hint={"x": .2, "y": .35}, size_hint=(.15, .3),
                                    source="Images/creation_station.png")
        single_player.bind(on_press=lambda button: switch("Character Selection", self.manager, "down",
                                                          screen_type=CharacterSelection))
        multiplayer = ImageButton(pos_hint={"x": .5, "y": .35}, size_hint=(.3, .3), source="Images/multiplayer.png")
        multiplayer.bind(on_press=lambda button: switch("Multiplayer", self.manager, "left", screen_type=Multiplayer))
        self.add_widget(float_layout)
        float_layout.add_widget(menu)
        float_layout.add_widget(single_player)
        float_layout.add_widget(multiplayer)
