"""
Stress test for chat application
CMPE 148 - Team No Sleep

Tests performance under load with many clients and messages
Useful for analyzing protocol behavior with Wireshark
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import threading
import time
from server import ChatServer
from client import ReliableClient


def stress_test_many_clients(num_clients=10, messages_per_client=20):
    """
    Stress test with many concurrent clients

    Args:
        num_clients: Number of clients to simulate
        messages_per_client: Messages each client sends
    """
    print(f"\n{'='*60}")
    print(f"STRESS TEST: {num_clients} clients, {messages_per_client} messages each")
    print(f"{'='*60}\n")

    # Start server
    print("[TEST] Starting server...")
    server = ChatServer('127.0.0.1', 5562)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    time.sleep(2)

    # Track statistics
    stats = {
        'clients_connected': 0,
        'clients_failed': 0,
        'messages_sent': 0,
        'messages_failed': 0,
        'total_time': 0,
    }
    stats_lock = threading.Lock()

    def client_worker(client_id):
        """Worker function for each client"""
        username = f"StressUser{client_id}"
        client = ReliableClient('127.0.0.1', 5562)

        try:
            # Connect
            if not client.connect(username):
                with stats_lock:
                    stats['clients_failed'] += 1
                return

            with stats_lock:
                stats['clients_connected'] += 1

            # Send messages
            for i in range(messages_per_client):
                message = f"Message {i} from {username}"
                if client.send_chat_message(message):
                    with stats_lock:
                        stats['messages_sent'] += 1
                else:
                    with stats_lock:
                        stats['messages_failed'] += 1

                time.sleep(0.1)  # Small delay between messages

            # Disconnect
            client.disconnect()

        except Exception as e:
            print(f"[ERROR] Client {client_id}: {e}")
            with stats_lock:
                stats['clients_failed'] += 1

    # Launch all clients
    print(f"[TEST] Launching {num_clients} clients...")
    start_time = time.time()

    threads = []
    for i in range(num_clients):
        t = threading.Thread(target=client_worker, args=(i,))
        t.start()
        threads.append(t)
        time.sleep(0.1)  # Stagger client connections

    # Wait for all clients to finish
    print("[TEST] Waiting for clients to complete...")
    for t in threads:
        t.join()

    end_time = time.time()
    stats['total_time'] = end_time - start_time

    # Print results
    print(f"\n{'='*60}")
    print("STRESS TEST RESULTS")
    print(f"{'='*60}")
    print(f"Clients connected:    {stats['clients_connected']}/{num_clients}")
    print(f"Clients failed:       {stats['clients_failed']}")
    print(f"Messages sent:        {stats['messages_sent']}/{num_clients * messages_per_client}")
    print(f"Messages failed:      {stats['messages_failed']}")
    print(f"Total time:           {stats['total_time']:.2f} seconds")
    print(f"Messages per second:  {stats['messages_sent']/stats['total_time']:.2f}")
    print(f"{'='*60}\n")

    # Cleanup
    server.stop()
    time.sleep(1)

    return stats


def throughput_test(duration_seconds=30):
    """
    Test maximum throughput

    Args:
        duration_seconds: How long to run the test
    """
    print(f"\n{'='*60}")
    print(f"THROUGHPUT TEST: {duration_seconds} seconds")
    print(f"{'='*60}\n")

    # Start server
    server = ChatServer('127.0.0.1', 5563)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    time.sleep(2)

    # Connect a single client
    client = ReliableClient('127.0.0.1', 5563)
    if not client.connect("ThroughputTester"):
        print("[ERROR] Failed to connect client")
        server.stop()
        return

    # Send messages as fast as possible
    print(f"[TEST] Sending messages for {duration_seconds} seconds...")
    message_count = 0
    start_time = time.time()
    end_time = start_time + duration_seconds

    while time.time() < end_time:
        if client.send_chat_message(f"Throughput test message {message_count}"):
            message_count += 1

    elapsed = time.time() - start_time

    # Results
    print(f"\n{'='*60}")
    print("THROUGHPUT TEST RESULTS")
    print(f"{'='*60}")
    print(f"Duration:             {elapsed:.2f} seconds")
    print(f"Messages sent:        {message_count}")
    print(f"Throughput:           {message_count/elapsed:.2f} msg/sec")
    print(f"Avg latency:          {elapsed/message_count*1000:.2f} ms/msg")
    print(f"{'='*60}\n")

    # Cleanup
    client.disconnect()
    server.stop()
    time.sleep(1)


def latency_test(num_messages=100):
    """
    Test message latency (round-trip time)

    Args:
        num_messages: Number of messages to test
    """
    print(f"\n{'='*60}")
    print(f"LATENCY TEST: {num_messages} messages")
    print(f"{'='*60}\n")

    # Start server
    server = ChatServer('127.0.0.1', 5564)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    time.sleep(2)

    # Connect client
    client = ReliableClient('127.0.0.1', 5564)
    if not client.connect("LatencyTester"):
        print("[ERROR] Failed to connect client")
        server.stop()
        return

    # Measure latency for each message
    latencies = []

    print("[TEST] Measuring latencies...")
    for i in range(num_messages):
        start = time.time()
        client.send_chat_message(f"Latency test {i}")
        end = time.time()
        latency_ms = (end - start) * 1000
        latencies.append(latency_ms)

        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{num_messages}")

    # Calculate statistics
    avg_latency = sum(latencies) / len(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)

    # Results
    print(f"\n{'='*60}")
    print("LATENCY TEST RESULTS")
    print(f"{'='*60}")
    print(f"Messages tested:      {num_messages}")
    print(f"Average latency:      {avg_latency:.2f} ms")
    print(f"Min latency:          {min_latency:.2f} ms")
    print(f"Max latency:          {max_latency:.2f} ms")
    print(f"{'='*60}\n")

    # Cleanup
    client.disconnect()
    server.stop()
    time.sleep(1)


def main():
    """Run all stress tests"""
    print("\n" + "="*60)
    print("CHAT APPLICATION STRESS TESTS")
    print("CMPE 148 - Team No Sleep")
    print("="*60)

    # Test 1: Many clients
    stress_test_many_clients(num_clients=5, messages_per_client=10)

    # Test 2: More intensive
    stress_test_many_clients(num_clients=10, messages_per_client=20)

    # Test 3: Throughput
    throughput_test(duration_seconds=10)

    # Test 4: Latency
    latency_test(num_messages=50)

    print("\n" + "="*60)
    print("ALL STRESS TESTS COMPLETED")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
