from os import walk, makedirs
import cv2
import numpy as np
import pickle
from pathlib import Path
from shutil import copy
import base64


# A function to create a dictionary for the character specified with the keys being the actions of the character and the
# values being lists of the pathnames of each image within that state.
def make_dict(character_name, path="Images"):
    image_dict = {}  # This will be a dictionary containing lists of pathnames
    for subdir, dirs, files in walk(path + "/" + character_name):  # Finds each file in the character name folder
        temp_subdir = subdir.split("/")
        # os.walk uses backslashes but this doesnt work on android so these lines turn everything into forward slashes
        temp_subdir.extend(temp_subdir[1].split("\\"))
        del (temp_subdir[1])
        temp_subdir.remove(path)
        temp_subdir.remove(character_name)
        temp_subdir = "".join(temp_subdir)  # Theses 4 lines are for formatting the path into just the subdir name
        if not temp_subdir:
            continue
        image_dict[temp_subdir] = list()
        for i in range(len(files)):
            # Add the file path to the dictionary
            image_dict[temp_subdir].append("Images/" + character_name + "/" + temp_subdir + "/" + str(i + 1) + ".png")
    return image_dict


# Basically the opposite of the make_dict function because this uses a dictionary to create folders with images saved.
def make_new_character_directories(character_name, image_dict, drawing, old_character_name):
    char_path = "Images/" + character_name + "/"
    makedirs(char_path)
    saveable_drawing = {}
    for pos in drawing:
        # Turn the values into tuples containing rgba rather than kivy Color objects so it can be pickled
        if drawing[pos].rgba != [0, 0, 0, 0]:
            saveable_drawing[pos] = drawing[pos].rgba
    copy("Images/" + old_character_name + "/info.txt", char_path)
    with open(char_path + "rects_colors.pickle", "wb") as output_file:
        pickle.dump(saveable_drawing, output_file)  # Save the drawing so it can be edited later by the player
    for key in image_dict:
        key_path = char_path + key + "/"
        makedirs(key_path)
        for i, image in enumerate(image_dict[key]):
            save_image(image, key_path + str(i + 1) + ".png")
            if key == "idle" and i == 0:  # This is for making a cropped preview image for the character
                cropped_image = crop_image(image)
                save_image(cv2.resize(cropped_image, (cropped_image.shape[1] * 5, cropped_image.shape[0] * 5),
                                      interpolation=cv2.INTER_NEAREST), char_path + "preview.png")


def drawing_to_image(drawing):  # Turns the initial drawing in the format of a dict with pos as keys to image
    if not drawing:
        return np.zeros((30, 30, 4))
    temp_list = []
    # Make the dictionary into a 1D list and multiply each colour value by 255 because kivy uses a 0-1 range for rgba
    for key in drawing:
        temp_list.append(list(map(lambda x: x * 255, drawing[key].rgba)))
    im_arr = np.array(temp_list)  # Make the 1D list into a 1D image array
    # noinspection PyArgumentList
    im_arr = np.flipud(im_arr.reshape(30, 30, 4))  # Reshape the image array to become 3D
    return im_arr


def get_info(folder, character=True):  # Access the information file for the character
    info_dict = {}
    if character:
        pathname = "Images/" + folder + "/info.txt"
    else:
        pathname = folder
    with open(pathname, "r") as info:
        info_list = info.read().split("\n")
        for i in range(0, len(info_list), 2):
            info_dict[info_list[i]] = info_list[i + 1].split(";")
            try:
                info_dict[info_list[i]] = list(map(int, info_dict[info_list[i]]))
            except ValueError:
                pass
    return info_dict


def crop_image(im_arr, hashing=False):  # Only want to crop width since this is constant except for when hashing
    # Turn the values of the rgba axis into a combination of all of them, so an empty pixel will have a value of 0.
    image_data = im_arr.max(axis=2)
    # Find columns where all pixels has a value > 0, so not an empty column or row
    non_empty_columns = np.where(image_data.max(axis=0) > 0)[0]
    # Create the dimensions containing the first and last non_empty row
    crop_box = (min(non_empty_columns), max(non_empty_columns))
    im_arr = im_arr[:, crop_box[0]:crop_box[1] + 1, :]  # Crop the image array
    if hashing:  # Crop rows as well
        non_empty_rows = np.where(image_data.max(axis=1) > 0)[0]
        crop_box = (min(non_empty_rows), max(non_empty_rows))
        im_arr = im_arr[crop_box[0]:crop_box[1] + 1, :, :]
    return im_arr


def make_image_array(pathname):
    # cv2.imread creates an image array from a pathname. The -1 is to make it keep alpha channel.
    # The slicing afterwards is there because cv2 use bgra rather than rgba so this is converting it to rgba.
    # IMPORTANT: The image array is in the format [y][x][colour] not [x][y][colour] like expected.
    # x and y are integers and color is a list of 4 integers up to 255.
    im_arr = cv2.imread(pathname, -1)[:, :, [2, 1, 0, 3]]
    return im_arr


