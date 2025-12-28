import socket

# we need threading to stop multiple clients using same function anyway
import threading
from chat_room import chat_room
from protocol import send_message, recv_message
from client import client

HOST = "0.0.0.0"   # Listen on all network interfaces
PORT = 5000        # Port clients will connect to

clients = dict()     # dict, maps user name -> client obj
chat_rooms = dict()  # Dictionary to hold chat room instances, maps room name -> Room instance
lock = threading.Lock()

def create_room(room_name, owner):
    # create a new chat_room obj and assign respective room name to room object
    temp_room = chat_room(room_name, owner)
    chat_rooms[room_name] = temp_room
    # Prints out the room name and its creator
    print(f"[+] Room '{room_name}' created by {owner}")

# the computation for assigning a user to a room, prompts user to join or create one
def assign_room(conn, name):
    msg = recv_message(conn)
    room_name = msg.get("ROOM_NAME") if msg else None

    # handles whether the client wants to join or create a room

    if msg and msg.get("TYPE") == "CREATE_ROOM":
        create_room(room_name, name)

    elif msg and msg.get("TYPE") == "JOIN_ROOM":
        
        # if user intends to join a room, it utilizes the add_user() function and adds the respective user
        Room = chat_rooms.get(room_name)
        if Room:
            Room.add_user(name)

    return room_name

# Every client will thats connected to the relay server will have an instance of this (the instance is hosted here ofc)
def handle_client(conn, addr):
    # prints the ip address of the client that connects to the relay
    print(f"[+] Connected: {addr}")

    msg = recv_message(conn)

    name = None
    chat_room_name = None

    # recieves the name from the client
    if isinstance(msg, dict) and msg.get("TYPE") == "SEND":
        name = msg.get("NAME")

    # if the name is null, then it closes the TCP socket of that client and returns
    if not name:
        send_message(conn, {"TYPE": "ERROR", "MESSAGE": "Invalid registration message"})
        conn.close()
        return

    # if 2 clients try connect at same time the lock makes sure each action happens 1 after the other
    with lock:
        
        # checks if the name is already taken, gives an "ERROR" type message
        if name in clients:
            send_message(conn, {"TYPE": "ERROR", "MESSAGE": "Name already taken"})
            conn.close()
            return
        
        # otherwise adds the client to the clients dict
        # clients[name] = conn

        # sends a confirmation message back to the client

        # send message with chat_room info
        send_message(conn, {"CHAT_ROOMS": chat_rooms, "TYPE": "REGISTERED", "MESSAGE": f"Welcome to the VPS server, {name}!\n"})

        # assign room computation (save in a function)
        chat_room_name = assign_room(conn, name)

        # maps client name -> client object
        clients[name] = client(conn, name, chat_room_name)

        # broadcasts user to room regardless if they created it or joined
        chat_rooms[chat_room_name].broadcast(clients, name)

    try:
        while True:
            
            # returns back a msg to let the user know if they are still in a room
            in_room = chat_rooms[chat_room_name].in_room(name)
            send_message(conn, {"TYPE": "CHECK", "IN_ROOM": in_room})

            if in_room:
                # recieves the message from the client
                msg = recv_message(conn)

                if not msg:
                    break

                if msg.get("TYPE") == "SEND":
                
                    room_instance = chat_rooms.get(msg.get("ROOM"))

                    if room_instance:
                        room_instance.send_message("RECIEVE", msg.get("MESSAGE"), clients, from_user=name)
            else:
                # user is not in room since they were removed, gets user assigned to a room

                # send message with chat_room info
                send_message(conn, {"TYPE": "REJOIN", "CHAT_ROOMS": chat_rooms, "NAME": name})
                assign_room(conn, name)

    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        print(f"[-] User disconnected: {name} from {addr}")
        with lock:
            if name in clients:
                del clients[name]
        conn.close()


def main():
    # This creates a tcp socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # bypasses "Address already in use" error
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Incoming traffic requests get sent to server
    server.bind((HOST, PORT))
    # Socket is now listening (bascially open to requests)
    server.listen()

    print(f"[+] Relay server listening on {HOST}:{PORT}")
    print("[+] Waiting for clients to connect...")

    # Loop running forever waiting for clients
    while True:
        # Code pauses here until client tries connecting
        conn, addr = server.accept()
        # Creates a new thread that will run the handle_client function
        thread = threading.Thread(
            target=handle_client,
            args=(conn, addr),
            # daemon means it will exit automatically
            daemon=True
        )
        thread.start()


if __name__ == "__main__":
    main()

    