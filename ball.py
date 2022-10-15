from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Rectangle
import math
from random import randint
import time
from os.path import isfile


# Class for the ball. Inherits the Image class from kivy.
class Ball(Image):
    def __init__(self, surface):
        super().__init__()
        self.size_hint = (None, None)
        self.pos = (Window.width / 2, Window.height / 2)  # Start in the middle
        self.z = Window.height / 3
        self.x_speed = randint(int(self.width * -0.5), int(self.width * .5))  # Have a random x_speed
        self.y_speed = 0
        self.z_speed = 0
        self.speed = 0
        # Get the friction constant from the surface
        self.surface_friction = float(surface[surface.index("[") + 1:surface.index("]")])
        self.completion_ticks = 10
        self.throwing_team = None  # This is the team that the ball was thrown by
        self.character = None  # The character holding the ball
        self.midair = True
        self.has_bounced = False
        self.rolling = False
        self.passed = False
        self.throw_type = None
        self.source = "Images/ball.png"
        self.size = (Window.width / 35, Window.height / 20)
        self.timer = time.time()

    # Called every tick of the game
    def update(self):
        self.x += self.x_speed
        self.z += self.z_speed
        self.y += self.y_speed
        self.speed = math.sqrt(
            (self.x_speed / self.width) ** 2 + (self.z_speed / self.height) ** 2) * 30 / self.game.fps  # Pythagoras
        self.bounce()
        if self.character:
            self.rolling = False
            self.passed = False
        if self.rolling:
            # x_speed and z_speed are multiplied by surface_friction every tick. With a high fps, this would make
            # them decrease more rapidly since there are more ticks. Therefore, surface friction must be
            # exponentiated by a constant over the fps.
            self.x_speed *= self.surface_friction ** (30 / self.game.fps)
            self.z_speed *= self.surface_friction ** (30 / self.game.fps)
        if self.midair:
            # Since y_speed is subtracted from rather than multiplied by, the fps only has to multiply the constant.
            self.y_speed -= (self.height * 30 / self.game.fps) / self.completion_ticks  # Gravity
        else:
            self.y_speed = self.z_speed  # Make the ball's vertical speed 0
            if not self.character:
                self.y = self.z  # Make the ball on the ground.
        self.hot_potato()

    # Called when a character throws the ball
    def throw(self, target_x, target_z, throw_type):
        distance = math.sqrt((target_x - self.x) ** 2 + (target_z - self.z) ** 2)  # Pythagoras theorem.
        total_speed = self.width * 60 / self.game.fps  # Set the speed as a constant.
        self.throw_type = throw_type
        if throw_type == "heavy_throw":  # Increase the speed if it's a heavy throw, decrease it if it's a pass.
            total_speed *= 1.5
        if self.passed:
            total_speed *= 0.5
        self.completion_ticks = distance / total_speed  # Work out how many ticks it will take to reach the target.
        # Work out the separate x and z components of the speed based on the x and z distances and the number of ticks.
        self.x_speed = (target_x - self.x) / self.completion_ticks
        self.z_speed = (target_z - self.z) / self.completion_ticks
        # self.height / 4 makes the trajectory look more realistic.
        self.y_speed = self.z_speed + (self.height / 4) * 30 / self.game.fps
        if throw_type == "light_throw":  # Make the trajectory more looping for light_throw.
            self.y_speed += (self.height / 4) * 30 / self.game.fps

    def bounce(self):
        if self.y < self.z < Window.height * .65:  # If the ball is touching the ground.
            # If the ball bounced last frame and is still going downwards i.e. the ball is very slow.
            if self.has_bounced and self.y_speed < self.z_speed:
                self.passed = False
                self.midair = False
                self.y_speed = self.z_speed
                self.y = self.z
                self.rolling = True
                return
            self.has_bounced = True
            self.throwing_team = None  # Once the ball has bounced, it doesn't do damage.
            self.x_speed *= self.surface_friction  # Doesn't have to be exponentiated by fps since it only happens once.
            self.z_speed *= self.surface_friction
            # Multiply the vertical speed by friction and then take it away from the z_speed.
            self.y_speed = self.z_speed - self.surface_friction * (self.y_speed - self.z_speed)
            self.y += self.y_speed
        else:
            self.has_bounced = False
        if self.z < 0 or self.z > Window.height * .64:  # If the ball has hit the upper or lower boundaries.
            self.z_speed *= -.8
            self.y_speed = self.z_speed + .8 * (self.y_speed + self.z_speed)
            self.z += self.z_speed
        if self.x < 0 or self.x > Window.width - self.width:  # If the ball has hit the left or right boundaries.
            self.x_speed *= -.8
            self.x += self.x_speed

    # Called when the ball hits a player.
    def hit_player(self):
        self.x_speed *= -.7
        self.y_speed *= .7
        self.z_speed *= .7
        self.throwing_team = None
        self.update()

    # If a team is time-wasting with the ball, the ball will explode, damaging them.
    def hot_potato(self):
        if self.midair and not self.passed:  # Reset timer whenever the ball is thrown.
            self.timer = time.time()
        if time.time() - self.timer > 7:  # After 7 seconds, explode.
            self.explode()
            self.timer = time.time()  # Reset timer.

    def explode(self):
        if self.character:
            self.character.do_throw(explosion=True)
        else:
            self.midair = True
            self.rolling = False
            self.throw(Window.width - self.center_x, randint(0, int(Window.height/3)), "light_throw")
            self.y_speed += self.height * 10 / self.game.fps  # Give a slight boost to the ball's vertical speed.
        if self.center_x < Window.width / 2:  # Set the throwing team as the team on the other side.
            self.throwing_team = 2
        else:
            self.throwing_team = 1
        # Animate the explosion
        self.explosion_animation()

    # Recursive function for animating the explosion.
    def explosion_animation(self, counter=1, explosion=None):
        if not explosion:
            with self.canvas:
                explosion = Rectangle(source="Explosion/1.png", width=self.width*2, height=self.height*2, pos=self.pos)
        if isfile("Explosion/" + str(counter) + ".png"):
            explosion.source = "Explosion/" + str(counter) + ".png"
            # Animate the next frame in 0.025 seconds.
            Clock.schedule_once(lambda clock: self.explosion_animation(counter=counter+1, explosion=explosion), .025)
        else:  # Once all the images have been animated, remove the explosion.
            self.canvas.remove(explosion)
