import socket
from protocol import send_message, recv_message

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("72.62.81.113", 5000))

# strip whitespace from user inputs
user = input("Enter your name: ").strip()
to_connect = input("Enter the name of the person you want to connect to: ").strip()

# "type" denotes the type of message being sent, in this case being a registration message
send_message(s, {"TYPE": "REGISTER", "NAME": user})

while True:
    msg = input("> ")
    if not msg:
        continue
    
    # the type is a SEND message, that will be sent to the other user
    # each key in dict points to a value that will be used in the relay server file
    send_message(s, {
        "FROM": user,
        "TYPE": "SEND", 
        "TO": to_connect, 
        "MESSAGE": msg
    })