def save_image(im_arr, pathname):
    # Slicing required for same reason as in make_image_array
    cv2.imwrite(pathname, im_arr[:, :, [2, 1, 0, 3]], [cv2.IMWRITE_PNG_COMPRESSION, 9])


def image_search(im_arr, head_dimensions):
    # This function finds the uppermost pixel and then calculates using head dimensions, where the head is.
    image_y, image_x = im_arr.shape[:2]
    for y in range(-head_dimensions[0], image_y - head_dimensions[1]):
        for x in range(-head_dimensions[2], image_x - head_dimensions[3]):
            test = (im_arr[y, x] == (0, 0, 0, 255))
            if test.all():
                return [y + head_dimensions[0], y + head_dimensions[1], x + head_dimensions[2], x + head_dimensions[3]]


# Replace the pixels where the head was with the new image
def combine_images(filename, head_dimensions, replacement_im_array):
    im_array = make_image_array(filename)
    head_section = image_search(im_array, head_dimensions)
    im_array[head_section[0]:head_section[1], head_section[2]:head_section[3]] = replacement_im_array
    return im_array


def find_sections(character_name):  # This is only used for new characters upon creation, never called by the program
    character = make_dict(character_name)
    info = get_info(character_name)
    head_dimensions = info["head_dimensions"]
    section_locations = {}
    for key in character:  # Go through each animation in the character directory
        for file in character[key]:  # Go through each image in the animation
            section_locations[file] = {}
            # Remove the head, np.zeros creates an empty array
            im_arr = combine_images(file, head_dimensions, np.zeros((head_dimensions[1] - head_dimensions[0],
                                                                     head_dimensions[3] - head_dimensions[2], 4)))
            for section in info:  # Go through each section
                if section.endswith("colour"):  # If this is a section_colour and not other info like head_dimensions
                    section_locations[file][section] = {}  # Create a new dictionary for this section
                    color = info[section]  # Get the color of that section
                    for x in range(0, im_arr.shape[1]):  # Go through each column of pixels in the image
                        section_locations[file][section][x] = list()  # Create a list for that column
                        first_pixel = True  # This is for the first pixel of each column of the section color.
                        for y in range(0, im_arr.shape[0]):  # Go through each pixel in the column
                            test = (im_arr[y, x] == color)
                            if test.all() and first_pixel:  # If this pixel is the right colour and is the first
                                section_locations[file][section][x].append(y)  # Add it to the list for that column
                                first_pixel = False
                            elif not test.all() and not first_pixel:
                                section_locations[file][section][x].append(y)  # Add it to the list for that column
                                first_pixel = True
                        if not section_locations[file][section][x]:
                            del section_locations[file][section][x]
    with open("Images/" + character_name + "/section_locations.pickle", "wb") as output_file:
        pickle.dump(section_locations, output_file)  # Serialise the dictionary and save it


def swap_colors(im_arr, section_colors, section_locations, original_pathname):
    section_locations = section_locations[original_pathname]  # Get the section locations for this file
    for section in section_locations:  # Go through each section
        if section_colors[section]:  # If the section colors list contains a value for this section
            for x in section_locations[section]:  # Go through each column
                for i in range(0, len(section_locations[section][x]), 2):  # Get every odd value
                    # Get every value between the first and last in a column
                    for y in range(section_locations[section][x][i], section_locations[section][x][i + 1]):
                        # Set the pixel to the new colour
                        im_arr[y, x] = list(map(lambda num: num * 255, section_colors[section]))
    return im_arr


def hash_image(image, section_colors, name):
    # Cropping the image both makes the hashing faster and decreases the similarities between images
    try:
        image = crop_image(image, hashing=True)
        hash_output = int.from_bytes(image.tobytes(),
                                     "little")  # Convert the image array to bytes and then convert to int
        for i in range(3, 5):
            # XOR hash with the itself bit shifted to the left by i and then multiply the hash by i
            hash_output ^= hash_output << i
            hash_output *= i
        # At this point hash_output is a huge number (approximately 10^70000). We need to reduce the size of
        # hash_output to the hash table size. The best way to do this is with modulo. The hash will be used for
        # directory names so the character limit is 248 on Windows and 255 on Linux. However, we don't need the hash
        # to be that long to prevent collisions and the larger the number we modulo by the slower the hash will be. A
        # more reasonable size would be about 50 characters. The final hash won't be an integer (this would make the
        # table size 10^50 if we wanted 50 characters). Instead the hash will be converted to base 64. This means
        # that the table size can be 64^50 which is approximately 2x10^90. When using modulo for hashing we want to
        # modulo by a coprime of the initial number. This is to deal with any patterns that may occur in the number
        # which would result in collisions otherwise. Fortunately it isn't hard to find a prime close to 64^50
        # because 2^n - 1 is always prime (Mersenne primes).
        hash_output %= 64 ** 50 - 1
        byte_length = (hash_output.bit_length() + 7) // 8  # This is needed for converting an integer to bytes
        hash_output = hash_output.to_bytes(byte_length, "little")
    except ValueError:  # This means that the image is empty.
        hash_output = b""
    # The previous section of the hash only dealt with the head of the character but now we have to take into account
    # the colours of the character's skin, clothes and shoes.
    for section in section_colors.values():
        if section:  # If the user hasn't picked a new colour, section will be None
            # Round each value to 2 d.p. and concatenate as a string
            section = "".join(map(lambda x: str(round(x, 2)), section[:-1]))
        else:
            section = "0"
        hash_output += section.encode("utf-8")
    hash_output += name.encode("utf-8")  # name is the name of the character's body which the new character is based on
    # '/' is not allowed in filenames so replace with '_'
    return base64.b64encode(hash_output).decode("utf-8").replace("/", "_")


