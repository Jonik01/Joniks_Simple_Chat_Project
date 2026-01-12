import tkinter as tk
from tkinter import messagebox
import socket
import threading

# GUI class for the chat client
class ChatClientGUI:
    def __init__(self):
        self.root=tk.Tk()
        self.root.title("Chat Client")
        self.root.geometry("400x500")
        self.client_socket=None
        self.username=""
        self.current_chat_partner=None
        self.known_users = []

        self.build_login_screen()
        self.root.mainloop()

    #builds initial login screen for the user
    def build_login_screen(self):
        default_value = 'localhost' ##DEFAULT VALUE - Change for convenience
       
        #setup login frame
        self.login_frame=tk.Frame(self.root)
        self.login_frame.pack(fill='both', expand=True, padx=20, pady=20)
        tk.Label(self.login_frame, text="Welcome to Chat", font=("Arial", 20)).pack(pady=20)
       
        #server IP entry
        tk.Label(self.login_frame, text="Server IP:").pack(anchor='w')
        self.ipentry=tk.Entry(self.login_frame)
        self.ipentry.insert(0, default_value)
        self.ipentry.pack(fill='x', pady=5)
       
        #username entry
        tk.Label(self.login_frame, text="Username:").pack(anchor='w')
        self.name_entry=tk.Entry(self.login_frame)
        self.name_entry.pack(fill='x', pady=5)
        #"connect" button
        btn = tk.Button(self.login_frame, text="Connect", command=self.connect_to_server, bg="lightblue")
        btn.pack(fill='x', pady=20)
        #Use 'Enter' to continue
        self.ipentry.bind('<Return>', self.connect_to_server)
        self.name_entry.bind('<Return>', self.connect_to_server)

    #connects to server and builds chat screen
    def connect_to_server(self,event=None):
        ip=self.ipentry.get()
        username = self.name_entry.get().strip()
        if not ip or not username:
            messagebox.showerror("Error", "Please enter both IP and Username")
            return  
        try: #establish connection
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((ip, 10000))
            self.client_socket.recv(1024)
            # Send username for registration
            self.client_socket.send(username.encode('utf-8'))
            self.username = username
            #switch frame to chat screen
            self.login_frame.destroy()
            self.build_list_screen()
            #start listening thread
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect: {e}")

    #chat "contacts" screen
    def build_list_screen(self):
        self.root.geometry("400x500") ##Window Size Control
        self.root.title(f"Logged in as: {self.username}")
        self.list_frame=tk.Frame(self.root)
        self.list_frame.pack(fill='both', expand=True, padx=20, pady=20)
        #title header
        tk.Label(self.list_frame, text="Active Users", font=("Arial", 16, "bold"), bg="#ddd").pack(fill='x', pady=5)
        
        self.users_container = tk.Frame(self.list_frame)
        self.users_container.pack(fill='both', expand=True, padx=10, pady=10)
        if self.known_users:
            self.update_user_list(self.known_users)
        else:
            self.status_label = tk.Label(self.users_container, text="Waiting for user list...", fg="gray")
            self.status_label.pack()

    #Runs in a background thread. Listens for server signals.
    def receive_messages(self):
        while True:
            try:
                # Wait for message
                message = self.client_socket.recv(1024).decode('utf-8')
                # If connection closes, stop loop
                if not message:
                    break
                # Update user list if message contains "List:"
                if message.startswith("LIST:"):
                    user_csv = message[5:] 
                    active_users = user_csv.split(",")
                    self.known_users=active_users
                    #Update list if list is active
                    if hasattr(self, 'list_frame') and self.list_frame.winfo_exists():
                        self.update_user_list(active_users)
                elif message.startswith("MSG:"):
                    # Format: MSG:SenderName:Content
                    parts = message.split(':', 2)
                    sender = parts[1]
                    content = parts[2]
                    # Only show if we are currently chatting with this person
                    if hasattr(self, 'current_chat_partner') and self.current_chat_partner == sender:
                         self.append_message(f"{sender}: {content}")
                    else:
                        print(f"Notification: Message from {sender}")
            
            except Exception as e:
                print(f"Error receiving message: {e}")
                break
    
    #Update the displayed list of active users
    def update_user_list(self, active_users):
        for widget in self.users_container.winfo_children():
            widget.destroy()
        for user in active_users:
            user = user.strip()
            # Skip self
            if user!=self.username and user!="":
                btn = tk.Button(self.users_container, text=f"Chat with {user}", bg="white",  font=("Arial", 12),command=lambda u=user: self.start_chat(u))
                btn.pack(fill='x', pady=2)
            #if no others online
            if len(self.users_container.winfo_children()) == 0:
                tk.Label(self.users_container, text="No other users online", fg="gray").pack()
    
    #Start chat with specific user
    def start_chat(self, target_user):
        self.current_chat_partner = target_user
        #Update to chat frame
        self.list_frame.destroy()
        self.build_chat_screen()

    #Constructing chat UI    
    def build_chat_screen(self):
        #Chat view
        self.root.title(f"Chatting with {self.current_chat_partner}")
        #Main Frame
        self.chat_frame = tk.Frame(self.root)
        self.chat_frame.pack(fill='both', expand=True, padx=10, pady=10)
        #Back button
        back_btn = tk.Button(self.chat_frame, text="<- Back", command=self.go_back_to_list)
        back_btn.pack(anchor='w', pady=5)
        #Chat history
        self.chat_history = tk.Text(self.chat_frame, height=20, state='disabled', bg="#f0f0f0")
        self.chat_history.pack(fill='both', expand=True, pady=5)
        #Input Area
        input_frame = tk.Frame(self.chat_frame)
        input_frame.pack(fill='x', pady=5)
        self.msg_entry = tk.Entry(input_frame)
        self.msg_entry.pack(side='left', fill='x', expand=True, padx=5)
        #Allow 'Enter' key for sending message
        self.msg_entry.bind("<Return>", lambda event: self.send_message()) 
        send_btn = tk.Button(input_frame, text="Send", command=self.send_message, bg="lightgreen")
        send_btn.pack(side='right')
    
    #To return from chat back to users list
    def go_back_to_list(self):
        #End chat and return to list
        self.current_chat_partner = None
        self.chat_frame.destroy()
        self.build_list_screen()

    #New message Handling   
    def send_message(self):
        #Send text to server
        text = self.msg_entry.get()
        if not text:
            return
        #Clear input
        self.msg_entry.delete(0, tk.END)
        #Display my own message in the history
        self.append_message(f"Me: {text}")
        if self.client_socket:
            full_msg = f"{self.current_chat_partner}:{text}"
            self.client_socket.send(full_msg.encode('utf-8'))
    
    #Helper function for scrolling history
    def append_message(self, text):
        self.chat_history.config(state='normal') # Unlock
        self.chat_history.insert(tk.END, text + "\n")
        self.chat_history.config(state='disabled') # Lock again
        self.chat_history.see(tk.END) # Auto-scroll to bottom
    
                    

if __name__ == "__main__":
    ChatClientGUI()