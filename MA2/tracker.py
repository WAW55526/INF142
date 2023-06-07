from collections import defaultdict
from os import environ
from random import choice
from selectors import EVENT_READ, DefaultSelector
from socket import create_server, socket

TRACKER = environ.get("TRACKER", "localhost")

tracker: defaultdict[bytes, set[str]] = defaultdict(set)
selector = DefaultSelector()


def serve(peer: str, data: bytes) -> bytes:
    match data.split(b" ", 1):
        case [b"ADD", file]:
            print(f"Adding {file.decode()}")
            tracker[file].add(peer)
            reply = b"OK "
        case [b"REMOVE", file]:
            try:
                tracker[file].remove(peer)
                if not len(tracker[file]):
                    del tracker[file]
            except ValueError:
                reply = b"BAD File does not exist"
            else:
                reply = b"OK "
        case [b"GET_PEER", file]:
            if peer_set := tracker.get(file):
                reply = b"OK " + choice(tuple(peer_set))[0].encode()
            else:
                reply = b"BAD File does not exist"
        case [b"LIST_FILES"]:
            reply = b"OK " + b" ".join(tracker)
        case _:
            reply = b"BAD Method not supported"
    return reply


def read(conn: socket) -> None:
    request_message = conn.recv(1024)
    if request_message:
        peer = conn.getpeername()
        conn.sendall((serve(peer, request_message)))
    else:
        selector.unregister(conn)
        conn.close()

def accept(sock: socket) -> None:
    conn, address = sock.accept()
    print("accepted", conn, "from", address)
    conn.setblocking(False)
    selector.register(conn, EVENT_READ, read)


def main() -> None:
    sock = create_server((TRACKER, 12000))
    sock.setblocking(False)
    selector.register(sock, EVENT_READ, accept)

    while True:
        events = selector.select()
        for key, _ in events:
            key.data(key.fileobj)


if __name__ == "__main__":
    main()
