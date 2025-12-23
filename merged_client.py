import socket
import threading
from protocol import recv_message, send_message

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
        else:
            print(f"Received unknown message type: {msg.get("TYPE")} - MSG: {msg.get("MESSAGE")}")


def main():
    # creates a socket and connects to the server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("72.62.81.113", 5000))

    user = input("Enter your username: ")
    to_connect = input("Enter the username of the person you want to connect to: ")

    # establishes the connection to the server by passing the a register message
    send_message(s, {"TYPE": "REGISTER", "NAME": user})

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

        send_message(s, {"FROM": user, "TYPE": "SEND", "TO": to_connect, "MESSAGE": text})
    
    try:
        s.close()
    except:
        pass

if __name__ == "__main__":
    main()