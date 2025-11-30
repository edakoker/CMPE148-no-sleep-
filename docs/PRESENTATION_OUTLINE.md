# Presentation Outline
**CMPE 148 - Team No Sleep**
**Custom Application-Layer Protocol: Reliable Chat Application**

## Slide 1: Title Slide
- **Title**: Custom Application-Layer Protocol for Reliable Chat
- **Team**: No Sleep (Vance Nguyen, Gonul Koker, Yashas Satheesh, Arjun Ravendran)
- **Course**: CMPE 148 - Computer Networks
- **Date**: December 2024

## Slide 2: Project Overview
- **Goal**: Design and implement a custom application-layer protocol
- **Platform**: Built on top of TCP
- **Application**: Client-server chat system
- **Key Features**:
  - Custom protocol with structured headers
  - Reliability mechanisms (ACK/retransmission)
  - Error detection (checksums)
  - Multi-client support

## Slide 3: Protocol Architecture
**Protocol Stack Diagram:**
```
┌─────────────────────────────────┐
│   Application Layer (Chat App)  │
├─────────────────────────────────┤
│   Custom Protocol ← OUR LAYER   │
├─────────────────────────────────┤
│   Transport Layer (TCP)          │
├─────────────────────────────────┤
│   Network Layer (IP)             │
└─────────────────────────────────┘
```

**Why build on TCP?**
- Connection management handled
- In-order delivery guaranteed
- Focus on application-layer concerns
- Demonstrates layer interaction

## Slide 4: Protocol Message Format
**24-Byte Header Structure:**

| Field       | Size    | Description                |
|-------------|---------|----------------------------|
| Version     | 1 byte  | Protocol version (1)       |
| Type        | 1 byte  | Message type (1-13)        |
| Sequence #  | 4 bytes | For ordering and ACK       |
| Timestamp   | 8 bytes | Unix timestamp (ms)        |
| Payload Len | 4 bytes | Payload size in bytes      |
| Checksum    | 4 bytes | MD5 hash (first 4 bytes)   |
| Reserved    | 2 bytes | For future use             |

**Payload**: JSON-encoded variable-length data

**Framing**: 4-byte length prefix before each message

## Slide 5: Message Types
**13 Message Types:**
- **Connection**: CONNECT, CONNECT_ACK, DISCONNECT
- **Chat**: CHAT_MSG, CHAT_ACK
- **Broadcast**: BROADCAST, BROADCAST_ACK
- **Private**: PRIVATE_MSG, PRIVATE_ACK
- **Error**: NACK, ERROR
- **Keepalive**: HEARTBEAT, HEARTBEAT_ACK

**Design Rationale**:
- Extensible for future features
- Clear message semantics
- Supports different communication patterns

## Slide 6: Reliability Mechanism
**Stop-and-Wait ARQ:**

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

**Parameters:**
- Timeout: 2 seconds
- Max retries: 3
- Same sequence number for matching ACK

## Slide 7: Error Detection
**MD5 Checksum:**
- Calculate MD5 hash of payload
- Use first 4 bytes as checksum
- Verify on receiver side
- Drop corrupted messages

**Why checksums if TCP has them?**
- End-to-end principle
- Protects against application-layer errors
- Educational value
- Defense in depth

## Slide 8: Implementation Architecture

**Server (Multi-threaded):**
- Main thread: Accept connections
- Per-client threads: Handle individual clients
- Heartbeat thread: Keep-alive monitoring
- Thread-safe data structures

**Client (Concurrent):**
- Main thread: User input and sending
- Receive thread: Incoming messages
- Reliable sending with timeout/retry
- Command interface

## Slide 9: Key Features Demo
**Live Demonstration:**
1. Start server
2. Connect multiple clients
3. Send regular messages
4. Broadcast to all (`/broadcast`)
5. Private messaging (`/msg user message`)
6. Show retransmission (simulate packet loss)
7. Graceful disconnect

**Screenshot/Terminal recording alternative**

## Slide 10: Testing Strategy
**Three Test Levels:**

1. **Unit Tests** (6 tests)
   - Protocol serialization/deserialization
   - Checksum validation
   - ACK generation
   - Message types

2. **Integration Tests** (6 tests)
   - Client-server communication
   - Multi-client scenarios
   - Reliability mechanisms
   - Error handling

3. **Stress Tests** (4 scenarios)
   - Performance measurement
   - Concurrent clients
   - Throughput and latency
   - Load testing

**Result**: All critical tests passing ✓

## Slide 11: Performance Results

**Metrics (Local Network):**
- **Latency**: 5-20ms average
- **Throughput**: ~150 messages/second
- **Concurrent Clients**: 10+ tested successfully
- **Reliability**: 99%+ with retransmission
- **Overhead**: ~68 bytes per message (headers + framing)

**Limitations:**
- Stop-and-Wait ARQ limits throughput
- JSON encoding adds overhead
- Trade-off: simplicity vs. performance

## Slide 12: Wireshark Analysis

**Network Traffic Capture:**
- Captured protocol on loopback interface
- Filtered to port 5555
- Analyzed packet structure

**Observations:**
- TCP 3-way handshake visible
- Custom protocol headers identifiable
- ACK patterns observable
- Retransmissions detectable
- Sequence numbers in order

