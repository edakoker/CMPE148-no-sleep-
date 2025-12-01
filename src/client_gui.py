"""
GUI Chat Client
CMPE 148 - Team No Sleep

Simple graphical interface for the chat application using Tkinter
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import threading
import sys
from client import ReliableClient
from protocol import ProtocolMessage

class ChatGUI:
    """Graphical User Interface for Chat Client"""

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("CMPE 148 Chat - Team No Sleep")
        self.window.geometry("600x500")
        self.window.configure(bg='#2C3E50')

        # Client instance
        self.client = None
        self.connected = False

        # Create UI
        self._create_connection_frame()
        self._create_chat_frame()
        self._create_input_frame()

        # Start with chat disabled
        self._set_chat_enabled(False)

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_connection_frame(self):
        """Create connection controls at the top"""
        conn_frame = tk.Frame(self.window, bg='#34495E', pady=10)
        conn_frame.pack(fill=tk.X, padx=10, pady=(10, 0))

        # Username
        tk.Label(conn_frame, text="Username:", bg='#34495E', fg='white',
                font=('Arial', 10)).pack(side=tk.LEFT, padx=(10, 5))

        self.username_entry = tk.Entry(conn_frame, width=15, font=('Arial', 10))
        self.username_entry.pack(side=tk.LEFT, padx=5)
        self.username_entry.bind('<Return>', lambda e: self.connect())

        # Server (optional)
        tk.Label(conn_frame, text="Server:", bg='#34495E', fg='white',
                font=('Arial', 10)).pack(side=tk.LEFT, padx=(20, 5))

        self.server_entry = tk.Entry(conn_frame, width=12, font=('Arial', 10))
        self.server_entry.insert(0, "127.0.0.1")
        self.server_entry.pack(side=tk.LEFT, padx=5)

        # Port
        tk.Label(conn_frame, text="Port:", bg='#34495E', fg='white',
                font=('Arial', 10)).pack(side=tk.LEFT, padx=(10, 5))

        self.port_entry = tk.Entry(conn_frame, width=6, font=('Arial', 10))
        self.port_entry.insert(0, "5555")
        self.port_entry.pack(side=tk.LEFT, padx=5)

        # Connect button
        self.connect_btn = tk.Button(conn_frame, text="Connect",
                                     command=self.connect,
                                     bg='#27AE60', fg='white',
                                     font=('Arial', 10, 'bold'),
                                     padx=15, cursor='hand2')
        self.connect_btn.pack(side=tk.LEFT, padx=10)

        # Status label
        self.status_label = tk.Label(conn_frame, text="Disconnected",
                                     bg='#34495E', fg='#E74C3C',
                                     font=('Arial', 9, 'italic'))
        self.status_label.pack(side=tk.LEFT, padx=10)

    def _create_chat_frame(self):
        """Create chat display area"""
        chat_frame = tk.Frame(self.window, bg='#2C3E50')
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Chat display with scrollbar
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            width=50,
            height=20,
            font=('Arial', 10),
            bg='#ECF0F1',
            fg='#2C3E50',
            state='disabled'
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # Configure text tags for colors
        self.chat_display.tag_config('system', foreground='#7F8C8D', font=('Arial', 9, 'italic'))
        self.chat_display.tag_config('self', foreground='#2980B9', font=('Arial', 10, 'bold'))
        self.chat_display.tag_config('other', foreground='#27AE60', font=('Arial', 10, 'bold'))
        self.chat_display.tag_config('broadcast', foreground='#E67E22', font=('Arial', 10, 'bold'))
        self.chat_display.tag_config('private', foreground='#8E44AD', font=('Arial', 10, 'bold'))
        self.chat_display.tag_config('error', foreground='#E74C3C', font=('Arial', 10, 'bold'))

    def _create_input_frame(self):
        """Create message input area"""
        input_frame = tk.Frame(self.window, bg='#34495E', pady=10)
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Message entry
        self.msg_entry = tk.Entry(input_frame, font=('Arial', 11))
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5))
        self.msg_entry.bind('<Return>', lambda e: self.send_message())

        # Send button
        self.send_btn = tk.Button(input_frame, text="Send",
                                  command=self.send_message,
                                  bg='#3498DB', fg='white',
                                  font=('Arial', 10, 'bold'),
                                  padx=20, cursor='hand2')
        self.send_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Help text
        help_frame = tk.Frame(self.window, bg='#2C3E50')
        help_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        help_text = "Commands: /broadcast <msg> | /msg <user> <msg> | /quit"
        tk.Label(help_frame, text=help_text, bg='#2C3E50', fg='#95A5A6',
                font=('Arial', 8)).pack()

    def _set_chat_enabled(self, enabled):
        """Enable or disable chat controls"""
        state = 'normal' if enabled else 'disabled'
        self.msg_entry.config(state=state)
        self.send_btn.config(state=state)

    def connect(self):
        """Connect to chat server"""
        if self.connected:
            messagebox.showinfo("Info", "Already connected!")
            return

        username = self.username_entry.get().strip()
        server = self.server_entry.get().strip()
        port_str = self.port_entry.get().strip()

        # Validate inputs
        if not username:
            messagebox.showerror("Error", "Please enter a username!")
            self.username_entry.focus()
            return

        try:
            port = int(port_str)
        except ValueError:
            messagebox.showerror("Error", "Invalid port number!")
            self.port_entry.focus()
            return

        # Disable connection controls
        self.username_entry.config(state='disabled')
        self.server_entry.config(state='disabled')
        self.port_entry.config(state='disabled')
        self.connect_btn.config(state='disabled', text="Connecting...")

        # Create client
        self.client = ReliableClient(server, port)

        # Override display methods to route to GUI
        self.client._display_chat_message = self._display_chat_message
        self.client._display_private_message = self._display_private_message
        self.client._display_broadcast_message = self._display_broadcast_message
        self.client._display_error = self._display_error
        self.client._show_prompt = lambda: None  # Disable terminal prompt

        # Connect in background thread
        def connect_thread():
            if self.client.connect(username):
                self.window.after(0, self._on_connect_success, username)
            else:
                self.window.after(0, self._on_connect_failure)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _on_connect_success(self, username):
        """Called when connection succeeds"""
        self.connected = True
        self.status_label.config(text=f"Connected as {username}", fg='#27AE60')
        self.connect_btn.config(text="Disconnect", state='normal', bg='#E74C3C',
                               command=self.disconnect)
        self._set_chat_enabled(True)
        self.msg_entry.focus()

        self._add_to_chat(f"✓ Connected to {self.server_entry.get()}:{self.port_entry.get()}\n", 'system')
        self._add_to_chat(f"✓ Registered as '{username}'\n", 'system')
        self._add_to_chat("=" * 50 + "\n", 'system')

    def _on_connect_failure(self):
        """Called when connection fails"""
        self.username_entry.config(state='normal')
        self.server_entry.config(state='normal')
        self.port_entry.config(state='normal')
        self.connect_btn.config(state='normal', text="Connect")

        messagebox.showerror("Connection Failed",
                           "Could not connect to server.\nMake sure the server is running.")

    def disconnect(self):
        """Disconnect from server"""
        if self.client and self.connected:
            self.client.disconnect()

        self.connected = False
        self.status_label.config(text="Disconnected", fg='#E74C3C')
        self.connect_btn.config(text="Connect", bg='#27AE60', command=self.connect)
        self._set_chat_enabled(False)

        self.username_entry.config(state='normal')
        self.server_entry.config(state='normal')
        self.port_entry.config(state='normal')

        self._add_to_chat("\n✗ Disconnected from server\n", 'system')

    def send_message(self):
        """Send message from input field"""
        if not self.connected or not self.client:
            return

        message = self.msg_entry.get().strip()
        if not message:
            return

        # Clear input
        self.msg_entry.delete(0, tk.END)

        # Handle commands
        if message.startswith('/'):
            self._handle_command(message)
        else:
            # Regular chat message
            if self.client.send_chat_message(message):
                # Display own message
                self._add_to_chat(f"{self.client.username}: ", 'self')
                self._add_to_chat(f"{message}\n")
            else:
                self._add_to_chat("✗ Failed to send message\n", 'error')

    def _handle_command(self, cmd):
        """Handle slash commands"""
        if cmd.startswith('/broadcast '):
            message = cmd[11:].strip()
            if message:
                if self.client.send_broadcast(message):
                    self._add_to_chat("[BROADCAST] ", 'broadcast')
                    self._add_to_chat(f"{self.client.username}: {message}\n")
                else:
                    self._add_to_chat("✗ Failed to send broadcast\n", 'error')
            else:
                self._add_to_chat("✗ Usage: /broadcast <message>\n", 'error')

        elif cmd.startswith('/msg '):
            parts = cmd[5:].split(None, 1)
            if len(parts) == 2:
                recipient, message = parts
                if self.client.send_private_message(recipient, message):
                    self._add_to_chat(f"[To {recipient}] ", 'private')
                    self._add_to_chat(f"{message}\n")
                else:
                    self._add_to_chat(f"✗ Failed to send private message\n", 'error')
            else:
                self._add_to_chat("✗ Usage: /msg <username> <message>\n", 'error')

        elif cmd == '/quit':
            self.disconnect()

        elif cmd == '/help':
            self._add_to_chat("\nAvailable commands:\n", 'system')
            self._add_to_chat("  /broadcast <msg> - Send to all users\n", 'system')
            self._add_to_chat("  /msg <user> <msg> - Private message\n", 'system')
            self._add_to_chat("  /quit - Disconnect\n", 'system')
            self._add_to_chat("  /help - Show this help\n\n", 'system')

        else:
            self._add_to_chat(f"✗ Unknown command: {cmd.split()[0]}\n", 'error')
            self._add_to_chat("  Type /help for available commands\n", 'error')

    def _display_chat_message(self, message: ProtocolMessage):
        """Display received chat message"""
        username = message.payload.get('username', 'Unknown')
        msg_text = message.payload.get('message', '')

        self.window.after(0, lambda: self._add_to_chat(f"{username}: ", 'other'))
        self.window.after(0, lambda: self._add_to_chat(f"{msg_text}\n"))

    def _display_private_message(self, message: ProtocolMessage):
        """Display private message"""
        sender = message.payload.get('sender', 'Unknown')
        msg_text = message.payload.get('message', '')

        self.window.after(0, lambda: self._add_to_chat(f"[PRIVATE from {sender}] ", 'private'))
        self.window.after(0, lambda: self._add_to_chat(f"{msg_text}\n"))

    def _display_broadcast_message(self, message: ProtocolMessage):
        """Display broadcast message"""
        username = message.payload.get('username', 'Unknown')
        msg_text = message.payload.get('message', '')

        self.window.after(0, lambda: self._add_to_chat(f"[BROADCAST] {username}: ", 'broadcast'))
        self.window.after(0, lambda: self._add_to_chat(f"{msg_text}\n"))

    def _display_error(self, message: ProtocolMessage):
        """Display error message"""
        error = message.payload.get('error', 'Unknown error')

        self.window.after(0, lambda: self._add_to_chat(f"✗ ERROR: {error}\n", 'error'))

    def _add_to_chat(self, text, tag=None):
        """Add text to chat display"""
        self.chat_display.config(state='normal')
        if tag:
            self.chat_display.insert(tk.END, text, tag)
        else:
            self.chat_display.insert(tk.END, text)
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')

    def on_closing(self):
        """Handle window close"""
        if self.connected:
            if messagebox.askokcancel("Quit", "You are still connected. Disconnect and quit?"):
                self.disconnect()
                self.window.destroy()
        else:
            self.window.destroy()

    def run(self):
        """Start the GUI"""
        self.window.mainloop()


def main():
    """Main entry point for GUI client"""
    app = ChatGUI()
    app.run()


if __name__ == '__main__':
    main()
