import tkinter as tk
from tkinter import messagebox
import socket
import threading

#TODO add new message notifications
#TODO add indicator to username at all times
#TODO modernize UI

# GUI class for the chat client
class ChatClientGUI:
    default_ip = 'localhost' ##Default value, Change for convenince
    def __init__(self):
        self.root=tk.Tk()
        self.root.title("Chat Client")
        self.root.geometry("400x600")
        self.colors={
            'bg': "#e9e9e9",        # Light Grey (Main Background)
            'header': '#2f3640',    # Dark Slate (Top bars)
            'text_light': 'white',  # Text on dark backgrounds
            'accent': '#00a8ff',    # Bright Blue (Buttons)
            'alert': '#e84118',     # Red (Notifications/Disconnects)
            'me_msg': 'blue',       # My message color
            'partner_msg': "#029109",  # Partner message color
            'partner_header': "#03D10D" #Partner Header color
        }
        self.root.configure(bg=self.colors['bg'])

        self.client_socket=None
        self.username=""
        self.current_chat_partner=None
        self.known_users = []
        self.chat_log={}
        self.last_ip = self.default_ip 
        self.last_username = ""
        self.unread_messages={}

        self.build_login_screen()
        self.root.mainloop()

    #builds initial login screen for the user
    def build_login_screen(self):

        #setup login frame
        self.login_frame=tk.Frame(self.root,bg=self.colors['bg'])
        self.login_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        #Header label
        tk.Label(self.login_frame, text="Welcome to Chat", bg=self.colors['bg'], font=("Segoe UI", 20, "bold")).pack(pady=20)
       
        #server IP entry
        tk.Label(self.login_frame, text="Server IP:", bg=self.colors['bg']).pack(anchor='w')
        self.ipentry = tk.Entry(self.login_frame, font=("Segoe UI", 12), relief="flat")
        self.ipentry.insert(0, self.last_ip)
        self.ipentry.pack(fill='x', pady=5)
       
        #username entry
        tk.Label(self.login_frame, text="Username:", bg=self.colors['bg']).pack(anchor='w')
        self.name_entry = tk.Entry(self.login_frame, font=("Segoe UI", 12), relief="flat")
        self.name_entry.insert(0, self.last_username)
        self.name_entry.pack(fill='x', pady=5)
        
        #"connect" button
        btn = tk.Button(self.login_frame, text="Connect", command=self.connect_to_server, 
                        bg=self.colors['accent'], fg='white', 
                        font=("Segoe UI", 12, "bold"), relief="flat")
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
            # Send username for registration
            self.client_socket.send(username.encode('utf-8'))
            response = self.client_socket.recv(1024).decode('utf-8')
            #Check username availability
            if "taken" in response:
                messagebox.showerror("Login failed", "Username already taken")
                self.client_socket.close()
                return
            if "LIST:" in response:
                list_part = response.split("LIST:")[1]
                self.known_users = list_part.split(",")

            ## IF REACHED - USER CONNECTED ##
            self.username = username
            self.last_ip = ip
            self.last_username = username
            #switch frame to chat screen
            self.login_frame.destroy()
            self.build_list_screen()
            #start listening thread
            threading.Thread(target=self.receive_messages, daemon=True).start()
        
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect: {e}")

    #Creates dark bar with (Name | IP)
    def build_status_bar(self, parent_frame):
        status_frame = tk.Frame(parent_frame, bg=self.colors['header'], height=30)
        status_frame.pack(side='bottom', fill='x')
         #Text (Name | IP)
        status_text = f" Logged in as: {self.username}  |  Server: {self.last_ip}"
        lbl = tk.Label(status_frame, text=status_text, 
                       bg=self.colors['header'], fg=self.colors['text_light'], 
                       font=("Helvetica", 9))
        lbl.pack(side='left', padx=10, pady=5)
        #Logout Button
        logout_btn = tk.Button(status_frame, text="Logout", 
                               bg=self.colors['header'], fg=self.colors['alert'], 
                               font=("Segoe UI", 9, "bold"), relief="flat",
                               activebackground=self.colors['header'],
                               activeforeground="white",
                               command=self.logout)
        logout_btn.pack(side='right', padx=10, pady=5)

    #Chat users list
    def build_list_screen(self):
        #Clear the window
        for widget in self.root.winfo_children():
            widget.destroy()
            
        #Main Container
        self.list_frame = tk.Frame(self.root, bg=self.colors['bg'])
        self.list_frame.pack(fill='both', expand=True)

        #Header
        header = tk.Frame(self.list_frame, bg=self.colors['header'], height=60)
        header.pack(fill='x')
        tk.Label(header, text="Active Users", bg=self.colors['header'], 
                 fg=self.colors['text_light'], font=("Segoe UI", 18, "bold")).pack(pady=15)

        #Container for User Buttons
        self.users_container = tk.Frame(self.list_frame, bg=self.colors['bg'])
        self.users_container.pack(fill='both', expand=True, padx=20, pady=20)

        #Populate List (or show waiting text)
        if self.known_users:
            self.update_user_list(self.known_users)
        else:
            self.status_label = tk.Label(self.users_container, text="Waiting for users...", 
                                         bg=self.colors['bg'], fg="gray")
            self.status_label.pack()
            
        #Status Bar
        self.build_status_bar(self.list_frame)
    
    
    #Runs in a background thread. Listens for server signals.
    def receive_messages(self):
        while True:
            try:
                # Wait for message
                if self.client_socket:
                    message = self.client_socket.recv(1024).decode('utf-8')
                else:
                    break
                
                # If connection closes, stop loop
                if not message:
                    self.root.after(0,self.handle_disconnect)
                    break
                
                # Update user list if message contains "List:"
                if message.startswith("LIST:"):
                    user_csv = message[5:] 
                    active_users = user_csv.split(",")
                    self.known_users=active_users
                    #Update list if list is active
                    if hasattr(self, 'list_frame') and self.list_frame.winfo_exists():
                        self.root.after(0,self.update_user_list,active_users)
                
                #Handle chat messages. (Format: MSG:SenderName:Content)
                elif message.startswith("MSG:"):
                    parts = message.split(':', 2)
                    sender = parts[1]
                    content = parts[2]

                    #If user disconnects while in chat
                    if sender=="Server":
                        expected_message=f"{self.current_chat_partner} has left the chat."
                        if self.current_chat_partner and content == expected_message:
                            self.root.after(0,self.on_partner_disconnect)
                        continue
                    
                    #Save to chat log
                    if sender not in self.chat_log:
                        self.chat_log[sender]=[]
                    self.chat_log[sender].append(f"{sender}: {content}")

                    # Only show if we are currently chatting with this person
                    if hasattr(self, 'current_chat_partner') and self.current_chat_partner == sender:
                         #Show if chatting
                         self.append_message(f"{sender}: {content}", "partner_msg")
                    else:
                        #Add to unread if not chatting
                        self.unread_messages[sender] = self.unread_messages.get(sender, 0) + 1
                        
                        # Refresh the list screen so notification appears
                        if hasattr(self, 'list_frame') and self.list_frame.winfo_exists():
                            self.root.after(0, self.update_user_list, self.known_users)
            
            except Exception as e:
                print(f"Connection lost: {e}")
                # Trigger disconnect on error
                self.root.after(0, self.handle_disconnect)
                break
    
    #Update the displayed list of active users
    def update_user_list(self, active_users):
        #Clear old widgets
        for widget in self.users_container.winfo_children():
            widget.destroy()
        
        for user in active_users:
            user = user.strip()
            # Skip self
            if user!=self.username and user!="":
                #TODO implement unread
                unread_count = self.unread_messages.get(user, 0)
                
                ## COMPLEX BUTTON (User | unread messages(amount)) ##
                
                #Create Row (button bg)
                row_frame = tk.Frame(self.users_container, bg="white", cursor="hand2")
                row_frame.pack(fill='x', pady=2)
                #Name Label (Black Text)
                name_lbl = tk.Label(row_frame, text=f"  {user}", bg="white", fg="black", 
                                    font=("Segoe UI", 12, "bold"), anchor="w")
                name_lbl.pack(side='left', fill='x', expand=True, ipady=10)
                #Unread Label (Red Text) - Only if unread messages exist
                if unread_count > 0:
                    count_text = f"({unread_count} New!)  "
                    count_lbl = tk.Label(row_frame, text=count_text, bg="white", 
                                         fg=self.colors['alert'], # Red
                                         font=("Segoe UI", 12))
                    count_lbl.pack(side='right')
                    
                    # Make the red text clickable too
                    count_lbl.bind("<Button-1>", lambda e, u=user: self.start_chat(u))

                #Make clickable
                row_frame.bind("<Button-1>", lambda e, u=user: self.start_chat(u))
                name_lbl.bind("<Button-1>", lambda e, u=user: self.start_chat(u))
    
    #Start chat with specific user
    def start_chat(self, target_user):
        self.current_chat_partner = target_user
        #Mark messages as read
        if target_user in self.unread_messages:
            self.unread_messages[target_user] = 0
        # Switch to chat screen
        self.list_frame.destroy()
        self.build_chat_screen()
        # Load History
        if target_user in self.chat_log:
            for msg in self.chat_log[target_user]:
                # Who sent the message (for coloring)
                tag = "me_msg" if msg.startswith("Me:") else "partner_msg"
                self.append_message(msg, tag)

    #Constructing chat UI    
    def build_chat_screen(self):
        #Frame Setup
        self.chat_frame = tk.Frame(self.root, bg=self.colors['bg'])
        self.chat_frame.pack(fill='both', expand=True)
        
        #Header
        header = tk.Frame(self.chat_frame, bg=self.colors['header'], height=50)
        header.pack(fill='x')
        
        #Back Button
        back_btn = tk.Button(header, text="◀ Back", command=self.go_back_to_list,
                             bg=self.colors['header'], fg='white', relief='flat', font=("Arial", 12, "bold"))
        back_btn.pack(side='left', padx=10)
        
        #Title
        tk.Label(header, text=f"{self.current_chat_partner}", 
                 bg=self.colors['header'], fg=self.colors['partner_header'], font=("Segoe UI", 15, "bold")).pack(side='left', padx=20, pady=5)

        #Chat History (White Box)
        self.chat_history = tk.Text(self.chat_frame, height=20, state='disabled', 
                                    bg="white", font=("Segoe UI", 10), relief="flat", padx=10, pady=10)
        self.chat_history.pack(fill='both', expand=True, padx=10, pady=10)
        
        #[COLORS] Register tags for Blue/Green text
        self.chat_history.tag_config('alert', foreground=self.colors['alert'])
        self.chat_history.tag_config('me_msg', foreground=self.colors['me_msg'])
        self.chat_history.tag_config('partner_msg', foreground=self.colors['partner_msg'])
        
        #Input Area
        input_frame = tk.Frame(self.chat_frame, bg=self.colors['bg'])
        input_frame.pack(fill='x', padx=10, pady=5)
        self.msg_entry = tk.Entry(input_frame, font=("Segoe UI", 12), relief="flat", bg="white")
        self.msg_entry.pack(side='left', fill='x', expand=True, padx=5, ipady=5)
        self.msg_entry.bind("<Return>", lambda event: self.send_message()) 
        send_btn = tk.Button(input_frame, text="SEND", command=self.send_message, 
                             bg=self.colors['accent'], fg='white', relief='flat', font=("Segoe UI", 10, "bold"))
        send_btn.pack(side='right', ipadx=10)

        # Status Bar
        self.build_status_bar(self.chat_frame)
    
    #To return from chat back to users list
    def go_back_to_list(self, events=None):
        #End chat and return to list
        self.root.unbind("<Key>")
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
        
        #Save own message to log
        msg_to_save=f"Me: {text}"
        if self.current_chat_partner not in self.chat_log:
            self.chat_log[self.current_chat_partner]=[]
        self.chat_log[self.current_chat_partner].append(msg_to_save)
        
        #Display my own message in the history
        self.append_message(f"Me: {text}")
        if self.client_socket:
            full_msg = f"{self.current_chat_partner}:{text}"
            self.client_socket.send(full_msg.encode('utf-8'))
    
    #Helper function for scrolling history
    def append_message(self, text, tags=None):
        self.chat_history.config(state='normal') # Unlock
        self.chat_history.insert(tk.END, text + "\n",tags)
        self.chat_history.config(state='disabled') # Lock again
        self.chat_history.see(tk.END) # Auto-scroll to bottom
    
    #Display msg and go back to list on partner disconnect
    def on_partner_disconnect(self):
        msg = f"User '{self.current_chat_partner}' has left the chat."
        self.append_message(msg, "alert")
        self.append_message("Press any key to return to list...", "alert")
        #Freeze inputs
        self.msg_entry.config(state='disabled')
        #Bind inputs to go back to list
        self.chat_frame.focus_set()
        self.root.bind("<Key>", self.go_back_to_list)

    def logout(self):
        self.handle_disconnect(show_alert=False)

    #Handles user disconnects
    def handle_disconnect(self,show_alert=True):
        #Dont run again if connection closed
        if not self.client_socket:
            return
        #Cleanup sockets
        try:
            self.client_socket.close()
        except:
            pass
        self.client_socket=None
        
        if show_alert==True:
            messagebox.showerror("Disconnected","Lost connection to server. Returning to login screen") #Notify user about disconnect
        
        #Destroy widgets
        self.root.unbind("<Key>")
        for widget in self.root.winfo_children():
            widget.destroy()
        #Reset info
        self.username = ""
        self.current_chat_partner = None
        self.known_users = []
        self.chat_log = {}
        self.unread_messages = {}
        #Reframe to login
        self.build_login_screen()
    
                    

if __name__ == "__main__":
    ChatClientGUI()