from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.graphics import Rectangle
from misc import switch, ImageButton


# Screen for showing available lobbies.
class Join(Screen):
    def __init__(self, name, username, friends, protocol, transport):
        super().__init__()
        self.name = name
        self.username = username
        self.friends = friends
        self.protocol = protocol
        self.protocol.join_screen = self
        self.transport = transport
        back = ImageButton(pos_hint={"x": .01, "top": .99}, size_hint=(0.1, 0.1), source="Images/back.png")
        back.bind(on_press=lambda button: switch("Multiplayer", self.manager, "right"))
        self.refresh_button = ImageButton(pos_hint={"x": .8, "y": .9}, size_hint=(0.1, 0.1),
                                          source="Images/refresh.png")
        self.refresh_button.bind(on_press=lambda button: self.refresh())
        scroll = ScrollView(size_hint=(.8, None), pos_hint={"x": .1, "y": .1}, size=(Window.width*.8, Window.height*.8))
        self.canvas.add(Rectangle(pos=(Window.width*.1, Window.height*.1), size=(Window.width*.8, Window.height*.8)))
        self.grid_layout = GridLayout(cols=3, size_hint_y=None, row_default_height=Window.height*.1,
                                      spacing=[Window.width*.001, Window.height*.01], padding=Window.height*.01)
        self.grid_layout.bind(minimum_height=self.grid_layout.setter('height'))
        scroll.add_widget(self.grid_layout)
        float_layout = FloatLayout()
        self.add_widget(float_layout)
        float_layout.add_widget(back)
        float_layout.add_widget(self.refresh_button)
        float_layout.add_widget(scroll)

    # Called when the screen is entered.
    def on_pre_enter(self):
        self.transport.write("leave\n".encode("utf-8"))  # In case the user is still considered to be in a lobby.
        self.transport.write("list_lobbies\n".encode("utf-8"))

    def show_lobbies(self, message):
        self.refresh_button.color = (1, 1, 1, 1)
        self.grid_layout.clear_widgets()
        if message == "":
            self.grid_layout.add_widget(Button(background_normal='', background_down='', background_color=(0, 0, 0, .2),
                                               font_name="pixel_font.otf", color=(0, 0, 0, 1),
                                               font_size=Window.height * 0.025, text="There are no available lobbies"))
            return
        lobbies = message.split(";;")
        hosts = []
        for i in range(len(lobbies)):
            lobbies[i] = lobbies[i].split(";")
            if lobbies[i][0] in hosts or lobbies[i][0] == self.username:  # If the user is host of the lobby, ignore it.
                del lobbies[i]
            elif lobbies[i][0] in self.friends:  # If a friend is host, move it to the start of the list.
                lobbies.insert(0, lobbies.pop(i))
            hosts.append(lobbies[i][0])
        for lobby in lobbies[:100]:  # Get the first 100 lobbies.
            if int(lobby[1]) < 6:  # If the lobby is not full.
                self.grid_layout.add_widget(Button(background_normal='', background_down='', color=(0, 0, 0, 1),
                                                   background_color=(0, 0, 0, .2), font_name="pixel_font.otf",
                                                   font_size=Window.height * 0.025, text=lobby[0] + "'s game"))
                self.grid_layout.add_widget(Button(background_normal='', background_down='', color=(0, 0, 0, 1),
                                                   background_color=(0, 0, 0, .2), font_name="pixel_font.otf",
                                                   font_size=Window.height * 0.025, text=lobby[1] + "/6 players"))
                self.grid_layout.add_widget(Button(font_name="pixel_font.otf", color=(1, 1, 1, 1),
                                                   font_size=Window.height * 0.025, text="Join",
                                                   on_press=lambda button: self.transport.write(
                                                       ("request;" + lobby[0] + "\n").encode("utf-8"))))

    def refresh(self):
        self.refresh_button.color = (.5, .5, .5, 1)
        self.transport.write("list_lobbies\n".encode("utf-8"))
