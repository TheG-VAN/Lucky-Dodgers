from kivy.uix.screenmanager import Screen, NoTransition, SlideTransition
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.core.window import Window
from paint_widget import PaintWidget
from gallery import Gallery
from misc import ImageButton, Menu, get_characters, switch
from os.path import isfile
import image_editing
import pickle


# This is the screen for creating new characters. Inherits the Screen class from kivy.
class CreationStation(Screen):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.character = ""
        self.section_colors = {"skin_colour": None, "top_colour": None, "bottoms_colour": None, "shoe_colour": None}
        self.section_locations = None
        self.start_layout = FloatLayout()  # Layout that will show before a character is selected
        start_guide = Image(pos_hint={"x": .1, "y": .75}, size_hint=(0.8, 0.2), source="Images/pick_char.png")
        characters = get_characters()
        character_picker = GridLayout(pos_hint={"x": .05, "y": .05}, size_hint=(0.9, 0.75), rows=1)
        for character in characters:  # Create an ImageButton for each character
            # Only create a button if the character is pre-made.
            if not isfile("Images/" + character + "/section_locations.pickle"):
                continue
            character_picker.add_widget(ImageButton(source=characters[character],
                                                    on_press=self.set_character))
        self.start_layout.add_widget(start_guide)
        self.start_layout.add_widget(character_picker)
        self.float_layout = FloatLayout()
        self.drawing_canvas = PaintWidget()
        self.drawing_canvas.bind(on_draw=lambda canvas: self.on_draw(used_colors_layout, color_picker.color,
                                                                     color_picker))
        menu = Menu("left")
        pencil = ImageButton(pos_hint={"x": .05, "y": .6}, size_hint=(0.1, 0.1),
                             source="Images/pencil.png", color=(.5, .5, .5, 1))
        pencil.bind(on_press=lambda button: self.drawing_canvas.set_tool(button, fill, "pencil"))
        fill = ImageButton(pos_hint={"x": .15, "y": .6}, size_hint=(0.1, 0.1), source="Images/fill.png")
        fill.bind(on_press=lambda button: self.drawing_canvas.set_tool(button, pencil, "fill"))
        color_picker = ColorPicker(pos_hint={"x": .75, "y": .1}, size_hint=(0.2, 0.6), color=(0, 0, 0, 1))
        # Get rid of the values and sliders on the box above the color wheel
        color_picker.children[0].children[1].clear_widgets()
        # Add an image to the box above the color wheel
        color_picker.children[0].children[1].add_widget(Image(source="Images/current_colour.png"))
        # When color changes, call the set color function of the drawing canvas
        color_picker.bind(color=lambda picker, color: self.drawing_canvas.set_color(color))
        small_pencil = ImageButton(pos_hint={"x": .05, "y": .45}, size_hint=(0.05, 0.1),
                                   source="Images/small_pencil.png", color=(.5, .5, .5, 1))
        small_pencil.bind(on_press=lambda button: self.drawing_canvas.set_pencil(button, [medium_pencil,
                                                                                 large_pencil], 1))
        medium_pencil = ImageButton(pos_hint={"x": .125, "y": .45}, size_hint=(0.05, 0.1),
                                    source="Images/medium_pencil.png")
        medium_pencil.bind(on_press=lambda button: self.drawing_canvas.set_pencil(button, [small_pencil,
                                                                                  large_pencil], 2))
        large_pencil = ImageButton(pos_hint={"x": .2, "y": .45}, size_hint=(0.05, 0.1),
                                   source="Images/large_pencil.png")
        large_pencil.bind(on_press=lambda button: self.drawing_canvas.set_pencil(button, [small_pencil,
                                                                                 medium_pencil], 3))
        used_colors_layout = GridLayout(pos_hint={"x": .05, "y": .1}, size_hint=(0.2, 0.3), cols=3, spacing=[10, 10])
        save = ImageButton(pos_hint={"x": .9375, "y": .025}, size_hint=(0.05, 0.1), source="Images/save.png")
        save.bind(on_press=lambda button: saving_popup.open())
        save.bind(on_release=lambda button: self.on_save(self.character, self.drawing_canvas.rects_colors,
                                                         self.section_colors, save_popup, saving_popup))
        preview_button = ImageButton(pos_hint={"x": .05, "y": .75}, size_hint=(0.2, 0.1), source="Images/preview.png")
        preview_button.bind(on_press=lambda button: self.get_preview(paint_mode, preview_mode, preview,
                                                                     self.drawing_canvas.rects_colors))
        self.undo_button = ImageButton(pos_hint={"x": .1, "y": .875}, size_hint=(0.05, 0.1),
                                       source="Images/undo.png", color=(.7, .5, .2, 1))
        self.undo_button.bind(on_press=lambda button: self.drawing_canvas.undo(button, self.redo_button,
                                                                               self.drawing_canvas.undo_list,
                                                                               self.drawing_canvas.redo_list))
        self.redo_button = ImageButton(pos_hint={"x": .16, "y": .875}, size_hint=(0.05, 0.1),
                                       source="Images/redo.png", color=(.7, .5, .2, 1))
        self.redo_button.bind(on_press=lambda button: self.drawing_canvas.undo(button, self.undo_button,
                                                                               self.drawing_canvas.redo_list,
                                                                               self.drawing_canvas.undo_list))
        self.undo_num = Label(pos_hint={"x": .11, "y": .89}, size_hint=(0.01, 0.02),
                              text=str(len(self.drawing_canvas.undo_list)), color=(0, 0, 0, 1),
                              font_name="pixel_font.otf", font_size=Window.height * 0.02)
        self.redo_num = Label(pos_hint={"right": .2, "y": .89}, size_hint=(0.01, 0.02),
                              text=str(len(self.drawing_canvas.redo_list)), color=(0, 0, 0, 1),
                              font_name="pixel_font.otf", font_size=Window.height * 0.02)
        restart_confirmation = ImageButton(source="Images/restart.png")
        restart_confirmation.bind(on_press=self.restart)
        restart_popup = Popup(pos_hint={"x": .3, "y": .35}, size_hint=(.4, .3),
                              content=restart_confirmation, title="")
        restart_button = ImageButton(pos_hint={"x": .9375, "y": .875}, size_hint=(0.05, 0.1),
                                     source="Images/cancel.png")
        restart_button.bind(on_press=lambda button: restart_popup.open())
        gallery_button = ImageButton(pos_hint={"x": .75, "y": .75}, size_hint=(.2, .1), source="Images/gallery.png")
        gallery_button.bind(on_press=lambda button: switch("Gallery", self.manager, "up", screen_type=Gallery))
        preview = Image(pos_hint={"center_x": .5, "y": .05}, size_hint=(0.4, 0.8))
        draw = ImageButton(pos_hint={"x": .05, "y": .75}, size_hint=(0.2, 0.1), source="Images/draw.png")
        draw.bind(on_press=lambda button: self.toggle_mode(preview_mode, paint_mode))
        skin_color = ImageButton(pos_hint={"x": .05, "y": .65}, size_hint=(0.2, 0.1), source="Images/skin_colour.png")
        skin_color.bind(on_press=lambda button: self.change_color("skin_colour", color_picker.color,
                                                                  preview, self.drawing_canvas.rects_colors,
                                                                  used_colors_layout, color_picker.color, color_picker))
        top_color = ImageButton(pos_hint={"x": .05, "y": .57}, size_hint=(0.2, 0.1), source="Images/top_colour.png")
        top_color.bind(on_press=lambda button: self.change_color("top_colour", color_picker.color,
                                                                 preview, self.drawing_canvas.rects_colors,
                                                                 used_colors_layout, color_picker.color, color_picker))
        bottoms_color = ImageButton(pos_hint={"x": .05, "y": .49}, size_hint=(0.2, 0.1),
                                    source="Images/bottoms_colour.png")
        bottoms_color.bind(on_press=lambda button: self.change_color("bottoms_colour", color_picker.color,
                                                                     preview, self.drawing_canvas.rects_colors,
                                                                     used_colors_layout, color_picker.color,
                                                                     color_picker))
        shoe_color = ImageButton(pos_hint={"x": .05, "y": .41}, size_hint=(0.2, 0.1), source="Images/shoe_colour.png")
        shoe_color.bind(on_press=lambda button: self.change_color("shoe_colour", color_picker.color,
                                                                  preview, self.drawing_canvas.rects_colors,
                                                                  used_colors_layout, color_picker.color, color_picker))
        save_popup = Popup(pos_hint={"x": .3, "y": .35}, size_hint=(.4, .3),
                           content=Image(source="Images/saved.png"), title="")
        saving_popup = Popup(pos_hint={"x": .3, "y": .35}, size_hint=(.4, .3),
                             content=Image(source="Images/saving.png"), title="")
        paint_mode = [self.drawing_canvas, menu, pencil, fill, color_picker, small_pencil, preview_button, save,
                      self.undo_button, self.redo_button, gallery_button, medium_pencil, large_pencil,
                      used_colors_layout, restart_button, self.undo_num, self.redo_num]
        preview_mode = [color_picker, used_colors_layout, save, preview, restart_button,
                        draw, skin_color, top_color, bottoms_color, shoe_color, menu, gallery_button]
        self.add_widget(self.start_layout)
        self.start_layout.add_widget(Menu("left"))
        for widget in paint_mode:
            self.float_layout.add_widget(widget)

    def set_character(self, character):
        self.character = character.source.split("/")[1]
        self.remove_widget(self.start_layout)
        self.add_widget(self.float_layout)
        with open("Images/" + self.character + "/section_locations.pickle", "rb") as char_file:
            # Load the serialised dictionary into self.section_locations
            self.section_locations = pickle.load(char_file)

    def toggle_mode(self, current_mode, next_mode):
        for widget in current_mode:
            self.float_layout.remove_widget(widget)
        for widget in next_mode:
            self.float_layout.add_widget(widget)

    def get_preview(self, current_mode, next_mode, preview, drawing):
        image_editing.main(self.character, drawing, self.section_colors, self.section_locations, preview=True)
        preview.source = "Images/preview_image.png"
        preview.reload()  # This is need to update the image because the source didn't change.
        self.toggle_mode(current_mode, next_mode)

    def change_color(self, section, new_color, preview, drawing, colors_layout, color, color_picker):
        if self.section_colors[section] == new_color:  # If the requested color is already the section color, return.
            return
        # Have to add the [:] so it is a copy, otherwise the section color changes whenever new_color changes
        # This leads to all the sections having the same color at all times
        self.color_used(colors_layout, color, color_picker)
        self.section_colors[section] = new_color[:]
        image_editing.main(self.character, drawing, self.section_colors, self.section_locations, preview=True)
        preview.reload()  # This is need to update the image because the source didn't change.

    def on_save(self, old_character_name,  replacement_drawing, section_colors, save_popup, saving_popup):
        image_editing.main(old_character_name, replacement_drawing, section_colors, self.section_locations)
        saving_popup.dismiss()
        save_popup.open()
        if not self.manager.has_screen("Gallery"):
            self.manager.add_widget(Gallery(name="Gallery"))
        self.manager.get_screen("Gallery").changes_made = True

    def restart(self, button=None):
        if button:
            # Kivy popups contain a grid layout then a box layout and then the content so 3 parent levels are needed
            button.parent.parent.parent.dismiss()
            # This is here because otherwise it is possible to double press the button which causes an error
            button.parent.remove_widget(button)
        manager = self.manager
        manager.transition = NoTransition()
        manager.remove_widget(self)  # Remove this screen
        # Create a fresh new screen (python garbage collection makes sure the old screen doesn't use up any memory so
        # you can restart as much as wanted with no memory errors.
        manager.add_widget(CreationStation(self.name))
        manager.current = self.name
        manager.transition = SlideTransition()

    def load_character(self, character_name):
        manager = self.manager
        self.restart()
        with open("Images/" + character_name + "/rects_colors.pickle", "rb") as char_file:
            # Load the serialised dictionary into self.section_locations
            temp_rects_colors = pickle.load(char_file)
        for pos in temp_rects_colors:
            manager.current_screen.drawing_canvas.rects_colors[pos].rgba = temp_rects_colors[pos]

    def on_draw(self, used_colors_layout, color, color_picker):
        self.color_used(used_colors_layout, color, color_picker)
        self.update_undo_nums()

    # Method for updating the numbers next to the undo and redo buttons and change the colours of the buttons.
    def update_undo_nums(self):
        for undo_widgets in [[self.undo_num, self.undo_button, self.drawing_canvas.undo_list],
                             [self.redo_num, self.redo_button, self.drawing_canvas.redo_list]]:
            undo_widgets[0].text = str(len(undo_widgets[2]))
            if undo_widgets[0].text == "0":
                undo_widgets[0].color = (0, 0, 0, 1)
                undo_widgets[1].color = (.7, .7, 0, 1)
            else:
                undo_widgets[0].color = (0, 0, .3, 1)
                undo_widgets[1].color = (1, 1, 1, 1)

    def color_used(self, grid_layout, color, color_picker):
        color_picker.color = color  # Set the colour of the color_picker to the chosen colour
        for button in grid_layout.children:
            if button.background_color == color:  # If this colour has been used before leave the function
                return
        new_btn = Button(background_normal="", background_color=color)  # Create a new button with the chosen colour
        # When pressed, the button calls a function which sets the colour as the button's colour
        new_btn.bind(on_press=lambda x: self.color_btn_pressed(new_btn.background_color, color_picker))
        grid_layout.add_widget(new_btn)

    @staticmethod
    def color_btn_pressed(color, color_picker):
        color_picker.color = color  # Set the colour of the color_picker to the chosen colour
