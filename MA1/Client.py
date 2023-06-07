from socket import socket

def request_to_server(sock: socket, message: str) -> str:
    sock.sendall(message.encode())
    return sock.recv(1024).decode()

if __name__ == "__main__":
    sock = socket()
    sock.connect(("localhost", 12000))
    role = request_to_server(sock, "newrole ")
    
    while True:
        print(f"You are {role}")

        if role == "Advisor":
            input("Press enter when ready: ")
            print(request_to_server(sock, "ready "))
            print(sock.recv(1024).decode()) #wait for question
            
            answer = input("Answer> ")
            print(request_to_server(sock, "answer_question " + answer)) # Send answer and get "OK" back

            print("--------------------")
            print("Type 'newrole' to switch to Advisee")
            print("To exit type anything else")
            command = input("> ")
            if command == "newrole":
                role = request_to_server(sock, "newrole ") # Extra space so split() does not get an error
            else:
                break

        else: #Advisee
            question = input("Question> ")
            status = request_to_server(sock, "ask_question " + question)
            while status == "Queue empty":
                print("No available advisor, try again later")
                question = input("Question> ")
                status = request_to_server(sock, "ask_question " + question)
            print(status)
            print(sock.recv(1024).decode()) #Wait for answer

            print("--------------------")
            print("Type 'newrole' to switch to Advisor")
            print("To exit type anything else")
            command = input("> ")
            if command == "newrole":
                role = request_to_server(sock, "newrole ") # Extra space so split() does not get an error
            else:
                break
