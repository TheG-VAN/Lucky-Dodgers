from misc import switch
from twisted.internet import protocol
from online_images import send_images
from os import makedirs
from twisted.internet.reactor import callLater


# Class that handles online communication with the server. Inherits the Protocol class from twisted.
class Client(protocol.Protocol):
    characters_received = False
    images = b''
    scheduled_timout = None

    # Called when the client connects to the server.
    def connectionMade(self):
        if self.scheduled_timout:
            self.scheduled_timout.cancel()
        self.transport.setTcpNoDelay(True)  # This prevents the Nagle algorithm which delays and coalesces messages
        self.factory.parent.transport = self.transport
        if self.username != "":  # If the user already has a username.
            self.factory.parent.initialise_connection()
        else:
            self.factory.parent.set_username()

    # Called when the client receives a message from the server.
    def dataReceived(self, data):
        try:
            # Messages always end in "\n" in case they get combined so they can be split up again.
            messages = data.decode('utf-8').split("\n")
        except UnicodeDecodeError:  # This means that the message is an image instead.
            messages = self.receive_images(data)
        for message in messages:
            if message.startswith("unknown_characters"):
                message = message.replace("unknown_characters;", "")
                if message == "":  # If there are no unknown characters, start.
                    self.factory.parent.create_buttons()
                else:
                    self.send_images(message.split(";"))
            elif message == "username_taken":
                self.factory.parent.username_taken()
            elif message == "username_accepted":
                self.factory.parent.username_accepted()
            elif message == "added_friend":
                self.factory.parent.added_friend()
            elif message == "no_friend":
                self.factory.parent.no_friend()
            elif message == "download_success":
                self.factory.parent.create_buttons()
            elif message.startswith("friends_statuses"):
                self.factory.parent.friends_statuses(message)
            elif message.startswith("teams"):
                message = message.replace("teams;", "")
                self.lobby_screen.update_slots(message)
            elif message.startswith("lobbies"):
                message = message.replace("lobbies;", "")
                self.join_screen.show_lobbies(message)
            elif message.startswith("request"):
                message = message.replace("request;", "")
                self.lobby_screen.request_received(message)
            elif message == "accepted":
                switch("Lobby", self.join_screen.manager, "down")
            elif message.startswith("start"):
                self.lobby_screen.start_game()
            elif message.startswith("characters_chosen"):
                if not self.characters_received:  # Only do this once.
                    self.characters_received = True
                    self.character_selection.enter_game(message)
            elif message.startswith("update"):
                self.game.receive_message(message.replace("update;", ""))

    def send_images(self, characters):
        data = send_images(characters)
        self.transport.write(data)

    def receive_images(self, data):
        self.images += data
        messages = []
        if b'start' in data:
            messages = self.images.split(b'[delimiter]')
            messages = ("".join(list(map(lambda x: x.decode("utf-8"), messages[:messages.index(b"start")])))).split(
                "\n")
        if b'end' in data:
            self.images = self.images.split(b'[delimiter]')
            # Capture any messages that were sent before the images
            messages = ("".join(list(map(lambda x: x.decode("utf-8"), self.images[:self.images.index(b"start")]))) +
                        "".join(list(map(lambda x: x.decode("utf-8"),
                                         self.images[self.images.index(b"end") + 1:])))).split("\n")
            for image in self.images[self.images.index(b"start") + 1:self.images.index(b"end")]:
                try:
                    pathname = image.decode("utf-8").replace("Character Storage", "Images")
                except UnicodeDecodeError:
                    try:
                        with open(pathname, "w+b") as file:
                            file.write(image)
                    # w+ mode creates the file if it doesn't exist but doesn't create the directory if it doesn't exist.
                    except FileNotFoundError:
                        makedirs("/".join(pathname.split("/")[:-1]))  # Create the directory.
                        with open(pathname, "w+b") as file:
                            file.write(image)
        return messages


# Factory for the client protocol. Inherits the ClientFactory class from twisted.
class ClientFactory(protocol.ClientFactory):
    protocol = Client

    def __init__(self, parent, username):
        self.protocol.username = username
        self.parent = parent

    def clientConnectionLost(self, connector, reason):
        connector.connect()  # Try to reconnect
        self.protocol.scheduled_timeout = callLater(5, connector.stopConnecting)  # Timeout after 5 seconds

    def clientConnectionFailed(self, connector, reason):
        self.parent.disconnected(reason.getErrorMessage())
