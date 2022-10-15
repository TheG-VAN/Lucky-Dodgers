from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.clock import Clock
from kivy.graphics import Rectangle, Color, Triangle
import math
from copy import deepcopy
from misc import set_color
from random import randint


class Character(Image):
    def __init__(self, image_dict, ball, team):
        super().__init__()
        self.image_dict = image_dict
        self.allow_stretch = True
        self.ball = ball
        self.unit_x = Window.width / 200  # Create a distance unit that is scaled to window size
        self.unit_y = Window.height / 100
        self.size_hint = (None, None)
        self.size = (self.unit_x*30, self.unit_y*30)
        # Boundaries of the pitch
        self.init_bounds = [[Window.width / 12, Window.width / 2.6], [Window.height / 7.8, Window.height / 1.8]]
        if team == 2:
            # Change the horizontal boundaries to the other side and reverse them.
            self.init_bounds[0] = list(map(lambda x: Window.width - self.width - x, self.init_bounds[0]))[::-1]
        # deepcopy is used because otherwise a change to self.bounds will change self.init_bounds.
        self.bounds = deepcopy(self.init_bounds)
        # Start at a random position.
        self.y = randint(int(self.bounds[1][0]), int(self.bounds[1][1]))
        self.x = randint(int(self.bounds[0][0]), int(self.bounds[0][1]))
        self.z = self.y
        self.team = team
        self.cache_images()
        self.angle = 0
        self.texture = self.image_dict["idle"][0].texture
        self.state = "idle"
        self.prev_state = "idle"
        self.state_is_continuous = True  # If true, the state is repeating e.g. idle, otherwise it is a one-time action.
        self.has_ball = False
        self.had_ball = False  # This is used to determine which player sends the ball information in multiplayer.
        self.running_jump = False
        self.teammates = []
        self.enemies = []
        self.state_frames = {}  # This is a dictionary of all the current frames of each state.
        self.animation_speeds = {}
        for state in self.image_dict:
            self.state_frames[state] = 0
            self.animation_speeds[state] = 1
        self.animation_speeds["idle"] = 0.5
        self.animation_speeds["idle_ball"] = 0.5
        self.animation_speeds["pick_up"] = 0.5
        self.throw = None
        self.health = 100
        self.dead = False
        self.selected = False
        with self.canvas:
            Color(0, 0, 0, 1)
            self.base_bar = Rectangle()  # Create a black bar beneath the healthbar to look like an outline.
            Color(0, 1, 0, 1)
            self.healthbar = Rectangle()
            self.selected_cursor_colour = Color(1, 0, 0, 0)
            self.selected_cursor = Triangle(points=[self.center_x, self.top + self.unit_y * 2,
                                            self.center_x - 2 * self.unit_x, self.top + 5 * self.unit_y,
                                            self.center_x + 2 * self.unit_x, self.top + 5 * self.unit_y])

    # Store the image textures in a dictionary.
    def cache_images(self):
        # Kivy automatically caches images but flipping the images wouldn't work.
        for state in self.image_dict:
            for i in range(len(self.image_dict[state])):
                # nocache is set as tru to prevent kivy's automatic caching.
                self.image_dict[state][i] = CoreImage(self.image_dict[state][i], nocache=True)
                if self.team == 2:  # Make team 2 face the other way.
                    self.image_dict[state][i].texture.flip_horizontal()

    # Called every tick of the game.
    def update(self):
        self.update_enemies_and_teammates()
        if len(self.enemies) == 0 or len(self.teammates) == 0:  # Game over.
            self.parent.parent.quit()
        self.update_healthbar()
        if self.dead:
            return
        self.change_bounds()
        if self.ball.throwing_team and self.collision():  # If the ball has been thrown and has hit the character.
            if self.ball.passed:
                # If the ball was passed by a teammate.
                if self.team == self.ball.throwing_team and not self.had_ball:
                    self.ball.throwing_team = None
                    self.state = "pick_up"
                    self.state_frames["pick_up"] = 2
            elif self.team != self.ball.throwing_team:  # If the ball was thrown by an enemy.
                self.hit()
        if self.ball.character != self:
            if self.ball.character:  # If someone else now has the ball.
                self.had_ball = False
            self.has_ball = False
        if self.state == "jump":
            self.jump_movement()
        else:
            self.running_jump = False
            self.z = self.y
            # If the ball is on the floor, is touching the character, is slow, no-one else has the ball and the
            # character wasn't just hit by the ball.
            if self.floor_collision() and not self.ball.throwing_team and self.ball.speed < 5 / self.game.fps and \
                    not self.ball.character and not self.color == [1, .3, .3, 1]:
                teammate_picking_up = False
                for teammate in self.teammates:
                    if teammate.state == "pick_up":
                        teammate_picking_up = True
                if not teammate_picking_up:  # If a teammate is already picking the ball up, don't pick it up.
                    self.pick_up()
        if self.state == "pick_up" and self.state_frames[self.state] == 2:  # If the character has finished picking up.
            self.has_ball = True
            self.ball.color = (0, 0, 0, 0)
            self.ball.character = self
        if self.has_ball:
            self.had_ball = True
            if self in self.parent.parent.controllable_sprites:
                for teammate in self.parent.parent.controllable_sprites:
                    teammate.selected = False  # Deselect the characters that don't have the ball.
                self.selected = True  # Select the character with the ball.
            self.ball.midair = False
            self.ball.x_speed = 0
            self.ball.y_speed = 0
            self.ball.z_speed = 0
            self.ball.x = self.center_x
            self.ball.y = self.center_y
            self.ball.z = self.y
        if self.selected:
            self.reposition_selected_cursor()
            self.selected_cursor_colour.a = 1  # Make the cursor visible.
        else:
            self.selected_cursor_colour.a = 0  # Make the cursor invisible.
        if self.state_frames[self.state] == len(self.image_dict[self.state]) - 1 and \
                (self.state == "light_throw" or self.state == "heavy_throw"):  # If character is at the end of the throw
            self.do_throw()

    # Method for changing the image to the next one.
    def animate_next_frame(self):
        self.prev_state = self.state
        try:
            self.texture = self.image_dict[self.state][int(self.state_frames[self.state])].texture
            # Increment the frame by the animation speed.
            self.state_frames[self.state] += self.animation_speeds[self.state]
        except IndexError:  # The animation is complete.
            self.state_frames[self.state] = 0
            if not self.state_is_continuous:
                self.idle()
                self.state_is_continuous = True
        if self.state_is_continuous:
            self.idle()  # Automatically go back to idle.

    # Changes the bounds so that the character can retrieve the ball if it is outside of the pitch on their side.
    def change_bounds(self):
        if not self.ball.character:
            if self.team == 1:
                if self.ball.x - self.width / 2 < self.init_bounds[0][0]:  # If the ball is off on the left.
                    self.bounds[0][0] = -self.width / 2
                else:
                    self.bounds[0][0] = self.init_bounds[0][0]
                if self.ball.x - self.width < self.init_bounds[0][1]:  # If the ball is on the character's side.
                    if self.ball.z < self.init_bounds[1][0]:  # If the ball is off on the bottom.
                        self.bounds[1][0] = 0
                    else:
                        self.bounds[1][0] = self.init_bounds[1][0]
                    if self.ball.z > self.init_bounds[1][1]:  # If the ball is off on the top.
                        self.bounds[1][1] = Window.height * 0.65
                    else:
                        self.bounds[1][1] = self.init_bounds[1][1]
            else:
                if self.ball.x - self.width / 2 > self.init_bounds[0][1]:  # If the ball is off on the right.
                    self.bounds[0][1] = Window.width - self.width / 2
                else:
                    self.bounds[0][1] = self.init_bounds[0][1]
                if self.ball.x > self.init_bounds[0][0]:  # If the ball is on the character's side.
                    if self.ball.z < self.init_bounds[1][0]:  # If the ball is off on the bottom.
                        self.bounds[1][0] = 0
                    else:
                        self.bounds[1][0] = self.init_bounds[1][0]
                    if self.ball.z > self.init_bounds[1][1]:  # If the ball is off on the top.
                        self.bounds[1][1] = Window.height * 0.65
                    else:
                        self.bounds[1][1] = self.init_bounds[1][1]
        else:
            self.bounds = deepcopy(self.init_bounds)  # Reset the boundaries.

    # Called when the joystick is moved or when the AI is controlling the character.
    def run(self, angle):
        if not self.running_jump:  # If the character is in a running jump they can't change direction.
            self.angle = angle
            if not self.state_is_continuous:  # Don't interrupt a one-time action e.g. catch.
                return
            self.state_is_continuous = True
            if self.has_ball:
                self.state = "run_ball"
            else:
                self.state = "run"
        # Ensure the character stays within the bounds.
        # If direction is right or x is greater than the left-most boundary.
        if math.cos(self.angle) > 0 or self.x > self.bounds[0][0]:
            # If direction is left or x is less than the right-most boundary.
            if math.cos(self.angle) < 0 or self.x < self.bounds[0][1]:
                # Use trig to get the amount x should be increased by.
                self.x += self.unit_x * math.cos(self.angle) * 30 / self.game.fps
        # If direction is up or x is greater than the bottom-most boundary.
        if math.sin(self.angle) > 0 or self.z > self.bounds[1][0]:
            # If direction is down or x is less than the top-most boundary.
            if math.sin(self.angle) < 0 or self.z < self.bounds[1][1]:
                # y and z are increase by the same amount because the player is staying on the ground.
                self.y += self.unit_y * math.sin(self.angle) * 30 / self.game.fps
                self.z += self.unit_y * math.sin(self.angle) * 30 / self.game.fps

    def jump(self):
        if self.state == "run":  # If the player is currently running, do a running jump.
            self.running_jump = True
        self.state_is_continuous = False
        self.state = "jump"

    def jump_movement(self):
        if self.running_jump:
            self.run(self.angle)
        if self.state_frames["jump"] > 1:  # Jump movement starts on the 3rd frame.
            # Increase height by a constantly decreasing amount.
            self.y += self.unit_y * (len(self.image_dict["jump"]) / 2 + 1 - self.state_frames["jump"]) * \
                      60 / self.game.fps

    def idle(self):
        if self.has_ball:
            self.state = "idle_ball"
        else:
            self.state = "idle"

    def pick_up(self):
        self.ball.midair = False
        self.state_is_continuous = False
        self.state = "pick_up"

    def catch(self):
        if not self.state_is_continuous:  # Don't interrupt anything.
            return
        self.state_is_continuous = False
        self.state = "catch"

    def light_throw(self):
        if not self.ball.midair and self.has_ball:
            self.state_is_continuous = False
            self.state = "light_throw"
            self.state_frames[self.state] = 0  # Resetting the frame allows feinting.
            self.has_ball = False

    def heavy_throw(self):
        if not self.ball.midair and self.has_ball:
            self.state_is_continuous = False
            self.state = "heavy_throw"
            self.state_frames[self.state] = 0
            self.has_ball = False

    def do_throw(self, throw_to_enemies=True, explosion=False):
        try:
            target_x, target_z = self.find_target(throw_to_enemies=throw_to_enemies)
        except TypeError:  # If no target is found.
            return
        if explosion:
            target_x *= -1  # Make the ball go into the player holding it.
        self.ball.color = (1, 1, 1, 1)
        self.ball.character = None
        throw_type = self.state
        self.ball.throwing_team = self.team
        self.ball.midair = True
        if not throw_to_enemies:
            self.ball.passed = True
        else:
            self.ball.passed = False
        self.ball.y = self.center_y
        self.ball.throw(target_x, target_z, throw_type)

    def pass_to_teammate(self):
        if len(self.teammates) > 1:
            self.has_ball = False
            self.ball.character = None
            self.do_throw(throw_to_enemies=False)

    # Update the lists of enemies and teammates.
    def update_enemies_and_teammates(self):
        for sprite in self.parent.parent.sprites:
            try:
                if sprite not in self.enemies and sprite not in self.teammates and sprite.health > 0:
                    if sprite.team == self.team:
                        self.teammates.append(sprite)
                    else:
                        self.enemies.append(sprite)
            except AttributeError:
                pass
        for group in self.enemies, self.teammates:
            for sprite in group:
                if sprite.health < 0:
                    group.remove(sprite)

    # Function finds the character (either enemy or teammate depending on the type of throw) whose angle from the
    # thrower is closest to the current/most recent angle made on the joystick.
    def find_target(self, throw_to_enemies=True):
        angle = math.pi * 2  # Start with just above the maximum angle.
        chosen_target = None
        if throw_to_enemies:
            target_list = self.enemies
        else:
            target_list = self.teammates
        for target in target_list:
            if target == self:
                continue
            dif_x = target.center_x - self.center_x
            dif_z = target.z - self.z
            target_angle = math.atan(dif_z / dif_x)
            # Have to sin and then asin self.angle to get the lowest version of the angle e.g. pi rad becomes 0 rad.
            angle_dif = abs(target_angle-math.asin(math.sin(self.angle)))
            if angle_dif < angle:
                angle = angle_dif
                chosen_target = target
        if chosen_target:
            return [chosen_target.center_x, chosen_target.z]

    # Return true if the ball is touching or is very close to the centre of the player.
    def collision(self):
        if math.isclose(self.ball.z, self.z, abs_tol=self.unit_x*5) and \
                math.isclose(self.ball.center_x, self.center_x, abs_tol=self.unit_x*10) and \
                self.y - self.z <= self.ball.y - self.ball.z < self.height:
            return True

    # Used for picking up rather than getting hit. Due to this, the ball must also be close to the ground.
    def floor_collision(self):
        if math.isclose(self.ball.y, self.ball.z, abs_tol=self.unit_x) and self.collision():
            return True

    # Method for changing the value and location of the healthbar.
    def update_healthbar(self):
        if self.health <= 0:
            self.base_bar.size = (0, 0)
            self.healthbar.size = (0, 0)
            self.selected_cursor_colour.a = 0
            self.color = [*self.color[:-1], float(self.color[-1]) - 1.5 / self.game.fps]  # Slowly fade away.
            if self.color[-1] <= 0 and not self.dead:
                for enemy in self.enemies:
                    try:
                        del enemy.enemies[enemy.enemies.index(self)]  # Remove self from enemy's enemy list.
                    except ValueError:
                        pass
                for teammate in self.teammates:
                    try:
                        del teammate.teammates[teammate.teammates.index(self)]
                    except ValueError:
                        pass
                self.dead = True
            if self.has_ball:
                self.ball.midair = True
                self.has_ball = False
                self.ball.color = (1, 1, 1, 1)
                self.ball.character = None
        else:
            health_width = self.width/200*self.health
            self.healthbar.size = (health_width, self.unit_y)
            self.healthbar.pos = (self.center_x-self.width/4, self.top+self.unit_y)
            self.base_bar.size = (self.width/2+self.unit_y/2, self.unit_y*3/2)
            self.base_bar.pos = (self.center_x-self.width/4-self.unit_y/4, self.top+self.unit_y*3/4)

    # Called when the ball hits the player.
    def hit(self):
        if self.state == "catch" and self.state_frames[self.state] < 6:  # If the player caught in time.
            self.ball.midair = False
            self.ball.throwing_team = None
            self.ball.passed = False
            self.has_ball = True
            self.ball.color = (0, 0, 0, 0)
            self.ball.character = self
            self.idle()
            return
        if self.color == [1, .3, .3, 1]:  # Prevent double hits
            return
        if self.ball.throw_type == "light_throw":
            self.health -= 20
        else:
            self.health -= 25
        self.ball.hit_player()
        self.color = (1, .3, .3, 1)  # Go red.
        Clock.schedule_once(lambda clock: set_color(self, (1, 1, 1, 1)), 0.25)  # Return to normal colour in 0.25 secs.
        if self.state != "jump":
            self.state = "hit"  # Don't interrupt the jump animation.
            self.state_is_continuous = False

    # Moves the selected cursor to above the player's head.
    def reposition_selected_cursor(self):
        self.selected_cursor.points = [self.center_x, self.top + self.unit_y * 2,
                                       self.center_x - 2 * self.unit_x, self.top + 5 * self.unit_y,
                                       self.center_x + 2 * self.unit_x, self.top + 5 * self.unit_y]
