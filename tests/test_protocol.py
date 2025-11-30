"""
Unit tests for protocol implementation
CMPE 148 - Team No Sleep

Tests protocol message serialization, deserialization, and reliability features
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from protocol import ProtocolMessage, MessageType, MessageBuilder


def test_message_serialization():
    """Test that messages can be serialized and deserialized correctly"""
    print("Testing message serialization...")

    # Create a test message
    original = MessageBuilder.chat_message("Alice", "Hello, World!", 42)

    # Serialize
    data = original.serialize()
    print(f"  Serialized message: {len(data)} bytes")

    # Deserialize
    reconstructed = ProtocolMessage.deserialize(data)

    # Verify
    assert reconstructed is not None, "Deserialization failed"
    assert reconstructed.msg_type == MessageType.CHAT_MSG
    assert reconstructed.sequence_num == 42
    assert reconstructed.payload['username'] == "Alice"
    assert reconstructed.payload['message'] == "Hello, World!"

    print("  ✓ Serialization test passed")


def test_checksum_validation():
    """Test that checksum detects corrupted messages"""
    print("Testing checksum validation...")

    original = MessageBuilder.chat_message("Bob", "Test message", 1)
    data = original.serialize()

    # Corrupt the data
    corrupted = bytearray(data)
    corrupted[-1] ^= 0xFF  # Flip bits in last byte

    # Try to deserialize
    result = ProtocolMessage.deserialize(bytes(corrupted))

    assert result is None, "Corrupted message should fail checksum"
    print("  ✓ Checksum validation test passed")


def test_ack_creation():
    """Test ACK message creation"""
    print("Testing ACK creation...")

    msg = MessageBuilder.chat_message("Charlie", "ACK me", 100)
    ack = msg.create_ack()

    assert ack.msg_type == MessageType.CHAT_ACK
    assert ack.sequence_num == 100  # Same sequence number
    assert ack.payload['ack_for'] == 100

    print("  ✓ ACK creation test passed")


def test_message_types():
    """Test different message types"""
    print("Testing different message types...")

    # Connect message
    connect = MessageBuilder.connect_message("Dave", 1)
    assert connect.msg_type == MessageType.CONNECT

    # Disconnect message
    disconnect = MessageBuilder.disconnect_message("Dave", 2)
    assert disconnect.msg_type == MessageType.DISCONNECT

    # Broadcast message
    broadcast = MessageBuilder.broadcast_message("Eve", "Hello all", 3)
    assert broadcast.msg_type == MessageType.BROADCAST

    # Private message
    private = MessageBuilder.private_message("Frank", "Grace", "Secret", 4)
    assert private.msg_type == MessageType.PRIVATE_MSG
    assert private.payload['recipient'] == "Grace"

    print("  ✓ Message types test passed")


def test_sequence_numbers():
    """Test that different messages have different sequence numbers"""
    print("Testing sequence numbers...")

    msg1 = MessageBuilder.chat_message("User1", "Message 1", 1)
    msg2 = MessageBuilder.chat_message("User1", "Message 2", 2)

    assert msg1.sequence_num != msg2.sequence_num
    print("  ✓ Sequence number test passed")


def test_large_payload():
    """Test handling of large messages"""
    print("Testing large payload...")

    large_message = "x" * 10000  # 10KB message
    msg = MessageBuilder.chat_message("BigSender", large_message, 999)

    # Serialize and deserialize
    data = msg.serialize()
    reconstructed = ProtocolMessage.deserialize(data)

    assert reconstructed is not None
    assert reconstructed.payload['message'] == large_message
    assert len(reconstructed.payload['message']) == 10000

    print("  ✓ Large payload test passed")


def run_all_tests():
    """Run all protocol tests"""
    print("\n" + "=" * 50)
    print("Running Protocol Tests")
    print("=" * 50 + "\n")

    tests = [
        test_message_serialization,
        test_checksum_validation,
        test_ack_creation,
        test_message_types,
        test_sequence_numbers,
        test_large_payload,
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
            failed += 1

    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50 + "\n")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
