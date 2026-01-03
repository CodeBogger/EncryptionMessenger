class Client:
    
    def __init__(self, socket, user_name, assigned_room):
        self.socket = socket
        self.user_name = user_name
        self.assigned_room = assigned_room

    def get_name(self):
        return self.user_name
    
    def get_socket(self):
        return self.socket
    
    def get_assigned_room(self):
        return self.assigned_room
    
    def change_room(self, name):
        self.assigned_room = name