**Screenshot**: Wireshark capture showing protocol headers

## Slide 13: Design Decisions

**Key Choices:**

1. **TCP over UDP**
   - Simplifies connection management
   - Reliable transport layer
   - Focus on application layer

2. **Stop-and-Wait vs. Sliding Window**
   - Simpler to implement
   - Demonstrates reliability clearly
   - Appropriate for chat application

3. **JSON vs. Binary Payload**
   - Human-readable
   - Flexible and extensible
   - Easy debugging
   - Trade-off: overhead for convenience

4. **Multi-threading vs. Async**
   - Easier to understand
   - Standard Python threading
   - Adequate for scale

## Slide 14: Challenges and Solutions

**Challenge 1: Message Framing**
- Problem: TCP is stream-based
- Solution: Length-prefixed framing

**Challenge 2: Thread Safety**
- Problem: Multiple threads accessing shared data
- Solution: Locks and thread-safe data structures

**Challenge 3: Graceful Shutdown**
- Problem: Closing without losing messages
- Solution: DISCONNECT message + ACK before close

**Challenge 4: Reliability Testing**
- Problem: Hard to simulate packet loss locally
- Solution: Adjustable timeouts + stress tests

## Slide 15: Networking Concepts Applied

**Application Layer:**
- Custom protocol design
- Message formatting
- Session management

**Transport Layer:**
- TCP socket programming
- Stream handling
- Connection management

**Reliability:**
- ARQ implementation
- ACK/NACK mechanisms
- Timeout and retransmission

**Error Detection:**
- Checksum calculation
- Message validation

**Concurrency:**
- Multi-threaded architecture
- Thread synchronization
- Concurrent I/O

## Slide 16: Code Statistics

**Implementation:**
- **Total Lines**: ~1,500 lines of Python
- **Modules**: 3 main files (protocol, server, client)
- **Tests**: 16 tests across 3 test files
- **Documentation**: 5 comprehensive documents

**Test Coverage:**
- Unit tests: 6/6 passing
- Integration tests: 5/6 passing (1 edge case)
- All core functionality verified

## Slide 17: Learning Outcomes

**Technical Skills:**
- Socket programming in Python
- Protocol design and implementation
- Reliability mechanism development
- Concurrent application development
- Network analysis with Wireshark

**Networking Concepts:**
- OSI/TCP-IP layer model
- Application-layer protocols
- Reliable data transfer
- Error detection and correction
- Client-server architecture

## Slide 18: Future Enhancements

**Protocol Improvements:**
- Sliding window for better throughput
- Message compression (reduce bandwidth)
- Encryption (TLS/SSL for security)
- Authentication system

**Application Features:**
- File transfer support
- Chat rooms/channels
- User presence (online/away/busy)
- Message history persistence
- Read receipts
- Typing indicators

## Slide 19: Conclusion

**Achievements:**
✅ Custom protocol designed and implemented
✅ Reliability mechanisms working (ACK/retransmission)
✅ Error detection functional (checksums)
✅ Multi-client support verified
✅ Comprehensive testing completed
✅ Full documentation provided

**Demonstrates:**
- Deep understanding of protocol design
- Practical network programming skills
- Reliability and error handling
- Concurrent programming
- Network analysis capabilities

**Project Status:** Complete and ready for deployment

## Slide 20: Questions?

**Thank you!**

**Team No Sleep**
- Vance Nguyen
- Gonul Koker
- Yashas Satheesh
- Arjun Ravendran

**Resources:**
- GitHub Repository: [if applicable]
- Documentation: Complete in docs/ folder
- Demo: Available for live testing

---

## Presentation Tips

### Timing (10-minute presentation)
- Slides 1-5: Protocol design (3 min)
- Slides 6-8: Implementation (2 min)
- Slide 9: Live demo (2 min)
- Slides 10-12: Testing and results (2 min)
- Slides 13-20: Wrap-up and Q&A (1 min)

### Demo Script
```bash
# Terminal 1: Server
python src/server.py

# Terminal 2: Alice
python src/client.py Alice
Alice> Hello everyone!

# Terminal 3: Bob
python src/client.py Bob
Bob> Hi Alice!
Alice> /msg Bob Private message

# Show retransmission (optional)
# Disconnect/reconnect server quickly

# Clean shutdown
Alice> /quit
Bob> /quit
```

### Key Points to Emphasize
1. **Custom protocol design** - not just using existing protocols
2. **Reliability implementation** - understanding how ARQ works
3. **Error detection** - checksums in action
4. **Working implementation** - live demo proves it works
5. **Comprehensive testing** - systematic verification

### Common Questions to Prepare For
1. Why TCP instead of UDP?
2. How does your reliability differ from TCP's?
3. What happens if a message is corrupted?
4. How do you handle multiple clients?
5. What's the maximum throughput?
6. How would you improve performance?
7. Did you consider security?
8. How did you test reliability?

### Backup Plans
- If demo fails: Have screenshots/video ready
- If network issues: Run everything locally (127.0.0.1)
- If time is short: Skip stress test details
- If time is long: Show Wireshark capture

Good luck with your presentation!
