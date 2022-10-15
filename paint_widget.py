from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line, Rotate, PushMatrix, PopMatrix
from collections import OrderedDict, deque
import math
from copy import copy


def rotate_button(button):
    with button.canvas.before:
        PushMatrix()  # Without push and pop matrix, the rotate function rotates all widgets.
        Rotate(angle=180, origin=button.center)
    with button.canvas:
        PopMatrix()


# Function used to round to the nearest something that's not a power of 10.
def specific_rounding(value, rounding_number, subtractor=0):
    # The rounding is done to the nearest rounding_number so if rounding_number = 4, rounding is done to the nearest 4.
    # This is because round(x / 4) * 4 rounds x the nearest 4. This is used in the program to round the touch position
    # to the nearest rectangle to be painted on. The subtractor is needed because the rounding needs to be done relative
    # to the position from the start of the widget but the value given is relative to the position of the screen.
    return round((value - subtractor) / rounding_number) * rounding_number + subtractor


# This is the canvas that the player draws on. Inherits the wiget class from kivy.
class PaintWidget(Widget):
    def __init__(self):
        super().__init__()
        self.register_event_type('on_draw')
        width = min(Window.width*0.45, Window.height*0.9)
        self.pos = ((Window.width-width)/2, (Window.height-width)/2)  # Set the widget's position based on its size.
        self.rect_width = int(width / 30)
        self.rounding_number = float(self.rect_width)  # The number things will be rounded to.
        self.size = (specific_rounding(width, self.rounding_number),
                     specific_rounding(width, self.rounding_number))
        self.tool = "pencil"  # Current tool in use is pencil.
        self.rects_colors = OrderedDict()  # An ordered dictionary containing the colours of each dot.
        self.undo_list = deque(maxlen=99)  # A list with a limit of 100 elements.
        self.redo_list = deque(maxlen=99)
        self.pencil_state = "pencil"  # Determines whether pencil button is in pencil or rubber mode.
        self.color = (1, 1, 1, 1)  # Initial colour is black.
        self.pencil_size = 1  # Number of rects drawn by a single tap of the pencil.
        with self.canvas:
            Rectangle(pos=self.pos, size=self.size)  # Create a background.
            Color(0, 0, 0)  # Set line color as black.
            # Make a grid.
            for i in range(int(self.y + self.rect_width), int(self.y + self.height), self.rect_width):
                Line(points=[self.x, i, self.x + self.width, i])
            for i in range(int(self.x + self.rect_width), int(self.x + self.width), self.rect_width):
                Line(points=[i, self.y, i, self.y + self.height])
            # Create all the dots and make them transparent.
            for pos_y in range(int(self.y), int(self.y + self.height), self.rect_width):
                for pos_x in range(int(self.x), int(self.x + self.width), self.rect_width):
                    # Ensure that the grid being made is 30x30.
                    if pos_y == int(self.y) + self.rect_width * 30 or pos_x == int(self.x) + self.rect_width * 30:
                        continue
                    self.rects_colors[(pos_x, pos_y)] = Color(0, 0, 0, 0)
                    Rectangle(pos=(pos_x, pos_y), size=(self.rect_width, self.rect_width))
        self.prev_touch = None

    def on_touch_down(self, touch):  # This method is called when the screen is touched.
        self.size = (round(Window.width * 0.4, -1), round(Window.height * 0.8, -1))  # Resets the size of the canvas.
        # Get the rounded pos
        pos = (specific_rounding(touch.x-self.rect_width/2.0, self.rounding_number, subtractor=self.x),
               specific_rounding(touch.y-self.rect_width/2.0, self.rounding_number, subtractor=self.y))
        if pos in self.rects_colors.keys():  # Ensure that the click was in the grid.
            if self.rects_colors[pos].rgba != self.color or self.tool == "rubber":
                if self.tool == "rubber" and self.rects_colors[pos].a == 0:
                    return
                self.redo_list.clear()
                self.parent.parent.update_undo_nums()
                if self.tool == "pencil":
                    self.pencil(pos)
                elif self.tool == "rubber":
                    self.pencil(pos, erase=True)
                else:
                    self.undo_list.append(self.copy_rects_colors())
                    self.fill(pos, self.rects_colors[pos].rgba)

    def on_touch_move(self, touch):  # This method is called when the player holds down and moves their finger.
        # Kivy's drag detection struggles with quick movements. What happens is that there is a large gap between two
        # touches. This results in large blank spaces on the canvas between two squares drawn in. I have to simulate
        # touches between the previous touch and the current touch.
        if self.prev_touch:
            if self.prev_touch.opos == touch.opos:  # If the previous touch was part of the same drag as this touch.
                # Find the distance between the previous touch and the current touch using Pythagoras.
                dist = math.sqrt((touch.x-self.prev_touch.x)**2 + (touch.y-self.prev_touch.y)**2)
                # The simulated touches will be self.rect_width/2 apart.
                # If the distance is less than this, we don't need simulated touches.
                if dist > self.rect_width / 2:
                    # Find the angle between the previous touch and the current touch.
                    angle = math.atan2((touch.y-self.prev_touch.y), (touch.x-self.prev_touch.x))
                    count = int(dist // (self.rect_width/2))  # The number of simulated touches needed.
                    x_increment = self.rect_width/2 * math.cos(angle)
                    y_increment = self.rect_width/2 * math.sin(angle)
                    for i in range(count):
                        # self.on_touch_down takes a touch object as a parameter and uses the x and y properties of the
                        # touch object. We need to create a fake object with these properties to call the function.
                        new_touch = type('new_touch', (object,), {'x': self.prev_touch.x + x_increment * i,
                                                                  'y': self.prev_touch.y + y_increment * i})()
                        self.on_touch_down(new_touch)
        self.on_touch_down(touch)
        self.prev_touch = copy(touch)  # Have to copy it so it doesn't get overwritten by the next call.

    def set_tool(self, button, other_button, tool):
        if tool == "pencil" and self.tool != "fill":  # If the player clicks on pencil while pencil/rubber is active.
            if self.tool == "pencil":
                self.tool = "rubber"
            else:
                self.tool = "pencil"
            rotate_button(button)
            self.pencil_state = self.tool
        elif tool == "pencil" and self.tool == "fill":  # If the player clicks on pencil while fill is active.
            self.tool = self.pencil_state  # Switch self.tool to whatever mode the pencil was in (either pencil/rubber).
        else:
            self.tool = tool
        button.color = (.5, .5, .5, 1)
        other_button.color = (1, 1, 1, 1)

    def set_pencil(self, button, other_buttons, size):  # Used to set the dot size of the pencil.
        self.pencil_size = size
        button.color = (.5, .5, .5, 1)
        for other_button in other_buttons:
            other_button.color = (1, 1, 1, 1)

    def set_color(self, color):
        self.color = color  # Sets self.color as the colour picked by the player on the ColorPicker widget.

    def pencil(self, pos, erase=False, color=None):
        # Nested loops to create a square with height and width pencil_size.
        if not color:
            color = self.color
        self.undo_list.append({})
        for x in range(self.pencil_size):
            for y in range(self.pencil_size):
                # If the current pos is out of bounds, skip to the next pos.
                if (pos[0]+self.rect_width*x, pos[1]+self.rect_width*y) not in self.rects_colors.keys():
                    continue
                self.undo_list[-1][(pos[0]+self.rect_width*x, pos[1]+self.rect_width*y)] = \
                    self.rects_colors[(pos[0]+self.rect_width*x, pos[1]+self.rect_width*y)].rgba
                if erase:
                    # Makes the rectangle at pos transparent.
                    self.rects_colors[(pos[0]+self.rect_width*x, pos[1]+self.rect_width*y)].rgba = (0, 0, 0, 0)
                else:
                    self.draw((pos[0]+self.rect_width*x, pos[1]+self.rect_width*y), color)  # Call the draw method.

    def draw(self, pos, color):
        self.rects_colors[pos].rgba = color  # Makes the rectangle at pos have self.color as its color.
        self.dispatch("on_draw")

    def on_draw(self):  # This is an event that is dispatched when a pixel is drawn.
        pass

    def fill(self, pos, init_color, color=None):
        if not color:
            color = self.color
        if pos not in self.rects_colors.keys():  # If the current pos is out of bounds.
            return
        if init_color == color:  # If the rectangle is already the desired colour.
            return
        # If the rectangle is a different colour to the first rectangle that was clicked on.
        if self.rects_colors[pos].rgba != init_color:
            return
        self.draw(pos, color)  # Fill in that rectangle.
        # Repeat the function with the next rectangle to the left, right, up and down.
        self.fill((pos[0]+self.rect_width, pos[1]), init_color, color=color)
        self.fill((pos[0]-self.rect_width, pos[1]), init_color, color=color)
        self.fill((pos[0], pos[1]+self.rect_width), init_color, color=color)
        self.fill((pos[0], pos[1]-self.rect_width), init_color, color=color)

    def undo(self, button, other_button, start_list, end_list):  # If button is undo, other_button is redo etc.
        if start_list:
            temp_rects_colors = start_list.pop()
            end_list.append({})
            for pos in temp_rects_colors:
                end_list[-1][pos] = self.rects_colors[pos].rgba
                self.rects_colors[pos].rgba = temp_rects_colors[pos]
            other_button.color = (1, 1, 1, 1)
        if not start_list:
            button.color = (.7, .7, 0, 1)
        self.parent.parent.update_undo_nums()

    def copy_rects_colors(self):  # Used to copy the colours of self.rects_colors and returning the result.
        temp_rects_colors = {}
        for pos in self.rects_colors:
            temp_rects_colors[pos] = self.rects_colors[pos].rgba
        return temp_rects_colors
