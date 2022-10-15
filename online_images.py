from image_editing import make_dict


# Function for formatting the images to be sent top and from the client and server.
def send_images(characters, path="Images"):
    data = b"[delimiter]start[delimiter]"
    for character in characters:
        if character:
            image_dict = make_dict(character, path=path)
            for value in image_dict.values():
                for pathname in value:
                    pathname = pathname.replace("Images", path)
                    with open(pathname, "rb") as image:
                        data += pathname.encode("utf-8") + b'[delimiter]' + image.read() + b'[delimiter]'
    data += b'[delimiter]end[delimiter]'
    return data
