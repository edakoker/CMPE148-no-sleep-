#!/usr/bin/env python3
"""
Run all tests for the chat application
CMPE 148 - Team No Sleep
"""

import sys
import subprocess

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def run_test(test_file, description):
    """Run a single test file"""
    print("\n" + "="*70)
    print(f"Running: {description}")
    print("="*70 + "\n")

    result = subprocess.run([sys.executable, test_file])

    if result.returncode == 0:
        print(f"\n✓ {description} PASSED")
        return True
    else:
        print(f"\n✗ {description} FAILED")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("CMPE 148 - Custom Chat Protocol Test Suite")
    print("Team No Sleep")
    print("="*70)

    tests = [
        ("tests/test_protocol.py", "Unit Tests (Protocol)"),
        ("tests/test_integration.py", "Integration Tests (Client-Server)"),
    ]

    results = []
    for test_file, description in tests:
        results.append(run_test(test_file, description))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(results)
    total = len(results)

    for i, (test_file, description) in enumerate(tests):
        status = "✓ PASSED" if results[i] else "✗ FAILED"
        print(f"{description}: {status}")

    print(f"\nTotal: {passed}/{total} test suites passed")
    print("="*70 + "\n")

    if passed == total:
        print("🎉 All tests passed! Ready for demo.")
        return 0
    else:
        print("⚠️ Some tests failed. Please review.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
