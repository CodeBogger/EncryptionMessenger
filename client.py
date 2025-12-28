# Important to note, for vast majority of code "messages" arent actually referring to actual typed messages
# It refers to the bytes sent between clients & relay_server, these messages for most part contain 
# socket & a map of instructions

import socket
import threading
from protocol import recv_message, send_message
import queue

inbox = queue.Queue() # messages from server
outbox = queue.Queue() # lines from user input

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

# Info on the client
state = {
    # Is it currently active (needed for loops)
    'RUNNING': True,
    # If its currently in a room
    'IN_ROOM': False,
    # Name of room its in
    'ROOM': None,
    # username
    'USER': None,
}

# used to pause / resume the input thread when we need to ask room questions in main thread
input_enabled = threading.Event()
# .set() means good to go, whilst .clear() means continue waiting
input_enabled.set()

def main():
    # creates a socket and connects to the server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("72.62.81.113", 5000))

    user = input("Enter your username: ")
    send_message(s, {"TYPE": "SEND", "NAME": user})

    state['USER'] = user # assign username to user

    # receive the registered message before starting receiver thread
    # This message should always be sent from relay server upon connection
    msg = recv_message(s)
    if msg and msg.get('TYPE') != 'REGISTERED':
        print("Did not receive REGISTERED from server. Exiting.")
        print("Relay server might not be hosted")
        s.close()
        return
    
    print(f"\n[Server]: {msg.get('MESSAGE') if msg else ''}")
    choose_room(s, msg)

    # start threads
    # For recieving messages
    t_recv = threading.Thread(target=receiver_loop, args=(s,), daemon=True)
    t_recv.start()

    # For recieving user inputs (from keyboard) and sending them to relay server
    t_in = threading.Thread(target=input_loop, daemon=True)
    t_in.start()

    # main loop, updates state and sends msgs
    while state['RUNNING']:
        # process inbound messages from relay_server and elsewhere
        try:
            # This inner loop isnt needed but its more effective
            # It pulls stuff from the inbox, like new messages 
            while True:
                # .get_nowait() doesnt wait on an empty que
                # it will try get first value, if nothing exists it throws error, (which is handled)
                # this allows for this thread to not get stuck here and do other stuff
                # it is extremely lightweight and uses hardly any cpu 
                msg = inbox.get_nowait()

                # mType is the action the message wants complete
                mType = msg.get('TYPE')

                # This is used to update if the client is in a chat room
                if mType == "CHECK":
                    state['IN_ROOM'] = msg.get('IN_ROOM')

                # Recieve will have parameters (sender, message)
                elif mType == "RECEIVE":
                    print(f"{msg.get('FROM')}: {msg.get('MESSAGE')}")

                # Broadcast will just have parameter message (no sender)
                elif mType == "BROADCAST":
                    print(f"[Broadcast]: {msg.get('MESSAGE')}")
                
                elif mType == "REJOIN":
                    # user is NO LONGER in room, updating state
                    state['IN_ROOM'] = False
                    state['ROOM'] = None

                    # rejoin message should carry updated chat_rooms
                    print("\n[Server]: You are no longer in a room. Rejoin required.")
                    choose_room(s, msg)
                
                elif mType == "DISCONNECT":
                    print("Server disconnected.")
                    state['RUNNING'] = False

        # if the que is empty, just continue the while loop repeatedly
        except queue.Empty:
            pass

        # now for outbound messages, processing user input and sending back to relay_server
        try:
            message_type, contents = outbox.get_nowait()

            if message_type == 'QUIT':
                print("Closing")
                state['RUNNING'] = False
                break

            if message_type == 'CHAT':
                if not state['IN_ROOM']:
                    print("[Client]: You are not currently in a room. Wait for REJOIN / CHECK.")
                else:
                    send_message(s, {"TYPE": "SEND", "ROOM": state['ROOM'], "MESSAGE": contents})

        except queue.Empty:
            pass
    
    # if they aren't in a room, the message from relay_server.py is captured in the reciever loop thread above. it will be handled there
    state['RUNNING'] = False
    input_enabled.set()
    try:
        s.close()
    except:
        pass
# creates a room, communicates the room name, room owner ("only user"), and type "CREATE_ROOM" all in a dict
def create_room(socket, room_name, owner):
    send_message(socket, {"TYPE": "CREATE_ROOM", "ROOM_NAME": room_name, "OWNER": owner})

# sends msg to socket, relay_server captures that msg and executes command to join a current room
def join_room(socket, room_name, password = ""):
    send_message(socket, {"TYPE": "JOIN_ROOM", "ROOM_NAME": room_name, "PASSWORD": password})

def receiver_loop(s: socket.socket):
    # only placed allowed to call recv_message()
    # pushes every message into inbox, in the queue

    while state['RUNNING']:
        msg = recv_message(s)
        if msg is None:
            inbox.put({"TYPE": "DISCONNECT"})
            state['RUNNING'] = False
            return
        inbox.put(msg)

def input_loop():
    # reads user input and pushes lines into outbox
    # does not touch socket

    while state['RUNNING']:
        input_enabled.wait() # paused during room selection / rejoin prompts
        if not state['RUNNING']:
            break

        try:
            line = input()
        except Exception:
            outbox.put(('QUIT', None))
            break

        if line is None or len(line) == 0:
            continue

        text = line.strip()
        if text.lower() == "exit":
            outbox.put(("QUIT", None))
            continue
        
        # pushes input into outbox queue, where all user inputs are stored
        outbox.put(("CHAT", text))

def print_rooms(chat_rooms):
    print("\nAvailable chat rooms:")

    for room_name, room_obj in chat_rooms.items():
            print(f"- {room_name} (Owner: {room_obj.get_owner()})")
            print(f"  Users: {room_obj.list_users()}")
    print("\n")
     
def choose_room(s, msg):
    input_enabled.clear()

    chat_rooms = msg.get("CHAT_ROOMS") if msg else {}
    room_name = None
    
    print_rooms(chat_rooms)

    choice = None

    if len(chat_rooms) > 0:
        while choice not in ("y", "n"):
            choice = input("Do you want to join an existing chat room? (y/n): ").strip()
    
            if choice == "y":
                while room_name not in chat_rooms.keys():
                    room_name = input("Enter the name of the chat room to join: ")
                join_room(s, room_name)
            else:
                room_name = input("Enter the name of the new chat room: ")
                create_room(s, room_name, state['USER'])
    else:
        print("There are currently no chat rooms to join. Please create one. ")
        room_name = input("Enter the name of the new chat room: ")
        create_room(s, room_name, state['USER'])

    # update client's room state
    state['ROOM'] = room_name
    state['IN_ROOM'] = True

    input_enabled.set()
    return room_name



if __name__ == "__main__":
    main()