def main(old_character_name, replacement_drawing, section_colors, section_locations, preview=False):
    new_character_name = None
    old_character = make_dict(old_character_name)
    info = get_info(old_character_name)
    head_dimensions = info["head_dimensions"]
    replacement_image = drawing_to_image(replacement_drawing)
    # Resize the image to the head dimensions
    replacement_im_array = cv2.resize(replacement_image, (head_dimensions[3] - head_dimensions[2],
                                                          head_dimensions[1] - head_dimensions[0]),
                                      # This gets rid of interpolation which would make the image blurry
                                      interpolation=cv2.INTER_NEAREST)
    if preview:
        combined_image = combine_images(old_character["idle"][0], head_dimensions, replacement_im_array)
        color_swapped_image = swap_colors(combined_image, section_colors, section_locations,
                                          original_pathname=old_character["idle"][0])
        cropped_image = crop_image(color_swapped_image)
        # Resize image so it can be seen at full size on the screen
        resized_image = cv2.resize(cropped_image, (cropped_image.shape[1] * 5, cropped_image.shape[0] * 5),
                                   interpolation=cv2.INTER_NEAREST)
        save_image(resized_image, "Images/preview_image.png")
        return
    final_images = {}  # This will be a dictionary of lists containing images
    for key in old_character:
        final_images[key] = []
        for filename in old_character[key]:
            combined_image = combine_images(filename, head_dimensions, replacement_im_array)
            combined_image = swap_colors(combined_image, section_colors, section_locations, original_pathname=filename)
            final_images[key].append(combined_image)
            if key == "idle" and len(final_images[key]) == 1:
                new_character_name = hash_image(replacement_image, section_colors, old_character_name)
                if Path("Images/" + new_character_name).is_dir():  # If this character already exists
                    return
    make_new_character_directories(new_character_name, final_images, replacement_drawing, old_character_name)
    return


########################################################################################################################
def temp():
    d = make_dict("kirk")
    final_images = {}
    for state in d:
        final_images[state] = []
        for pathname in d[state]:
            im_arr = make_image_array(pathname)
            for x in range(0, im_arr.shape[1]):
                for y in range(0, im_arr.shape[0]):
                    if (im_arr[y, x] == [0, 0, 0, 255]).all():
                        try:
                            if (im_arr[y+13, x] == [0, 0, 0, 255]).all() or (im_arr[y-13, x] == [0, 0, 0, 255]).all():
                                continue
                        except IndexError:
                            pass
                        if (im_arr[y, x-1] == [39, 39, 39, 255]).all():
                            for i in range(1000):
                                if not (im_arr[y, x + i] == [0, 0, 0, 255]).all():
                                    if (im_arr[y, x + i] == [39, 39, 39, 255]).all():
                                        for j in range(i):
                                            im_arr[y, x + j] = [39, 39, 39, 255]
                                    break
                        if (im_arr[y-1, x] == [39, 39, 39, 255]).all():
                            for i in range(1000):
                                if not (im_arr[y + i, x] == [0, 0, 0, 255]).all():
                                    if (im_arr[y + i, x] == [39, 39, 39, 255]).all():
                                        for j in range(i):
                                            im_arr[y + j, x] = [39, 39, 39, 255]
                                    break
            bg = np.zeros(im_arr.shape)
            im_arr = cv2.resize(im_arr, None, fx=0.9, fy=1, interpolation=cv2.INTER_NEAREST)
            bg[bg.shape[0]-im_arr.shape[0]:bg.shape[0], int((bg.shape[1]-im_arr.shape[1])/2):int((bg.shape[1]-im_arr.shape[1])/2) + im_arr.shape[1], :] = im_arr
            final_images[state].append(bg)
    make_new_character_directories("kirk4", final_images, {}, "kirk")
########################################################################################################################
