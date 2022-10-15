from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.graphics import Rectangle, Color, Line
from kivy.core.window import Window
from misc import ImageButton, switch
from image_editing import get_info


# This is the screen for changing the controls of the game. The user can change the size, opacity and colours of the
# buttons and joysticks. Inherits the Screen class from kivy.
class ControlsChanger(Screen):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.config = get_info("config.ini", character=False)
        with self.canvas:
            self.background = Rectangle(source="Images/[0.7]background_mud.png", size=Window.size)
        restart_confirmation = ImageButton(source="Images/cancel_text.png")
        restart_confirmation.bind(on_press=self.cancel)
        set_to_default = ImageButton(source="Images/set_to_default.png")
        set_to_default.bind(on_press=self.set_to_default)
        restart_grid_layout = GridLayout(cols=1)
        restart_grid_layout.add_widget(restart_confirmation)
        restart_grid_layout.add_widget(set_to_default)
        restart_popup = Popup(pos_hint={"x": .3, "y": .35}, size_hint=(.4, .3),
                              content=restart_grid_layout, title="")
        restart_button = ImageButton(pos_hint={"x": .9375, "y": .875}, size_hint=(0.05, 0.1),
                                     source="Images/cancel.png")
        restart_button.bind(on_press=lambda button: restart_popup.open())
        save = ImageButton(pos_hint={"x": .0125, "y": .875}, size_hint=(0.05, 0.1), source="Images/save.png")
        save.bind(on_press=lambda button: self.save())
        color_picker = ColorPicker(pos_hint={"x": .5, "y": .6}, size_hint=(.2, .4))
        color_picker.children[0].remove_widget(color_picker.children[0].children[1])
        color_picker.bind(color=lambda picker, color: self.set_color(color))
        self.scale_slider = Slider(min=.5, max=2, value=1, cursor_size=(Window.width*.025, Window.width*.025),
                                   background_width=Window.width*.05)
        self.scale_slider.bind(on_touch_move=lambda slider, touch: self.slider_touched(slider, "scale"))
        self.scale_slider.bind(on_touch_down=lambda slider, touch: self.slider_touched(slider, "scale"))
        self.alpha_slider = Slider(min=0, max=1, value=.7, cursor_size=(Window.width*.025, Window.width*.025),
                                   background_width=Window.width*.05)
        self.alpha_slider.bind(on_touch_down=lambda slider, touch: self.slider_touched(slider, "alpha"))
        self.alpha_slider.bind(on_touch_move=lambda slider, touch: self.slider_touched(slider, "alpha"))
        slider_layout = GridLayout(rows=2, cols=1, pos_hint={"x": .2, "y": .775}, size_hint=(.2, .2))
        slider_layout.add_widget(self.scale_slider)
        slider_layout.add_widget(self.alpha_slider)
        # The kivy ScatterLayout widgets are used for the buttons and joystick because it allows enlargement.
        button_1_scatter = ScatterLayout(do_rotation=False, do_scale=False, do_translation=False, id="button_1",
                                         pos=(float(self.config["button_1_pos"][0])*Window.width,
                                              float(self.config["button_1_pos"][1])*Window.height),
                                         size_hint=self.config["button_1_size"])
        button_1_scatter.add_widget(Image(source="Images/circle.png", color=self.config["button_1_color"],
                                          size_hint=(1, 1)))
        button_2_scatter = ScatterLayout(do_rotation=False, do_scale=False, do_translation=False, id="button_2",
                                         pos=(float(self.config["button_2_pos"][0]) * Window.width,
                                              float(self.config["button_2_pos"][1]) * Window.height),
                                         size_hint=self.config["button_2_size"])
        button_2_scatter.add_widget(Image(source="Images/circle.png", color=self.config["button_2_color"],
                                          size_hint=(1, 1)))
        button_3_scatter = ScatterLayout(do_rotation=False, do_scale=False, do_translation=False, id="button_3",
                                         pos=(float(self.config["button_3_pos"][0]) * Window.width,
                                              float(self.config["button_3_pos"][1]) * Window.height),
                                         size_hint=self.config["button_3_size"])
        button_3_scatter.add_widget(Image(source="Images/circle.png", color=self.config["button_3_color"],
                                          size_hint=(1, 1)))
        joystick_scatter = ScatterLayout(do_rotation=False, do_scale=False, do_translation=False, id="joystick",
                                         pos=(float(self.config["joystick_pos"][0]) * Window.width,
                                              float(self.config["joystick_pos"][1]) * Window.height),
                                         size_hint=self.config["joystick_size"], auto_bring_to_front=False)
        joystick_scatter.add_widget(Image(source="Images/circle.png", color=[0, 0, 0, .3],
                                          size_hint=(.6, .6), pos_hint={"center_x": .5, "center_y": .5}))
        joystick_scatter.add_widget(Image(source="Images/circle.png", color=self.config["joystick_color"],
                                          size_hint=(.4, .4), pos_hint={"center_x": .5, "center_y": .5}))
        float_layout = FloatLayout()
        self.add_widget(float_layout)
        float_layout.add_widget(restart_button)
        float_layout.add_widget(save)
        float_layout.add_widget(color_picker)
        float_layout.add_widget(slider_layout)
        self.scatters = [joystick_scatter, button_1_scatter, button_2_scatter, button_3_scatter]
        for scatter in self.scatters:
            float_layout.add_widget(scatter)
            scatter.outline_color = Color(1, 1, 1, 0)
            scatter.outline = Line(close=True)
            scatter.canvas.add(scatter.outline_color)
            scatter.canvas.add(scatter.outline)
        self.selected_scatter = None

    def cancel(self, button):
        if button:
            button.parent.parent.parent.parent.dismiss()
            button.parent.clear_widgets()
        switch("Main Menu", self.manager, "right")
        self.manager.remove_widget(self)

    # Called when the user touches the screen.
    def on_touch_down(self, touch):
        scatter_touched = False
        for scatter in self.scatters:
            if scatter.collide_point(*touch.pos):  # If the user touched the scatter.
                self.selected_scatter = scatter
                scatter.outline.points = (0, 0, 0, scatter.height, scatter.width, scatter.height, scatter.width, 0)
                scatter.outline_color.a = 1
                scatter_touched = True
                self.scale_slider.value = self.selected_scatter.scale
                self.alpha_slider.value = self.selected_scatter.children[0].children[0].color[-1]
        for scatter in self.scatters:
            if scatter != self.selected_scatter and scatter_touched:  # Make the outline invisible if not selected.
                scatter.outline_color.a = 0
        if not scatter_touched:  # This is required so that touch still works for buttons and the colour wheel.
            super().on_touch_down(touch)

    # Called when the user drags their finger after touching the screen.
    def on_touch_move(self, touch):
        # Make sure the scatter doesn't go above a certain point unless it is the joystick.
        if self.selected_scatter and (touch.y + self.selected_scatter.height *
                                      self.selected_scatter.scale/2 < Window.height*.6 or
                                      len(self.selected_scatter.children[0].children) == 2) \
                and (self.selected_scatter.collide_point(*touch.opos) or touch.id == 1):
            touch.id = 1
            self.selected_scatter.pos = (touch.x-self.selected_scatter.width*self.selected_scatter.scale/2,
                                         touch.y-self.selected_scatter.height*self.selected_scatter.scale/2)

    def slider_touched(self, slider, slider_type):
        if self.selected_scatter:
            if slider_type == "scale":
                self.selected_scatter.scale = slider.value
            elif slider_type == "alpha":
                self.selected_scatter.children[0].children[0].color[-1] = slider.value

    def set_color(self, color):
        if self.selected_scatter:
            # Change only the rgb values.
            self.selected_scatter.children[0].children[0].color[0:3] = color[0:3]

    def save(self):
        for scatter in self.scatters:
            self.config[scatter.id + "_pos"] = (scatter.x / Window.width, scatter.y / Window.height)
            self.config[scatter.id + "_size"] = list(map(lambda x: x*scatter.scale, scatter.size_hint))
            self.config[scatter.id + "_color"] = scatter.children[0].children[0].color
        with open("config.ini", "w") as config:
            config_list = []
            for key in self.config.keys():
                config_list.append(key + "\n" + ";".join(map(str, self.config[key])))
            config.write("\n".join(config_list))
        Popup(pos_hint={"x": .3, "y": .35}, size_hint=(.4, .3),
              content=Image(source="Images/saved.png"), title="").open()
        switch("Main Menu", self.manager, "right")

    def set_to_default(self, button):
        self.cancel(button)
        with open("config.ini", "w") as config:
            with open("default_config.ini", "r") as default_config:
                config.write(default_config.read())
