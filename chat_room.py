# Relay server uses this class to send messages to everyone in chat room, 

from protocol import send_message

class chat_room:

    # new instance of chat_room object, creates a users list and automatically adds the user that created the obj to list
    def __init__(self, room_name, name):
        self.room_name = room_name
        self.admins = [name]
        self.users = []
        self.add_user(name)
        # The first person in list will be the owner of the room

    def get_chat_room_name(self):
        return self.room_name
    
    def add_user(self, name):
        self.users.append(name)
    
    # removes a user
    def remove_user(self, user):
        self.users.remove(user)

    # lists user
    def list_users(self):
        return self.users
    
    def get_owner(self):
        return self.users[0]

    # broadcast msg to server, printing that a new user had joined the room, (displays for user that joined too)
    # passes to the send_message function below for slight optimization
    def broadcast(self, clients, name):
        self.send_message("BROADCAST", f"Welcome to the chat room {name}!", clients)

    # Checks if a username is in a room (string -> boolean)
    def in_room(self, user):
        return user in self.users
    
    # from_user is a default argument so broadcast msg essentially "bypasses" the check within the loop, printing to the user that joined also
    def send_message(self, type, message, clients, from_user=""):
        if from_user in self.admins and message[0] == "!":
            msglist = message.split(" ")
            command = msglist[0]
            match command:
                case "!remove":
                    user = msglist[1]
                    self.users.remove(user)

                case "!listusers":
                    send_message(clients[from_user].get_socket(), {"TYPE": "BROADCAST", "MESSAGE": self.users})

                case "!makeadmin":
                    user = msglist[1]
                    if user in self.users: 
                        self.admins.append(user)
                        send_message(clients[from_user].get_socket(), {"TYPE": "BROADCAST", "MESSAGE": f"Made {user} admin"})
                    else:
                        send_message(clients[from_user].get_socket(), {"TYPE": "BROADCAST", "MESSAGE": f"{user} does not exist"}) 
        else:
            # loops thru every user in that room and sends the corresponding message to them
            # .get_socket() is function in client.
            for user in self.users:
                if user != from_user:
                    send_message(clients[user].get_socket(), {"TYPE": type, "FROM": from_user, "MESSAGE": message})