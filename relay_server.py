import socket

# we need threading to stop multiple clients using same function anyway
import threading
from chat_room import chat_room
from protocol import send_message, recv_message

HOST = "0.0.0.0"   # Listen on all network interfaces
PORT = 5000        # Port clients will connect to

clients = dict()      # List of connected client sockets
lock = threading.Lock()
chat_rooms = dict()  # Dictionary to hold chat room instances, maps room name -> Room instance

def create_room(socket, room_name, owner, rooms_dict):
    Room = chat_room(room_name, socket, owner)
    rooms_dict[room_name] = Room

# Every client will thats connected to the relay server will have an instance of this (the instance is hosted here ofc)
def handle_client(conn, addr):
    # prints the ip address of the client that connects to the relay
    print(f"[+] Connected: {addr}")

    msg = recv_message(conn)

    name = None
    room = None

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
        clients[name] = conn

        # sends a confirmation message back to the client
        send_message(conn, {"TYPE": "REGISTERED", "MESSAGE": f"Welcome to the VPS server, {name}!"})

    print("\nAvailable chat rooms:")
    for room_name, room in chat_rooms.items():
        print(f"- {room_name} (Owner: {room.owner()})")
        print(f"  Users: {room.list_users()}")
    print("\n")

    chat_room_name = None

    if len(chat_rooms) > 0:
        user_choice = None

        while user_choice != "y" and user_choice != "n":
            user_choice = input("Do you want to join an existing chat room? (y/n): ").lower()

        if user_choice == "y":

            while chat_room_name not in chat_rooms.keys():
                chat_room_name = input("Enter the name of the chat room to join: ")

        else:
            chat_room_name = input("Enter a name for the new chat room: ")
            create_room(conn, chat_room_name, name, chat_rooms)
            print("\n")
    else:
        print("No chat rooms available. Please create one on the server first.")
        chat_room_name = input("Enter a name for the new chat room: ")

        create_room(conn, chat_room_name, name, chat_rooms)
        print("\n")

    send_message(conn, {"TYPE": "BROADCAST", "MESSAGE": f"{msg.get('MESSAGE') if msg else 'You have joined the server.'}\n"})
    print(f"[+] User registered: {name} from {addr}, Room: {chat_room_name}")

    try:
        while True:
            
            # recieves the message from the client
            msg = recv_message(conn)
            if not msg:
                break

            if msg.get("TYPE") == "SEND" or msg.get("TYPE") == "BROADCAST":
                
                room_instance = chat_rooms.get(room)
                if room_instance:
                    room_instance.send_message(name, msg.get("MESSAGE"), clients)

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

    