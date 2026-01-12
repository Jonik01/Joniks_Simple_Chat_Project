import socket
import threading
import sys

#TODO implement GUI version later

host='localhost' #change to fit server address
port=10000

# 1. Function to continuously listen for messages from the server
def receive_messages(sock):
    while True:
        try:
            # Wait for data
            message = sock.recv(1024).decode('utf-8')
            
            if message:
                print(f"\n{message}")
            else:
                # Empty message means server closed connection
                print("\nDisconnected from server.")
                sock.close()
                sys.exit()
                
        except Exception as e:
            print(f"\nError receiving message: {e}")
            sock.close()
            sys.exit()

# 2. Setup Client Socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (host, port)

try:
    print(f"Connecting to {server_address[0]} port {server_address[1]}...")
    client_socket.connect(server_address)
    print("Connected! You can start typing messages.")
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)

#Start the Listening Thread
receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
receive_thread.daemon = True # Kills this thread if the main program exits
receive_thread.start()

# 4. Main Loop: Handle Sending (User Input)
while True:
    try:
        # Wait for user input
        message_to_send = input() 
        
        if message_to_send.lower() == 'quit':
            break
            
        client_socket.send(message_to_send.encode('utf-8'))
        
    except KeyboardInterrupt:
        # Handle Ctrl+C
        break
    except Exception as e:
        print(f"Error sending message: {e}")
        break

print("Closing connection...")
client_socket.close()