import socket
import sys

#setup client socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('localhost', 10000)
print("Connecting to {} port {}".format(*server_address))
try:    
    client_socket.connect(server_address)
except Exception as e:
    print("Connection failed: {}".format(e))
    sys.exit(1)
print("Connected to server at {}:{}".format(*server_address))
