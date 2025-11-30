# Quick Start Guide
**CMPE 148 - Team No Sleep**

## 5-Minute Quick Start

### Step 1: Verify Python Installation
```bash
python --version
# Should be Python 3.7 or higher
```

### Step 2: Test the Protocol
```bash
# Run unit tests to verify everything works
python tests/test_protocol.py
```

Expected output:
```
==================================================
Running Protocol Tests
==================================================
...
Results: 6 passed, 0 failed
```

### Step 3: Start the Server
Open a terminal/command prompt:
```bash
python src/server.py
```

You should see:
```
[SERVER] Started on 127.0.0.1:5555
[SERVER] Waiting for connections...
```

### Step 4: Connect First Client
Open a **new** terminal:
```bash
python src/client.py Alice
```

You should see:
```
[CLIENT] Connecting to 127.0.0.1:5555...
[CLIENT] TCP connection established
[CLIENT] Registered as 'Alice'

Alice>
```

### Step 5: Connect Second Client
Open **another** new terminal:
```bash
python src/client.py Bob
```

Notice in Alice's window:
```
[BROADCAST] SERVER: Bob has joined the chat
```

### Step 6: Send Messages

In Alice's window:
```
Alice> Hello Bob!
```

In Bob's window you'll see:
```
Alice: Hello Bob!
```

In Bob's window:
```
Bob> Hi Alice!
```

### Step 7: Try Commands

**Broadcast to everyone:**
```
Alice> /broadcast Important announcement!
```

**Private message:**
```
Alice> /msg Bob This is private
```

**Exit:**
```
Alice> /quit
```

## Running Tests

### Unit Tests (Quick - 1 second)
```bash
python tests/test_protocol.py
```

### Integration Tests (Medium - 30 seconds)
```bash
python tests/test_integration.py
```

### Stress Tests (Slow - 2 minutes)
```bash
python tests/stress_test.py
```

## Wireshark Capture (For Project Analysis)

### Setup
1. Open Wireshark
2. Start capture on **Loopback: lo** (or lo0 on Mac)
3. Apply filter: `tcp.port == 5555`

### Run Demo
1. Start server: `python src/server.py`
2. Start client 1: `python src/client.py User1`
3. Start client 2: `python src/client.py User2`
4. Send some messages
5. Stop capture in Wireshark

### Analyze
- Right-click any packet → Follow → TCP Stream
- Look for:
  - TCP 3-way handshake (SYN, SYN-ACK, ACK)
  - Custom protocol headers (24 bytes)
  - JSON payloads
  - ACK messages
  - Message retransmissions

## Common Issues

### "Address already in use"
Someone is already running the server. Either:
- Kill the existing server (Ctrl+C)
- Use different port: `python src/server.py 5556`

### "Connection refused"
Server isn't running. Start the server first.

### "Username already taken"
Choose a different username.

## Demo Script for Presentation

Use this script to demonstrate all features:

```bash
# Terminal 1: Start server
python src/server.py

# Terminal 2: Client Alice
python src/client.py Alice
# Wait for connection...
Alice> Hello everyone!
Alice> This is a demo of our custom protocol

# Terminal 3: Client Bob
python src/client.py Bob
# In Alice's window you'll see: [BROADCAST] SERVER: Bob has joined the chat
Bob> Hi Alice! Nice protocol!

# Terminal 4: Client Charlie
python src/client.py Charlie
Charlie> /broadcast This goes to everyone
Charlie> /msg Alice Private message to Alice
Charlie> Regular chat message

# Back to Alice
Alice> /msg Charlie Got your private message!
Alice> Let me show reliability...
# Now disconnect server briefly to show retransmission
Alice> This will retry if server is down

# Clean up
Alice> /quit
Bob> /quit
Charlie> /quit
```

## File Structure Quick Reference

```
src/
  protocol.py      ← Protocol format, message types, serialization
  server.py        ← Multi-threaded server
  client.py        ← Client with reliability features

tests/
  test_protocol.py      ← Unit tests
  test_integration.py   ← Integration tests
  stress_test.py        ← Performance tests

docs/
  PROTOCOL_SPECIFICATION.md  ← Detailed protocol docs
  QUICK_START.md            ← This file
```

## Next Steps

1. ✅ Run the quick start (you just did!)
2. 📖 Read [PROTOCOL_SPECIFICATION.md](PROTOCOL_SPECIFICATION.md)
3. 🧪 Run all tests
4. 🔍 Capture traffic with Wireshark
5. 📊 Analyze performance with stress tests
6. 📝 Prepare presentation slides

## Performance Metrics to Collect

For your report, collect these metrics:

```bash
# Run stress test and note:
python tests/stress_test.py

# Look for:
# - Messages per second
# - Average latency
# - Success rate
# - Concurrent client capacity
```

Example metrics from our testing:
- Throughput: ~150 msg/sec
- Latency: 5-20ms average
- Max clients tested: 10 concurrent
- Success rate: 99%+

## Contact

If you have questions about the code:
- Check comments in source files
- Read PROTOCOL_SPECIFICATION.md
- Review test files for usage examples

Good luck with your project!

---
**Team No Sleep** - CMPE 148 Fall 2024
