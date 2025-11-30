# Custom Application-Layer Protocol Specification
**CMPE 148 - Team No Sleep**

## 1. Overview

This document specifies a custom application-layer protocol designed for reliable client-server chat communication. The protocol operates on top of TCP, adding application-specific reliability mechanisms, message typing, and error detection.

### 1.1 Design Goals
- **Reliability**: Ensure message delivery through ACK/retransmission
- **Ordered Delivery**: Maintain message order using sequence numbers
- **Error Detection**: Detect corrupted messages using checksums
- **Extensibility**: Support multiple message types
- **Efficiency**: Minimize overhead while maintaining reliability

### 1.2 Protocol Stack Position
```
┌─────────────────────────────────┐
│   Application Layer (Chat App)  │
├─────────────────────────────────┤
│   Custom Protocol (This Layer)  │  ← Our Protocol
├─────────────────────────────────┤
│   Transport Layer (TCP)          │
├─────────────────────────────────┤
│   Network Layer (IP)             │
├─────────────────────────────────┤
│   Link Layer (Ethernet/WiFi)     │
└─────────────────────────────────┘
```

## 2. Message Format

### 2.1 Overall Structure
Every protocol message consists of:
1. **Fixed Header** (24 bytes)
2. **Variable Payload** (JSON-encoded data)

```
┌───────────────────────────────────────────────────────────┐
│                    Header (24 bytes)                       │
├───────────────────────────────────────────────────────────┤
│                 Payload (Variable length)                  │
└───────────────────────────────────────────────────────────┘
```

### 2.2 Header Format (24 bytes)

| Field         | Size    | Type            | Description                           |
|---------------|---------|-----------------|---------------------------------------|
| Version       | 1 byte  | uint8           | Protocol version (currently 1)        |
| Type          | 1 byte  | uint8           | Message type (see section 2.3)        |
| Sequence #    | 4 bytes | uint32          | Sequence number for ordering/ACK      |
| Timestamp     | 8 bytes | uint64          | Unix timestamp in milliseconds        |
| Payload Len   | 4 bytes | uint32          | Length of payload in bytes            |
| Checksum      | 4 bytes | uint32          | MD5 checksum (first 4 bytes)          |
| Reserved      | 2 bytes | uint16          | Reserved for future use (set to 0)    |

**Network Byte Order**: All multi-byte fields use big-endian (network byte order)

**Header Packing Format** (Python struct): `!BBIQIHH`
- `!` = Network byte order (big-endian)
- `B` = unsigned char (1 byte)
- `I` = unsigned int (4 bytes)
- `Q` = unsigned long long (8 bytes)
- `H` = unsigned short (2 bytes)

### 2.3 Message Types

| Value | Type              | Description                                   | ACK Required |
|-------|-------------------|-----------------------------------------------|--------------|
| 1     | CONNECT           | Client connection request                     | Yes          |
| 2     | CONNECT_ACK       | Connection acknowledgment                     | No           |
| 3     | DISCONNECT        | Client disconnect notification                | Yes          |
| 4     | CHAT_MSG          | Regular chat message                          | Yes          |
| 5     | CHAT_ACK          | Chat message acknowledgment                   | No           |
| 6     | BROADCAST         | Broadcast message to all users                | Yes          |
| 7     | BROADCAST_ACK     | Broadcast acknowledgment                      | No           |
| 8     | PRIVATE_MSG       | Private message to specific user              | Yes          |
| 9     | PRIVATE_ACK       | Private message acknowledgment                | No           |
| 10    | NACK              | Negative acknowledgment (error)               | No           |
| 11    | ERROR             | Error message                                 | No           |
| 12    | HEARTBEAT         | Keep-alive message                            | Yes          |
| 13    | HEARTBEAT_ACK     | Keep-alive acknowledgment                     | No           |

### 2.4 Payload Format

Payloads are JSON-encoded dictionaries with message-specific fields.

