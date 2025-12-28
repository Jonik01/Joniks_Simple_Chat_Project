import socket
import sys

#setup server socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('localhost', 10000)
print("connecting to {} port {}".format(*server_address))
sock.bind(server_address)

#start listening for incoming connections
sock.listen(1)
while True:
    print("Awaiting connection...")
    connection, client_address = sock.accept()
print("Connection from", client_address)

