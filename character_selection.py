from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.graphics import Color, Line
from kivy.clock import Clock
from misc import ImageButton, switch, get_characters
from game import Game
from random import choice
from os.path import isfile


# A class for the character selection screen. Inherits the Screen class from kivy. Has optional parameters for online.
class CharacterSelection(Screen):
    def __init__(self, name, character_choices=3, multiplayer=False, protocol=None, transport=None, username=None,
                 team=None):
        super().__init__()
        self.name = name
        self.init_character_choices = character_choices
        self.character_choices = character_choices
        self.multiplayer = multiplayer
        self.protocol = protocol
        self.team = team
        if protocol:
            self.protocol.character_selection = self
        self.transport = transport
        self.username = username
        self.characters = []
        float_layout = FloatLayout()
        leave_button = Button(background_normal='', background_color=(1, 1, 1, 1), text="Leave?",
                              font_name="pixel_font.otf", color=(0, 0, 0, 1), font_size=Window.height * 0.1)
        leave_button.bind(on_press=lambda button: self.leave(leave_popup))
        leave_popup = Popup(pos_hint={"x": .3, "y": .35}, size_hint=(.4, .3),
                            content=leave_button, title="")
        back = ImageButton(pos_hint={"x": .01, "top": .99}, size_hint=(0.1, 0.1), source="Images/back.png")
        back.bind(on_press=lambda button: leave_popup.open())
        cancel = ImageButton(pos_hint={"x": .94, "top": .99}, size_hint=(0.05, 0.1), source="Images/cancel.png")
        cancel.bind(on_press=self.cancel)
        pick_label = Label(pos_hint={"x": .15, "y": .7}, size_hint=(0.7, 0.3),
                           text="Pick " + str(self.character_choices) + " character" +
                                ("s" if self.character_choices > 1 else ""),
                           font_name="pixel_font.otf", color=(0, 0, 0, 1), font_size=Window.height * 0.1)
        character_scroll = ScrollView(pos_hint={"x": .05, "y": .125}, size_hint=(.9, .7), bar_color=(1, 1, 1, 1),
                                      bar_inactive_color=(1, 1, 1, .6), bar_width=Window.height / 100)
        self.character_picker = GridLayout(padding=[0, Window.height*.1, 0, Window.height*.05], size_hint=(None, 1),
                                           rows=1)
        character_scroll.add_widget(self.character_picker)
        self.start_button = Button(size_hint=(.2, .075), pos_hint={"x": .75, "y": .025}, background_normal='',
                                   background_color=(.3, .4, .3, .7), text="Start", font_name="pixel_font.otf",
                                   color=(0, 0, 0, 1), font_size=Window.height * 0.05, background_down="")
        self.start_button.bind(on_press=lambda button: self.start())
        self.add_widget(float_layout)
        float_layout.add_widget(back)
        float_layout.add_widget(cancel)
        float_layout.add_widget(character_scroll)
        float_layout.add_widget(pick_label)
        float_layout.add_widget(self.start_button)

    # Method for reducing the timer by one and automatically starting if the timer goes to zero.
    def countdown(self, timer):
        timer.text = str(int(timer.text) - 1)
        if int(timer.text) < 1:
            self.countdown_schedule.cancel()
            for i in range(self.character_choices):
                self.characters.append(choice(list(get_characters().keys())))  # Choose a random character.
            self.start_button.background_color = (.5, 1, .5, .7)
            self.start()

    def on_pre_enter(self):  # Gets called when the screenmanager starts switching to this screen.
        if self.multiplayer:
            self.timer = Label(size_hint=(.1, .1), pos_hint={"x": .025, "y": .05}, text="10",
                               font_name="pixel_font.otf", color=(0, 0, 0, 1), font_size=Window.height * 0.1)
            self.add_widget(self.timer)
            self.countdown_schedule = Clock.schedule_interval(lambda instance: self.countdown(self.timer), 1)
        characters = get_characters()
        self.character_picker.clear_widgets()
        num_characters = 0
        for character in characters:  # Create an ImageButton for each character
            if not isfile(characters[character]):
                continue
            char_button = ImageButton(source=characters[character])
            char_button.bind(on_press=self.character_pressed)
            char_button.reload()
            self.character_picker.add_widget(char_button)
            num_characters += 1
        self.character_picker.width = num_characters * Window.height * 0.5

    # Called when the user taps on a character.
    def character_pressed(self, button):
        if self.character_choices > 0:  # Don't do anything if the user has selected all their characters.
            self.character_choices -= 1
            color = [0, 0, 0]
            color[2-self.character_choices] = 1  # Create a colour (either red, green or blue).
            rect_color = Color(*color)
            self.character_picker.canvas.add(rect_color)
            # Make a rounded rectangle outline with size depending on which choice it is.
            self.character_picker.canvas.add(Line(rounded_rectangle=[button.x + Window.width * .05 - Window.width *
                                                                     (2-self.character_choices) * .005,
                                                                     button.y + Window.height * .01 - Window.height *
                                                                     (2-self.character_choices) * .01,
                                                                     button.width - Window.width * .1 + Window.width *
                                                                     (2-self.character_choices) * .01,
                                                                     button.height + Window.height *
                                                                     (2-self.character_choices) * .02,
                                                                     Window.width*.05],
                                                  width=Window.width*.005))
            self.characters.append(button.source.split("/")[1])
            if self.character_choices == 0:  # If all the choices have been made.
                self.start_button.background_color = (.5, 1, .5, .7)
                self.start_button.background_down = "atlas://data/images/defaulttheme/button_pressed"

    # Called when the cancel button is pressed.
    def cancel(self, button=False):
        if button:
            for instruction in self.character_picker.canvas.children:
                if hasattr(instruction, "points"):  # Remove all the rounded rectangles.
                    self.character_picker.canvas.remove(instruction)
            self.characters = []
            self.character_choices = self.init_character_choices
            self.start_button.background_color = (.3, .4, .3, .7)
        else:
            self.manager.remove_widget(self)
            del self

    def leave(self, popup):
        if self.multiplayer:
            self.transport.write("leave\n".encode("utf-8"))
        switch("Play", self.manager, "up")
        popup.dismiss()
        self.cancel()

    def start(self):
        if self.start_button.background_color == [.5, 1, .5, .7]:
            if self.multiplayer:
                self.transport.write(("characters;" + ";".join(self.characters) + ";" + self.team + "\n").
                                     encode("utf-8"))  # Send a message containing the characters chosen and the team.
                self.add_widget(Popup(pos_hint={"x": .1, "y": .35}, size_hint=(.8, .3), auto_dismiss=False,
                                      content=Label(text="Waiting for players", font_name="pixel_font.otf",
                                                    font_size=Window.height * 0.05), title=""))
            else:
                self.manager.add_widget(Game("Game", self.characters))
                switch("Game", self.manager, "down")
                self.cancel()

    def enter_game(self, message):
        message = message.replace("characters_chosen;", "")  # Message is a 3 dimensional array in string form.
        background = message.split(";;;")[-1]
        message = message.split(";;;")[0]
        message = message.split(";;")
        output = {}
        for user in message:
            if not user == "":
                user = user.split(";")
                output[user[0]] = user[1:]
        self.manager.add_widget(Game("Game", output, multiplayer=True, username=self.username, protocol=self.protocol,
                                     transport=self.transport, background=background))
        switch("Game", self.manager, "down")
        self.cancel()