#### 2.4.1 CONNECT Message
```json
{
  "username": "string",
  "action": "connect"
}
```

#### 2.4.2 CHAT_MSG Message
```json
{
  "username": "string",
  "message": "string"
}
```

#### 2.4.3 BROADCAST Message
```json
{
  "username": "string",
  "message": "string",
  "broadcast": true
}
```

#### 2.4.4 PRIVATE_MSG Message
```json
{
  "sender": "string",
  "recipient": "string",
  "message": "string",
  "private": true
}
```

#### 2.4.5 ACK Messages
```json
{
  "ack_for": <sequence_number>,
  "status": "success"
}
```

#### 2.4.6 NACK Message
```json
{
  "nack_for": <sequence_number>,
  "reason": "string",
  "status": "failure"
}
```

## 3. Reliability Mechanism

### 3.1 Stop-and-Wait ARQ
The protocol implements a simplified Stop-and-Wait Automatic Repeat Request (ARQ) scheme:

1. **Sender** sends message with unique sequence number
2. **Sender** waits for ACK with matching sequence number
3. If **timeout** occurs (2 seconds), retransmit message
4. Retry up to **3 times** before giving up
5. **Receiver** sends ACK immediately upon receiving message

### 3.2 Sequence Numbers
- Each message has a unique sequence number
- Sequence numbers increment monotonically
- ACK messages contain the sequence number they acknowledge
- Allows matching ACKs to original messages

### 3.3 Timeout and Retransmission
```
Client                          Server
  |                               |
  |--- CHAT_MSG (seq=42) -------->|
  |                               |
  |    [waiting for ACK]          |
  |                               |
  |    [timeout after 2s]         |
  |                               |
  |--- CHAT_MSG (seq=42) -------->| (retransmission)
  |                               |
  |<------ ACK (ack_for=42) ------|
  |                               |
```

### 3.4 Error Detection
- **Checksum**: First 4 bytes of MD5 hash of payload
- Receiver verifies checksum on all messages
- Corrupted messages are silently dropped
- Sender will retransmit due to missing ACK

## 4. Connection Management

### 4.1 Connection Establishment
```
Client                          Server
  |                               |
  |=== TCP 3-way handshake ======>| (handled by OS)
  |                               |
  |--- CONNECT (username) ------->|
  |                               |
  |                (verify username available)
  |                               |
  |<------ CONNECT_ACK -----------|
  |                               |
  [Connection established]
```

### 4.2 Duplicate Username Handling
```
Client                          Server
  |                               |
  |--- CONNECT (username) ------->|
  |                               |
  |                (username already taken)
  |                               |
  |<------ NACK (reason) ---------|
  |                               |
  [Connection rejected]
```

### 4.3 Graceful Disconnection
```
Client                          Server
  |                               |
  |--- DISCONNECT --------------->|
  |                               |
  |<------ ACK -------------------|
  |                               |
  |=== TCP close ================>|
  |                               |
```

### 4.4 Keep-Alive (Heartbeat)
- Server sends HEARTBEAT every 30 seconds
- Client responds with HEARTBEAT_ACK
- If no response for 90 seconds, connection considered dead
- Prevents ghost connections from crashes

## 5. Message Flow Diagrams

### 5.1 Broadcast Message
```
Client A        Server          Client B
  |               |               |
  |-- BROADCAST ->|               |
  |               |--- BROADCAST->|
  |<-- BCAST_ACK--|               |
  |               |<-- BCAST_ACK--|
  |               |               |
```

### 5.2 Private Message
```
Client A        Server          Client B
  |               |               |
  |-- PRIVATE --->|               |
  |(to: B)        |--- PRIVATE -->|
  |               |(from: A)      |
  |<-- PRIV_ACK --|               |
  |               |<-- PRIV_ACK --|
  |               |               |
```

