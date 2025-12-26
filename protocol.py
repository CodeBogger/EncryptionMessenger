import pickle, struct

MAX_LEN = 10 * 1024 * 1024  # 10 MB safety cap

def send_message(sock, obj):
    payload = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
    sock.sendall(struct.pack("!I", len(payload)) + payload)

def recv_exact(sock, n):
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return b""
        data += chunk
    return data

def recv_message(sock):
    header = recv_exact(sock, 4)
    if not header:
        return None
    (length,) = struct.unpack("!I", header)
    if length > MAX_LEN:
        raise ValueError(f"Message too large: {length}")
    payload = recv_exact(sock, length)
    if not payload:
        return None
    return pickle.loads(payload)