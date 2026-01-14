import socket
import sys
import threading

class ChatServer:
    def __init__(self, host='0.0.0.0', port=10000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}
    
    def broadcast_user_list(self):
    #function to broadcast list of active participants
        user_list = ', '.join(self.clients.keys())
        message = f"LIST: {user_list}"
        for client in self.clients.values():
           try:
               client.send(message.encode('utf-8'))
           except:
               pass

    def handle_client(self, connection, client_address):
    #function to handle client connections
        print("Connection from", client_address)
        current_username = None
        try:
            #Registration phase
            while True:
                current_username = connection.recv(2048).decode('utf-8').strip()
                if current_username in self.clients:
                    connection.send("Username already taken. Please choose another.".encode('utf-8'))
                else:
                    break
            self.clients[current_username] = connection
            print(f"User {current_username} registered.")
            self.broadcast_user_list()
            
            #MAIN CHAT LOOP
            while True:
                message = connection.recv(2048).decode('utf-8')
                if not message:
                    break
                
                if ':' in message:
                    target_name, content = message.split(':', 1)
                    target_name = target_name.strip()
                    
                    if target_name in self.clients:
                        target_socket = self.clients[target_name]
                        send_format = f"MSG:{current_username}:{content}"
                        target_socket.send(send_format.encode('utf-8'))
                    else:
                        print(f"User {target_name} not found")

        except Exception as e:
            print("Error:", e)
            
        finally:
            if current_username in self.clients:
                del self.clients[current_username]
                self.broadcast_user_list()
            print("Closing connection from", client_address)
            connection.close()


    #Main accept loop
    def start(self):
        try:
            # Bind and open the socket for listening to 5 connections
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5) 
            self.server_socket.settimeout(1.0) #refreshing for inturrupt detection
            print(f"Server started on {self.host}:{self.port}")
            print("Waiting for connections...")
            
            while True:
                try:
                    # 1. Accept new connection
                    client_socket, client_address = self.server_socket.accept()
                    # 2. Spawn a new thread for this client
                    thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
                    thread.daemon=True
                    thread.start()
                except socket.timeout:
                    continue
        except KeyboardInterrupt:
            print("\nInturrupt Detected!\n Server Stopping...\n")       
        except Exception as e:
            print(f"Server failed to start: {e}")
        finally:
            self.server_socket.close()


if __name__ == "__main__":
    server = ChatServer()
    server.start()
