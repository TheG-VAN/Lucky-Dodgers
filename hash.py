from hashlib import md5
import cv2
from image_editing import crop_image
import base64
import pickle
from random import random, randint
import numpy as np


def hash_image(image):
    image = crop_image(image, hashing=True)
    return md5(image.tobytes()).hexdigest()


def custom_hash_image(image, section_colors, name):
    # Cropping the image both makes the hashing faster and decreases the similarities between images
    image = crop_image(image, hashing=True)
    hash_output = int.from_bytes(image.tobytes(), "little")  # Convert the image array to bytes and then convert to int
    for i in range(3, 5):
        # XOR hash with the itself bit shifted to the left by i and then multiply the hash by i
        hash_output ^= hash_output << i
        hash_output *= i
    # At this point hash_output is a huge number (approximately 10^70000). We need to reduce the size of hash_output to
    # the hash table size. The best way to do this is with modulo. The hash will be used for directory names so the
    # character limit is 248 on Windows and 255 on Linux. However, we don't need the hash to be that long to prevent
    # collisions and the larger the number we modulo by the slower the hash will be. A more reasonable size would be
    # between 50 and 100 characters. The final hash won't be an integer (this would make the table size 10^50 if we
    # wanted 50 characters). Instead the hash will be converted to base 64. This means that the table size can be 64^50
    # which is approximately 2x10^90. When using modulo for hashing we want to modulo by a coprime of the initial
    # number. This is to deal with any patterns that may occur in the number which would result in collisions otherwise.
    # Fortunately it isn't hard to find a prime close to 64^50 because 2^n - 1 is always prime (Mersenne primes)
    hash_output %= 64**50 - 1
    byte_length = (hash_output.bit_length() + 7) // 8  # This is needed for converting an integer to bytes
    hash_output = hash_output.to_bytes(byte_length, "little")
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
