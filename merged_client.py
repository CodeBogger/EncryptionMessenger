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
            print(f"[Server]: {msg.get("MESSAGE")}")
        elif msg.get("TYPE") == "BROADCAST":
            print(f"[Broadcast] {msg.get("MESSAGE")}")
        else:
            print(f"Received unknown message type: {msg.get("TYPE")} - MSG: {msg.get("MESSAGE")}")


def main():
    # creates a socket and connects to the server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("72.62.81.113", 5000))

    user = input("Enter your username: ")
    send_message(s, {"TYPE": "SEND", "NAME": user})

    t = threading.Thread(target=reciever_loop, args=(s,), daemon=True)
    t.start()

    # Sender loop
    while True:
        try:
            text = input('You: ')
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