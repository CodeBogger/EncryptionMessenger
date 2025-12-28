import socket
import threading
from protocol import recv_message, send_message
import queue

inbox = queue.Queue() # messages from server
outbox = queue.Queue() # lines from user input

state = {
    'RUNNING': True,
    'IN_ROOM': False,
    'ROOM': None,
    'USER': None,
}

# used to pause / resume the input thread when we need to ask room questions in main thread
input_enabled = threading.Event()
input_enabled.set()

# create room if user intends to, join room if there is a room and user intends to join a room
# creates a room, communicates the room name, room owner ("only user"), and type "CREATE_ROOM" all in a dict
def create_room(socket, room_name, owner):
    send_message(socket, {"TYPE": "CREATE_ROOM", "ROOM_NAME": room_name, "OWNER": owner})

# sends msg to socket, relay_server captures that msg and executes command to join a current room
def join_room(socket, room_name):
    send_message(socket, {"TYPE": "JOIN_ROOM", "ROOM_NAME": room_name})

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

        if line is None:
            continue

        text = line.strip()
        if text.lower() in ("quit", "exit"):
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

def main():
    # creates a socket and connects to the server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("72.62.81.113", 5000))

    user = input("Enter your username: ")
    send_message(s, {"TYPE": "SEND", "NAME": user})

    state['USER'] = user # assign username to user

    # receive the registered message before starting receiver thread
    msg = recv_message(s)
    if msg and msg.get('TYPE') != 'REGISTERED':
        print("Did not receive REGISTERED from server. Exiting.")
        s.close()
        return
    
    print(f"\n[Server]: {msg.get('MESSAGE') if msg else ''}")
    choose_room(s, msg)

    # start threads
    t_recv = threading.Thread(target=receiver_loop, args=(s,), daemon=True)
    t_recv.start()

    t_in = threading.Thread(target=input_loop, daemon=True)
    t_in.start()

    # main loop, updates state and sends msgs
    while state['RUNNING']:
        # process inbound messages from relay_server and elsewhere
        try:
            while True:
                msg = inbox.get_nowait()
                mType = msg.get('TYPE')

                if mType == "CHECK":
                    state['IN_ROOM'] = msg.get('IN_ROOM')

                elif mType == "RECEIVE":
                    print(f"{msg.get('FROM')}: {msg.get('MESSAGE')}")

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

        except queue.Empty:
            pass

        # now for outbound messages, processing user input and sending back to relay_server
        try:
            message_type, contents = outbox.get_nowait()

            if message_type == 'QUIT':
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

if __name__ == "__main__":
    main()