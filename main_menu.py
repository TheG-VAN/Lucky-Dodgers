from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from misc import switch, ImageButton
from controls_changer import ControlsChanger
from creation_station import CreationStation
from play import Play
from kivy.utils import platform


class MainMenu(Screen):
    def __init__(self, name):
        super().__init__()  # Initialises the screen (parent class)
        self.name = name  # self.name is used by manager to differentiate between screens.
        float_layout = FloatLayout()  # Float layout is where buttons and other widgets are placed.
        # Create the title
        title = Image(pos_hint={"x": 0.1, "y": 0.65}, size_hint=(0.8, 0.3), source="Images/title.png")
        # Create a button called play. pos_hint determines the position of the button relative to the size of the
        # window. size_hint is the same but for size. source is the location of the image file of the button.
        play = ImageButton(pos_hint={"x": 0.35, "y": 0.25}, size_hint=(0.3, 0.3), source="Images/play.png")
        options = ImageButton(pos_hint={"x": 0.75, "y": 0.3}, size_hint=(0.1, 0.2), source="Images/options.png")
        creation_station = ImageButton(pos_hint={"x": 0.15, "y": 0.3}, size_hint=(0.1, 0.2),
                                       source="Images/creation_station.png")
        # When the play button is pressed, it calls the function "switch".
        play.bind(on_press=lambda button: switch("Play", self.manager, "down", screen_type=Play))
        options.bind(on_press=lambda button: switch("Controls Changer", self.manager, "left",
                                                    screen_type=ControlsChanger))
        creation_station.bind(on_press=lambda button: switch("Creation Station", self.manager,
                                                             "right", screen_type=CreationStation))
        self.add_widget(float_layout)  # Adding the float layout to the screen.
        float_layout.add_widget(title)
        float_layout.add_widget(play)
        float_layout.add_widget(options)
        float_layout.add_widget(creation_station)
        if platform == "android":
            start_button = ImageButton()
            start_button.bind(on_press=self.remove_widget)
            self.add_widget(start_button)
