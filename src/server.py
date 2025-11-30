"""
Chat Server Implementation
CMPE 148 - Team No Sleep

Demonstrates:
- Socket programming with TCP
- Multi-client handling with threading
- Application-layer protocol implementation
- Connection state management
- Message broadcasting (multiplexing)
"""

import socket
import threading
import time
from typing import Dict, Optional
from protocol import ProtocolMessage, MessageType, MessageBuilder


class ClientConnection:
    """
    Represents a single client connection
    Maintains connection state and reliability information
    """

    def __init__(self, conn: socket.socket, addr: tuple, client_id: int):
        self.conn = conn
        self.addr = addr
        self.client_id = client_id
        self.username: Optional[str] = None
        self.connected = True
        self.last_heartbeat = time.time()

        # Reliability: Track sent messages awaiting ACK
        self.pending_acks: Dict[int, ProtocolMessage] = {}
        self.lock = threading.Lock()

    def send_message(self, message: ProtocolMessage) -> bool:
        """
        Send a message to this client over TCP socket

        Args:
            message: ProtocolMessage to send

        Returns:
            bool: True if sent successfully
        """
        try:
            data = message.serialize()
            # Send length prefix first (4 bytes) for message framing
            length_prefix = len(data).to_bytes(4, byteorder='big')
            self.conn.sendall(length_prefix + data)
            return True
        except Exception as e:
            print(f"Error sending to {self.username or self.addr}: {e}")
            self.connected = False
            return False

    def close(self):
        """Close the client connection"""
        try:
            self.conn.close()
        except:
            pass
        self.connected = False


