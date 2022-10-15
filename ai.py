from character import Character
import math
import random
from numpy.random import normal


# Inherits the Character class. Adds computer-controlled functionality to the Character.
class AI(Character):
    def __init__(self, image_dict, ball, team):
        super().__init__(image_dict, ball, team)  # Initialise the parent class (Character) to get the same attributes.
        self.current_angle = math.radians(random.randint(0, 360))  # Start off with a random angle
        self.walk_tick = 0
        self.acted = False
        self.thrown = False
        self.prev_angle = 0

    # Called every tick of the game.
    def update(self):
        if not self.selected:  # If the character is selected, ignore all the additional AI methods.
            self.run()
            self.defend()
            self.random_throw()
        super().update()

    # Overrides the run method of Character. Will generate an angle based on the circumstances and then call the
    # overridden run method with the generated angle.
    def run(self, angle=None):
        if not self.selected:  # Ignore the overridden section if the character is selected.
            # First find the x and z distances of the character to the ball.
            dif_x = self.center_x - self.ball.x
            dif_z = self.z - self.ball.z
            angle = self.get_angle(dif_z, dif_x)  # Get the angle from the character to the ball.
            if not self.ball.throwing_team or self.ball.throwing_team == self.team:  # If the ball hasn't been thrown.
                self.thrown = False
            # If the ball has been thrown by the opponent
            if self.ball.throwing_team and self.ball.throwing_team != self.team:
                if self.thrown:  # If the angle has already been generated, don't create a new angle.
                    angle = self.prev_angle
                else:
                    # Find the direction the ball is travelling.
                    ball_angle = self.get_angle(self.ball.z_speed, self.ball.x_speed)
                    # We want the AI to try to move away from the ball. The best way to do this is to move perpendicular
                    # to the ball's direction of travel. However, this is not realistic and the AIs will all move in the
                    # same/opposite directions. Instead, the AI should move perpendicular to the thrower. However,
                    # this still has the possibility that the ball is thrown to a different player and the AI runs into
                    # the ball. To prevent this, the AI will run perpendicular to the thrower in the way that moves away
                    # from the ball.
                    if angle < ball_angle:
                        angle -= math.pi / 2
                    else:
                        angle += math.pi / 2
                    self.prev_angle = angle
                    self.thrown = True
            elif self.ball.character or not self.bounds[0][0] + self.width / 10 < self.ball.x < \
                    self.bounds[0][1] + self.width:  # If someone has the ball or the ball is in the other side.
                angle = self.random_angle()
            else:  # This means that the ball is on the AI's side and no-one has picked it up
                distance = math.sqrt(dif_x ** 2 + dif_z ** 2)  # Get the distance to the ball
                counter = 0
                for sprite in self.teammates:
                    if math.sqrt((sprite.center_x - sprite.ball.x) ** 2 + (sprite.z - sprite.ball.z) ** 2) < \
                            distance:  # If the teammate is closer to the ball than the AI
                        if counter == 1:  # If two teammates are closer then move randomly
                            angle = self.random_angle()
                        else:
                            counter += 1
                if dif_x > 0:
                    angle += math.pi  # The angle was away from the ball before now it is towards the ball.
        super().run(angle)  # Call the original run function with the generated angle.

    # Generate a random angle but not every tick since this would just make the AI vibrate in place
    def random_angle(self):
        # walk_tick is incremented every tick so it has to be divided by the fps to get a constant time.
        if self.walk_tick * 30 / self.game.fps < random.randint(10, 15):
            self.walk_tick += 1
        else:  # If the AI has run in the same direction for long enough.
            # We want the AIs to run randomly but weighted towards the back of their half.
            mean = 0
            # For team 1, pi radians as the angle is towards the back of their half whereas 0 is for team 2
            if self.team == 1:
                mean = math.pi
            self.current_angle = normal(mean, math.pi/2)  # Use the normal distribution with standard deviation as pi/2
            self.walk_tick = 0  # Reset the walk timer.
        return self.current_angle

    # Jump, catch or do nothing. Only do the action once per throw
    def defend(self):
        if self.ball.throwing_team and self.ball.throwing_team != self.team:
            if not self.acted:
                dif_x = self.center_x - self.ball.x
                dif_z = self.z - self.ball.z
                angle = self.get_angle(dif_z, dif_x)
                ball_angle = self.get_angle(self.ball.z_speed, self.ball.x_speed)
                if math.sqrt(dif_x ** 2 + dif_z ** 2) < self.width * 2:  # If the ball is close to the AI
                    if abs(angle - ball_angle) < 0.1:  # If the ball is going towards the AI
                        chance = random.randint(0, 2)  # 1/3 chance for each action
                        if chance == 0:
                            super().jump()
                        elif chance == 1:
                            super().catch()
                    self.acted = True
        else:
            self.acted = False  # Reset once the ball is no longer in midair.

    @staticmethod
    def get_angle(a, b):
        try:
            angle = math.atan(a / b)
        except ZeroDivisionError:  # If b is zero set angle as a right angle (pi/2 radians)
            angle = math.pi / 2
        return angle

    def random_throw(self):
        if self.has_ball and random.randint(0, self.game.fps) < 3:  # Only do sometimes when the character has the ball.
            chance = random.randint(0, 2)
            if chance < 1:
                super().light_throw()
            elif chance < 2:
                super().heavy_throw()
            else:
                super().pass_to_teammate()
