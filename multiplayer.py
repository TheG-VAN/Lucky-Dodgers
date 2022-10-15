from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from misc import switch, ImageButton
from lobby import Lobby
from join import Join
from image_editing import get_info
from misc import get_characters
from kivy.support import install_twisted_reactor
import sys
from os.path import isfile

if 'twisted.internet.reactor' in sys.modules:
    del sys.modules['twisted.internet.reactor']
install_twisted_reactor()  # This is required to allow the kivy and twisted event loops to work together.
from twisted.internet import reactor
from client import ClientFactory


# This is the screen for multiplayer. It inherits the Screen class from kivy.
class Multiplayer(Screen):
    def __init__(self, name):
        super().__init__()
        self.name = name
        info = get_info("online_info.ini", character=False)
        self.username = "".join(map(str, info["username"]))
        self.friends = info["friends"]
        self.client_factory = ClientFactory(self, self.username)
        self.transport = None
        reactor.connectTCP(info["server_ip"][0], 50000, self.client_factory)  # Start the client.
        connecting = Label(text="[color=ff0000]A[/color]ttempting to connect...", font_name="pixel_font.otf",
                           size_hint=(0.7, 0.3), pos_hint={"x": .15, "y": .35}, color=(0, 0, 0, 1),
                           font_size=Window.height * 0.1, markup=True)
        self.tracker = 0
        self.add_widget(connecting)
        Clock.schedule_interval(lambda instance: self.animate_text(connecting), .05)
        back = ImageButton(pos_hint={"x": .01, "top": .99}, size_hint=(0.1, 0.1), source="Images/back.png")
        back.bind(on_press=lambda button: switch("Play", self.manager, "right"))
        self.add_widget(back)
        self.requested_username = ""
        self.requested_friend = ""

    # This method makes the colour red flow through the text.
    def animate_text(self, label):
        if label not in self.children:
            return
        s = "Attempting to connect..."
        self.tracker += 1
        if self.tracker == len(s):
            self.tracker = 0
        # Have darker reds towards the edges of the section of text being coloured.
        label.text = s[:self.tracker] + "[color=550000]" + s[self.tracker:self.tracker + 1] + "[/color]" + \
            "[color=990000]" + s[self.tracker + 1:self.tracker + 2] + "[/color]" + \
            "[color=ff0000]" + s[self.tracker + 2:self.tracker + 3] + "[/color]" + \
            "[color=990000]" + s[self.tracker + 3:self.tracker + 4] + "[/color]" + \
            "[color=550000]" + s[self.tracker + 4:self.tracker + 5] + "[/color]" + \
            s[self.tracker + 5:]

    # This method sends information to the server about username, friends and characters.
    def initialise_connection(self):
        self.transport.write(("username;" + self.username + "\n").encode("utf-8"))
        characters = get_characters()
        characters_list = []
        friend_characters_list = []
        for character in characters:  # Create an ImageButton for each character
            if isfile("Images/" + character + "/section_locations.pickle"):  # If character is built-in
                continue
            elif isfile(characters[character]):  # If the character was made by the user.
                characters_list.append(character)
            else:
                friend_characters_list.append(character)
        self.transport.write(("custom_characters;" + ";".join(characters_list) + "\n").encode("utf-8"))
        self.transport.write(("friends;;" + ";".join(self.friends) + ";;" +
                              ";".join(friend_characters_list) + "\n").encode("utf-8"))

    # Called when the screen is entered.
    def on_pre_enter(self):
        if self.transport:
            self.initialise_connection()

    # This method creates a popup allowing the user to enter a username.
    def set_username(self):
        popup_layout = GridLayout(cols=1, spacing=Window.width * .01)
        popup_layout.add_widget(Label(text="Create a username", font_name="pixel_font.otf",
                                      font_size=Window.height * 0.07))
        username_input = TextInput(text="Username", multiline=False, font_name="pixel_font.otf",
                                   font_size=Window.height * 0.07)
        # Filter out certain punctuation.
        username_input.input_filter = lambda text, from_undo: "".join(char for char in text if char not in
                                                                      "|\\?*<\":>+[]/'")[:20 - len(username_input.text)]
        popup_layout.add_widget(username_input)
        confirm_button = Button(text="Confirm", background_normal='', background_color=(.5, 1, .5, .5),
                                font_name="pixel_font.otf", font_size=Window.height * 0.07)
        confirm_button.bind(on_press=lambda button: self.username_confirmed(username_input.text))
        cancel_button = Button(text="Cancel", background_normal='', background_color=(1, .5, .5, .5),
                               font_name="pixel_font.otf", font_size=Window.height * 0.07)
        cancel_button.bind(on_press=lambda button: (switch("Play", self.manager, "right"),
                                                    self.manager.remove_widget(self), self.username_popup.dismiss()))
        popup_layout.add_widget(confirm_button)
        popup_layout.add_widget(cancel_button)
        self.username_popup = Popup(pos_hint={"x": .1, "y": .2}, size_hint=(.8, .6), title="", auto_dismiss=False,
                                    content=popup_layout)
        self.username_popup.open()

    def username_confirmed(self, text):
        self.transport.write(("wants_username;" + text + "\n").encode("utf-8"))
        self.requested_username = text

    def friend_username_confirmed(self, text):
        if text in self.friends:
            Popup(pos_hint={"x": .2, "y": .35}, size_hint=(.6, .3), title="",
                  content=Label(text="Already your friend", font_name="pixel_font.otf",
                                font_size=Window.height * 0.05)).open()
        elif text == self.username:
            Popup(pos_hint={"x": .15, "y": .35}, size_hint=(.7, .3), title="",
                  content=Label(text="You can't be your own friend", font_name="pixel_font.otf",
                                font_size=Window.height * 0.05)).open()
        else:
            self.transport.write(("add_friend;" + text + "\n").encode("utf-8"))
            self.requested_friend = text

    @staticmethod
    def username_taken():
        Popup(pos_hint={"x": .2, "y": .35}, size_hint=(.6, .3), title="",
              content=Label(text="Username taken", font_name="pixel_font.otf", font_size=Window.height * 0.05)).open()

    # This method locally saves the username.
    def username_accepted(self):
        self.username = self.requested_username
        with open("online_info.ini", "r") as online_info:
            info_list = online_info.read().split("\n")
            info_list[info_list.index("username") + 1] = self.username
        with open("online_info.ini", "w") as online_info:
            online_info.write("\n".join(info_list))
        self.username_popup.dismiss()
        self.initialise_connection()

    @staticmethod
    def no_friend():
        Popup(pos_hint={"x": .2, "y": .35}, size_hint=(.6, .3), title="",
              content=Label(text="Player doesn't exist", font_name="pixel_font.otf",
                            font_size=Window.height * 0.05)).open()

    # This method saves the friend locally.
    def added_friend(self):
        self.friends.append(self.requested_friend)
        with open("online_info.ini", "r") as online_info:
            info_list = online_info.read().split("\n")
            if info_list[info_list.index("friends") + 1] != "":
                info_list[info_list.index("friends") + 1] += ";"
            info_list[info_list.index("friends") + 1] += self.requested_friend
        with open("online_info.ini", "w") as online_info:
            online_info.write("\n".join(info_list))
        Popup(pos_hint={"x": .2, "y": .35}, size_hint=(.6, .3), title="",
              content=Label(text="Added friend", font_name="pixel_font.otf",
                            font_size=Window.height * 0.05)).open()
        self.initialise_connection()  # Send the new changed data to the server.

    # Only do this once connected to the server.
    def create_buttons(self):
        self.clear_widgets()
        back = ImageButton(pos_hint={"x": .01, "top": .99}, size_hint=(0.1, 0.1), source="Images/back.png")
        back.bind(on_press=lambda button: switch("Play", self.manager, "right"))
        host_button = Button(size_hint=(.6, .3), pos_hint={"x": .2, "y": .55}, background_normal='',
                             background_color=(.5, .5, .5, .5), text="Host Game", font_name="pixel_font.otf",
                             color=(0, 0, 0, 1), font_size=Window.height * 0.15)
        if self.manager.has_screen("Lobby"):
            self.manager.remove_widget(self.manager.get_screen("Lobby"))
        self.manager.add_widget(Lobby("Lobby", self.username, self.client_factory.protocol, self.transport))
        host_button.bind(on_press=lambda button: switch("Lobby", self.manager, "left"))
        join_button = Button(size_hint=(.6, .3), pos_hint={"x": .2, "y": .15}, background_normal='',
                             background_color=(.5, .5, .5, .5), text="Join Game", font_name="pixel_font.otf",
                             color=(0, 0, 0, 1), font_size=Window.height * 0.15)
        if self.manager.has_screen("Join"):
            self.manager.remove_widget(self.manager.get_screen("Join"))
        self.manager.add_widget(Join("Join", self.username, self.friends, self.client_factory.protocol, self.transport))
        join_button.bind(on_press=lambda button: switch("Join", self.manager, "left"))
        self.create_friends_popup()
        friends_button = Button(size_hint=(.2, .1), pos_hint={"x": .8, "y": .9}, background_normal='',
                                background_color=(.5, .7, .5, .5), text="Friends", font_name="pixel_font.otf",
                                color=(0, 0, 0, 1), font_size=Window.height * 0.05)
        friends_button.bind(on_press=lambda button: self.friends_popup.open())
        float_layout = FloatLayout()
        self.add_widget(float_layout)
        float_layout.add_widget(back)
        float_layout.add_widget(host_button)
        float_layout.add_widget(join_button)
        float_layout.add_widget(friends_button)

    # Create a popup for friends which will have two tabs.
    def create_friends_popup(self):
        friends_tabs = TabbedPanel(do_default_tab=False, tab_width=Window.width * .44, tab_height=Window.height * .1)
        friends_tab = TabbedPanelItem(text="Friends", font_name="pixel_font.otf", font_size=Window.height * .05)
        scroll = ScrollView(size_hint=(1, None), pos_hint={"x": .1, "y": .1},
                            size=(Window.width * .8, Window.height * .7))
        self.friends_layout = GridLayout(cols=3, size_hint_y=None, row_default_height=Window.height * .1,
                                         spacing=[Window.width * .001, Window.height * .01],
                                         padding=Window.height * .01)
        self.friends_layout.bind(minimum_height=self.friends_layout.setter('height'))
        friends_tab.add_widget(scroll)
        add_friends_tab = TabbedPanelItem(text="Add a friend", font_name="pixel_font.otf",
                                          font_size=Window.height * .05)
        add_friends_layout = GridLayout(cols=1, spacing=Window.width * .01, padding=Window.width * .05)
        add_friends_layout.add_widget(Label(text="Enter friend's username", font_name="pixel_font.otf",
                                            font_size=Window.height * 0.07))
        username_input = TextInput(text="Username", multiline=False, font_name="pixel_font.otf",
                                   font_size=Window.height * 0.07)
        username_input.input_filter = lambda text, from_undo: "".join(char for char in text if char not in
                                                                      "|\\?*<\":>+[]/'")[:20 - len(username_input.text)]
        add_friends_layout.add_widget(username_input)
        add_friends_tab.add_widget(add_friends_layout)
        confirm_button = Button(text="Confirm", background_normal='', background_color=(.5, 1, .5, .5),
                                font_name="pixel_font.otf", font_size=Window.height * 0.07)
        confirm_button.bind(on_press=lambda button: self.friend_username_confirmed(username_input.text))
        add_friends_layout.add_widget(confirm_button)
        friends_tabs.add_widget(friends_tab)
        friends_tabs.add_widget(add_friends_tab)
        scroll.add_widget(self.friends_layout)
        self.friends_popup = Popup(pos_hint={"x": .05, "y": .05}, size_hint=(.9, .9), content=friends_tabs, title="",
                                   separator_height=0)
        self.friends_popup.bind(on_open=lambda popup: self.transport.write(
            ("check_status;" + ";".join(self.friends) + "\n").encode("utf-8")))
        friends_tab.bind(on_press=lambda tab: self.transport.write(
            ("check_status;" + ";".join(self.friends) + "\n").encode("utf-8")))

    # Update the friends popup with the current statuses of the user's friends.
    def friends_statuses(self, message):
        self.friends_layout.clear_widgets()
        friends = message.split(";;")[1:-1]
        for friend in friends:
            friend = friend.split(";")
            if friend[0] == "":
                if len(friends) == 1:
                    self.friends_layout.add_widget(Button(background_normal='', background_down='',
                                                          background_color=(1, 1, 1, .8), font_name="pixel_font.otf",
                                                          color=(0, 0, 0, 1), font_size=Window.height * 0.025,
                                                          text="You have no friends"))
                    return
                continue
            self.friends_layout.add_widget(Button(background_normal='', background_down='',
                                                  background_color=(1, 1, 1, .8), font_name="pixel_font.otf",
                                                  color=(0, 0, 0, 1), font_size=Window.height * 0.025, text=friend[0]))
            if friend[1].startswith("in_lobby"):
                friend[1] = friend[1].split("-")
                self.friends_layout.add_widget(Button(background_normal='', background_down='',
                                                      background_color=(1, 1, 1, .8), font_name="pixel_font.otf",
                                                      color=(0, 0, 0, 1), font_size=Window.height * 0.025,
                                                      text="In a lobby: " + friend[1][2] + "/6"))
                self.friends_layout.add_widget(Button(font_name="pixel_font.otf", color=(1, 1, 1, 1),
                                                      font_size=Window.height * 0.025, text="Join",
                                                      on_press=lambda button:
                                                      self.transport.write(
                                                          ("request;" + friend[1][1] + "\n").encode("utf-8"))))
            else:
                self.friends_layout.add_widget(Button(background_normal='', background_down='',
                                                      background_color=(1, 1, 1, .8), font_name="pixel_font.otf",
                                                      color=(0, 0, 0, 1), font_size=Window.height * 0.025,
                                                      text=friend[1]))
                self.friends_layout.add_widget(Button(background_normal='', background_down='',
                                                      background_color=(0, 0, 0, 0)))

    # Called when the user is disconnected from the server.
    def disconnected(self, error_message):
        # If the user is no longer in multiplayer, don't interrupt them.
        if self.manager.current_screen != self and error_message.startswith("TCP connection timed out:"):
            return
        Popup(pos_hint={"x": .3, "y": .35}, size_hint=(.4, .3),
              content=Label(text="Connection Failed", font_name="pixel_font.otf",
                            color=(1, 1, 1, 1), font_size=Window.height * 0.05), title="").open()
        switch("Play", self.manager, "right")
        if self.manager.has_screen("Lobby"):
            self.manager.remove_widget(self.manager.get_screen("Lobby"))
        if self.manager.has_screen("Join"):
            self.manager.remove_widget(self.manager.get_screen("Join"))
        self.manager.remove_widget(self)
        del self
