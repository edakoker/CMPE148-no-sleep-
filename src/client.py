"""
Chat Client Implementation
CMPE 148 - Team No Sleep

Demonstrates:
- TCP socket connection to server
- Reliable message delivery with ACK/retransmission
- Timeout handling
- Concurrent send/receive with threading
"""

import socket
import threading
import time
import sys
from typing import Optional, Dict
from protocol import ProtocolMessage, MessageType, MessageBuilder


class ReliableClient:
    """
    Chat client with reliability features

    Implements:
    - Stop-and-Wait ARQ for reliable delivery
    - Timeout and retransmission
    - Sequence number tracking
    """

    def __init__(self, server_host: str = '127.0.0.1', server_port: int = 5555):
        """
        Initialize client

        Args:
            server_host: Server IP address
            server_port: Server port number
        """
        self.server_host = server_host
        self.server_port = server_port
        self.socket: Optional[socket.socket] = None
        self.username: Optional[str] = None

        # Sequence number management
        self.sequence_num = 0
        self.seq_lock = threading.Lock()

        # Reliability: Track messages awaiting ACK
        self.pending_acks: Dict[int, tuple] = {}  # seq_num -> (message, timestamp, retries)
        self.ack_lock = threading.Lock()

        # Timeouts and retries
        self.ACK_TIMEOUT = 2.0  # 2 seconds
        self.MAX_RETRIES = 3

        # Connection state
        self.connected = False
        self.running = False

        # Receive thread
        self.receive_thread: Optional[threading.Thread] = None

    def get_next_sequence(self) -> int:
        """Get next sequence number (thread-safe)"""
        with self.seq_lock:
            seq = self.sequence_num
            self.sequence_num += 1
            return seq

    def connect(self, username: str) -> bool:
        """
        Connect to server and register username

        Demonstrates:
        - TCP 3-way handshake (handled by OS)
        - Application-layer connection establishment
        - Reliable request/response with ACK

        Returns:
            bool: True if connected successfully
        """
        try:
            # Create TCP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Set timeout for connection
            self.socket.settimeout(10.0)

            print(f"[CLIENT] Connecting to {self.server_host}:{self.server_port}...")

            # Connect to server (TCP 3-way handshake)
            self.socket.connect((self.server_host, self.server_port))

            print(f"[CLIENT] TCP connection established")

            # Remove timeout for normal operation
            self.socket.settimeout(None)

            self.running = True
            self.username = username

            # Start receive thread
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()

            # Send connection message
            connect_msg = MessageBuilder.connect_message(username, self.get_next_sequence())

            # Send with reliability (wait for ACK)
            if self._send_reliable(connect_msg):
                self.connected = True
                print(f"[CLIENT] Registered as '{username}'")
                return True
            else:
                print("[CLIENT] Failed to register with server")
                self.disconnect()
                return False

        except socket.timeout:
            print("[CLIENT] Connection timeout")
            return False
        except Exception as e:
            print(f"[CLIENT] Connection error: {e}")
            return False

    def _send_reliable(self, message: ProtocolMessage) -> bool:
        """
        Send message with reliability guarantee

        Implements Stop-and-Wait ARQ:
        1. Send message
        2. Wait for ACK with timeout
        3. Retransmit if timeout
        4. Give up after MAX_RETRIES

        Demonstrates: Reliable data transfer over network

        Returns:
            bool: True if ACK received, False if failed
        """
        seq_num = message.sequence_num
        retries = 0

        while retries <= self.MAX_RETRIES:
            # Send message
            if not self._send_message(message):
                return False

            # Record pending ACK
            with self.ack_lock:
                self.pending_acks[seq_num] = (message, time.time(), retries)

            # Wait for ACK with timeout
            start_time = time.time()
            while time.time() - start_time < self.ACK_TIMEOUT:
                with self.ack_lock:
                    if seq_num not in self.pending_acks:
                        # ACK received!
                        return True
                time.sleep(0.1)

            # Timeout - retransmit
            retries += 1
            if retries <= self.MAX_RETRIES:
                print(f"[CLIENT] Timeout waiting for ACK (seq={seq_num}), retrying {retries}/{self.MAX_RETRIES}...")

        # Failed after all retries
        print(f"[CLIENT] Failed to get ACK after {self.MAX_RETRIES} retries (seq={seq_num})")
        with self.ack_lock:
            if seq_num in self.pending_acks:
                del self.pending_acks[seq_num]
        return False

    def _send_message(self, message: ProtocolMessage) -> bool:
        """
        Send message over socket (no reliability)

        Args:
            message: ProtocolMessage to send

        Returns:
            bool: True if sent
        """
        try:
            data = message.serialize()
            # Length-prefixed framing
            length_prefix = len(data).to_bytes(4, byteorder='big')
            self.socket.sendall(length_prefix + data)
            return True
        except Exception as e:
            print(f"[CLIENT] Send error: {e}")
            self.connected = False
            return False

    def _receive_loop(self):
        """
        Receive messages from server (runs in separate thread)

        Demonstrates: Concurrent operations - simultaneous send/receive
        """
        while self.running:
            try:
                message = self._receive_message()
                if message is None:
                    break

                self._handle_received_message(message)

            except Exception as e:
                if self.running:
                    print(f"[CLIENT] Receive error: {e}")
                break

        self.connected = False
        self.running = False

    def _receive_message(self) -> Optional[ProtocolMessage]:
        """
        Receive a complete message from socket

        Returns:
            ProtocolMessage or None
        """
        try:
            # Receive length prefix
            length_data = self._recv_exact(4)
            if not length_data:
                return None

            msg_length = int.from_bytes(length_data, byteorder='big')

            # Receive message
            msg_data = self._recv_exact(msg_length)
            if not msg_data:
                return None

            # Deserialize
            message = ProtocolMessage.deserialize(msg_data)
            return message

        except Exception as e:
            if self.running:
                print(f"[CLIENT] Receive error: {e}")
            return None

    def _recv_exact(self, length: int) -> Optional[bytes]:
        """Receive exact number of bytes"""
        data = b''
        while len(data) < length:
            chunk = self.socket.recv(length - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def _handle_received_message(self, message: ProtocolMessage):
        """
        Handle received message based on type
        """
        msg_type = message.msg_type

        # Handle ACK messages - remove from pending
        if msg_type in [MessageType.CONNECT_ACK, MessageType.CHAT_ACK,
                        MessageType.BROADCAST_ACK, MessageType.PRIVATE_ACK,
                        MessageType.HEARTBEAT_ACK]:
            self._handle_ack(message)

        # Handle NACK - negative acknowledgment
        elif msg_type == MessageType.NACK:
            self._handle_nack(message)

        # Handle incoming chat/broadcast messages
        elif msg_type == MessageType.CHAT_MSG:
            self._display_chat_message(message)
            # Send ACK back
            ack = message.create_ack()
            self._send_message(ack)

        elif msg_type == MessageType.BROADCAST:
            self._display_broadcast_message(message)
            # Send ACK back
            ack = message.create_ack()
            self._send_message(ack)

        elif msg_type == MessageType.PRIVATE_MSG:
            self._display_private_message(message)
            # Send ACK back
            ack = message.create_ack()
            self._send_message(ack)

        elif msg_type == MessageType.ERROR:
            self._display_error(message)

        elif msg_type == MessageType.HEARTBEAT:
            # Respond to heartbeat
            ack = message.create_ack()
            self._send_message(ack)

    def _handle_ack(self, message: ProtocolMessage):
        """
        Handle ACK received from server

        Demonstrates: Reliability - ACK processing
        """
        ack_for = message.payload.get('ack_for')
        if ack_for is not None:
            with self.ack_lock:
                if ack_for in self.pending_acks:
                    del self.pending_acks[ack_for]

    def _handle_nack(self, message: ProtocolMessage):
        """Handle negative acknowledgment"""
        nack_for = message.payload.get('nack_for')
        reason = message.payload.get('reason', 'Unknown error')
        print(f"[ERROR] Message {nack_for} rejected: {reason}")

        with self.ack_lock:
            if nack_for in self.pending_acks:
                del self.pending_acks[nack_for]

    def _display_chat_message(self, message: ProtocolMessage):
        """Display received chat message"""
        username = message.payload.get('username', 'Unknown')
        msg_text = message.payload.get('message', '')
        print(f"\n{username}: {msg_text}")
        self._show_prompt()

    def _display_broadcast_message(self, message: ProtocolMessage):
        """Display broadcast message"""
        username = message.payload.get('username', 'Unknown')
        msg_text = message.payload.get('message', '')
        print(f"\n[BROADCAST] {username}: {msg_text}")
        self._show_prompt()

    def _display_private_message(self, message: ProtocolMessage):
        """Display private message"""
        sender = message.payload.get('sender', 'Unknown')
        msg_text = message.payload.get('message', '')
        print(f"\n[PRIVATE from {sender}]: {msg_text}")
        self._show_prompt()

    def _display_error(self, message: ProtocolMessage):
        """Display error message"""
        error = message.payload.get('error', 'Unknown error')
        print(f"\n[ERROR] {error}")
        self._show_prompt()

    def _show_prompt(self):
        """Show input prompt"""
        print(f"{self.username}> ", end='', flush=True)

    def send_chat_message(self, message: str) -> bool:
        """
        Send a chat message

        Args:
            message: Message text

        Returns:
            bool: True if sent successfully
        """
        if not self.connected:
            print("[ERROR] Not connected to server")
            return False

        chat_msg = MessageBuilder.chat_message(
            self.username,
            message,
            self.get_next_sequence()
        )

        return self._send_reliable(chat_msg)

    def send_broadcast(self, message: str) -> bool:
        """Send broadcast message to all users"""
        if not self.connected:
            print("[ERROR] Not connected to server")
            return False

        broadcast_msg = MessageBuilder.broadcast_message(
            self.username,
            message,
            self.get_next_sequence()
        )

        return self._send_reliable(broadcast_msg)

    def send_private_message(self, recipient: str, message: str) -> bool:
        """
        Send private message to specific user

        Args:
            recipient: Username of recipient
            message: Message text

        Returns:
            bool: True if sent
        """
        if not self.connected:
            print("[ERROR] Not connected to server")
            return False

        private_msg = MessageBuilder.private_message(
            self.username,
            recipient,
            message,
            self.get_next_sequence()
        )

        return self._send_reliable(private_msg)

    def disconnect(self):
        """Disconnect from server"""
        if self.connected:
            disconnect_msg = MessageBuilder.disconnect_message(
                self.username,
                self.get_next_sequence()
            )
            self._send_message(disconnect_msg)

        self.connected = False
        self.running = False

        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        print("[CLIENT] Disconnected")

    def run_interactive(self):
        """
        Run interactive chat interface

        Commands:
        - /broadcast <message> - Send to all users
        - /msg <user> <message> - Send private message
        - /quit - Exit
        - Otherwise: regular chat message
        """
        print("\n=== Chat Client ===")
        print("Commands:")
        print("  /broadcast <message> - Send to all users")
        print("  /msg <user> <message> - Private message")
        print("  /quit - Exit")
        print("=" * 50)

        self._show_prompt()

        try:
            while self.connected:
                user_input = input()

                if not user_input:
                    self._show_prompt()
                    continue

                # Parse commands
                if user_input.startswith('/quit'):
                    break

                elif user_input.startswith('/broadcast '):
                    message = user_input[11:].strip()
                    if message:
                        self.send_broadcast(message)

                elif user_input.startswith('/msg '):
                    parts = user_input[5:].split(None, 1)
                    if len(parts) == 2:
                        recipient, message = parts
                        self.send_private_message(recipient, message)
                    else:
                        print("[ERROR] Usage: /msg <username> <message>")

                else:
                    # Regular chat message
                    self.send_chat_message(user_input)

                self._show_prompt()

        except KeyboardInterrupt:
            print("\n[CLIENT] Interrupted")
        except EOFError:
            pass
        finally:
            self.disconnect()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python client.py <username> [host] [port]")
        sys.exit(1)

    username = sys.argv[1]
    host = sys.argv[2] if len(sys.argv) > 2 else '127.0.0.1'
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 5555

    client = ReliableClient(host, port)

    if client.connect(username):
        client.run_interactive()


if __name__ == '__main__':
    main()
