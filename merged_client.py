import socket
import threading
from relay_server import chat_rooms
from protocol import recv_message, send_message
from chat_room import chat_room

def create_room(socket, room_name, owner, rooms_dict):
    Room = chat_room(room_name, socket, owner)
    rooms_dict[room_name] = Room

def reciever_loop(s: socket.socket):

    while True:
        msg = recv_message(s)

        if msg is None:
            print("Server disconnected. Exiting...")
            break
            
        if msg.get("TYPE") == "RECIEVE":
            print(f"{msg["FROM"]}: {msg["MESSAGE"]}")
        elif msg.get("TYPE") == "REGISTERED":
            print("You are registered with the server.")
        elif msg.get("TYPE") == "BROADCAST":
            print(f"[Broadcast] {msg.get("MESSAGE")}")
        else:
            print(f"Received unknown message type: {msg.get("TYPE")} - MSG: {msg.get("MESSAGE")}")


def main():
    # creates a socket and connects to the server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("72.62.81.113", 5000))

    user = input("Enter your username: ")

    # displays the chat rooms available
    rooms = chat_rooms

    print("\nAvailable chat rooms:")
    for room_name, room in rooms.items():
        print(f"- {room_name} (Owner: {room.owner()})")
        print(f"  Users: {room.list_users()}")
    print("\n")

    name = None

    if len(rooms) > 0:
        user_choice = None

        while user_choice != "y" and user_choice != "n":
            user_choice = input("Do you want to join an existing chat room? (y/n): ").lower()

        if user_choice == "y":

            while name not in rooms.keys():
                name = input("Enter the name of the chat room to join: ")

        else:
            name = input("Enter a name for the new chat room: ")
            create_room(s, name, user, rooms)
            print("\n")
    else:
        print("No chat rooms available. Please create one on the server first.")
        name = input("Enter a name for the new chat room: ")

        create_room(s, name, user, rooms)
        print("\n")
        

    t = threading.Thread(target=reciever_loop, args=(s,), daemon=True)
    t.start()

    # Sender loop
    while True:
        try:
            text = input()
        except KeyboardInterrupt:
            break
    
        if not text:
            continue
        if text in ("exit", "quit"):
            break

        send_message(s, {"TYPE": "SEND", "FROM": user, "MESSAGE": text})
    
    try:
        s.close()
    except:
        pass

if __name__ == "__main__":
    main()