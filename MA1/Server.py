from selectors import DefaultSelector, EVENT_READ
from socket import socket
from collections import deque
import random

queue = deque() # Advisors waiting for a question
connections = {} # Connections and their roles {conn : role}
pairs = {} # Keep track of which Advisor is talking to which Advisee {Advisor : Advisee}

def RandomRole(conn):
    #First connection is allways Advisee
    if len(connections) == 0:
        connections[conn] = "Advisee"
        return "Advisee"
    
    #Second connection is allways the opposite of the first
    elif len(connections) == 1:
        existing_role = list(connections.values())[0]
        if existing_role == "Advisee":
            connections[conn] = "Advisor"
        else:
            connections[conn] = "Advisee"
        return connections[conn]
    
    #After we have at least one of each role, the rest will be random
    isAdvisee = random.randint(0, 1)
    if isAdvisee:
        connections[conn] = "Advisee"
    else:
        connections[conn] = "Advisor"
    return connections[conn]

def response(request, conn):
    method, value = request.split(" ", 1) # Split string in two at the first space

    if method == "newrole":
        if conn in connections:
            if connections[conn] == "Advisor":
                connections[conn] = "Advisee"
            else:
                connections[conn] = "Advisor"
            return connections[conn]
        return RandomRole(conn)
    
    elif method == "ask_question": # Only Advisees use this
        if len(queue) == 0:
            return "Queue empty"
        
        advisor = queue.pop()
        pairs[advisor] = conn # Assign advisor to an Advisee {Advisor : Advisee}
        advisor.sendall(value.encode())
        return "Waiting for answer..."
    
    elif method == "answer_question": # Only Advisors use this
        advisee = pairs[conn]
        del pairs[conn] # Remove assignment
        advisee.sendall(value.encode()) # Send answer back to Advisee
        return "OK"

    elif method == "ready": # Advisor enters the queue, waiting for a question 
        queue.appendleft(conn)
        return "Waiting for question..."
    
    else:
        return f"{method} is not a valid method"

def accept(sock): # New connection
    conn, address = sock.accept()
    print("accepted", conn, "from", address)
    conn.setblocking(False)
    sel.register(conn, EVENT_READ)

def read(conn): # New server request
    request_message = conn.recv(1024)
    if not request_message:
        if conn in queue:
            queue.remove(conn)
        del connections[conn] # Remove user from list of connections when they disconnect
        sel.unregister(conn)
        conn.close()
    else:
        conn.sendall((response(request_message.decode(), conn)).encode())


sel = DefaultSelector()
sock = socket()
sock.bind(("localhost", 12000))
sock.listen()
sock.setblocking(False)
sel.register(sock, EVENT_READ, True)

while True:
    events = sel.select()
    for key, _ in events:
        if key.data:
            accept(key.fileobj)
        else:
            read(key.fileobj)