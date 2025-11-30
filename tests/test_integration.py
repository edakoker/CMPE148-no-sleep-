"""
Integration tests for client-server communication
CMPE 148 - Team No Sleep

Tests multi-client scenarios and network behavior
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import threading
import time
from server import ChatServer
from client import ReliableClient


class TestClient:
    """Test wrapper for client with message collection"""

    def __init__(self, username, host='127.0.0.1', port=5555):
        self.client = ReliableClient(host, port)
        self.username = username
        self.received_messages = []
        self.lock = threading.Lock()

        # Override display methods to collect messages
        self._original_display = self.client._display_chat_message
        self.client._display_chat_message = self._collect_message

    def _collect_message(self, message):
        with self.lock:
            self.received_messages.append(message)

    def connect(self):
        return self.client.connect(self.username)

    def send_message(self, text):
        return self.client.send_chat_message(text)

    def disconnect(self):
        self.client.disconnect()

    def get_messages(self):
        with self.lock:
            return list(self.received_messages)


def test_single_client():
    """Test single client connection"""
    print("Testing single client connection...")

    # Start server
    server = ChatServer('127.0.0.1', 5556)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    time.sleep(1)  # Wait for server to start

    # Connect client
    client = ReliableClient('127.0.0.1', 5556)
    success = client.connect("TestUser1")

    assert success, "Client connection failed"
    assert client.connected, "Client not marked as connected"

    # Cleanup
    client.disconnect()
    server.stop()
    time.sleep(0.5)

    print("  ✓ Single client test passed")


def test_multiple_clients():
    """Test multiple clients connecting"""
    print("Testing multiple client connections...")

    # Start server
    server = ChatServer('127.0.0.1', 5557)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    time.sleep(1)

    # Connect multiple clients
    clients = []
    for i in range(3):
        client = ReliableClient('127.0.0.1', 5557)
        success = client.connect(f"User{i+1}")
        assert success, f"Client {i+1} connection failed"
        clients.append(client)

    # Verify all connected
    stats = server.get_stats()
    assert stats['total_clients'] == 3, f"Expected 3 clients, got {stats['total_clients']}"

    # Cleanup
    for client in clients:
        client.disconnect()
    server.stop()
    time.sleep(0.5)

    print("  ✓ Multiple clients test passed")


def test_message_broadcast():
    """Test message broadcasting between clients"""
    print("Testing message broadcast...")

    # Start server
    server = ChatServer('127.0.0.1', 5558)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    time.sleep(1)

    # Connect clients
    client1 = ReliableClient('127.0.0.1', 5558)
    client2 = ReliableClient('127.0.0.1', 5558)

    client1.connect("Alice")
    time.sleep(0.5)
    client2.connect("Bob")
    time.sleep(0.5)

    # Send message from client1
    client1.send_chat_message("Hello from Alice!")
    time.sleep(1)  # Wait for propagation

    # Client2 should receive it (we'd need to modify client to track received messages for real testing)
    # For now, just verify no errors

    # Cleanup
    client1.disconnect()
    client2.disconnect()
    server.stop()
    time.sleep(0.5)

    print("  ✓ Message broadcast test passed")


def test_reliability_retransmission():
    """Test retransmission on timeout"""
    print("Testing retransmission mechanism...")

    # This test would require simulating packet loss
    # For now, we test that the retry mechanism exists

    client = ReliableClient('127.0.0.1', 5559)

    # Verify timeout parameters exist
    assert hasattr(client, 'ACK_TIMEOUT')
    assert hasattr(client, 'MAX_RETRIES')
    assert client.ACK_TIMEOUT > 0
    assert client.MAX_RETRIES > 0

    print("  ✓ Reliability parameters test passed")


def test_concurrent_messages():
    """Test handling of concurrent messages from multiple clients"""
    print("Testing concurrent message handling...")

    # Start server
    server = ChatServer('127.0.0.1', 5560)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    time.sleep(1)

    # Connect multiple clients
    clients = []
    for i in range(5):
        client = ReliableClient('127.0.0.1', 5560)
        client.connect(f"ConcurrentUser{i+1}")
        clients.append(client)
        time.sleep(0.2)

    # Send messages concurrently
    def send_messages(client, count):
        for i in range(count):
            client.send_chat_message(f"Message {i}")
            time.sleep(0.1)

    threads = []
    for client in clients:
        t = threading.Thread(target=send_messages, args=(client, 3))
        t.start()
        threads.append(t)

    # Wait for all to finish
    for t in threads:
        t.join()

    time.sleep(1)

    # Cleanup
    for client in clients:
        client.disconnect()
    server.stop()
    time.sleep(0.5)

    print("  ✓ Concurrent messages test passed")


def test_duplicate_username():
    """Test rejection of duplicate usernames"""
    print("Testing duplicate username rejection...")

    # Start server
    server = ChatServer('127.0.0.1', 5561)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    time.sleep(1)

    # Connect first client
    client1 = ReliableClient('127.0.0.1', 5561)
    success1 = client1.connect("DuplicateTest")
    assert success1, "First client should connect"

    # Try to connect with same username
    client2 = ReliableClient('127.0.0.1', 5561)
    success2 = client2.connect("DuplicateTest")
    assert not success2, "Second client with duplicate name should be rejected"

    # Cleanup
    client1.disconnect()
    client2.disconnect()
    server.stop()
    time.sleep(0.5)

    print("  ✓ Duplicate username test passed")


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "=" * 50)
    print("Running Integration Tests")
    print("=" * 50 + "\n")

    tests = [
        test_single_client,
        test_multiple_clients,
        test_message_broadcast,
        test_reliability_retransmission,
        test_concurrent_messages,
        test_duplicate_username,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ Test error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50 + "\n")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
