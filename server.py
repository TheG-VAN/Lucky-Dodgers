from twisted.internet import reactor, protocol
from os import makedirs, path
from online_images import send_images
from random import choice


# Class that handles online communication with clients. Inherits the Protocol class from twisted.
class Server(protocol.Protocol):
    username = None
    lobby = None
    team = None
    ingame = False
    images = b''
    previous_status = ""

    # Called when a message is received from a client.
    def dataReceived(self, data):
        try:
            messages = data.decode('utf-8').split("\n")
        except UnicodeDecodeError:
            messages = self.receive_images(data)
        for message in messages:
            if message.startswith("username") and not self.username:
                self.transport.setTcpNoDelay(True)
                self.username = message.replace("username;", "")
                self.factory.clients[self.username] = self
            elif message.startswith("wants_username"):
                if self.check_username(message):
                    self.transport.write("username_taken\n".encode("utf-8"))
                else:
                    self.transport.write("username_accepted\n".encode("utf-8"))
            elif message.startswith("add_friend"):
                if self.check_username(message):
                    self.transport.write("added_friend\n".encode("utf-8"))
                else:
                    self.transport.write("no_friend\n".encode("utf-8"))
            elif message.startswith("custom_characters"):
                self.custom_characters(message)
            elif message.startswith("friends"):
                self.get_friends_images(message)
            elif message.startswith("check_status"):
                self.friends_statuses(message)
            elif message == "list_lobbies":
                self.list_lobbies()
            elif message == "create_lobby" and not self.lobby:
                self.create_lobby()
            elif message.startswith("request"):
                self.pass_on_request(message)
            elif message.startswith("accept"):
                self.accept(message)
            elif message == "start":
                self.start()
            elif message == "leave":
                self.connectionLost(leaving=True)
            elif message.startswith("team"):
                team = message.partition(";")[-1]
                if len(self.factory.pending_lobbies[self.lobby][team]) == 3 or team == self.team:
                    team = "centre"
                self.factory.pending_lobbies[self.lobby][self.team].remove(self.username)
                self.factory.pending_lobbies[self.lobby][team].append(self.username)
                self.team = team
                self.send_teams()
            elif message.startswith("characters"):
                self.character_selection(message)
            if message.startswith("update"):
                self.ingame = True
                self.update(message)
            else:
                self.ingame = False

    # Called when a client disconnects. This method handles them being removed from lobbies they were in.
    def connectionLost(self, reason=None, leaving=False):
        if self.lobby:
            if self.lobby in self.factory.lobbies:
                if self.username in self.factory.lobbies[self.lobby]:
                    message = self.previous_status.replace("update;", "").split(";;")
                    for i in range(len(message)):
                        message[i] = message[i].split(";")
                        if message[i][0] != "ball":
                            message[i][7] = "disconnected"
                        message[i] = ";".join(message[i])
                    message = "update;" + ";;".join(message)
                    self.update(message)
                    del self.factory.lobbies[self.lobby][self.username]
            # If they were the host of a pending lobby, either make the next player host or delete the lobby if there
            # are no other players.
            if self.factory.pending_lobbies[self.lobby]["host"] == self.username:
                if len(self.factory.pending_lobbies[self.lobby]["all_players"]) > 1:
                    self.factory.pending_lobbies[self.lobby]["host"] = \
                        self.factory.pending_lobbies[self.lobby]["all_players"][1]
                else:
                    del self.factory.pending_lobbies[self.lobby]
            self.factory.pending_lobbies[self.lobby][self.team].remove(self.username)
            self.factory.pending_lobbies[self.lobby]["all_players"].remove(self.username)
            self.send_teams()  # Update the teams for the other users.
            self.lobby = None
        if self.username and not leaving:
            del self.factory.clients[self.username]

    # Checks if the username has already been used.
    @staticmethod
    def check_username(message):
        username = message.partition(";")[-1]
        if path.isfile("Character Storage/" + username + ".txt"):
            return True
        else:
            return False

    # Checks if the server has the characters saved already and update the user's info file.
    def custom_characters(self, message):
        output = "unknown_characters;"
        characters = message.replace("custom_characters;", "").split(";")
        for character in characters:
            if not path.isdir("Character Storage/" + character):
                output += character + ";"
        with open("Character Storage/" + self.username + ".txt", "w+") as user_file:
            user_file.write("\n".join(characters))
        output += "\n"
        self.transport.write(output.encode("utf-8"))

    # Get the data of all the images of the user's friends that they don't have and send them.
    def get_friends_images(self, message):
        message = message.split(";;")[1:]
        friends = message[0].split(";")
        friend_images = message[1].split(";")
        characters = []
        for friend in friends:
            if friend == "":
                continue
            with open("Character Storage/" + friend + ".txt", "r") as images_file:
                characters.extend(images_file.read().split("\n"))
        characters = list(set(characters))  # Converting images to a set removes any duplicates
        for character in characters:
            if character in friend_images:
                characters.remove(character)
        data = send_images(characters, path="Character Storage")
        self.transport.write(data)

    # Format the message into images and save them.
    def receive_images(self, data):
        self.images += data
        messages = []
        if b'start' in data:
            messages = self.images.split(b'[delimiter]')
            messages = "".join(list(map(lambda x: x.decode("utf-8"), messages[:messages.index(b"start")]))).split("\n")
        if b'end' in data:
            self.images = self.images.split(b'[delimiter]')
            # Capture any messages that were sent before the images
            messages = ("".join(list(map(lambda x: x.decode("utf-8"), self.images[:self.images.index(b"start")]))) +
                        "".join(list(map(lambda x: x.decode("utf-8"),
                                         self.images[self.images.index(b"end") + 1:])))).split("\n")
            for image in self.images[self.images.index(b"start") + 1:self.images.index(b"end")]:
                try:
                    pathname = image.decode("utf-8").replace("Images", "Character Storage")
                except UnicodeDecodeError:
                    try:
                        with open(pathname, "w+b") as file:
                            file.write(image)
                    except FileNotFoundError:
                        makedirs("/".join(pathname.split("/")[:-1]))
                        with open(pathname, "w+b") as file:
                            file.write(image)
        self.transport.write("download_success\n".encode("utf-8"))
        return messages

    # Get the current statuses of the user's friends and send them.
    def friends_statuses(self, message):
        friends = message.split(";")[1:]
        output = "friends_statuses;;"
        for friend in friends:
            output += friend + ";"
            if friend in self.factory.clients:
                if self.factory.clients[friend].lobby:
                    if self.factory.clients[friend].ingame:
                        output += "In a game;;"
                    else:
                        output += "in_lobby-" + \
                                  self.factory.pending_lobbies[self.factory.clients[friend].lobby]["host"] \
                                  + "-" + str(len(self.factory.pending_lobbies[self.factory.clients[friend].lobby]
                                                  ["all_players"])) + ";;"
                else:
                    output += "Online;;"
            else:
                output += "Offline;;"
        output += "\n"
        self.transport.write(output.encode("utf-8"))

    # Send all the pending lobbies.
    def list_lobbies(self):
        hosts = []
        for lobby in self.factory.pending_lobbies:
            if lobby in self.factory.lobbies:  # If the players are in a game.
                continue
            if len(self.factory.pending_lobbies[lobby]["all_players"]) > 0:
                if not self.factory.clients[self.factory.pending_lobbies[lobby]["host"]].ingame:
                    hosts.append(self.factory.pending_lobbies[lobby]["host"] + ";" +
                                 str(len(self.factory.pending_lobbies[lobby]["all_players"])))
            else:
                del self.factory.pending_lobbies[lobby]
        self.transport.write(("lobbies;" + ";;".join(hosts) + "\n").encode("utf-8"))

    # Create a new pending lobby.
    def create_lobby(self):
        self.lobby = len(self.factory.pending_lobbies) + 1
        self.factory.pending_lobbies[self.lobby] = {}
        self.factory.pending_lobbies[self.lobby]["host"] = self.username
        self.factory.pending_lobbies[self.lobby]["team_1"] = []
        self.factory.pending_lobbies[self.lobby]["team_2"] = []
        self.factory.pending_lobbies[self.lobby]["centre"] = [self.username]
        self.factory.pending_lobbies[self.lobby]["all_players"] = [self.username]
        self.team = "centre"
        self.send_teams()

    # Pass a request to join from a user to the host of the lobby they want to join.
    def pass_on_request(self, message):
        host = message.partition(";")[-1]
        if host in self.factory.clients:
            if self.factory.clients[host].lobby:
                self.factory.clients[host].transport.write(("request;" + self.username + "\n").encode("utf-8"))
            else:
                self.transport.write("fail\n".encode("utf-8"))
        else:
            self.transport.write("fail\n".encode("utf-8"))

    # Accept a request to join a lobby.
    def accept(self, message):
        player_name = message.partition(";")[-1]
        if player_name in self.factory.clients:
            if not self.factory.clients[player_name].lobby and \
                    len(self.factory.pending_lobbies[self.lobby]["all_players"]) < 6:
                self.factory.pending_lobbies[self.lobby]["centre"].append(player_name)
                self.factory.pending_lobbies[self.lobby]["all_players"].append(player_name)
                self.factory.clients[player_name].team = "centre"
                self.factory.clients[player_name].lobby = self.lobby
                self.factory.clients[player_name].transport.write("accepted\n".encode("utf-8"))
                self.send_teams()
        else:
            self.transport.write("fail\n".encode("utf-8"))

    # Start a game from the pending lobby.
    def start(self):
        try:
            for name in self.factory.pending_lobbies[self.lobby]["all_players"]:
                try:
                    self.factory.clients[name].transport.write("start\n".encode("utf-8"))
                except KeyError:
                    self.factory.pending_lobbies[self.lobby][self.team].remove(name)
        except KeyError:
            self.transport.write("fail\n".encode("utf-8"))
        self.factory.lobbies[self.lobby] = {}
        self.factory.lobbies[self.lobby]["characters"] = 0

    # Send the updated teams to all the users in the pending lobby.
    def send_teams(self):
        try:
            for name in self.factory.pending_lobbies[self.lobby]["all_players"]:
                try:
                    self.factory.clients[name]. \
                        transport.write(("teams;" +
                                         ";".join(self.factory.pending_lobbies[self.lobby]["team_1"]) + ";;" +
                                         ";".join(self.factory.pending_lobbies[self.lobby]["centre"]) + ";;" +
                                         ";".join(self.factory.pending_lobbies[self.lobby]["team_2"]) + ";;" +
                                         self.factory.pending_lobbies[self.lobby]["host"] + "\n")
                                        .encode("utf-8"))
                except KeyError:
                    self.factory.pending_lobbies[self.lobby]["all_players"].remove(name)
        except KeyError:
            pass

    # Send all th characters selected to the users in the lobby.
    def character_selection(self, message):
        message = message.split(";")
        if self.username not in self.factory.lobbies[self.lobby]:
            self.factory.lobbies[self.lobby][self.username] = []
            for character in message[1:]:
                self.factory.lobbies[self.lobby][self.username].append(character)
                if character != "team_1" and character != "team_2":
                    self.factory.lobbies[self.lobby]["characters"] += 1
        if self.factory.lobbies[self.lobby]["characters"] == 6:  # Once all the characters have been chosen.
            background = choice(["Images/[0.7]background_mud.png", "Images/[0.6]background_grass.png",
                                 "Images/[0.7]background_night.png", "Images/[0.3]background_snow.png"])
            try:
                for name in self.factory.lobbies[self.lobby]:
                    if name == "characters":
                        continue
                    try:
                        output = ""
                        for user in self.factory.lobbies[self.lobby]:
                            if user == "characters":
                                continue
                            output += user + ";"
                            for character in self.factory.lobbies[self.lobby][user]:
                                output += character + ";"
                            output += ";"
                        self.factory.clients[name].transport.write(
                            ("characters_chosen;" + output + ";" + background + "\n").encode("utf-8"))
                    except KeyError:
                        del self.factory.lobbies[self.lobby][name]
            except KeyError:
                self.transport.write("fail\n".encode("utf-8"))

    # Pass on the updates to all the users in the lobby.
    def update(self, message):
        self.previous_status = message
        try:
            for name in self.factory.lobbies[self.lobby]:
                if name == "characters" or name == self.username:
                    continue
                self.factory.clients[name].transport.write((message+"\n").encode("utf-8"))
        except KeyError:
            self.transport.write("fail\n".encode("utf-8"))


class ServerFactory(protocol.Factory):
    def __init__(self):
        self.protocol = Server
        self.clients = {}
        # self.pending_lobbies will be a dictionary with keys being lobbies and the values being dictionaries of each
        # lobby's teams and players.
        self.pending_lobbies = {}
        # self.lobbies will be a dictionary with keys being lobbies and values being dictionaries of each players
        # characters.
        self.lobbies = {}


# Start the server.
reactor.listenTCP(50000, ServerFactory())
reactor.run()
