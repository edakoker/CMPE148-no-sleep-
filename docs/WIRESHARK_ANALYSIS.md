# Wireshark Protocol Analysis Guide
**CMPE 148 - Team No Sleep**

## Overview

This guide explains how to capture and analyze the custom chat protocol using Wireshark, demonstrating understanding of protocol behavior and network analysis.

## Setup Instructions

### 1. Install Wireshark
- **Windows**: Download from https://www.wireshark.org/
- **macOS**: `brew install wireshark` or download from website
- **Linux**: `sudo apt-get install wireshark`

### 2. Configure Wireshark Permissions
On Linux/macOS, you may need to run Wireshark with appropriate permissions to capture on loopback interface.

### 3. Select Capture Interface
Since we're running locally, capture on the **loopback interface**:
- Windows: `Adapter for loopback traffic capture`
- macOS: `lo0`
- Linux: `lo` or `Loopback: lo`

## Capture Workflow

### Step 1: Start Wireshark
1. Open Wireshark
2. Select loopback interface
3. Start capture (blue shark fin icon)

### Step 2: Apply Display Filter
In the filter bar, enter:
```
tcp.port == 5555
```

This shows only traffic on our application's port.

### Step 3: Run the Application
```bash
# Terminal 1
python src/server.py

# Terminal 2
python src/client.py Alice

# Terminal 3
python src/client.py Bob
```

### Step 4: Generate Traffic
Send various messages to capture different protocol behaviors:
- Connection establishment
- Regular chat messages
- Broadcast messages
- Private messages
- Disconnection

### Step 5: Stop Capture
Click the red stop button in Wireshark.

## Analysis Tasks

### Task 1: Identify TCP 3-Way Handshake

**What to look for:**
1. SYN packet (client → server)
2. SYN-ACK packet (server → client)
3. ACK packet (client → server)

**How to find:**
- Filter: `tcp.flags.syn == 1`
- Should see 2 packets: SYN and SYN-ACK

**Questions to answer:**
- What are the initial sequence numbers?
- What is the window size?
- Which TCP options are negotiated?

**Screenshot to include:**
- Capture showing the 3-way handshake
- Packet details showing TCP flags

### Task 2: Analyze Custom Protocol Headers

**What to look for:**
The first 24 bytes of payload contain our protocol header.

**How to analyze:**
1. Select a packet with data (PSH, ACK flags)
2. Right-click → Follow → TCP Stream
3. Look at the raw bytes (toggle "Show data as" to "Hex Dump")

**Header breakdown (24 bytes):**
```
Byte 0:       Version (0x01)
Byte 1:       Message Type (0x01-0x0D)
Bytes 2-5:    Sequence Number (4 bytes, big-endian)
Bytes 6-13:   Timestamp (8 bytes, big-endian)
Bytes 14-17:  Payload Length (4 bytes, big-endian)
Bytes 18-21:  Checksum (4 bytes)
Bytes 22-23:  Reserved (0x0000)
```

**Example analysis:**
```
01 04 00 00 00 2A ...
│  │  └─────┘
│  │     └─ Sequence number = 42
│  └─ Type = 4 (CHAT_MSG)
└─ Version = 1
```

**Questions to answer:**
- Can you identify the message type from the header?
- What is the sequence number?
- How large is the payload?
- Can you verify the checksum?

**Screenshot to include:**
- TCP stream showing hex dump with header highlighted
- Annotations showing header fields

### Task 3: Observe Message Framing

**What to look for:**
Before each protocol message, there's a 4-byte length prefix.

**How to analyze:**
1. Follow TCP stream
2. Look for pattern: 4-byte length, then message
3. Verify length matches actual data

**Example:**
```
00 00 00 5A  01 04 ...
└─────┘
   └─ Length = 90 bytes (0x5A)
```

**Questions to answer:**
- Why do we need length-prefixed framing?
- What happens if length is incorrect?
- How does this handle TCP's stream nature?

### Task 4: Track ACK/Reliability Mechanism

**What to look for:**
For each CHAT_MSG, there should be a CHAT_ACK with matching sequence number.

**How to analyze:**
1. Find a CHAT_MSG packet (Type = 0x04)
2. Note its sequence number
3. Find corresponding CHAT_ACK (Type = 0x05)
4. Verify sequence numbers match

**Timing analysis:**
- Measure time between message and ACK
- This is your Round-Trip Time (RTT)

**Questions to answer:**
- What is the average RTT?
- Do all messages get ACKed?
- What is the ACK ratio (ACKs per message)?

**Screenshot to include:**
- Two packets: message and its ACK
- Highlight matching sequence numbers
- Show timestamp difference

### Task 5: Observe Retransmission

**How to trigger retransmission:**

Option 1: Simulate network delay
```python
# In client.py, temporarily reduce timeout
self.ACK_TIMEOUT = 0.1  # Very short timeout
```

Option 2: Kill and restart server quickly
1. Send message from client
2. Immediately kill server (Ctrl+C)
3. Restart server within 2 seconds
4. Watch client retransmit

**What to look for:**
- Same message sent multiple times
- Identical sequence numbers
- 2-second gaps between retransmissions

**Questions to answer:**
- How many times does it retry?
- What is the timeout value?
- How can you identify retransmissions?

**Screenshot to include:**
- Multiple packets with same sequence number
- Time delta between retransmissions

### Task 6: Analyze Message Payloads

**What to look for:**
After the 24-byte header, the payload is JSON-encoded.

**How to analyze:**
1. Follow TCP stream
2. Toggle to "ASCII" view
3. Find JSON data after header

**Example payloads:**

CONNECT message:
```json
{"username": "Alice", "action": "connect"}
```

CHAT_MSG:
```json
{"username": "Alice", "message": "Hello!"}
```