class ChatServer:
    """
    Multi-threaded Chat Server implementing custom protocol

    Architecture:
    - Main thread: Accept incoming connections
    - Per-client threads: Handle individual client messages
    - Broadcast thread: Send periodic heartbeats
    """

    def __init__(self, host: str = '127.0.0.1', port: int = 5555):
        """
        Initialize chat server

        Args:
            host: Server IP address (localhost for testing)
            port: Port number (application-layer port)
        """
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None

        # Client management
        self.clients: Dict[int, ClientConnection] = {}
        self.clients_lock = threading.Lock()
        self.next_client_id = 1

        # Username to client mapping
        self.username_to_client: Dict[str, ClientConnection] = {}

        # Server sequence number for messages
        self.sequence_num = 0
        self.seq_lock = threading.Lock()

        # Server state
        self.running = False

    def get_next_sequence(self) -> int:
        """Get next sequence number (thread-safe)"""
        with self.seq_lock:
            seq = self.sequence_num
            self.sequence_num += 1
            return seq

    def start(self):
        """
        Start the server and begin accepting connections

        Demonstrates: Socket programming - server setup
        1. Create socket (TCP)
        2. Bind to address
        3. Listen for connections
        4. Accept connections in loop
        """
        try:
            # Create TCP socket
            # AF_INET = IPv4, SOCK_STREAM = TCP
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Set socket options: allow address reuse
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind to address (IP + Port)
            self.server_socket.bind((self.host, self.port))

            # Listen for connections (backlog = 5)
            self.server_socket.listen(5)

            self.running = True
            print(f"[SERVER] Started on {self.host}:{self.port}")
            print(f"[SERVER] Waiting for connections...")

            # Start heartbeat thread
            heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            heartbeat_thread.start()

            # Accept connections loop
            while self.running:
                try:
                    # Accept blocks until a client connects
                    # Returns: (socket object, address)
                    conn, addr = self.server_socket.accept()

                    # Create client connection object
                    with self.clients_lock:
                        client_id = self.next_client_id
                        self.next_client_id += 1
                        client_conn = ClientConnection(conn, addr, client_id)
                        self.clients[client_id] = client_conn

                    print(f"[SERVER] New connection from {addr} (ID: {client_id})")

                    # Spawn new thread to handle this client
                    # Demonstrates: Multiplexing - handling multiple clients
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_conn,),
                        daemon=True
                    )
                    client_thread.start()

                except Exception as e:
                    if self.running:
                        print(f"[SERVER] Error accepting connection: {e}")

        except Exception as e:
            print(f"[SERVER] Fatal error: {e}")
        finally:
            self.stop()

    def _handle_client(self, client: ClientConnection):
        """
        Handle messages from a single client (runs in separate thread)

        Demonstrates:
        - Protocol message handling
        - State management
        - Reliable delivery with ACKs
        """
        print(f"[SERVER] Handler started for client {client.client_id}")

        try:
            while client.connected and self.running:
                # Receive message with length prefix
                message = self._receive_message(client.conn)

                if message is None:
                    # Connection closed or error
                    break

                # Update last heartbeat time
                client.last_heartbeat = time.time()

                # Process message based on type
                self._process_message(client, message)

        except Exception as e:
            print(f"[SERVER] Error handling client {client.username or client.client_id}: {e}")
        finally:
            self._disconnect_client(client)

    def _receive_message(self, conn: socket.socket) -> Optional[ProtocolMessage]:
        """
        Receive a complete protocol message from socket

        Message framing:
        1. Receive 4-byte length prefix
        2. Receive exact number of bytes specified
        3. Deserialize into ProtocolMessage

        Returns:
            ProtocolMessage or None if connection closed
        """
        try:
            # Receive length prefix (4 bytes)
            length_data = self._recv_exact(conn, 4)
            if not length_data:
                return None

            msg_length = int.from_bytes(length_data, byteorder='big')

            # Receive exact message length
            msg_data = self._recv_exact(conn, msg_length)
            if not msg_data:
                return None

            # Deserialize
            message = ProtocolMessage.deserialize(msg_data)
            return message

        except Exception as e:
            print(f"[SERVER] Error receiving message: {e}")
            return None

    def _recv_exact(self, conn: socket.socket, length: int) -> Optional[bytes]:
        """
        Receive exact number of bytes from socket
        TCP is stream-based, so we need to loop until we get all bytes
        """
        data = b''
        while len(data) < length:
            chunk = conn.recv(length - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def _process_message(self, client: ClientConnection, message: ProtocolMessage):
        """
        Process received message based on type

        Demonstrates: Application-layer protocol handling
        """
        msg_type = message.msg_type

        if msg_type == MessageType.CONNECT:
            self._handle_connect(client, message)

        elif msg_type == MessageType.DISCONNECT:
            self._handle_disconnect(client, message)

        elif msg_type == MessageType.CHAT_MSG:
            self._handle_chat_message(client, message)

        elif msg_type == MessageType.BROADCAST:
            self._handle_broadcast(client, message)

        elif msg_type == MessageType.PRIVATE_MSG:
            self._handle_private_message(client, message)

        elif msg_type == MessageType.HEARTBEAT:
            self._handle_heartbeat(client, message)

        elif msg_type in [MessageType.CHAT_ACK, MessageType.BROADCAST_ACK,
                          MessageType.PRIVATE_ACK, MessageType.CONNECT_ACK]:
            self._handle_ack(client, message)

        else:
            print(f"[SERVER] Unknown message type: {msg_type}")

    def _handle_connect(self, client: ClientConnection, message: ProtocolMessage):
        """Handle client connection request"""
        username = message.payload.get('username', f'User{client.client_id}')

        # Check if username is taken
        with self.clients_lock:
            if username in self.username_to_client:
                # Send NACK
                nack = message.create_nack("Username already taken")
                client.send_message(nack)
                return

            # Register username
            client.username = username
            self.username_to_client[username] = client

        print(f"[SERVER] Client {client.client_id} registered as '{username}'")

        # Send ACK
        ack = message.create_ack()
        client.send_message(ack)

        # Broadcast join message to all other clients
        join_msg = MessageBuilder.broadcast_message(
            'SERVER',
            f'{username} has joined the chat',
            self.get_next_sequence()
        )
        self._broadcast_message(join_msg, exclude_client=client)

    def _handle_disconnect(self, client: ClientConnection, message: ProtocolMessage):
        """Handle client disconnect request"""
        ack = message.create_ack()
        client.send_message(ack)
        client.connected = False

    def _handle_chat_message(self, client: ClientConnection, message: ProtocolMessage):
        """
        Handle regular chat message

        Demonstrates: Reliability - send ACK back to sender
        """
        username = message.payload.get('username', client.username)
        msg_text = message.payload.get('message', '')

        print(f"[CHAT] {username}: {msg_text}")

        # Send ACK to sender
        ack = message.create_ack()
        client.send_message(ack)

        # Broadcast to all other clients
        self._broadcast_message(message, exclude_client=client)

    def _handle_broadcast(self, client: ClientConnection, message: ProtocolMessage):
        """Handle broadcast message"""
        username = message.payload.get('username', client.username)
        msg_text = message.payload.get('message', '')

        print(f"[BROADCAST] {username}: {msg_text}")

        # Send ACK to sender
        ack = message.create_ack()
        client.send_message(ack)

        # Broadcast to all clients including sender
        self._broadcast_message(message)

    def _handle_private_message(self, client: ClientConnection, message: ProtocolMessage):
        """
        Handle private message to specific user

        Demonstrates: Message routing in application layer
        """
        sender = message.payload.get('sender', client.username)
        recipient = message.payload.get('recipient')
        msg_text = message.payload.get('message', '')

        print(f"[PRIVATE] {sender} -> {recipient}: {msg_text}")

        # Send ACK to sender
        ack = message.create_ack()
        client.send_message(ack)

        # Forward to recipient
        with self.clients_lock:
            recipient_client = self.username_to_client.get(recipient)

        if recipient_client and recipient_client.connected:
            recipient_client.send_message(message)
        else:
            # Recipient not found - send error
            error_msg = MessageBuilder.error_message(
                f"User '{recipient}' not found or offline",
                self.get_next_sequence()
            )
            client.send_message(error_msg)

    def _handle_heartbeat(self, client: ClientConnection, message: ProtocolMessage):
        """Handle heartbeat/keepalive message"""
        ack = message.create_ack()
        client.send_message(ack)

    def _handle_ack(self, client: ClientConnection, message: ProtocolMessage):
        """Handle ACK received from client"""
        ack_for = message.payload.get('ack_for')
        if ack_for is not None:
            with client.lock:
                if ack_for in client.pending_acks:
                    del client.pending_acks[ack_for]

    def _broadcast_message(self, message: ProtocolMessage, exclude_client: Optional[ClientConnection] = None):
        """
        Broadcast message to all connected clients

        Demonstrates: Multiplexing - sending to multiple destinations
        """
        with self.clients_lock:
            clients_to_send = [c for c in self.clients.values()
                             if c.connected and c != exclude_client and c.username]

        for client in clients_to_send:
            client.send_message(message)

    def _disconnect_client(self, client: ClientConnection):
        """Clean up client disconnection"""
        print(f"[SERVER] Client {client.username or client.client_id} disconnected")

        with self.clients_lock:
            if client.client_id in self.clients:
                del self.clients[client.client_id]

            if client.username and client.username in self.username_to_client:
                del self.username_to_client[client.username]

        # Notify others
        if client.username:
            leave_msg = MessageBuilder.broadcast_message(
                'SERVER',
                f'{client.username} has left the chat',
                self.get_next_sequence()
            )
            self._broadcast_message(leave_msg)

        client.close()

    def _heartbeat_loop(self):
        """
        Periodic heartbeat to detect dead connections
        Demonstrates: Keep-alive mechanism
        """
        while self.running:
            time.sleep(30)  # Every 30 seconds

            with self.clients_lock:
                clients = list(self.clients.values())

            current_time = time.time()
            for client in clients:
                # Check if client is alive
                if current_time - client.last_heartbeat > 90:  # 90 second timeout
                    print(f"[SERVER] Client {client.username or client.client_id} timeout")
                    client.connected = False

    def stop(self):
        """Stop the server"""
        print("[SERVER] Shutting down...")
        self.running = False

        # Close all client connections
        with self.clients_lock:
            for client in self.clients.values():
                client.close()
            self.clients.clear()

        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

        print("[SERVER] Stopped")

    def get_stats(self) -> Dict:
        """Get server statistics"""
        with self.clients_lock:
            return {
                'total_clients': len(self.clients),
                'connected_users': [c.username for c in self.clients.values() if c.username],
                'sequence_number': self.sequence_num
            }


def main():
    """Main entry point for server"""
    import sys

    # Parse command line arguments
    host = '127.0.0.1'
    port = 5555

    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    if len(sys.argv) > 2:
        host = sys.argv[2]

    # Create and start server
    server = ChatServer(host, port)

    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[SERVER] Interrupted by user")
        server.stop()


if __name__ == '__main__':
    main()
