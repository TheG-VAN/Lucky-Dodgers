from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.graphics import Rectangle, Color, Ellipse
from kivy.garden.joystick import Joystick
from image_editing import make_dict, get_info
from misc import ImageButton, switch, get_characters
from character import Character
from ai import AI
from ball import Ball
from os.path import isdir
from random import choice
import math


# This is the screen where the actual game is played. Inherits the Screen class from kivy.
class Game(Screen):
    def __init__(self, name, characters, multiplayer=False, username="", protocol=None, transport=None,
                 background=None):
        super().__init__()
        self.name = name
        self.characters = characters
        self.multiplayer = multiplayer
        self.username = username
        self.protocol = protocol
        if protocol:
            self.protocol.game = self
        self.transport = transport
        self.messages = []
        self.selected_character = None
        if not background:
            # Choose a random background if one was not already given (in multiplayer).
            background = choice(["Images/[0.7]background_mud.png", "Images/[0.6]background_grass.png",
                                "Images/[0.7]background_night.png", "Images/[0.3]background_snow.png"])
        self.config = get_info("config.ini", character=False)
        self.fps = 60
        with self.canvas:
            Rectangle(source=background, size=Window.size)
        pause_button = ImageButton(pos_hint={"x": .475, "y": .9}, size_hint=(.05, .1),
                                   source="Images/pause.png", color=(1, 1, 1, .2))
        pause_button.bind(on_press=lambda button: pause_popup.open())
        pause_layout = GridLayout(cols=1)
        pause_layout.add_widget(Button(size_hint=(.3, .1), pos_hint={"x": .1, "y": .7}, background_normal='',
                                       background_color=(.5, .5, .5, .5), text="Quit", font_name="pixel_font.otf",
                                       color=(0, 0, 0, 1), font_size=Window.height * 0.05,
                                       on_press=lambda button: self.quit(popup=pause_popup)))
        pause_popup = Popup(title="Pause", title_font="pixel_font.otf", title_size=Window.height * 0.07,
                            title_align="center", size_hint=(.9, .9), content=pause_layout)
        joystick = CustomJoystick(pos_hint={"x": float(self.config["joystick_pos"][0]),
                                            "y": float(self.config["joystick_pos"][1])},
                                  size_hint=self.config["joystick_size"],
                                  pad_color=self.config["joystick_color"])
        # Calls the selected character's run function every tick of the game. But only when the schedule is active.
        # This will be only when the joystick is touched.
        self.run_schedule = Clock.schedule_interval(lambda instance: self.selected_character.run(joystick.radians),
                                                    1/self.fps)
        self.run_schedule.cancel()  # Make the schedule inactive.
        joystick.bind(on_touch_down=lambda stick, pad: self.check_touch_location(stick, pad, self.run_schedule))
        joystick.bind(on_touch_move=lambda stick, pad: self.check_touch_location(stick, pad, self.run_schedule))
        joystick.bind(on_touch_up=lambda stick, pad: self.run_schedule.cancel())
        jump_button = ImageButton(pos_hint={"x": float(self.config["button_1_pos"][0]),
                                            "y": float(self.config["button_1_pos"][1])},
                                  size_hint=self.config["button_1_size"],
                                  source="Images/circle.png", color=self.config["button_1_color"])
        jump_button.bind(on_press=lambda button: self.selected_character.jump())
        catch_button = ImageButton(pos_hint={"x": float(self.config["button_2_pos"][0]),
                                             "y": float(self.config["button_2_pos"][1])},
                                   size_hint=self.config["button_2_size"],
                                   source="Images/circle.png", color=self.config["button_2_color"])
        catch_button.bind(on_press=lambda button: self.selected_character.catch())
        switch_button = ImageButton(pos_hint={"x": float(self.config["button_3_pos"][0]),
                                              "y": float(self.config["button_3_pos"][1])},
                                    size_hint=self.config["button_3_size"],
                                    source="Images/circle.png", color=self.config["button_3_color"])
        switch_button.bind(on_press=lambda button: self.switch_characters())
        light_throw_button = ImageButton(pos_hint={"x": float(self.config["button_1_pos"][0]),
                                                   "y": float(self.config["button_1_pos"][1])},
                                         size_hint=self.config["button_1_size"],
                                         source="Images/circle.png", color=self.config["button_1_color"])
        light_throw_button.bind(on_press=lambda button: self.selected_character.light_throw())
        heavy_throw_button = ImageButton(pos_hint={"x": float(self.config["button_2_pos"][0]),
                                                   "y": float(self.config["button_2_pos"][1])},
                                         size_hint=self.config["button_2_size"],
                                         source="Images/circle.png", color=self.config["button_2_color"])
        heavy_throw_button.bind(on_press=lambda button: self.selected_character.heavy_throw())
        pass_button = ImageButton(pos_hint={"x": float(self.config["button_3_pos"][0]),
                                            "y": float(self.config["button_3_pos"][1])},
                                  size_hint=self.config["button_3_size"],
                                  source="Images/circle.png", color=self.config["button_3_color"])
        pass_button.bind(on_press=lambda button: self.selected_character.pass_to_teammate())
        ball = Ball(background)
        self.ball = ball
        self.sprites = [ball]
        self.controllable_sprites = []
        if multiplayer:
            self.calculating_ball = False
            if list(self.characters.keys()).index(self.username) == 0:
                self.calculating_ball = True
            self.online_characters = []
            for character in self.characters[self.username][:-1]:
                controllable_char = AI(make_dict(character), ball, int(self.characters[self.username][-1][-1]))
                self.sprites.append(controllable_char)
                self.controllable_sprites.append(controllable_char)
            self.selected_character = self.controllable_sprites[0]
            self.selected_character.selected = True

            # Create a new class for online characters which has reduced functionality so the online characters
            # aren't using any processing power.
            class OnlineCharacter(Character):
                prev_health = 100

                # The only method usually called in update that needs to be called is update_healthbar so override
                def update(self):
                    super().update_healthbar()

                def animate_next_frame(self):  # Have to override this function to prevent animation occurring locally.
                    pass

            for user in self.characters:
                if user != self.username:
                    for i, character in enumerate(self.characters[user][:-1]):
                        if not isdir("Images/" + character):  # If the user doesn't have the character.
                            character = choice(list(get_characters().keys()))
                        online_char = OnlineCharacter(make_dict(character), ball, int(self.characters[user][-1][-1]))
                        online_char.user = user
                        online_char.num = str(i)
                        self.sprites.append(online_char)
                        self.online_characters.append(online_char)

        else:
            for char in self.characters:
                self.controllable_sprites.append(AI(make_dict(char), ball, 1))
            self.selected_character = self.controllable_sprites[0]
            self.controllable_sprites[0].selected = True
            self.sprites.extend(self.controllable_sprites)
            for i in range(3):
                self.sprites.append(AI(make_dict(choice(list(get_characters().keys()))), ball, 2))
        self.sprite_layout = FloatLayout()
        self.float_layout = FloatLayout()
        self.add_widget(self.sprite_layout)
        self.add_widget(self.float_layout)
        self.float_layout.add_widget(pause_button)
        self.float_layout.add_widget(joystick)
        self.float_layout.add_widget(jump_button)
        self.has_ball_buttons = [light_throw_button, heavy_throw_button, pass_button]
        self.enemy_has_ball_buttons = [jump_button, catch_button, switch_button]
        self.buttons = [light_throw_button, heavy_throw_button, pass_button, jump_button, catch_button, switch_button]
        for sprite in self.sprites:
            self.sprite_layout.add_widget(sprite)
            sprite.game = self
        # Call these functions every tick.
        self.main_schedule = Clock.schedule_interval(lambda time: (self.update_sprites(), self.update_buttons(),
                                                                   self.arrange_sprites(), self.create_shadows(),
                                                                   self.send_data(), self.online_update(),
                                                                   self.variable_frame_rate(time=time)), 1/self.fps)
        # Need a separate speed for character animation because the speed of the animations has to stay constant.
        Clock.schedule_interval(lambda time: self.animate_sprites(), .05)

    # Called when the screen is entered.
    def on_pre_enter(self):
        # This is just to save resources. Removes the character creation screen when in a game.
        if self.manager.has_screen("Creation Station"):
            self.manager.remove_widget(self.manager.get_screen("Creation Station"))

    @staticmethod
    def check_touch_location(widget, touch, func):  # Checks if the user touched the widget.
        if widget.collide_point(*touch.opos):
            func()

    # Function for changing the frame rate of the game.
    def variable_frame_rate(self, time=None):
        # If the device was able to complete the previous tick in the correct amount of time, increase the fps.
        if math.isclose(time, 1 / self.fps, rel_tol=0.1):
            self.fps += 1
        elif self.fps > 1:  # Otherwise decrease the fps as long as it is above 1.
            self.fps -= 1
        self.main_schedule.timeout = 1 / self.fps
        self.run_schedule.timeout = 1 / self.fps

    def quit(self, popup=None):
        if self.manager:
            self.main_schedule.cancel()
            switch("Main Menu", self.manager, "up")
            self.manager.remove_widget(self)
            if popup:
                popup.dismiss()
            if self.multiplayer:
                self.transport.write("leave\n".encode("utf-8"))
            del self

    def animate_sprites(self):
        for sprite in self.sprites:
            try:
                sprite.animate_next_frame()
            except AttributeError:
                continue

    def update_sprites(self):
        if self.ball.character:
            self.ball.character.has_ball = True
        for sprite in self.sprites:
            sprite.update()
            try:
                if sprite.selected:
                    self.selected_character = sprite
                    if sprite.dead:
                        self.switch_characters()
            except AttributeError:
                pass

    def send_data(self):
        if self.multiplayer:
            output = "update;"
            for i, character in enumerate(self.controllable_sprites):
                output += ";".join([self.username, str(i), str(character.x/Window.width),
                                    str(character.y/Window.height), str(character.z/Window.height),
                                    character.prev_state, str(character.state_frames[character.prev_state]),
                                    str(character.health), str(character.color)])
                output += ";;"
                if character.has_ball:
                    self.calculating_ball = True
            output = output.strip(";;")
            if self.calculating_ball:
                output += "\nupdate;"
                ball_char_user = "None"
                ball_char_num = "None"
                if self.ball.character:
                    try:
                        ball_char_num = str(self.controllable_sprites.index(self.ball.character))
                        ball_char_user = self.username
                    except ValueError:  # This means that a different user now has the ball
                        self.calculating_ball = False
                        self.transport.write((output + "\n").encode("utf-8"))
                        return
                for character in self.online_characters:
                    if character.prev_health != character.health:
                        self.ball.hit_player()
                output += ";".join(["ball", str(self.ball.x/Window.width), str(self.ball.y/Window.height),
                                    str(self.ball.z/Window.height), str(self.ball.color), str(self.ball.midair),
                                    str(self.ball.speed), str(self.ball.throwing_team), ball_char_user, ball_char_num,
                                    str(self.ball.passed)])
            self.transport.write((output + "\n").encode("utf-8"))

    def update_buttons(self):
        for widget in self.buttons:
            try:
                self.float_layout.remove_widget(widget)
            except ValueError:
                pass
        if self.selected_character.has_ball:
            for widget in self.has_ball_buttons:
                self.float_layout.add_widget(widget)
        else:
            for widget in self.enemy_has_ball_buttons:
                self.float_layout.add_widget(widget)

    def switch_characters(self):
        self.selected_character.selected = False
        self.selected_character = self.controllable_sprites[self.controllable_sprites.index(self.selected_character)-1]
        self.selected_character.selected = True

    # Method for moving sprites in front of and behind each other.
    def arrange_sprites(self):
        # Sort the sprites in order of their z and remove then add them back in reverse order.
        for sprite in sorted(self.sprites, key=lambda widget: widget.z, reverse=True):
            self.sprite_layout.remove_widget(sprite)
            self.sprite_layout.add_widget(sprite)

    def create_shadows(self):
        for sprite in self.sprites:
            if not hasattr(sprite, "shadow"):
                sprite.canvas.before.add(Color(0, 0, 0, .3))
                sprite.shadow = Ellipse()
                sprite.canvas.before.add(sprite.shadow)
            # The shadow's size is dependent on the sprites size and height above ground.
            sprite.shadow.size = (sprite.width/2+(sprite.y-sprite.z)/2, sprite.height/3+(sprite.y-sprite.z)/2)
            sprite.shadow.pos = (sprite.center_x-sprite.width/5-(sprite.y-sprite.z)/4,
                                 sprite.z-sprite.height/6-(sprite.y-sprite.z)/4)
            try:
                if sprite.character:  # If the sprite is the ball.
                    sprite.canvas.before.clear()
                    del sprite.shadow
            except AttributeError:
                if sprite.health <= 0:
                    sprite.canvas.before.clear()
                    del sprite.shadow

    # Method for keeping the most recent message for each user.
    def receive_message(self, message):
        if message.split(";")[0] == "ball":
            try:
                if message.split(";")[8] != self.username:  # If the ball is not calculated by the user.
                    self.calculating_ball = False
            except IndexError:
                pass
        for i, user in enumerate(self.messages):
            if message.split(";")[0] == user.split(";")[0]:
                self.messages[i] = message
                return
        # This will only be reached if there are no messages kept from this user.
        self.messages.append(message)

    # Method for applying the attributes received in the messages to the online characters and ball.
    def online_update(self):
        for message in self.messages:
            message = message.split(";;")
            for i in range(len(message)):
                try:
                    message[i] = message[i].split(";")
                    if message[i][0] != "ball":
                        for character in self.online_characters:
                            if character.user == message[i][0] and character.num == message[i][1]:
                                character.x = float(message[i][2]) * Window.width
                                character.y = float(message[i][3]) * Window.height
                                character.z = float(message[i][4]) * Window.height
                                try:
                                    from image_editing import make_dict
                                    if character.texture != character.image_dict[message[i][5]][int(
                                            float(message[i][6]))].texture:
                                        character.texture = character.image_dict[message[i][5]][int(
                                            float(message[i][6]))].texture
                                except IndexError:
                                    pass
                                character.prev_health = character.health
                                try:
                                    character.health = float(message[i][7])
                                    character.color = message[i][8].replace("[", "").replace("]", "").split(", ")
                                except ValueError:
                                    character.prev_health = 0
                                    character.health = 0
                    elif not self.calculating_ball:
                        self.ball.x = float(message[i][1]) * Window.width
                        self.ball.y = float(message[i][2]) * Window.height
                        self.ball.z = float(message[i][3]) * Window.height
                        self.ball.color = list(map(int, message[i][4].replace("[", "").replace("]", "").split(", ")))
                        self.ball.midair = message[i][5] == "True"
                        self.ball.speed = float(message[i][6])
                        self.ball.throwing_team = None if message[i][7] == "None" else int(message[i][7])
                        self.ball.passed = message[i][10] == "True"
                        if message[i][8] == "None":
                            self.ball.character = None
                        else:
                            for character in self.online_characters:
                                if character.user == message[i][8] and character.num == message[i][9]:
                                    self.ball.character = character
                except IndexError:
                    pass


# Class for a joystick with certain properties.
class CustomJoystick(Joystick):
    def __init__(self, pos_hint=None, size_hint=None, pad_color=None):
        super().__init__(pos_hint=pos_hint, size_hint=size_hint)
        self.outer_background_color = [0, 0, 0, .3]
        self.outer_line_color = [0, 0, 0, 0]
        self.inner_background_color = [0, 0, 0, 0]
        self.inner_line_color = [0, 0, 0, 0]
        self.pad_background_color = pad_color
        self.pad_line_color = [0, 0, 0, 0]
        self.pad_size = .4
        self.inner_size = .3
        self.outer_size = .6