PRIVATE_MSG:
```json
{"sender": "Alice", "recipient": "Bob", "message": "Secret", "private": true}
```

**Questions to answer:**
- What is the payload overhead?
- How efficient is JSON encoding?
- Could binary encoding be better?

### Task 7: Connection Teardown

**What to look for:**
1. DISCONNECT message (Type = 0x03)
2. DISCONNECT_ACK
3. TCP FIN packets (4-way close)

**TCP connection termination:**
1. FIN from client
2. ACK from server
3. FIN from server
4. ACK from client

**Questions to answer:**
- Is the application-layer disconnect graceful?
- Which side initiates TCP close?
- Are there any lingering connections?

## Performance Measurements

### Latency Measurement

**Method:**
1. Find message → ACK pair
2. Note timestamps
3. Calculate difference

**Wireshark feature:**
- In packet details: Time → Time since previous displayed packet

**Calculate average:**
- Export packet list to CSV
- Use spreadsheet to calculate statistics

**Expected results:**
- Local loopback: 1-10ms
- Same network: 5-50ms

### Throughput Measurement

**Method:**
1. Statistics → Conversations
2. Select TCP tab
3. Find conversation on port 5555
4. Note bytes and duration

**Calculate:**
```
Throughput = Total Bytes / Duration
```

**Or use IO Graph:**
1. Statistics → I/O Graph
2. Filter: `tcp.port == 5555`
3. Observe bits/second over time

### Bandwidth Utilization

**Calculate overhead:**
```
Protocol Overhead = (Header Size + Framing) / Total Packet Size
                  = (24 + 4) / Total Size
```

**For a typical message:**
```
Length prefix: 4 bytes
Header:       24 bytes
Payload:      ~50 bytes (JSON)
TCP header:   20 bytes
IP header:    20 bytes
--------------
Total:        ~118 bytes
```

**Efficiency:**
```
Payload efficiency = Actual Message / Total Bytes
                   = ~30 bytes / 118 bytes
                   = ~25%
```

## Common Filters

### Useful Wireshark Filters

Show only our protocol traffic:
```
tcp.port == 5555
```

Show only data packets (no ACKs):
```
tcp.port == 5555 && tcp.len > 0
```

Show SYN packets:
```
tcp.flags.syn == 1 && tcp.port == 5555
```

Show retransmissions:
```
tcp.analysis.retransmission && tcp.port == 5555
```

Show packets from client to server:
```
tcp.dstport == 5555
```

Show packets from server to client:
```
tcp.srcport == 5555
```

## Export Options

### Export for Report

**Packet List:**
- File → Export Packet Dissections → As CSV

**TCP Stream:**
- Follow → TCP Stream → Save as (choose format)

**Screenshots:**
- Edit → Copy → ... as Image
- Paste into report

**Statistics:**
- Statistics → Protocol Hierarchy → Copy → CSV

## Analysis Checklist

Use this checklist for your report:

- [ ] Captured TCP 3-way handshake
- [ ] Identified protocol header structure
- [ ] Verified message framing (length prefix)
- [ ] Traced message → ACK pairs
- [ ] Observed retransmission (if possible)
- [ ] Analyzed different message types
- [ ] Examined JSON payloads
- [ ] Measured average latency
- [ ] Calculated throughput
- [ ] Analyzed protocol overhead
- [ ] Captured connection teardown
- [ ] Generated screenshots for report

## Report Sections

### Suggested Report Structure

**1. Capture Setup**
- Interface used
- Filter applied
- Test scenario description

**2. Protocol Analysis**
- Header format verification
- Message type identification
- Payload structure

**3. Reliability Mechanism**
- ACK behavior
- Retransmission evidence
- Timeout measurements

**4. Performance Analysis**
- Latency statistics
- Throughput measurements
- Overhead calculation

**5. Observations**
- Interesting findings
- Protocol behavior under load
- Potential improvements

**6. Conclusions**
- Protocol effectiveness
- Reliability verification
- Performance assessment

## Advanced Analysis

### TCP Window Analysis
- Statistics → TCP Stream Graphs → Window Scaling
- Observe TCP flow control

### Sequence Number Analysis
- Statistics → TCP Stream Graphs → Time Sequence (Stevens)
- Visualize data flow

### Expert Information
- Analyze → Expert Information
- Look for warnings or errors

## Troubleshooting Wireshark

### Can't see any packets
- Check interface selection (use loopback)
- Verify filter syntax
- Ensure application is running
- Check port number matches

### Permission denied
- Run Wireshark as admin (Windows)
- Add user to wireshark group (Linux)
- Use sudo (macOS/Linux)

### Too much traffic
- Apply more specific filters
- Use display filters, not capture filters
- Focus on specific IP addresses

## Example Analysis Output

### Sample Findings

**Latency:**
- Average: 8.3ms
- Min: 2.1ms
- Max: 45.7ms
- Std Dev: 7.2ms

**Throughput:**
- Messages/sec: 147
- Bytes/sec: 12,450
- Bits/sec: 99,600

**Reliability:**
- Messages sent: 200
- ACKs received: 200
- Retransmissions: 0
- Success rate: 100%

**Overhead:**
- Average packet size: 118 bytes
- Protocol overhead: 28 bytes (24%)
- TCP/IP overhead: 40 bytes (34%)
- Efficiency: 42%

## Resources

### Wireshark Documentation
- User Guide: https://www.wireshark.org/docs/wsug_html/
- Display Filters: https://wiki.wireshark.org/DisplayFilters
- Protocol Analysis: https://www.wireshark.org/docs/

### Protocol Analysis Tips
- Use colors to highlight different message types
- Create custom column layouts
- Save frequently-used filters as buttons

---

**Good luck with your analysis!**

Team No Sleep - CMPE 148 Fall 2024
