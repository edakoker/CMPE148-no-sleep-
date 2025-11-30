"""
Custom Application-Layer Protocol for Reliable Chat Application
CMPE 148 - Team No Sleep

Protocol Design incorporating key networking concepts:
- Structured message format with headers
- Sequence numbers for message ordering
- ACK/NACK for reliability
- Message types for different operations
- Checksums for error detection
"""

import struct
import json
import hashlib
from enum import IntEnum
from typing import Optional, Dict, Any

class MessageType(IntEnum):
    """Application-layer message types"""
    # Connection management
    CONNECT = 1
    CONNECT_ACK = 2
    DISCONNECT = 3

    # Chat messages
    CHAT_MSG = 4
    CHAT_ACK = 5

    # Broadcast messages
    BROADCAST = 6
    BROADCAST_ACK = 7

    # Private messages
    PRIVATE_MSG = 8
    PRIVATE_ACK = 9

    # Error handling
    NACK = 10
    ERROR = 11

    # Keepalive
    HEARTBEAT = 12
    HEARTBEAT_ACK = 13


class ProtocolMessage:
    """
    Custom Protocol Message Format

    Header Structure (24 bytes fixed):
    +-------------------+-------------------+-------------------+-------------------+
    | Version (1 byte)  | Type (1 byte)     | Sequence # (4B)   | Timestamp (8B)    |
    +-------------------+-------------------+-------------------+-------------------+
    | Payload Len (4B)  | Checksum (4B)     | Reserved (2B)     |
    +-------------------+-------------------+-------------------+

    Followed by variable-length payload (JSON encoded)

    This demonstrates:
    - Application-layer protocol design
    - Message framing and delimiting
    - Error detection (checksum)
    - Sequencing for reliability
    """

    VERSION = 1
    HEADER_SIZE = 24
    HEADER_FORMAT = '!BBIQIIH'  # Network byte order (big-endian)

    def __init__(self, msg_type: MessageType, sequence_num: int,
                 payload: Dict[str, Any], timestamp: Optional[int] = None):
        """
        Initialize a protocol message

        Args:
            msg_type: Type of message (from MessageType enum)
            sequence_num: Sequence number for ordering and ACK matching
            payload: Dictionary containing message data
            timestamp: Unix timestamp (auto-generated if not provided)
        """
        self.version = self.VERSION
        self.msg_type = msg_type
        self.sequence_num = sequence_num
        self.timestamp = timestamp or self._get_timestamp()
        self.payload = payload
        self.checksum = 0

    @staticmethod
    def _get_timestamp() -> int:
        """Get current Unix timestamp in milliseconds"""
        import time
        return int(time.time() * 1000)

    def _calculate_checksum(self, payload_bytes: bytes) -> int:
        """
        Calculate checksum for error detection
        Uses first 4 bytes of MD5 hash as checksum

        Demonstrates: Error detection mechanism at application layer
        """
        md5_hash = hashlib.md5(payload_bytes).digest()
        return struct.unpack('!I', md5_hash[:4])[0]

    def serialize(self) -> bytes:
        """
        Serialize message to bytes for transmission over network

        Process:
        1. Encode payload to JSON then bytes
        2. Calculate payload length and checksum
        3. Pack header with network byte order
        4. Concatenate header + payload

        Returns:
            bytes: Complete message ready for socket transmission
        """
        # Encode payload
        payload_json = json.dumps(self.payload)
        payload_bytes = payload_json.encode('utf-8')
        payload_len = len(payload_bytes)

        # Calculate checksum
        self.checksum = self._calculate_checksum(payload_bytes)

        # Pack header
        header = struct.pack(
            self.HEADER_FORMAT,
            self.version,           # 1 byte
            int(self.msg_type),     # 1 byte (convert enum to int)
            self.sequence_num,      # 4 bytes (unsigned int)
            self.timestamp,         # 8 bytes (unsigned long long)
            payload_len,            # 4 bytes (unsigned int)
            self.checksum,          # 4 bytes (unsigned int)
            0                       # 2 bytes reserved for future use
        )

        return header + payload_bytes

    @classmethod
    def deserialize(cls, data: bytes) -> Optional['ProtocolMessage']:
        """
        Deserialize bytes received from network into ProtocolMessage

        Process:
        1. Extract and unpack header
        2. Validate version
        3. Extract payload based on length
        4. Verify checksum
        5. Decode JSON payload

        Args:
            data: Raw bytes from socket

        Returns:
            ProtocolMessage if valid, None if corrupted/invalid
        """
        if len(data) < cls.HEADER_SIZE:
            return None

        # Unpack header
        header_data = struct.unpack(cls.HEADER_FORMAT, data[:cls.HEADER_SIZE])
        version, msg_type, seq_num, timestamp, payload_len, checksum, _ = header_data

        # Validate version
        if version != cls.VERSION:
            return None

        # Extract payload
        payload_start = cls.HEADER_SIZE
        payload_end = payload_start + payload_len

        if len(data) < payload_end:
            return None

        payload_bytes = data[payload_start:payload_end]

        # Verify checksum
        calculated_checksum = cls._calculate_checksum_static(payload_bytes)
        if calculated_checksum != checksum:
            return None

        # Decode payload
        try:
            payload_json = payload_bytes.decode('utf-8')
            payload = json.loads(payload_json)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None

        # Create message object
        msg = cls(MessageType(msg_type), seq_num, payload, timestamp)
        msg.checksum = checksum
        return msg

    @staticmethod
    def _calculate_checksum_static(payload_bytes: bytes) -> int:
        """Static version of checksum calculation for verification"""
        md5_hash = hashlib.md5(payload_bytes).digest()
        return struct.unpack('!I', md5_hash[:4])[0]

    def create_ack(self) -> 'ProtocolMessage':
        """
        Create an ACK message for this message

        Demonstrates: Reliability mechanism - acknowledgment
        ACK contains original sequence number for matching
        """
        ack_type_map = {
            MessageType.CONNECT: MessageType.CONNECT_ACK,
            MessageType.CHAT_MSG: MessageType.CHAT_ACK,
            MessageType.BROADCAST: MessageType.BROADCAST_ACK,
            MessageType.PRIVATE_MSG: MessageType.PRIVATE_ACK,
            MessageType.HEARTBEAT: MessageType.HEARTBEAT_ACK,
        }

        ack_type = ack_type_map.get(self.msg_type, MessageType.CHAT_ACK)

        return ProtocolMessage(
            msg_type=ack_type,
            sequence_num=self.sequence_num,  # Same seq num for matching
            payload={'ack_for': self.sequence_num, 'status': 'success'}
        )

    def create_nack(self, reason: str) -> 'ProtocolMessage':
        """
        Create a NACK (Negative Acknowledgment) for error cases

        Demonstrates: Error handling in reliability mechanism
        """
        return ProtocolMessage(
            msg_type=MessageType.NACK,
            sequence_num=self.sequence_num,
            payload={
                'nack_for': self.sequence_num,
                'reason': reason,
                'status': 'failure'
            }
        )

    def __repr__(self) -> str:
        return (f"ProtocolMessage(type={MessageType(self.msg_type).name}, "
                f"seq={self.sequence_num}, payload={self.payload})")


