from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.widget import WidgetException
from kivy.core.window import Window
from misc import switch, ImageButton
from character_selection import CharacterSelection


# Screen for showing the lobby the user is in.
class Lobby(Screen):
    def __init__(self, name, username, protocol, transport):
        super().__init__()
        self.name = name
        self.username = username
        self.protocol = protocol
        self.protocol.lobby_screen = self
        self.transport = transport
        leave_button = Button(background_normal='', background_color=(1, 1, 1, 1), text="Leave?",
                              font_name="pixel_font.otf", color=(0, 0, 0, 1), font_size=Window.height * 0.1)
        leave_button.bind(on_press=lambda button: self.leave(leave_popup))
        leave_popup = Popup(pos_hint={"x": .3, "y": .35}, size_hint=(.4, .3),
                            content=leave_button, title="")
        start_button = Button(background_normal='', background_color=(1, 1, 1, 1), text="Start?",
                              font_name="pixel_font.otf", color=(0, 0, 0, 1), font_size=Window.height * 0.1)
        start_button.bind(on_press=lambda button: self.start(button, start_popup))
        start_popup = Popup(pos_hint={"x": .3, "y": .35}, size_hint=(.4, .3),
                            content=start_button, title="")
        back = ImageButton(pos_hint={"x": .01, "top": .99}, size_hint=(0.1, 0.1), source="Images/back.png")
        back.bind(on_press=lambda button: leave_popup.open())
        self.start_button = Button(size_hint=(.3, .1), pos_hint={"x": .6, "y": .1}, background_normal='',
                                   background_color=(.3, .4, .3, .7), text="Start", font_name="pixel_font.otf",
                                   color=(0, 0, 0, 1), font_size=Window.height * 0.05, background_down="")
        self.start_button.bind(on_press=lambda button: start_popup.open() if self.start_button.background_color ==
                               [.5, 1, .5, .7] else None)
        team_1_btn = Button(size_hint=(.3, .1), pos_hint={"x": .1, "y": .7}, background_normal='',
                            background_color=(.5, .5, .5, .5), text="Team 1", font_name="pixel_font.otf",
                            color=(0, 0, 0, 1), font_size=Window.height * 0.05)
        team_1_btn.bind(on_press=lambda button: self.change_team("team_1"))
        team_2_btn = Button(size_hint=(.3, .1), pos_hint={"x": .6, "y": .7}, background_normal='',
                            background_color=(.5, .5, .5, .5), text="Team 2", font_name="pixel_font.otf",
                            color=(0, 0, 0, 1), font_size=Window.height * 0.05)
        team_2_btn.bind(on_press=lambda button: self.change_team("team_2"))
        self.team_slots = {"team_1": [], "team_2": [], "centre": []}
        for i in range(3):
            self.team_slots["team_1"].append(Button(size_hint=(.3, .1), pos_hint={"x": .1, "y": (.55-i*.15)},
                                                    background_normal='', background_down='',
                                                    background_color=(1, 1, 1, 1), font_name="pixel_font.otf",
                                                    color=(0, 0, 0, 1), font_size=Window.height * 0.05))
            self.team_slots["team_2"].append(Button(size_hint=(.3, .1), pos_hint={"x": .6, "y": (.55-i*.15)},
                                                    background_normal='', background_down='',
                                                    background_color=(1, 1, 1, 1), font_name="pixel_font.otf",
                                                    color=(0, 0, 0, 1), font_size=Window.height * 0.05))
            for j in range(2):
                self.team_slots["centre"].append(Button(size_hint=(.15, .075), pos_hint={"x": .425,
                                                                                         "y": (.725-(2*i+j)*.1)},
                                                        background_normal='', background_down='',
                                                        background_color=(1, 1, 1, 1), font_name="pixel_font.otf",
                                                        color=(0, 0, 0, 1), font_size=Window.height * 0.025))
        float_layout = FloatLayout()
        self.add_widget(float_layout)
        self.add_widget(self.start_button)
        float_layout.add_widget(back)
        float_layout.add_widget(team_1_btn)
        float_layout.add_widget(team_2_btn)
        for i in range(3):
            float_layout.add_widget(self.team_slots["team_1"][i])
            float_layout.add_widget(self.team_slots["team_2"][i])
            float_layout.add_widget(self.team_slots["centre"][i])
            float_layout.add_widget(self.team_slots["centre"][i+3])
        self.team_slots["centre"][0].text = self.username
        self.requests = []

    # Called when the screen is entered,
    def on_pre_enter(self):
        self.requests = []
        self.transport.write("create_lobby\n".encode("utf-8"))

    # Takes the message containing the teams and outs the players in their team's slots.
    def update_slots(self, message):
        message = message.split(";;")
        for i in range(3):
            message[i] = message[i].split(";")
            self.team_slots["team_1"][i].text = ""
            self.team_slots["team_2"][i].text = ""
            self.team_slots["centre"][i].text = ""
            self.team_slots["centre"][i+3].text = ""
        for i, user in enumerate(message[0]):
            self.team_slots["team_1"][i].text = user
        for i, user in enumerate(message[1]):
            self.team_slots["centre"][i].text = user
        for i, user in enumerate(message[2]):
            self.team_slots["team_2"][i].text = user
        if message[3] == self.username:
            try:
                self.add_widget(self.start_button)
            except WidgetException:
                pass
        else:
            try:
                self.remove_widget(self.start_button)
            except WidgetException:
                pass
        if message[1][0] == "":  # If there are no players in the centre
            if message[0][0] != "" and message[2][0] != "":
                # If both teams have at least 1 player
                self.start_button.background_color = (.5, 1, .5, .7)
                self.start_button.background_down = "atlas://data/images/defaulttheme/button_pressed"
                return
        self.start_button.background_color = (.3, .4, .3, .7)
        self.start_button.background_down = ""

    def change_team(self, new_team):
        self.transport.write(("team;" + new_team).encode("utf-8"))

    def request_received(self, username):
        if username in self.requests:  # If the user has already asked to join.
            return
        else:
            self.requests.append(username)
        popup_layout = GridLayout(cols=1)
        popup_layout.add_widget(Label(text=username + " wants to join", font_name="pixel_font.otf", color=(1, 1, 1, 1),
                                      font_size=Window.height * 0.025))
        popup_layout.add_widget(Button(text="Accept?", font_name="pixel_font.otf", color=(1, 1, 1, 1),
                                       font_size=Window.height * 0.025, on_press=lambda button:
                                       self.transport.write(("accept;" + username).encode("utf-8")),
                                       on_release=lambda btn: (popup_layout.parent.parent.parent.dismiss(),
                                                               self.requests.remove(username) if username in
                                                               self.requests else None)))
        Popup(pos_hint={"x": .15, "y": .35}, size_hint=(.7, .3), title="", content=popup_layout,
              on_dismiss=lambda btn: self.requests.remove(username) if username in self.requests else None).open()

    def leave(self, popup):
        self.transport.write("leave\n".encode("utf-8"))
        switch("Multiplayer", self.manager, "right")
        popup.dismiss()

    def start(self, button, popup):
        if self.start_button.background_color == [.5, 1, .5, .7]:
            popup.remove_widget(button)
            popup.dismiss()
            self.transport.write("start\n".encode("utf-8"))

    def start_game(self):
        character_choices = 1
        team = "team_2"
        for i in range(3):
            if self.username == self.team_slots["team_1"][i].text:
                team = "team_1"
        if self.username == self.team_slots[team][0].text:
            for slot in self.team_slots[team]:
                if slot.text == "":
                    character_choices += 1
        self.manager.add_widget(CharacterSelection("Character Selection", character_choices=character_choices,
                                                   multiplayer=True, protocol=self.protocol, transport=self.transport,
                                                   username=self.username, team=team))
        switch("Character Selection", self.manager, "down")
