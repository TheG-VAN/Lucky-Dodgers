from image_editing import hash_image
from random import random, randint
import numpy as np
import cv2


hashes_dict = {}  # Use a dictionary because finding duplicates is quick.
for i in range(1000000):  # Generate a million different images.
    section_colors = {'skin_colour': [random(), random(), random(), 1.0],  # Pick random colours for each section.
                      'top_colour': [random(), random(), random(), 1.0],
                      'bottoms_colour': [random(), random(), random(), 1.0],
                      'shoe_colour': [random(), random(), random(), 1.0]}
    images = []
    shapes = randint(1, 30)  # Create up to 30 random shapes and then combine them to make an image.
    for j in range(shapes):
        colors = []
        # The 3rd dimension is for colour, it is 1 instead of 4 for rgba because I want each value (r, g and b) to be
        # random so I have to do them separately.
        shape = [randint(1, int(30)), randint(1, int(30)), 1]
        for k in range(3):  # Create an array for r, g and b.
            colors.append(np.full(shape, randint(0, 255)))  # Create an array with random 3rd dimension.
        colors.append(np.full(shape, 255))  # Create the alpha bit of the array. We want it 255 to make the shape opaque
        images.append(np.concatenate(colors, axis=2))  # Combine all the colours together to make one shape.
    canvas = np.zeros((30, 30, 4))  # Create a blank 30x30 image array.
    for image in images:
        if image.shape[0] == 30:
            r_y = 0
        if image.shape[1] == 30:
            r_x = 0
        r_y = randint(0, 30 - image.shape[0])  # Make a random position for the shape to go.
        r_x = randint(0, 30 - image.shape[1])
        canvas[r_y:r_y+image.shape[0], r_x:r_x+image.shape[1], :] = image  # Put the image in the canvas.
    h = hash_image(canvas, section_colors, "kirk")  # Hash the image.
    if h in hashes_dict:  # If there is a collision, end the program.
        print("FAIL")
        break
    else:
        hashes_dict[h] = "hashed"
cv2.imwrite("test.png", canvas[:, :, [2, 1, 0, 3]], [cv2.IMWRITE_PNG_COMPRESSION, 9])