### 5.3 Message Retransmission (Packet Loss)
```
Client          Server
  |               |
  |-- CHAT_MSG -->X (lost)
  |               |
  [timeout 2s]    |
  |               |
  |-- CHAT_MSG -->| (retransmit)
  |               |
  |<--- ACK ------|
  |               |
```

## 6. Framing

Messages are framed using length prefixing to handle TCP's stream nature:

```
┌────────────────┬──────────────────────────┐
│  Length (4B)   │  Protocol Message        │
└────────────────┴──────────────────────────┘
```

1. **Length prefix**: 4 bytes, big-endian, indicates message size
2. **Protocol message**: Complete serialized message

This allows receiver to know exactly how many bytes to read.

## 7. Error Handling

### 7.1 Checksum Failure
- Message silently dropped
- Sender retransmits after timeout

### 7.2 Version Mismatch
- Message rejected
- Connection closed

### 7.3 Unknown Message Type
- Message logged and ignored
- Connection remains open

### 7.4 Malformed JSON
- Message rejected
- NACK sent if possible

### 7.5 Timeout After Max Retries
- Error reported to application
- Connection may be closed

## 8. Performance Characteristics

### 8.1 Overhead Analysis
- **Header overhead**: 24 bytes per message
- **Framing overhead**: 4 bytes length prefix
- **ACK overhead**: ~50 bytes per ACK message
- **Total per chat message**: ~100 bytes + payload

### 8.2 Latency
- **Minimum latency**: 1 RTT (send + ACK)
- **With retransmission**: Up to 4 RTTs (initial + 3 retries)
- **Timeout contribution**: Up to 6 seconds worst case (3 × 2s)

### 8.3 Throughput
Limited by Stop-and-Wait ARQ:
- Must wait for ACK before next message
- Theoretical max: ~500 messages/second (2ms RTT assumption)
- Practical: ~100-200 messages/second in testing

## 9. Security Considerations

### 9.1 Current Limitations
- **No encryption**: Messages sent in plaintext
- **No authentication**: Usernames can be spoofed
- **No authorization**: All users can message all others

### 9.2 Potential Improvements
- Add TLS/SSL layer below custom protocol
- Implement challenge-response authentication
- Add message signing for integrity

## 10. Future Extensions

### 10.1 Planned Features
- File transfer message type
- User status updates (online/away/busy)
- Message read receipts
- Group chat rooms

### 10.2 Protocol Versioning
Version field in header allows future protocol changes:
- v1: Current implementation
- v2: Could add encryption
- v3: Could add compression

Server/client negotiate version during connection.

## 11. Implementation Notes

### 11.1 Language-Specific Details
Current implementation in Python 3 uses:
- `socket` module for TCP
- `struct` module for binary packing
- `json` module for payload encoding
- `hashlib` for checksums

### 11.2 Threading Model
- **Server**: One thread per client + main accept thread
- **Client**: Receive thread + main send thread
- Thread-safe sequence number generation
- Locks for shared data structures

### 11.3 Platform Support
Protocol is platform-independent, tested on:
- Windows 10/11
- Linux (Ubuntu, Debian)
- macOS

## 12. Testing and Analysis

### 12.1 Unit Tests
- Message serialization/deserialization
- Checksum validation
- ACK generation
- Message type handling

### 12.2 Integration Tests
- Multi-client connections
- Message broadcasting
- Reliability/retransmission
- Concurrent message handling

### 12.3 Wireshark Analysis
To analyze protocol with Wireshark:
1. Capture on loopback interface (127.0.0.1)
2. Filter by port: `tcp.port == 5555`
3. Follow TCP stream to see protocol messages
4. Verify message format and reliability mechanisms

Look for:
- Message retransmissions (same sequence number)
- ACK patterns
- Timing between send and ACK

---

**Document Version**: 1.0
**Date**: December 2024
**Authors**: Team No Sleep (Vance Nguyen, Gonul Koker, Yashas Satheesh, Arjun Ravendran)