class MessageBuilder:
    """Helper class to build common message types"""

    @staticmethod
    def connect_message(username: str, seq_num: int) -> ProtocolMessage:
        """Create a connection request message"""
        return ProtocolMessage(
            msg_type=MessageType.CONNECT,
            sequence_num=seq_num,
            payload={'username': username, 'action': 'connect'}
        )

    @staticmethod
    def disconnect_message(username: str, seq_num: int) -> ProtocolMessage:
        """Create a disconnect message"""
        return ProtocolMessage(
            msg_type=MessageType.DISCONNECT,
            sequence_num=seq_num,
            payload={'username': username, 'action': 'disconnect'}
        )

    @staticmethod
    def chat_message(username: str, message: str, seq_num: int) -> ProtocolMessage:
        """Create a chat message"""
        return ProtocolMessage(
            msg_type=MessageType.CHAT_MSG,
            sequence_num=seq_num,
            payload={'username': username, 'message': message}
        )

    @staticmethod
    def broadcast_message(username: str, message: str, seq_num: int) -> ProtocolMessage:
        """Create a broadcast message to all clients"""
        return ProtocolMessage(
            msg_type=MessageType.BROADCAST,
            sequence_num=seq_num,
            payload={'username': username, 'message': message, 'broadcast': True}
        )

    @staticmethod
    def private_message(sender: str, recipient: str, message: str, seq_num: int) -> ProtocolMessage:
        """Create a private message to specific user"""
        return ProtocolMessage(
            msg_type=MessageType.PRIVATE_MSG,
            sequence_num=seq_num,
            payload={
                'sender': sender,
                'recipient': recipient,
                'message': message,
                'private': True
            }
        )

    @staticmethod
    def heartbeat_message(seq_num: int) -> ProtocolMessage:
        """Create a heartbeat/keepalive message"""
        return ProtocolMessage(
            msg_type=MessageType.HEARTBEAT,
            sequence_num=seq_num,
            payload={'type': 'heartbeat'}
        )

    @staticmethod
    def error_message(error_msg: str, seq_num: int) -> ProtocolMessage:
        """Create an error message"""
        return ProtocolMessage(
            msg_type=MessageType.ERROR,
            sequence_num=seq_num,
            payload={'error': error_msg}
        )
