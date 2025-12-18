import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("72.62.81.113", 5000))

while True:
    msg = input("> ")
    if not msg:
        continue
    s.sendall(msg.encode())
