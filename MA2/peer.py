from os import environ, listdir
from selectors import EVENT_READ, DefaultSelector
from socket import create_connection, create_server, socket
from threading import Thread
import sys

PEER = sys.argv[1]
TRACKER = environ.get("TRACKER", "localhost")
FOLDER = sys.argv[2]

selector = DefaultSelector()


def remote_call(sock: socket, message: bytes) -> bytes:
    """
    Sends a message to a socket and returns the response from the socket.

    Parameters
    ---------
    sock : socket
        A socket object representing the peer we're requesting from.
    message: bytes
        A byte object representing the message to forward.

    Returns
    -------
    answer : bytes
        The response to message we sent
    """
    sock.sendall(message)
    answer = sock.recv(1024)
    return answer


def serve_peer(data: bytes) -> bytes:
    """
    Processes a request from a peer and returns a response.

    Parameters
    ----------
    data: bytes
        A byte object representing the request recieved from a connected peer.

    Returns
    -------
    reply: bytes
        A byte object with the response to the given request.
    """
    match data.split(b" ", 1):
        case [b"GET_FILE", file]:
            try:
                with open(FOLDER + "/" + file.decode(), "rb") as f:
                    content = f.read()
            except FileNotFoundError:
                reply = b"BAD File does not exist"
            else:
                reply = b"OK " + content
        case _:
            reply = b"BAD Method not supported"
    return reply


def read_peer(conn: socket) -> None:
    """
    Reads data from a peer's connection and returns the response

    Parameters
    ----------
    conn: socket
       A socket object representing the connection to the peer 
    """
    request_message = conn.recv(1024)
    if request_message:
        conn.sendall((serve_peer(request_message)))
    else:
        selector.unregister(conn)
        conn.close()


def accept_peer(sock: socket) -> None:
    """
    Accepts a connection from a peer and registers it with the selector instantiated.

    Parameters
    ----------
    sock: socket
        A socket object representing the incoming socket
    """
    conn, address = sock.accept()
    print("accepted", conn, "from", address)
    conn.setblocking(False)
    selector.register(conn, EVENT_READ, read_peer)


def serve_peer_thread() -> None:
    """
    Starts a thread to listen for and process request from peers using selectors.
    """
    sock = create_server((PEER, 12005))
    sock.setblocking(False)
    selector.register(sock, EVENT_READ, accept_peer)


    while True:
        events = selector.select()
        for key, _ in events:
            key.data(key.fileobj)


def add_from_peer(tracker_sock: socket, file: str) -> None:
    """
    Sends a request to the tracker to add a file

    Parameters
    ----------
    tracker_sock: socket
        A socket object representing the connection to the peer.
    file: str
        A string representing the name of the file to add.
    """
    remote_call(tracker_sock, b"ADD " + file.encode())


def connect_to_tracker(address: tuple[str, int]) -> socket:
    """
    Connects to the tracker and adds all local files to its database.

    Parameters
    ----------
    address: tuple[str, int]
        A tuple representing the hostname and port number of the tracer.
    
    Returns
    -------
    tracker_sock: socket
        A socket representing the connection to the tracker.
    """
    tracker_sock = create_connection(address, source_address=(PEER, 0))
    for file in listdir(FOLDER):
        add_from_peer(tracker_sock, file)
    return tracker_sock


def disconnect_from_tracker(tracker_sock: socket) -> None:
    """
    Removes all local files from the tracker's database and closes the connection.
    
    Parameters
    ----------
    trakcer_sock: socket
        A socket representing the connection to the tracker.
    """
    for file in listdir(FOLDER):
        remote_call(tracker_sock, b"REMOVE " + file.encode())
    tracker_sock.close()


def list_files(tracker_sock: socket) -> list[str]:
    """
    Sends a request to the tracker to list all available files.

    Parameters
    ----------
    tracker_sock: socket
        A socket object representing the connection to the socket.

    Returns
    -------
    list_of_files: list[str]
        A list of files available but not in local files.
    """
    _, data = remote_call(tracker_sock, b"LIST_FILES").split(b" ", 1)
    remote_files = data.decode().split()
    local_files = listdir(FOLDER)

    return [file for file in remote_files if file not in local_files]


def get_peer(tracker_sock: socket, file: str) -> str:
    """
    Sends a request to the tracker to get the IP address of a peer with the requested file.

    Parameters
    ----------
    tracker_sock: socket
        A socket object representing the connection to the tracker.
    file: str
        A string representing the name of the requested file.

    Returns
    -------
    A string representing the IP address of the peer with the requested file, or an empty string if no peer is found.
    """
    status, address = remote_call(tracker_sock, b"GET_PEER " + file.encode()).split(b" ", 1)
    match status:
        case b"OK":
            return address.decode()
        case b"BAD":
            return ""


def download_file(peer: str, file: str) -> bool:
    """
    Downloads a file from a peer and saves it to the local directory.

    Parameters
    ----------
    peer: str
        A string representing the IP address of the peer to download from.
    file: str
        A string representing the name of the file to download.

    Returns
    -------
    True if the file was downloaded successfully, False otherwise.
    """
    with create_connection((peer, 12005)) as peer_sock:
        status, content = remote_call(peer_sock, b"GET_FILE " + file.encode()).split(b" ", 1)
        if status == b"BAD":
            print(content)
            return False
    with open(FOLDER + "/" + file, "wb") as f:
        f.write(content)
        return True


def main() -> None:
    Thread(target=serve_peer_thread, daemon=True).start()

    tracker_sock = connect_to_tracker((TRACKER, 12000))
    while True:
        available_files = list_files(tracker_sock)
        
        if not available_files:
            print("No new files")
            if input("Press 'Enter' to see files or 'q' to exit'> ") == 'q':
                break
            continue
        
        number_of_files = len(available_files)
        
        indexes = [str(number) for number in range(number_of_files)]
        
        for index, file in zip(indexes, available_files):
            print(f"{index}\t{file}")
        
        index = input("Index of the file to download or press 'Enter' to see files again> ")
        while index not in indexes + ['', 'q']:
            print(f"Invalid index. Select a number between 0 and {number_of_files-1}")
            index = input("Index of the file to download or press 'Enter' to see files again> ")
            
        if index == '':
            continue
        elif index == 'q':
            break

        file = available_files[int(index)]
        
        peer = get_peer(tracker_sock, file)
        
        if peer and download_file(peer, file):
            add_from_peer(tracker_sock, file)
            print("The file has been downloaded.")
        else:
            print("Download failed")
    
    disconnect_from_tracker(tracker_sock)


if __name__ == "__main__":
    main()
